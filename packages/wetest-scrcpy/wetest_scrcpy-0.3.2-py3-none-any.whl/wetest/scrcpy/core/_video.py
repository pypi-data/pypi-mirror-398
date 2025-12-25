# coding: utf-8
import atexit
import logging
import socket
import threading
import time
from dataclasses import dataclass
from typing import Optional, Tuple, Union

import av
import numpy as np
from construct import CString, FixedSized, Int16ub, Int32ub, Int64ub, Padding, Struct

from ._device import Device
from ._exceptions import FrameError
from ._socket import StreamSocket

logger = logging.getLogger(__name__)

device_config = Struct(
    Padding(1),
    "device_name" / FixedSized(64, CString("ascii")),
    "width" / Int16ub,
    "height" / Int16ub,
)

video_frame_header = Struct("pts" / Int64ub, "length" / Int32ub)


@dataclass
class DeviceConfigMeta:
    name: str
    width: int
    height: bytes


@dataclass
class VideoFrame:
    Pts: int
    Length: int
    Payload: bytes


class VideoConn(StreamSocket):
    def __init__(self, addr: Union[str, Tuple[str, int], socket.socket]):
        super().__init__(addr)
        self._device_meta = self._read_device_meta()

    def _read_device_meta(self) -> DeviceConfigMeta:
        buf = self.read(1 + 64 + 4)
        config = device_config.parse(buf)
        return DeviceConfigMeta(config.device_name, config.width, config.height)

    def read_video_frame(self) -> VideoFrame:
        buf = self.read(12)
        header = video_frame_header.parse(buf)
        payload = self.read(header.length)
        return VideoFrame(int(header.pts), int(header.length), payload)


class VideoStreamScreenshot:
    """基于视频流的截图服务"""

    def __init__(
        self,
        device: Device,
        timeout: float = 5,
    ):
        self._device = device
        self._sock = None
        self._timeout = timeout

        # 视频流处理线程相关
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # H.264解码相关
        self._decoder: Optional[av.VideoCodecContext] = None
        self._frame_ready = threading.Event()

        # 截图返回的最新帧
        self._latest_frame: Optional[np.ndarray] = None

    def start(self):
        """启动视频流解析转码"""
        # 加锁，当有多线程调用 get_screenshot，保证只有一个线程启动视频流解析转码
        # 之后的线程会直接在检查 self._running 时返回
        # 避免多线程竞争导致的 self._thread 资源泄漏
        with self._lock:
            if self._running:
                return

            self._running = True
            self._thread = threading.Thread(target=self._video_stream_worker, daemon=True)
            self._thread.start()
            logger.info("Start screenshot from video stream!")
            return self

    __enter__ = start

    def stop(self):
        """停止视频流解析转码"""
        if not self._running:
            return
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        if self._decoder:
            self._decoder = None
        self._close_socket()
        logger.info("Stop screenshot from video stream!")

    def _close_socket(self):
        if self._sock:
            self._sock.close()
            self._sock = None
            logger.debug("Close socket connection with scrcpy!")

    __del__ = stop
    # 与 CtrlConnection 保持一致，提供 close 方法
    close = stop

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def _video_stream_worker(self):
        """视频流解析转码"""

        # 对于高fps场景，在thread中实现协作式保活更为合理，不会出现 thread 频繁创建和销毁，避免大量资源开销和 thread 拉起和结束的耗时影响截图
        # 内层循环出现问题，就调用 restart_socket_connection，重新拉起 scrcpy 并创建新的socket
        # 外层循环出现问题（拉起失败），抛出异常（SocketError("Launch server failed"))，thread 结束，在调用 get_screenshot 时重新创建thread
        while self._running:
            self._sock = self._device.restart_socket_connection(self._sock, "video")
            try:
                with VideoConn(self._sock) as video_conn:
                    while self._running:
                        frame = video_conn.read_video_frame()
                        self._process_video_frame(frame)
            except Exception:
                logger.debug("Error in video stream worker", exc_info=True)

    def _process_video_frame(self, frame: VideoFrame) -> None:
        """处理单个视频帧"""
        if self._decoder is None:
            self._decoder = av.CodecContext.create("h264", "r")

        start_time = time.time()
        packets = self._decoder.parse(frame.Payload)
        for packet in packets:
            if packet:
                decoded_frames = self._decoder.decode(packet)
                # 倒序读取，确保获取最新帧
                for decoded_frame in reversed(decoded_frames):
                    img_array = decoded_frame.to_ndarray(format="bgr24")
                    if img_array is not None:
                        with self._lock:
                            self._latest_frame = img_array
                            logger.debug(f"Parsed image size: {img_array.shape}, duration: {time.time() - start_time}s")
                            self._frame_ready.set()
                            return

    def get_screenshot(self) -> np.ndarray:
        """获取最新截图

        Returns:
            OpenCV图像数组或None，格式为BGR
        """

        if not self._running:
            logger.debug("Video stream not running, invoke start() first")
            self.start()

        # 如果fps要求不高，应将协作式保活 (invoke self._device.restart_socket_connection）放到这里
        # 具体实现为，每次 _video_stream_worker 出现异常，就结束 thread，调用 get_screenshot 时，再重新启动 thread
        # 优点：低fps的时候，能够接受 thread 拉起和结束的耗时，且不会出现 thread 频繁被创建，不会造成较大的资源开销

        # 当前只在 _video_stream_worker 外层循环出现异常的时候，才重新启动 thread
        if isinstance(self._thread, threading.Thread) and not self._thread.is_alive():
            self._running = False
            logger.warning("Video stream thread is not alive, invoke start() to create a new thread")
            self.start()

        # 等待帧准备就绪
        if not self._frame_ready.wait(self._timeout):
            raise FrameError(f"Timeout waiting for new frame in {self._timeout}s")

        with self._lock:
            if self._latest_frame is None:
                raise FrameError("No new frame available")
            img_array = self._latest_frame.copy()
            logger.info(f"Get screenshot success, image size: {img_array.shape}")
            return img_array
