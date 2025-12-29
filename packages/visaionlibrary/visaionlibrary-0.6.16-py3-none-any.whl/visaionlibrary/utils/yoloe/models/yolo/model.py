from pathlib import Path

from visaionlibrary.utils.yoloe.engine.model import Model  
from visaionlibrary.utils.yoloe.models import yolo
from visaionlibrary.utils.yoloe.nn.tasks import DetectionModel, SegmentationModel, YOLOEModel, YOLOESegModel


class YOLO(Model):
    """YOLO (You Only Look Once) object detection model."""

    def __init__(self, model="yolo11n.pt", task=None, verbose=False):
        """Initialize YOLO model, switching to YOLOE if model filename contains 'yoloe'."""
        path = Path(model)
        if "yoloe" in path.stem and path.suffix in {".pt", ".yaml", ".yml"}:
            new_instance = YOLOE(path, task=task, verbose=verbose)
            self.__class__ = type(new_instance)
            self.__dict__ = new_instance.__dict__
        else:
            # Continue with default YOLO initialization
            super().__init__(model=model, task=task, verbose=verbose)

    @property
    def task_map(self):
        """Map head to model and predictor classes."""
        return {
            "detect": {
                "model": DetectionModel,
                "predictor": yolo.detect.DetectionPredictor,
            },
            "segment": {
                "model": SegmentationModel,
                "predictor": yolo.segment.SegmentationPredictor,
            },
        }


class YOLOE(Model):
    """YOLOE object detection and segmentation model."""

    def __init__(self, model="yoloe-v8s-seg.pt", task=None, verbose=False) -> None:
        """
        Initialize YOLOE model with a pre-trained model file.

        Args:
            model (str | Path): Path to the pre-trained model file. Supports *.pt and *.yaml formats.
            verbose (bool): If True, prints additional information during initialization.
        """
        super().__init__(model=model, task=task, verbose=verbose)

    @property
    def task_map(self):
        """Map head to model and predictor classes."""
        return {
            "detect": {
                "model": YOLOEModel,
                "predictor": yolo.detect.DetectionPredictor,
            },
            "segment": {
                "model": YOLOESegModel,
                "predictor": yolo.segment.SegmentationPredictor,
            },
        }

    def get_text_pe(self, texts):
        assert(isinstance(self.model, YOLOEModel))
        return self.model.get_text_pe(texts)
    
    def get_visual_pe(self, img, visual):
        assert(isinstance(self.model, YOLOEModel))
        return self.model.get_visual_pe(img, visual)

    def set_vocab(self, vocab, names):
        assert(isinstance(self.model, YOLOEModel))
        self.model.set_vocab(vocab, names=names)
    
    def get_vocab(self, names):
        assert(isinstance(self.model, YOLOEModel))
        return self.model.get_vocab(names)

    def set_classes(self, classes, embeddings):
        """
        Set classes.

        Args:
            classes (List(str)): A list of categories i.e. ["person"].
        """
        assert(isinstance(self.model, YOLOEModel))
        self.model.set_classes(classes, embeddings)
        # Remove background if it's given
        assert(" " not in classes)
        self.model.names = classes

        # Reset method class names
        # self.predictor = None  # reset predictor otherwise old names remain
        if self.predictor:
            self.predictor.model.names = classes
