import os
import numpy as np
from PIL import Image
import torch

from efficientvit.apps.utils import parse_unknown_args
from efficientvit.models.efficientvit.sam import EfficientViTSamAutomaticMaskGenerator, EfficientViTSamPredictor
from efficientvit.models.utils import build_kwargs_from_config
from efficientvit.sam_model_zoo import create_efficientvit_sam_model


class EfficientViTSAM:
    def __init__(self, model_path="efficientvit-sam-xl1", device="cuda:0", pred_iou_thresh=0.8, stability_score_thresh=0.85, min_mask_region_area=10):
        VISAION_DIR = os.getenv("VISAION_DIR")
        if VISAION_DIR is None:
            raise ValueError("VISAION_DIR is not set")

        self.device = device
        self.pred_iou_thresh = pred_iou_thresh
        self.stability_score_thresh = stability_score_thresh
        self.min_mask_region_area = min_mask_region_area
        
        opt = {}  # 额外的参数
        self.efficientvit_sam = create_efficientvit_sam_model(model_path, True)
        self.efficientvit_sam.to(device=self.device).eval()
        self.efficientvit_sam_predictor = EfficientViTSamPredictor(self.efficientvit_sam)
        self.efficientvit_mask_generator = EfficientViTSamAutomaticMaskGenerator(
            self.efficientvit_sam,
            pred_iou_thresh=pred_iou_thresh,
            stability_score_thresh=stability_score_thresh,
            min_mask_region_area=min_mask_region_area,
            **build_kwargs_from_config(opt, EfficientViTSamAutomaticMaskGenerator),
        )

    def predict_by_points(self, images:list[Image.Image], points:list[np.ndarray]=None, labels:list[int]=None, num_multimask_outputs:int=1):
        """
        Predict the masks of the images.
        Args:
            images: list[Image.Image]
            points: list[np.ndarray]
            labels: list[int]
            num_multimask_outputs: int
        Returns:
            masks_list: list[np.ndarray]
            scores_list: list[np.ndarray]
            logits_list: list[np.ndarray]
        """
        if len(images) == 0:
            raise ValueError("The length of images must be greater than 0")
        
        for image, point_coords, point_labels in zip(images, points, labels):
            assert point_coords is not None and point_labels is not None, "point_coords and point_labels must be provided"
            assert len(point_coords) == len(point_labels), "the length of point_coords and point_labels must be the same"
            assert len(point_coords) > 0, "the length of point_coords must be greater than 0"
            assert len(point_coords) == len(point_labels), "the length of point_coords and point_labels must be the same"

            input_image = np.array(image)
            self.efficientvit_sam_predictor.set_image(input_image)
            masks, _, _ = self.efficientvit_sam_predictor.predict(
                point_coords=point_coords,
                point_labels=point_labels,
                multimask_output=True if num_multimask_outputs > 1 else False,
            )

            yield masks, _, _


    def predict_by_bboxes(self, images:list[Image.Image], bboxes:list[np.ndarray]=None, num_multimask_outputs:int=1):
        """
        Predict the masks of the images.
        Args:
            images: list[Image.Image]
            bboxes: list[np.ndarray]
            num_multimask_outputs: int
        Returns:
            masks_list: list[np.ndarray]
            scores_list: list[np.ndarray]
            logits_list: list[np.ndarray]
        """
        if len(images) == 0:
            raise ValueError("The length of images must be greater than 0")
        
        for image, input_bboxes in zip(images, bboxes):
            assert input_bboxes is not None, "bbox must be provided"

            input_image = np.array(image)
            self.efficientvit_sam_predictor.set_image(input_image)

            # predict好像只能一个一个推理，TODO: 优化
            masks_list = []
            for input_bbox in input_bboxes:
                masks, _, _ = self.efficientvit_sam_predictor.predict(
                    point_coords=None,
                    point_labels=None,
                    box=np.array(input_bbox),
                    multimask_output=True if num_multimask_outputs > 1 else False,
                )
                masks = masks[None, :, :, :] if masks.ndim == 3 else masks
                masks_list.append(masks)
            
            
            masks_r = np.concatenate(masks_list, axis=0)



            masks_r = masks_r.cpu().numpy() if isinstance(masks_r, torch.Tensor) else masks_r
            
            yield masks_r, _, _
