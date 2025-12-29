import numpy as np
from enum import Enum

try:
    import cupy as cp
    _has_cuda = cp.cuda.is_available()
except ImportError:
    cp = None
    _has_cuda = False
    print("Cupy is not installed or no CUDA device is available. Falling back to NumPy.")


class Device(Enum):
    CPU = "cpu"
    CUDA = "cuda"


nu = np # Default to NumPy
_current_device = Device.CPU # Default device is CPU


def set_device(device: Device) -> None:
    """
    Sets the current device for tensor operations.
    @param device: The device to set, either Device.CPU or Device.CUDA
    """

    global nu, _current_device
    if device == Device.CPU:
        nu = np
    elif device == Device.CUDA:
        if not _has_cuda:
            raise RuntimeError("Cupy is not installed or no CUDA device is available.")
        nu = cp
    else:
        raise ValueError("device must be either Device.CPU or Device.CUDA")
    _current_device = device


def get_device() -> Device:
    """
    Returns the current device being used for tensor operations.
    @return: The current device, either Device.CPU or Device.CUDA
    """
    return _current_device