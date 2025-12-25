from .core._log import ScrcpyLogger

# 创建全局实例
scrcpy_logger = ScrcpyLogger(__package__)

from .api import screenshot
from .const import Action, CopyKey, KeyCode, PowerMode

# from .core._audio import AudioConnection, realtime_playback, record_to_file
from .core._control import CtrlConnection
from .core._device import AndroidDevice, Device, IOSDevice, LocalDevice
from .core._video import VideoStreamScreenshot

__all__ = [
    "Device",
    "AndroidDevice",
    "IOSDevice",
    "LocalDevice",
    "CtrlConnection",
    # "AudioConnection",
    # "realtime_playback",
    # "record_to_file",
    "screenshot",
    "VideoStreamScreenshot",
    "Action",
    "CopyKey",
    "KeyCode",
    "PowerMode",
    "scrcpy_logger",
]
