import os
import numpy as np
from PIL import Image
import torch
from visaionlibrary.utils.yoloe import YOLOE
from visaionlibrary.utils.yoloe.models.yolo.yoloe.predict_vp import YOLOEVPSegPredictor


class YoloE:
    def __init__(self, model_path="yoloe-v8l-seg.pt", device="cuda:0"):
        VISAION_DIR = os.getenv("VISAION_DIR")
        if VISAION_DIR is None:
            raise ValueError("VISAION_DIR is not set")
        self.model_path = os.path.join(VISAION_DIR, "weights", model_path)
        self.device = device
        self.model = YOLOE(self.model_path)
        self.model.to(self.device)


    def get_visual_pe(self, prompt_images:list[Image.Image], prompt_boxes:dict[str, list[np.ndarray]], prompt_names:list[str], **kwargs):
        """
        Get visual prompt embeddings from prompt images.
        Args:
            prompt_images: list[Image.Image]
            prompt_boxes: dict[str, list[np.ndarray]]
            prompt_names: list[str]
            **kwargs: dict
        Returns:
            prompt_names: list[list[str]] - flattened list of all class names
            visual_pe: list[np.ndarray] - list of visual prompt embeddings
        """
        assert "bboxes" in prompt_boxes and "cls" in prompt_boxes, f"prompt_boxes must contain 'bboxes' and 'cls'"
        assert len(prompt_images) == len(prompt_boxes["bboxes"]) == len(prompt_boxes["cls"]) == len(prompt_names), f"the length of prompt_image, prompt_boxes['bboxes'], prompt_boxes['cls'], and prompt_names must be the same"

        visual_pe_list = []
        for prompt_image, prompt_box, prompt_cls, prompt_name in zip(prompt_images, prompt_boxes["bboxes"], prompt_boxes["cls"], prompt_names):
            visual_prompt = dict(
                bboxes=prompt_box,
                cls=prompt_cls,
            )

            # Reset predictor before getting vpe to ensure YOLOEVPSegPredictor is used
            self.model.predictor = None
            self.model.predict(prompt_image, prompts=visual_prompt, predictor=YOLOEVPSegPredictor, return_vpe=True, **kwargs)
            # Get vpe from predictor immediately
            vpe = self.model.predictor.vpe
            vpe_np = vpe.detach().cpu().numpy()
            visual_pe_list.append(vpe_np)
        
        return prompt_names, visual_pe_list

    def visual(self, images:list[Image.Image], prompt_names:list[list[str]], visual_pe:list[np.ndarray], **kwargs):
        """
        Predict the visual prompt of the images.
        Args:
            images: list[Image.Image]
            prompt_names: list[list[str]]
            visual_pe: list[np.ndarray]
            **kwargs: dict
        Returns:
            list[Image.Image]
            list[str]
            list[float]
            list[list[float]]
            list[list[list[float]]]
        """
        assert len(prompt_names) == len(visual_pe), f"the length of prompt_names and visual_pe must be the same"

        for prompt_name, vpe_np in zip(prompt_names, visual_pe):
            vpe = torch.from_numpy(vpe_np).to(self.device)
            self.model.set_classes(prompt_name, vpe)
            self.model.predictor = None  # Reset predictor to apply new class count
            # Disable fuse when class count changes to avoid shape mismatch
            results = self.model.predict(images, save=False, fuse=False, **kwargs)
            for image_index,result in enumerate(results):
                classes_index = result.boxes.cls.detach().cpu().numpy()
                class_names = [prompt_name[int(class_index)] for class_index in classes_index]
                confidence = result.boxes.conf.detach().cpu().numpy()
                bboxes = result.boxes.xyxy.detach().cpu().numpy()
                if result.masks is not None:
                    masks = result.masks.cpu().numpy()
                else:
                    masks = None
                yield image_index, class_names, confidence, bboxes, masks

    def get_text_pe(self, prompt:list[str], **kwargs):
        """
        Predict the text prompt of the images.
        Args:
            prompt: list[str]
            **kwargs: dict
        Returns:
            np.ndarray
        """
        assert self.model is not None, "Model is not initialized"
        text_pe = self.model.get_text_pe(prompt)
        text_pe = text_pe.detach().cpu().numpy()
        return prompt, text_pe

    def text(self, images:list[Image.Image], prompt:list[str], text_pe:np.ndarray, **kwargs):
        """
        Predict the visual prompt of the images.
        Args:
            images: list[Image.Image]
            prompt: list[str]
            **kwargs: dict
        Returns:
            list[Image.Image]
            list[str]
            list[float]
            list[list[float]]
            list[list[list[float]]]
        """
        text_pe = torch.from_numpy(text_pe).to(self.device)
        assert text_pe.ndim == 3, "text_pe must be a 3D tensor"
        self.model.set_classes(prompt, text_pe)
        self.model.predictor = None  # Reset predictor to apply new class count
        # Disable fuse when class count changes to avoid shape mismatch
        results = self.model.predict(images, verbose=False, fuse=False, **kwargs)
        for image_index,result in enumerate(results):
            classes_index = result.boxes.cls.detach().cpu().numpy()
            class_names = [prompt[int(class_index)] for class_index in classes_index]
            confidence = result.boxes.conf.detach().cpu().numpy()
            bboxes = result.boxes.xyxy.detach().cpu().numpy()
            if result.masks is not None:
                masks = result.masks.cpu().numpy()
            else:
                masks = None
            yield image_index, class_names, confidence, bboxes, masks

AILabel = YoloE