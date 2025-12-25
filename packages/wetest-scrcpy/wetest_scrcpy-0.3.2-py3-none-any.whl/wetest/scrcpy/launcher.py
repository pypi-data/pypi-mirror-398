# coding: utf-8
import os
import threading

from time import sleep
from dataclasses import dataclass
from typing import Any, Callable, Optional, Tuple, Union

from adbutils import AdbConnection, AdbTimeout, AdbDevice, AdbError, Network, adb

from wetest.scrcpy.core._const import (
    EVENT_DISCONNECT,
    EVENT_FRAME,
    EVENT_INIT,
    LOCK_SCREEN_ORIENTATION_UNLOCKED,
)


SYSLOG_LINE_SPLITTER = b'\n'

class Launcher:
    def __init__(
        self,
        device: Optional[Union[AdbDevice, str, any]] = None,
        max_width: int = 1024,
        bitrate: int = 6000000,
        max_fps: int = 25,
        flip: bool = False,
        block_frame: bool = False,
        stay_awake: bool = False,
        lock_screen_orientation: int = LOCK_SCREEN_ORIENTATION_UNLOCKED,
        connection_timeout: int = 3000,  # miliseconds
        socket_prefix: str = "udt-scrcpy",
        encoder_name: Optional[str] = None,
    ):
        """
        Create a scrcpy client, this client won't be started until you call the start function

        Args:
            device: Android device, select first one if none, from serial if str
            max_width: frame width that will be broadcast from android server
            bitrate: bitrate
            max_fps: maximum fps, 0 means not limited (supported after android 10)
            flip: flip the video
            block_frame: only return nonempty frames, may block cv2 render thread
            stay_awake: keep Android device awake
            lock_screen_orientation: lock screen orientation, LOCK_SCREEN_ORIENTATION_*
            connection_timeout: timeout for connection, unit is ms
            encoder_name: encoder name, enum: [OMX.google.h264.encoder, OMX.qcom.video.encoder.avc, c2.qti.avc.encoder, c2.android.avc.encoder], default is None (Auto)
        """
        # Check Params
        assert max_width >= 0, "max_width must be greater than or equal to 0"
        assert bitrate >= 0, "bitrate must be greater than or equal to 0"
        assert max_fps >= 0, "max_fps must be greater than or equal to 0"
        assert (
            -1 <= lock_screen_orientation <= 3
        ), "lock_screen_orientation must be LOCK_SCREEN_ORIENTATION_*"
        assert (
            connection_timeout >= 0
        ), "connection_timeout must be greater than or equal to 0"
        assert encoder_name in [
            None,
            "OMX.google.h264.encoder",
            "OMX.qcom.video.encoder.avc",
            "c2.qti.avc.encoder",
            "c2.android.avc.encoder",
        ]

        # Params
        self.flip = flip
        self.max_width = max_width
        self.bitrate = bitrate
        self.max_fps = max_fps
        self.block_frame = block_frame
        self.stay_awake = stay_awake
        self.lock_screen_orientation = lock_screen_orientation
        self.connection_timeout = connection_timeout
        self.socket_prefix = socket_prefix
        self.encoder_name = encoder_name

        # Connect to device
        if device is None:
            device = adb.device_list()[0]
        elif isinstance(device, str):
            device = adb.device(serial=device)

        self.device = device

        # Need to destroy
        self.alive = False
        self._server_stream: Optional[AdbConnection] = None

        # Available if start with threaded or daemon_threaded
        self.stream_loop_thread = None

    def _deploy_server(self) -> None:
        """
        Deploy server to android device
        """
        src_jar = "resources/android/scrcpy-server"
        jar_name = "scrcpy-server.jar"
        server_file_path = os.path.join(
            os.path.abspath(os.path.dirname(__file__)), src_jar
        )
        self.device.sync.push(server_file_path, f"/data/local/tmp/udt/{jar_name}")
        commands = [
            f"CLASSPATH=/data/local/tmp/udt/{jar_name}",
            "app_process",
            "/",
            "com.genymobile.scrcpy.Server",
            "1.24",  # Scrcpy server version
            # "info",  # Log level: info, verbose...
            f"max_size={self.max_width}",  # Max screen width (long side)
            f"bit_rate={self.bitrate}",  # Bitrate of video
            f"max_fps={self.max_fps}",  # Max frame per second
            "tunnel_forward=true",  # Tunnel forward
            "rotation_autosync=true",
            f"udt_socket_name={self.socket_prefix}",
            "clipboard_autosync=false",
            "codec_options=duration=2",
            # f"lock_screen_orientation={self.lock_screen_orientation}",  # Lock screen orientation: LOCK_SCREEN_ORIENTATION
            # "-",  # Crop screen
            # "false",  # Send frame rate to client
            # "true",  # Control enabled
            # "0",  # Display id
            # "false",  # Show touches
            # "true" if self.stay_awake else "false",  # Stay awake
            # "-",  # Codec (video encoding) options
            # self.encoder_name or "-",  # Encoder name
            # "false",  # Power off screen after server closed
        ]

        self._server_stream: AdbConnection = self.device.shell(
            commands,
            stream=True,
        )

        # Wait for server to start
        self._server_stream.read(10)

    def _stream_loop(self) -> None:
        # self._server_stream.conn.setblocking(False)
        buf = bytearray()
        while self.alive:
            try:
                chunk = self._server_stream.read(256)
                buf.extend(chunk)
                # SYSLOG_LINE_SPLITTER is used to split each syslog line
                if SYSLOG_LINE_SPLITTER in buf:
                    lines = buf.split(SYSLOG_LINE_SPLITTER)

                    # handle partial last lines
                    if not buf.endswith(SYSLOG_LINE_SPLITTER):
                        buf = lines[-1]
                        lines = lines[:-1]
                    for line in lines:
                        if len(line) == 0:
                            continue
                        print(line.decode("utf-8"))
            except (AdbTimeout, BlockingIOError, ConnectionError, OSError) as e:  # Socket Closed
                if self.alive:
                    self.stop()
                    raise e

    def run(self, threaded: bool = False, daemon_threaded: bool = False) -> None:
        """
        Loop reading from _server_stream

        Args:
            threaded: Run stream loop in a different thread to avoid blocking
            daemon_threaded: Run stream loop in a daemon thread to avoid blocking
        """
        self._deploy_server()
        self.alive = True
        if threaded or daemon_threaded:
            self.stream_loop_thread = threading.Thread(
                target=self._stream_loop, daemon=daemon_threaded
            )
            self.stream_loop_thread.start()
        else:
            self._stream_loop()

    def stop(self) -> None:
        """
        Deploy server to android device
        """
        self.alive = False
        if self._server_stream is not None:
            try:
                self._server_stream.close()
            except Exception:
                pass
