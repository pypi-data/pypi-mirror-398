# coding: utf-8
import logging
import os
import socket
import struct
import time
from typing import Tuple, Union

from ._exceptions import SocketError

logger = logging.getLogger(__name__)


class StreamSocket:
    """wrapper to native python socket object to be used with construct as a stream"""

    def __init__(self, addr: Union[str, Tuple[str, int], socket.socket]):
        """
        Args:
            addr: can be /var/run/usbmuxd or localhost:27015 or (localhost, 27015)
        """
        if isinstance(addr, socket.socket):
            self._sock = addr
        else:
            if isinstance(addr, str):
                if ":" in addr:
                    host, port = addr.split(":", 1)
                    addr = (host, int(port))
                    family = socket.AF_INET
                elif os.path.exists(addr):
                    family = socket.AF_UNIX
                else:
                    raise SocketError(f"socket unix:{addr} unable to connect")
            else:
                family = socket.AF_INET
            self._sock = socket.socket(family, socket.SOCK_STREAM)
            self._sock.connect(addr)

    def send(self, data: Union[bytes, bytearray]) -> int:
        self._sock.sendall(data)
        return len(data)

    def recv(self, size: int) -> bytearray:
        """recv data from socket
        Args:
            bufsize: buffer size

        Raises:
            SocketError
        """
        buf = bytearray()
        while len(buf) < size:
            chunk = self._sock.recv(size - len(buf))
            if not chunk:
                raise SocketError("socket connection broken")
            buf.extend(chunk)
        return buf

    def read_frame(self) -> bytearray:
        lenbuf = self.read(4)
        (length,) = struct.unpack(">i", lenbuf)
        logger.debug(f"read_frame len:{length:08x}")
        return self.read(length)

    def close(self):
        self._sock.shutdown(socket.SHUT_RDWR)
        self._sock.close()

    def settimeout(self, interval: float):
        self._sock.settimeout(interval)

    def setblocking(self, blocking: bool):
        self._sock.setblocking(blocking)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    read = recv
    write = send


class FileSocket(socket.socket):
    """模拟socket，从H.264文件读取数据"""

    def __init__(self, file_path: str, loop: bool = True, fps: float = 25.0):
        self.file_path = file_path
        self.loop = loop
        self.fps = fps
        self.frame_interval = 1.0 / fps
        self._file = None
        self._last_frame_time = 0
        self._device_meta_sent = False
        self._fileno = 1

    def recv(self, size: int) -> bytes:
        """模拟socket的recv方法"""
        if not self._device_meta_sent:
            # 首次连接时发送设备元数据（模拟scrcpy协议）
            self._device_meta_sent = True
            return self._create_device_meta()

        if self._file is None:
            self._file = open(self.file_path, "rb")

        # 控制播放速度
        current_time = time.time()
        if self._last_frame_time > 0:
            elapsed = current_time - self._last_frame_time
            if elapsed < self.frame_interval:
                time.sleep(self.frame_interval - elapsed)

        data = self._file.read(size)

        # 如果文件读完且需要循环播放
        if not data and self.loop:
            self._file.close()
            self._file = open(self.file_path, "rb")
            data = self._file.read(size)

        if not data:
            raise ConnectionError("End of file reached")

        self._last_frame_time = time.time()
        return data

    def _create_device_meta(self) -> bytes:
        """创建设备元数据（模拟scrcpy协议）"""
        # 模拟设备配置：1字节padding + 64字节设备名 + 2字节宽度 + 2字节高度
        device_name = b"LocalDevice\x00" + b"\x00" * (64 - len(b"LocalDevice\x00"))
        width = (1080).to_bytes(2, "big")  # 默认宽度
        height = (1920).to_bytes(2, "big")  # 默认高度
        return b"\x00" + device_name + width + height

    def close(self):
        """关闭文件"""
        if self._file:
            self._file.close()
            self._file = None
        self._fileno = -1

    def shutdown(self, how):
        """空实现，避免调用真正的socket.shutdown"""
        pass

    def fileno(self):
        """返回文件描述符（用于socket健康检查）"""
        return self._fileno  # 返回有效的文件描述符

    def settimeout(self, timeout):
        """设置超时（空实现）"""
        pass

    def setblocking(self, blocking):
        """设置阻塞模式（空实现）"""
        pass

    read = recv
