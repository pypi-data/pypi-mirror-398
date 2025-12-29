from ..paint3d.textureGenPipeline import Tri3DPaintPipeline, Tri3DPaintConfig
from ..shape3d.pipelines import Tri3DDiTFlowMatchingPipeline
from typing import *
import shutil
import os
import torch
import torch.nn as nn
from .base import Pipeline
from PIL import Image
import numpy as np
import io
import rembg
from . import samplers
import onnxruntime as ort
import time
import cv2
import onnxruntime as ort
import argparse
from easydict import EasyDict as edict
import os
from ..paint3d.DifferentiableRenderer.mesh_utils import convert_obj_to_glb
from pathlib import Path

class TrellisImageTo3DPipeline(Pipeline):
    """
    Pipeline for inferring Trellis image-to-3D models.
    
    Args:
        models (dict[str, nn.Module]): The models to use in the pipeline.
        sparse_structure_sampler (samplers.Sampler): The sampler for the sparse structure.
        slat_sampler (samplers.Sampler): The sampler for the structured latent.
        slat_normalization (dict): The normalization parameters for the structured latent.
        image_cond_model (str): The name of the image conditioning model.
    """
    def __init__(
        self,
        models: dict[str, nn.Module] = None,
        sparse_structure_sampler: samplers.Sampler = None,
        slat_sampler: samplers.Sampler = None,
        slat_normalization: dict = None,
        image_cond_model: str = None,
    ):
        # if models is None:
        #     return
        # super().__init__(models)
        self.sparse_structure_sampler = sparse_structure_sampler
        self.slat_sampler = slat_sampler
        self.sparse_structure_sampler_params = {}
        self.slat_sampler_params = {}
        self.slat_normalization = slat_normalization
        self.rembg_session = None
        self.shape_pipeline = None
        self.paint_pipeline = None
    
    @staticmethod
    def from_pretrained(path: str) -> "TrellisImageTo3DPipeline":
        """
        Load a pretrained model.

        Args:
            path (str): The path to the model. Can be either local path or a Hugging Face repository.
        """

        shape_pipeline = Tri3DDiTFlowMatchingPipeline.from_single_file(
            ckpt_path=os.path.join(path, "shape/model.fp16.ckpt"),
            config_path=os.path.join(path, "shape/config.yaml"))
        
        current_dir = Path(__file__).resolve().parent
        cus_pip = current_dir.parent / "paint3d" / "tripaintpbr"
        
        # paint model
        max_num_view = 6
        resolution = 512
        conf = Tri3DPaintConfig(max_num_view, resolution)
        conf.realesrgan_ckpt_path = os.path.join(path, "ckpt/RealESRGAN_x4plus.pth")
        conf.multiview_cfg_path = os.path.join(path, "texture/paint.yaml")
        conf.custom_pipeline = str(cus_pip)
        conf.multiview_pretrained_path = path
        conf.dino_ckpt_path =  os.path.join(path, "dinov2-giant")
        conf.model_path = path
        paint_pipeline = Tri3DPaintPipeline(conf)
        
        models = {}
        pipeline = TrellisImageTo3DPipeline(
            models=None,
        )

        pipeline.shape_pipeline = shape_pipeline
        pipeline.paint_pipeline = paint_pipeline
        pipeline.path = path

        return pipeline
    
    def get_main_ratio(self, image):
        rgba = np.array(image)
        alpha = rgba[:, :, 3]
        h, w = alpha.shape
        _, binary = cv2.threshold(alpha, 0, 255, cv2.THRESH_BINARY)
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)

        main_area = np.max(stats[1:, cv2.CC_STAT_AREA])
        main_ratio = main_area / (h * w)

        return main_ratio
    
    def preprocess_image(self, input: Image.Image) -> Image.Image:
        """
        Preprocess the input image.
        """
        providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']

        # if has alpha channel, use it directly; otherwise, remove background
        has_alpha = False
        if input.mode == 'RGBA':
            alpha = np.array(input)[:, :, 3]
            if not np.all(alpha == 255):
                has_alpha = True
        if has_alpha:
            output = input
        else:
            input = input.convert('RGB')
            max_size = max(input.size)
            scale = min(1, 1024 / max_size)
            if scale < 1:
                input = input.resize((int(input.width * scale), int(input.height * scale)), Image.Resampling.LANCZOS)
            # if getattr(self, 'rembg_session', None) is None:
            #     os.environ['U2NET_HOME'] = str(self.path)
            #     self.rembg_session = rembg.new_session('u2net')
            os.environ['U2NET_HOME'] = str(self.path)
            
            if getattr(self, 'rembg_session', None) is None:
                print('使用 u2net !')
                self.rembg_session = rembg.new_session('u2net', providers=providers)
            if getattr(self, 'large_rembg_session', None) is None:
                print('使用 birefnet-general-lite !')
                self.large_rembg_session = rembg.new_session('birefnet-general-lite', providers=providers)
            
            output = rembg.remove(input, session=self.rembg_session)
            large_output = rembg.remove(input, session=self.large_rembg_session)

            main_ratio = self.get_main_ratio(output)
            large_main_ratio = self.get_main_ratio(large_output)

            if float(main_ratio-large_main_ratio) / min(main_ratio, large_main_ratio) <= 0.20:
                output = large_output
            # output = rembg.remove(input, session=self.rembg_session)
        
        output_np = np.array(output)
        alpha = output_np[:, :, 3]
        bbox = np.argwhere(alpha > 0.8 * 255)
        bbox = np.min(bbox[:, 1]), np.min(bbox[:, 0]), np.max(bbox[:, 1]), np.max(bbox[:, 0])
        center = (bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2
        size = max(bbox[2] - bbox[0], bbox[3] - bbox[1])
        size = int(size * 1.2)
        bbox = center[0] - size // 2, center[1] - size // 2, center[0] + size // 2, center[1] + size // 2
        output = output.crop(bbox)  # type: ignore
        output = output.resize((518, 518), Image.Resampling.LANCZOS)
        output = np.array(output).astype(np.float32) / 255
        output = output[:, :, :3] * output[:, :, 3:4]
        output = Image.fromarray((output * 255).astype(np.uint8))
        return output

    @torch.no_grad()
    def run(
        self,
        image: Image.Image,
        num_samples: int = 1,
        seed: int = 42,
        sparse_structure_sampler_params: dict = {},
        slat_sampler_params: dict = {},
        formats: List[str] = ['mesh', 'gaussian', 'radiance_field'],
        preprocess_image: bool = True,
    ) -> dict:
        """
        Run the pipeline.

        Args:
            image (Image.Image): The image prompt.
            num_samples (int): The number of samples to generate.
            seed (int): The random seed.
            sparse_structure_sampler_params (dict): Additional parameters for the sparse structure sampler.
            slat_sampler_params (dict): Additional parameters for the structured latent sampler.
            formats (List[str]): The formats to decode the structured latent to.
            preprocess_image (bool): Whether to preprocess the image.
        """
        if preprocess_image:
            image = self.preprocess_image(image)
        
        mesh_untextured = self.shape_pipeline(image=image)[0]

        output_mesh = self.paint_pipeline(
            mesh_path = mesh_untextured,
            image_path = image,
            output_mesh_path = None
        )
        
        return output_mesh