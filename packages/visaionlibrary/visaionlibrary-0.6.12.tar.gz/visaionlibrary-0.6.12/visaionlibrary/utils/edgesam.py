import os
import numpy as np
from PIL import Image
import torch

from edge_sam import sam_model_registry, SamPredictor

class EdgeSAM:
    def __init__(self, model_path="edge_sam.pth", device="cuda:0"):
        VISAION_DIR = os.getenv("VISAION_DIR")
        if VISAION_DIR is None:
            raise ValueError("VISAION_DIR is not set")
        self.model_path = os.path.join(VISAION_DIR, "weights", model_path)
        self.device = device

        model_type = "edge_sam"
        self.sam = sam_model_registry[model_type](checkpoint=self.model_path)
        self.sam.to(device=self.device)

        self.predictor = SamPredictor(self.sam)


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

            input_image = np.array(image)   # Image2numpy for EdgeSAM
            self.predictor.set_image(input_image)
            masks, scores, logits = self.predictor.predict(
                point_coords=point_coords,
                point_labels=point_labels,
                num_multimask_outputs=num_multimask_outputs,
                use_stability_score=True
            )

            yield masks, scores, logits


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

            input_image = np.array(image)   # Image2numpy for EdgeSAM
            self.predictor.set_image(input_image)
            input_box = torch.tensor(input_bboxes, device=self.device)
            transformed_boxes = self.predictor.transform.apply_boxes_torch(input_box, input_image.shape[:2])
            masks, scores, logits = self.predictor.predict_torch(
                point_coords=None,
                point_labels=None,
                boxes=transformed_boxes,
                num_multimask_outputs=num_multimask_outputs,
                features=self.predictor.features,
            )

            masks = masks.cpu().numpy() if isinstance(masks, torch.Tensor) else masks
            scores = scores.cpu().numpy() if isinstance(scores, torch.Tensor) else scores
            logits = logits.cpu().numpy() if isinstance(logits, torch.Tensor) else logits
            
            yield masks, scores, logits
