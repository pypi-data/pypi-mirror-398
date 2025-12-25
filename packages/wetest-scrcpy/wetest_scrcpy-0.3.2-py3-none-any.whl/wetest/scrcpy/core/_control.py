import logging
import struct
import time
from functools import cached_property, wraps
from typing import TYPE_CHECKING, Optional, Union

from pydantic import BaseModel

from ..const import (
    Action,
    ControlMessageType,
    ControlType,
    CopyKey,
    DeviceMessageType,
    KeyCode,
    PowerMode,
)
from ..core._exceptions import ProtocolError
from ..core._socket import StreamSocket
from ._device import Device

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    import numpy as np


class ScreenInfo(BaseModel):
    Width: int
    Height: int
    Rotate: int


class AppInfo(BaseModel):
    PackageName: str
    VersionCode: int
    VersionName: str


# 当前只重试一次
def retry(operation_name: str):
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except (ConnectionError, BrokenPipeError, OSError) as e:
                logger.warning(f"Socket {operation_name} failed, reconnecting: {e}")
                self._sock = self._device.restart_socket_connection(self._sock, "ctrl")
                self._sock.settimeout(self._timeout)
                return func(self, *args, **kwargs)

        return wrapper

    return decorator


class CtrlConnection(StreamSocket):
    def __init__(self, device: Device, timeout: float = 5):
        self._device = device
        self._timeout = timeout
        self._sock = self._device.restart_socket_connection(None, "ctrl")
        self._sock.settimeout(self._timeout)
        super().__init__(self._sock)

    @retry("write")
    def write(self, data: bytes):
        logger.debug(f"write data len: {len(data)}")
        return super().write(data)

    @retry("read")
    def read(self, size: int) -> bytes:
        return super().read(size)

    @cached_property
    def screen_info(self) -> ScreenInfo:
        """获取屏幕信息，支持懒加载"""
        return self.get_screen_info()

    def refresh_screen_info(self):
        """屏幕旋转后使用"""
        if hasattr(self, "screen_info"):
            delattr(self, "screen_info")

    def _send_control_msg(self, control_type: ControlType, msg: bytes = b"") -> bytes:
        """发送控制消息"""
        logger.info(f"send control type: {control_type.name} ({control_type.value})")
        package = struct.pack(">B", control_type) + msg
        self.write(package)
        return package

    def keycode(self, keycode: KeyCode, action: int = Action.DOWN, repeat: int = 0, meta: int = 0) -> bytes:
        """
        Send keycode to device

        Args:
            keycode: KeyCode.*
            action: Action.DOWN | Action.UP
            repeat: repeat count
        """
        msg = struct.pack(">Biii", action, keycode, repeat, meta)
        return self._send_control_msg(ControlType.INJECT_KEYCODE, msg)

    def press_button(self, keycode: KeyCode, delay: float = 0.1):
        self.keycode(keycode, Action.DOWN)
        delay = 0.1 if delay <= 0 else delay
        time.sleep(delay)
        self.keycode(keycode, Action.UP)

    def text(self, text: str) -> bytes:
        """
        Send text to device

        Args:
            text: text to send
        """

        buffer = text.encode("utf-8")
        msg = struct.pack(">i", len(buffer)) + buffer
        return self._send_control_msg(ControlType.INJECT_TEXT, msg)

    def touch(
        self,
        x: Union[float, int],
        y: Union[float, int],
        action: Action = Action.DOWN,
        screen_info: ScreenInfo = None,
        touch_id: int = -1,
    ) -> bytes:
        """
        Touch screen

        Args:
            x: horizontal position
            y: vertical position
            screen_info: ScreenInfo
                1. 使用比例坐标(0-1)，内部会根据当前设备屏幕尺寸进行转换
                2. 使用真实坐标
                2.1 screen_info 为空，使用当前设备屏幕尺寸和坐标
                2.2 screen_info 不为空，使用传入的屏幕尺寸和坐标，进行比例转换
            action: ACTION_DOWN | ACTION_UP | ACTION_MOVE
            touch_id: 用于模拟多指触控, 最多支持10个点。到达10个点后, 除非释放已按下的点, 否则不会触发其他点的事件
                1. 每个touch id 对应一个点
                2. touch id 无实际含义, 默认使用-1
        """
        if screen_info is None:
            screen_info = self.screen_info
        x, y = min(max(x, 0), screen_info.Width), min(max(y, 0), screen_info.Height)
        # 使用比例坐标
        if x <= 1.0 and y <= 1.0:
            x = x * screen_info.Width
            y = y * screen_info.Height
        msg = struct.pack(
            ">BqiiHHHi", action, touch_id, int(x), int(y), screen_info.Width, screen_info.Height, 0xFFFF, 1
        )
        return self._send_control_msg(ControlType.INJECT_TOUCH_EVENT, msg)

    def scroll(self, x: int, y: int, h: int, v: int) -> bytes:
        """
        Scroll screen

        - 存在兼容性问题，有些app(如百度地图)不支持注入scroll，可以使用swipe代替
        - 如果x或y超过屏幕尺寸，scroll注入无效

        Args:
            x: horizontal position
            y: vertical position
            h: horizontal movement
            v: vertical movement
        """

        x, y = max(x, 0), max(y, 0)
        msg = struct.pack(
            ">iiHHiii",
            int(x),
            int(y),
            int(self.screen_info.Width),
            int(self.screen_info.Height),
            int(h),
            int(v),
            1,  # Buttons
        )
        self._send_control_msg(ControlType.INJECT_SCROLL_EVENT, msg)

    def swipe(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        move_step_length: int = 5,
        move_steps_delay: float = 0.005,
    ) -> None:
        """
        Swipe on screen

        Args:
            start_x: start horizontal position
            start_y: start vertical position
            end_x: start horizontal position
            end_y: end vertical position
            move_step_length: length per step
            move_steps_delay: sleep seconds after each step
        :return:
        """

        self.touch(start_x, start_y, Action.DOWN)
        next_x = start_x
        next_y = start_y

        end_x = min(end_x, self.screen_info.Width)
        end_y = min(end_y, self.screen_info.Height)

        while next_x != end_x or next_y != end_y:
            if next_x != end_x:
                step = move_step_length if next_x < end_x else -move_step_length
                next_x = end_x if abs(next_x - end_x) <= move_step_length else next_x + step

            if next_y != end_y:
                step = move_step_length if next_y < end_y else -move_step_length
                next_y = end_y if abs(next_y - end_y) <= move_step_length else next_y + step

            self.touch(next_x, next_y, Action.MOVE)

            if next_x == end_x and next_y == end_y:
                self.touch(next_x, next_y, Action.UP)
                break
            time.sleep(move_steps_delay)

    def back_or_turn_screen_on(self, action: int = Action.DOWN) -> bytes:
        """
        1. 当屏幕开启时，
            back_or_turn_screen_on(Action.DOWN) + back_or_turn_screen_on(Action.UP)
            等价于
            press_button(KeyCode.BACK)
        2. 当屏幕关闭时，
            back_or_turn_screen_on(Action.DOWN) 点亮屏幕
            back_or_turn_screen_on(Action.UP) 不执行任何操作

        Args:
            action: ACTION.DOWN | ACTION.UP
        """
        msg = struct.pack(">B", action)
        return self._send_control_msg(ControlType.BACK_OR_SCREEN_ON, msg)

    def expand_notification_panel(self) -> bytes:
        """
        Expand notification panel
        """
        return self._send_control_msg(ControlType.EXPAND_NOTIFICATION_PANEL, b"")

    def expand_settings_panel(self) -> bytes:
        """
        Expand settings panel
        """
        return self._send_control_msg(ControlType.EXPAND_SETTINGS_PANEL, b"")

    def collapse_panels(self) -> bytes:
        """
        Collapse all panels
        """
        return self._send_control_msg(ControlType.COLLAPSE_PANELS, b"")

    def set_clipboard(self, text: str, paste: bool = False, sequence: int = 0) -> bytes:
        """
        Set clipboard

        - 在Android < 7, 不支持paste
            ref: scrcpy/server/src/main/java/com/genymobile/scrcpy/control/Controller.java:682

        Args:
            text: the string you want to set
            paste: paste now
            sequence: 0 means no ack, others need read ACK from server
        """
        buffer = text.encode("utf-8")
        msg = struct.pack(">q?i", sequence, paste, len(buffer)) + buffer
        return self._send_control_msg(ControlType.SET_CLIPBOARD, msg)

    def set_screen_power_mode(self, mode: int = PowerMode.NORMAL) -> bytes:
        """
        Set screen power mode
        PowerMode.NORMAL: 亮屏
        PowerMode.OFF: 熄屏

        Args:
            mode: PowerMode.NORMAL | PowerMode.OFF
        """
        msg = struct.pack(">b", mode)
        return self._send_control_msg(ControlType.SET_SCREEN_POWER_MODE, msg)

    def rotate_device(self) -> bytes:
        """
        Rotate device
        """
        return self._send_control_msg(ControlType.ROTATE_DEVICE, b"")

    def set_locale(self, locale: str) -> bytes:
        """
        Set device locale
        """
        locale = locale.encode("utf-8")
        msg = struct.pack(">i", len(locale)) + locale
        return self._send_control_msg(ControlMessageType.SET_LOCALE, msg)

    def read_device_msg(self) -> Optional[Union[str, bytes, int, BaseModel]]:
        (typ,) = struct.unpack(">B", self.read(1))
        try:
            device_msg_name = DeviceMessageType(typ).name
        except ValueError:
            device_msg_name = "unknown"
        logger.info(f"recv device msg type: {device_msg_name} ({typ})")

        if typ == DeviceMessageType.CLIPBOARD or typ == DeviceMessageType.GET_LOCALE:
            return self.read_frame().decode("utf-8")
        elif typ == DeviceMessageType.CAPTURE:
            return self.read_frame()
        elif typ == DeviceMessageType.GET_ROTATION:
            (rotation,) = struct.unpack(">i", self.read(4))
            return rotation
        elif typ == DeviceMessageType.GET_SCREENINFO:
            (width, height, rotation) = struct.unpack(">iii", self.read(12))
            return ScreenInfo(Width=width, Height=height, Rotate=rotation)
        elif typ == DeviceMessageType.GET_APPS:
            resp = self.read_frame()
            resp_str = resp.decode("utf-8").strip()
            apps = []
            app_entries = [entry.strip() for entry in resp_str.split(";") if entry.strip()]
            for entry in app_entries:
                parts = entry.split(",")
                package_name, version_code, version_name = parts
                apps.append(AppInfo(PackageName=package_name, VersionCode=version_code, VersionName=version_name))
            return apps
        else:
            logger.debug(f"ignore device msg type: {device_msg_name} ({typ})")

    def get_screen_info(self) -> ScreenInfo:
        """
        Get device's screen info
        """
        self.write(struct.pack(">b", ControlMessageType.GET_SCREENINFO))
        msg = self.read_device_msg()
        if isinstance(msg, ScreenInfo):
            logger.info(f"screen info: {msg}")
            return msg
        else:
            raise ProtocolError(f"invalid type:{type(msg)}")

    def get_rotation(self) -> int:
        """
        Get device's screen info
        """
        self.write(struct.pack(">b", ControlMessageType.GET_ROTATION))
        return self.read_device_msg()

    def screenshot(self, max_size: int = 1080, quality: int = 80) -> "np.ndarray":
        """
        - 适用于<=25fps的场景，对于需要高速截图的场景，请使用 VideoStreamScreenshot 类
        - 避免频繁切换max_size/ quality，会显著降低截图速度。如需多种尺寸，建议使用最高画质截图后自行缩放处理

        Args:
            max_size: 截图的最大尺寸，默认1080。
            如果屏幕的宽高超过 max_size
                - 按比例缩放到不超过 max_size
                - 保持原始宽高比不变
                - 最终尺寸会调整为 8 的倍数（ round8() ）以满足编码器要求
            如果屏幕的宽高小于max_size，不缩放，保持原始尺寸不变
            quality: 截图的质量，默认80，范围[1, 100]，底层使用 turbojpeg 库进行压缩

        Returns:
            BGR格式的numpy数组
        """
        import cv2
        import numpy as np

        self.write(struct.pack(">bii", ControlMessageType.CAPTURE, max_size, quality))
        # 与 video 返回保持一致，返回 numpy.array
        img_bytes = self.read_device_msg()
        img_array = np.frombuffer(img_bytes, dtype=np.uint8)
        return cv2.imdecode(img_array, cv2.IMREAD_COLOR)

    def get_locale(self) -> str:
        """
        Get a screenshot, jpeg bytes
        """
        self.write(struct.pack(">b", ControlMessageType.GET_LOCALE))
        return self.read_device_msg()

    def get_clipboard(self, copy_key: int = CopyKey.NONE) -> str:
        """
        Get clipboard
        - Android < 7, 不支持copy_key=COPY/ CUT
            ref: scrcpy/server/src/main/java/com/genymobile/scrcpy/control/Controller.java:655

        CopyKey.NONE: 无操作，直接读取剪切板内容
        CopyKey.COPY: 当前已选中一段内容，复制这段内容
        CopyKey.CUT: 当前已选中一段内容，剪切这段内容
        """
        # server 启动参数需要有`clipboard_autosync=false`，否则会一直阻塞无返回
        self.write(struct.pack(">bb", ControlType.GET_CLIPBOARD, copy_key))
        return self.read_device_msg()

    def list_apps(self):
        self.write(struct.pack(">b", ControlMessageType.GET_APPS))
        return self.read_device_msg()

    def heartbeat(self):
        self.write(struct.pack(">b", ControlMessageType.HEARTBEAT))
        return self.read_device_msg()
