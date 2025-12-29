from ..paint3d.DifferentiableRenderer.mesh_utils import convert_obj_to_glb
import tempfile
import os
import trimesh
import bpy
import math
import mathutils
import numpy as np
import io
from PIL import Image
import glob
from trimesh.transformations import rotation_matrix
import numpy as np
import shutil

def to_glb(
    mesh,
    simplify: float = 0.95,
    fill_holes: bool = True,
    fill_holes_max_size: float = 0.04,
    texture_size: int = 1024,
    debug: bool = False,
    verbose: bool = True,):

    # 创建临时 glb 文件
    with tempfile.NamedTemporaryFile(suffix=".glb", delete=False) as f:
        tmp_glb = f.name
    
    convert_obj_to_glb('textured_mesh.obj', tmp_glb)

    with open(tmp_glb, 'rb') as f:
        glb_data = f.read()
    
    # # frames
    # frames = get_image(tmp_glb)

    # # 用完删除（可选）
    # if os.path.exists(tmp_glb):
    #     os.remove(tmp_glb)
    
    # for name in ["textured_mesh.mtl", "textured_mesh.jpg", "textured_mesh.obj"]:
    #     if os.path.exists(name):
    #         os.remove(name)
    
    return [glb_data, 0, 0]

def to_thumbnail(gaussian):

    

    return ''

def to_stl(mesh):

    mesh.apply_scale(100.0)
    center = mesh.centroid
    R = rotation_matrix(np.radians(90), [1,0,0], center)
    mesh.apply_transform(R)

    return mesh

def to_gif(gaussian):
    
    return ''

def get_image(glb_path):

    # =============================
    # 路径配置
    # =============================
    out_dir = bpy.path.abspath("//frames")  # Blender 相对路径 → 真实路径
    frame_prefix = "frame_"                 # 文件名前缀
    os.makedirs(out_dir, exist_ok=True)

    # =============================
    # 新建干净场景 + 导入 GLB
    # =============================
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=glb_path)

    # =============================
    # 统一环境光（无阴影、稳定）
    # =============================
    def init_uniform_lighting():
        # 删除所有灯光
        bpy.ops.object.select_all(action="DESELECT")
        bpy.ops.object.select_by_type(type="LIGHT")
        bpy.ops.object.delete()

        # 创建 World
        if bpy.context.scene.world is None:
            world = bpy.data.worlds.new("World")
            bpy.context.scene.world = world
        else:
            world = bpy.context.scene.world

        world.use_nodes = True
        nodes = world.node_tree.nodes
        links = world.node_tree.links

        nodes.clear()

        bg = nodes.new(type="ShaderNodeBackground")
        bg.inputs["Color"].default_value = (1, 1, 1, 1)
        bg.inputs["Strength"].default_value = 1.0

        out = nodes.new(type="ShaderNodeOutputWorld")
        links.new(bg.outputs["Background"], out.inputs["Surface"])

    init_uniform_lighting()

    # =============================
    # 计算场景 bbox（世界坐标）
    # =============================
    all_objects = [o for o in bpy.context.scene.objects if o.type == 'MESH']

    min_corner = mathutils.Vector((1e9, 1e9, 1e9))
    max_corner = mathutils.Vector((-1e9, -1e9, -1e9))

    for obj in all_objects:
        for v in obj.bound_box:
            coord = obj.matrix_world @ mathutils.Vector(v)
            min_corner.x = min(min_corner.x, coord.x)
            min_corner.y = min(min_corner.y, coord.y)
            min_corner.z = min(min_corner.z, coord.z)
            max_corner.x = max(max_corner.x, coord.x)
            max_corner.y = max(max_corner.y, coord.y)
            max_corner.z = max(max_corner.z, coord.z)

    center = (min_corner + max_corner) / 2
    bbox_size = max_corner - min_corner
    bbox_w, bbox_d, bbox_h = bbox_size

    # =============================
    # Turntable（让模型转）
    # =============================
    turntable = bpy.data.objects.new("Turntable", None)
    turntable.location = center
    bpy.context.collection.objects.link(turntable)

    for obj in all_objects:
        obj.parent = turntable

    # =============================
    # 创建相机
    # =============================
    cam_data = bpy.data.cameras.new("Camera")
    cam_obj = bpy.data.objects.new("Camera", cam_data)
    bpy.context.collection.objects.link(cam_obj)

    # 相机 FOV → 距离（bbox 驱动）
    fov = cam_data.angle_y
    margin = 1.2
    d = max(bbox_d, bbox_h, bbox_w)
    distance = (d * margin) / (2 * math.tan(fov / 2))

    cam_obj.location = center + mathutils.Vector((
        0,
        -distance,
        d * 0.5
    ))

    # 相机看向模型中心
    direction = center - cam_obj.location
    cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

    bpy.context.scene.camera = cam_obj

    # =============================
    # Turntable 动画（360°）
    # =============================
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = 12
    scene.render.fps = 24

    turntable.rotation_euler = (0, 0, 0)
    turntable.keyframe_insert("rotation_euler", frame=scene.frame_start)

    turntable.rotation_euler = (
        0, 0,
        math.radians(360 * (scene.frame_end - 1) / scene.frame_end)
    )
    turntable.keyframe_insert("rotation_euler", frame=scene.frame_end)

    # =============================
    # 渲染设置（PNG + 透明）
    # =============================
    scene.render.engine = 'CYCLES'
    scene.render.film_transparent = True
    scene.cycles.samples = 16          # 原来 ~128
    scene.cycles.preview_samples = 8
    scene.cycles.use_denoising = True  # 开启去噪
    scene.render.use_persistent_data = True

    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.render.image_settings.color_depth = '8'

    scene.render.resolution_x = 512
    scene.render.resolution_y = 512

    for frame in range(scene.frame_start, scene.frame_end + 1):
        scene.frame_set(frame)
        scene.render.filepath = os.path.join(
            out_dir,
            f"{frame_prefix}{frame:04d}.png"
        )
        bpy.ops.render.render(write_still=True)

    frame_paths = sorted(glob.glob("frames/frame_*.png"))
    frames = [Image.open(p).convert("RGBA") for p in frame_paths]

    # 清空旧帧文件
    if os.path.exists(out_dir):
        if os.path.isdir(out_dir):
            shutil.rmtree(out_dir)
    
    return frames