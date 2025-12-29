"""Monkey patches to update/extend functionality of existing functions."""

import time
from pathlib import Path

import cv2
import numpy as np
import torch

# OpenCV Multilanguage-friendly functions ------------------------------------------------------------------------------
_imshow = cv2.imshow  # copy to avoid recursion errors


def imread(filename: str, flags: int = cv2.IMREAD_COLOR):
    """
    Read an image from a file.

    Args:
        filename (str): Path to the file to read.
        flags (int, optional): Flag that can take values of cv2.IMREAD_*. Defaults to cv2.IMREAD_COLOR.

    Returns:
        (np.ndarray): The read image.
    """
    return cv2.imdecode(np.fromfile(filename, np.uint8), flags)


def imwrite(filename: str, img: np.ndarray, params=None):
    """
    Write an image to a file.

    Args:
        filename (str): Path to the file to write.
        img (np.ndarray): Image to write.
        params (list of ints, optional): Additional parameters. See OpenCV documentation.

    Returns:
        (bool): True if the file was written, False otherwise.
    """
    try:
        cv2.imencode(Path(filename).suffix, img, params)[1].tofile(filename)
        return True
    except Exception:
        return False


def imshow(winname: str, mat: np.ndarray):
    """
    Displays an image in the specified window.

    Args:
        winname (str): Name of the window.
        mat (np.ndarray): Image to be shown.
    """
    _imshow(winname.encode("unicode_escape").decode(), mat)


# PyTorch functions ----------------------------------------------------------------------------------------------------
import pickle

_torch_load = torch.load  # copy to avoid recursion errors
_torch_save = torch.save


class _ModuleRedirectUnpickler(pickle.Unpickler):
    """Custom Unpickler that redirects module paths for backward compatibility."""
    
    def find_class(self, module, name):
        """Redirect old module paths to new ones."""
        # Module path mappings for backward compatibility
        module_mappings = {
            "ultralytics": "visaionlibrary.utils.yoloe",
            "ultralytics.yolo": "visaionlibrary.utils.yoloe",
            "ultralytics.yolo.utils": "visaionlibrary.utils.yoloe.utils",
            "ultralytics.yolo.v8": "visaionlibrary.utils.yoloe.yolo.v8",
            "ultralytics.yolo.data": "visaionlibrary.utils.yoloe.yolo.data",
            "ultralytics.nn": "visaionlibrary.utils.yoloe.nn",
            "ultralytics.nn.tasks": "visaionlibrary.utils.yoloe.nn.tasks",
            "ultralytics.nn.modules": "visaionlibrary.utils.yoloe.nn.modules",
            "ultralytics.models": "visaionlibrary.utils.yoloe.models",
            "ultralytics.utils": "visaionlibrary.utils.yoloe.utils",
        }
        
        # Check if we need to redirect the module
        if module in module_mappings:
            module = module_mappings[module]
        else:
            # Check for partial matches (e.g., ultralytics.nn.modules.conv -> visaionlibrary.utils.yoloe.nn.modules.conv)
            for old_prefix, new_prefix in module_mappings.items():
                if module.startswith(old_prefix + "."):
                    module = module.replace(old_prefix, new_prefix, 1)
                    break
        
        return super().find_class(module, name)


def torch_load(*args, **kwargs):
    """
    Load a PyTorch model with updated arguments to avoid warnings and module path redirects.

    This function wraps torch.load and adds the 'weights_only' argument for PyTorch 1.13.0+ to prevent warnings.
    It also uses a custom Unpickler to redirect old module paths to new ones for backward compatibility.

    Args:
        *args (Any): Variable length argument list to pass to torch.load.
        **kwargs (Any): Arbitrary keyword arguments to pass to torch.load.

    Returns:
        (Any): The loaded PyTorch object.

    Note:
        For PyTorch versions 2.0 and above, this function automatically sets 'weights_only=False'
        if the argument is not provided, to avoid deprecation warnings.
    """
    from visaionlibrary.utils.yoloe.utils.torch_utils import TORCH_1_13

    if TORCH_1_13 and "weights_only" not in kwargs:
        kwargs["weights_only"] = False

    # Use custom unpickler for module path redirection
    # Note: weights_only=True and pickle_module cannot be used together
    # Only add pickle_module if weights_only is not True
    if "pickle_module" not in kwargs and kwargs.get("weights_only") is not True:
        import pickle
        import types
        
        # Create a custom pickle module with our Unpickler
        custom_pickle = types.ModuleType("custom_pickle")
        custom_pickle.Unpickler = _ModuleRedirectUnpickler
        custom_pickle.load = lambda f: _ModuleRedirectUnpickler(f).load()
        
        # For other pickle functions, use the standard ones
        for attr in dir(pickle):
            if not hasattr(custom_pickle, attr):
                setattr(custom_pickle, attr, getattr(pickle, attr))
        
        kwargs["pickle_module"] = custom_pickle

    return _torch_load(*args, **kwargs)


def torch_save(*args, **kwargs):
    """
    Optionally use dill to serialize lambda functions where pickle does not, adding robustness with 3 retries and
    exponential standoff in case of save failure.

    Args:
        *args (tuple): Positional arguments to pass to torch.save.
        **kwargs (Any): Keyword arguments to pass to torch.save.
    """
    for i in range(4):  # 3 retries
        try:
            return _torch_save(*args, **kwargs)
        except RuntimeError as e:  # unable to save, possibly waiting for device to flush or antivirus scan
            if i == 3:
                raise e
            time.sleep((2**i) / 2)  # exponential standoff: 0.5s, 1.0s, 2.0s
