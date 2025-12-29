import os

# Set ENV variables (place before imports)
if not os.environ.get("OMP_NUM_THREADS"):
    os.environ["OMP_NUM_THREADS"] = "1"  # default for reduced CPU utilization during training

from visaionlibrary.utils.yoloe.models import YOLO, YOLOE
from visaionlibrary.utils.yoloe.utils.checks import check_yolo as checks

__all__ = (
    "YOLO",
    "YOLOE",
    "checks",
)
