from typing import Union

import cv2
import numpy as np

from .core._control import CtrlConnection
from .core._deprecated import deprecated
from .core._device import Device
from .core._video import VideoStreamScreenshot


@deprecated(
    """
    This function is deprecated and will be removed in a future version.
    Please use one of the following alternatives:
    
    1. CtrlConnection.screenshot() - for low to medium frequency screenshots (≤25fps)
    2. VideoStreamScreenshot.get_screenshot() - for high frequency screenshots (>25fps)
    
    Performance Tips:
    - Create a connection object once and reuse it for multiple screenshots
    - Avoid creating new connections for each screenshot operation
    
    Example usage:
    # For control-based screenshots (≤25fps)
    ctrl_conn = CtrlConnection(device)
    while True:
        screenshot = ctrl_conn.screenshot()
    
    # For video-based screenshots (high frequency)
    video_conn = VideoStreamScreenshot(device)
    while True:
        screenshot = video_conn.get_screenshot()
    """
)
def screenshot(
    dev_descriptor: Device,
    from_video: bool = False,
    to_bytes: bool = True,
    max_size: int = 1080,
    quality: int = 80,
    timeout: float = 5,
) -> Union[bytes, np.ndarray]:
    """
    Screenshot using control or video connection.

    Args:
        dev_descriptor(Device): device
        from_video (bool, optional): use video connection or control connection. Defaults to False (control connection).
        to_bytes (bool, optional): img format is bytes or np.array. Defaults to True (bytes).
        max_size (int): screenshot max size.
        quality (int): screenshot quality.
        timeout (float): socket timeout.


    Returns:
        Optional[bytes, np.ndarray]: screenshot in bytes or np.array.
    """

    device = dev_descriptor

    if from_video:
        return screenshot_from_video(device, to_bytes, timeout)
    return screenshot_from_ctrl(device, to_bytes, max_size, quality, timeout)


def screenshot_from_ctrl(device: Device, to_bytes: bool, max_size: int, quality: int, timeout: float = 5) -> bytes:
    """
    Screenshot using control connection.

    Args:
        device (Device): device.
        to_bytes (bool, optional): img format is bytes or np.array. Defaults to True (bytes).
        max_size (int): screenshot max size.
        quality (int): screenshot quality.

    Returns:
        bytes: jpeg bytes.
    """

    with CtrlConnection(device=device, timeout=timeout) as conn:
        img = conn.screenshot(max_size, quality)
        if not to_bytes:
            img_array = np.frombuffer(img, dtype=np.uint8)
            return cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        return img


def screenshot_from_video(device: Device, to_bytes: bool, timeout: float = 5) -> np.ndarray:
    """
    Screenshot using video connection.

    Args:
        device (Device): device.
        to_bytes (bool, optional): img format is bytes or np.array. Defaults to True (bytes).
        timeout (float): timeout for waiting for screenshot.

    Returns:
        np.ndarray: jpeg np.ndarray.
    """
    with VideoStreamScreenshot(device=device, timeout=timeout) as conn:
        img = conn.get_screenshot(timeout)
        if to_bytes:
            _, img_bytes = cv2.imencode(".jpg", img)
            return img_bytes.tobytes()
        return img
