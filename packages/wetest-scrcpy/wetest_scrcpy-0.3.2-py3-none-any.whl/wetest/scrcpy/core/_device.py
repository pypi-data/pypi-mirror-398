import logging
import socket
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Final, Optional, Tuple

from ._exceptions import ProtocolError, SocketError

if TYPE_CHECKING:
    import adbutils

logger = logging.getLogger(__name__)
SOCKET_TYPES: Final[Tuple[str]] = ("ctrl", "video", "audio")


@dataclass
class Device(ABC):
    """设备描述符基类"""

    def create_connection(self, stream_type: str) -> socket.socket:
        """校验流类型并创建连接"""
        if stream_type not in SOCKET_TYPES:
            raise ProtocolError(f"Invalid stream type: {stream_type}")
        return self._create_device_connection(stream_type)

    @abstractmethod
    def _create_device_connection(self, stream_type: str) -> socket.socket:
        """创建连接"""
        pass

    @abstractmethod
    def start_scrcpy(self) -> bool:
        """启动 scrcpy"""
        pass

    def restart_socket_connection(self, sock: socket.socket, stream_type: str) -> socket.socket:
        """确保socket连接可用，按需拉起server"""
        if self._is_socket_health(sock):
            return sock
        # self._sock 不可用，清理无效连接
        if sock:
            sock.close()

        try:
            # 尝试直接连接
            sock = self.create_connection(stream_type)
            logger.debug("Connected to scrcpy server")
        except ProtocolError:
            # socket name 错误，直接抛出异常
            raise
        except Exception:
            if not self.start_scrcpy():
                logger.debug("Launch server failed", exc_info=True)
                raise SocketError("Launch server failed")
            # 重新尝试连接
            sock = self.create_connection(stream_type)
            logger.debug("Restart scrcpy server and connected")
        return sock

    def _is_socket_health(self, sock: socket.socket) -> bool:
        """检查socket连接是否正常"""
        if not isinstance(sock, socket.socket) or sock.fileno() == -1:
            return False

        try:
            data = sock.recv(1, socket.MSG_PEEK)
            if data == b"":
                # 连接已断开
                logger.debug("Socket connection closed")
                return False
            else:
                # 连接正常，有数据可读
                logger.debug(f"Socket connection is healthy")
                return True
        except BlockingIOError:
            # 连接正常，无数据可读
            logger.debug(f"Socket connection is health, no data available")
            return True
        except Exception as e:
            logger.debug(f"Socket connection closed, error: {e}")
            return False


@dataclass
class AndroidDevice(Device):
    """Android 设备描述符"""

    serial: str = ""
    sock_prefix: str = "ct-scrcpy"

    def __post_init__(self):
        # 避免用户初始化时对 _server_stream 赋值
        # _server_stream 用于管理 scrcpy server 进程，避免在实例返回后，因为失去引用，被垃圾回收自动关闭
        self._server_stream: Optional["adbutils.AdbConnection"] = None

    def __del__(self):
        if self._server_stream:
            self._server_stream.close()
        self._server_stream = None

    def _create_device_connection(self, stream_type: str) -> socket.socket:
        from wetest.osplatform import android_conn

        return android_conn(serial=self.serial, network="localabstract", addr=f"{self.sock_prefix}-{stream_type}")

    def start_scrcpy(self) -> bool:
        """启动 scrcpy"""
        import adbutils

        jar_name = "scrcpy-server.jar"
        server_path = "resource/android/scrcpy-server"
        device_path = "/data/local/tmp/"

        device: adbutils.AdbDevice = adbutils.adb.device(serial=self.serial)
        resource_path = Path(__file__).parent.parent
        server_abs_path = resource_path / server_path
        device.sync.push(str(server_abs_path), device_path + jar_name)

        # 启动server命令
        commands = [
            "CLASSPATH=" + device_path + jar_name,
            "app_process",
            "/",
            "com.genymobile.scrcpy.Server",
            "1.2.4",
            "log_level=debug",
            "max_size=2048",
            "bit_rate=10000",
            "max_fps=25",
            "tunnel_forward=true",
            f"udt_socket_name={self.sock_prefix}",
            "clipboard_autosync=false",
            "audio_codec=aac",
        ]

        self._server_stream = device.shell(commands, stream=True)
        # 启动后打印固定日志
        # [server] INFO: Device: [Xiaomi] Redmi Redmi K30i 5G (Android 12)
        # [server] INFO: Start wait multi connection, version: 3.3.1
        # TODO dirty hack 待优化，当前和固定等待逻辑一致，应修改为检查端口是否listening
        self._server_stream.read(100)
        return not self._server_stream.closed


@dataclass
class IOSDevice(Device):
    """iOS 设备描述符"""

    udid: str = ""

    def _create_device_connection(self, stream_type: str) -> socket.socket:
        from wetest.osplatform import ios_conn

        if stream_type == "audio":
            raise ProtocolError("audio stream not supported on iOS")

        port = 21344 if stream_type == "video" else 21343
        return ios_conn(udid=self.udid, port=port)

    def start_scrcpy(self) -> bool:
        """启动 scrcpy"""
        from wetest.pyidb import Idb

        device = Idb(self.udid)
        ps = device.launch("com.wetest.wda-scrcpy.xctrunner")
        return ps is not None


@dataclass
class LocalDevice(Device):
    """本地设备描述符，用于使用h264视频文件作为视频源，使得调试的时候不需要依赖真机"""

    video_file_path: str
    loop: bool = True  # 是否循环播放
    fps: float = 25.0  # 播放帧率

    def __post_init__(self):
        if not Path(self.video_file_path).exists():
            raise FileNotFoundError(f"Video file not found: {self.video_file_path}")

    def _create_device_connection(self, stream_type: str) -> socket.socket:
        from ._socket import FileSocket

        """创建文件读取连接"""
        return FileSocket(self.video_file_path, self.loop, self.fps)

    def start_scrcpy(self) -> bool:
        """启动本地视频读取（无需启动真实的scrcpy服务）"""
        return True
