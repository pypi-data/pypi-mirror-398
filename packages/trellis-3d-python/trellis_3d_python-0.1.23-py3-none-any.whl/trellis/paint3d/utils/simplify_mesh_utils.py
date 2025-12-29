# Hunyuan 3D is licensed under the TENCENT HUNYUAN NON-COMMERCIAL LICENSE AGREEMENT
# except for the third-party components listed below.
# Hunyuan 3D does not impose any additional limitations beyond what is outlined
# in the repsective licenses of these third-party components.
# Users must comply with all terms and conditions of original licenses of these third-party
# components and must ensure that the usage of the third party components adheres to
# all relevant laws and regulations.

# For avoidance of doubts, Hunyuan 3D means the large language models and
# their software and algorithms, including trained model weights, parameters (including
# optimizer states), machine-learning model code, inference-enabling code, training-enabling code,
# fine-tuning enabling code and other elements of the foregoing made publicly available
# by Tencent in accordance with TENCENT HUNYUAN COMMUNITY LICENSE AGREEMENT.

import trimesh
import pymeshlab


def remesh_mesh(mesh_path, remesh_path):
    mesh = mesh_simplify_trimesh(mesh_path, remesh_path)


def mesh_simplify_trimesh(inputpath, outputpath, target_count=40000):
    # 先去除离散面
    ms = pymeshlab.MeshSet()
    if inputpath.endswith(".glb"):
        ms.load_new_mesh(inputpath, load_in_a_single_layer=True)
    else:
        ms.load_new_mesh(inputpath)
    ms.save_current_mesh(outputpath.replace(".glb", ".obj"), save_textures=False)
    # 调用减面函数
    courent = trimesh.load(outputpath.replace(".glb", ".obj"), force="mesh")
    face_num = courent.faces.shape[0]
    
    if face_num > target_count:
        new_count = max(int(face_num * 0.05), target_count)
        courent = courent.simplify_quadric_decimation(new_count)
    courent.export(outputpath)

def mesh_simplify_trimesh_mesh(
    mesh: trimesh.Trimesh,
    target_count=40000
):
    # trimesh → pymeshlab
    ms = pymeshlab.MeshSet()
    pm_mesh = pymeshlab.Mesh(
        vertex_matrix=mesh.vertices,
        face_matrix=mesh.faces
    )
    ms.add_mesh(pm_mesh)

    # 可在这里做清理
    ms.apply_filter("remove_isolated_pieces_wrt_diameter")

    # pymeshlab → trimesh
    m = ms.current_mesh()
    mesh = trimesh.Trimesh(
        vertices=m.vertex_matrix(),
        faces=m.face_matrix(),
        process=False
    )

    # trimesh 减面
    face_num = mesh.faces.shape[0]
    if face_num > target_count:
        new_count = max(int(face_num * 0.05), target_count)
        mesh = mesh.simplify_quadric_decimation(new_count)
    
    return mesh

