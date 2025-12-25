import fractions
import logging
import threading
import time
from typing import Optional

import av
import numpy as np

from ._audio import CHANNELS, FORMAT_SAMPLE_SIZE, RATE, AudioConnection
from ._device import Device
from ._video import VideoConn

logger = logging.getLogger(__name__)


class Recorder:
    """音视频同步录制器 (H.264/AAC -> MP4)"""

    def __init__(self, device: Device, output: str = "record.mp4", duration: Optional[float] = None):
        self._device = device
        self.output = output
        self.duration = duration

        self._running = False
        self._stop_event = threading.Event()
        self._threads = []
        self._started_at = None

        # Muxer
        self._container: Optional[av.container.OutputContainer] = None
        self._v_stream: Optional[av.video.stream.VideoStream] = None
        self._a_stream: Optional[av.audio.stream.AudioStream] = None
        self._mux_lock = threading.Lock()

        # Connections
        self._video_conn: Optional[VideoConn] = None
        self._audio_conn: Optional[AudioConnection] = None

        # Sync
        self._base_pts_video = None
        self._base_pts_audio = None

    def start(self):
        if self._running:
            return self

        self._running = True
        self._stop_event.clear()
        self._started_at = time.time()

        # 1. Initialize Container
        self._container = av.open(self.output, mode="w", format="mp4")

        # 2. Setup Connections & Streams
        try:
            # Video
            sock = self._device.restart_socket_connection(None, "video")
            self._video_conn = VideoConn(sock)
            
            # 使用 libx264 编码，保证兼容性
            self._v_stream = self._container.add_stream("h264", rate=30)
            self._v_stream.pix_fmt = "yuv420p"
            # 适当提高码率以保证画质
            # self._v_stream.bit_rate = 4000000 
            
            # Audio
            try:
                self._audio_conn = AudioConnection(self._device, timeout=5)
                # 使用 AAC 编码
                self._a_stream = self._container.add_stream("aac", rate=RATE)
                self._a_stream.channels = CHANNELS
                self._a_stream.layout = "stereo"
            except Exception as e:
                logger.warning(f"Audio recording unavailable: {e}")
                self._audio_conn = None

            # 3. Start Workers
            t_v = threading.Thread(target=self._video_worker, daemon=True)
            t_v.start()
            self._threads.append(t_v)

            if self._audio_conn:
                t_a = threading.Thread(target=self._audio_worker, daemon=True)
                t_a.start()
                self._threads.append(t_a)
                
            logger.info(f"Started recording to {self.output}")

        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            self.stop()
            raise

        return self

    def stop(self):
        if not self._running:
            return

        self._running = False
        self._stop_event.set()

        for t in self._threads:
            if t.is_alive():
                t.join(timeout=5)
        self._threads.clear()

        # Flush encoders
        self._flush_stream(self._v_stream)
        self._flush_stream(self._a_stream)

        if self._container:
            self._container.close()
            self._container = None

        if self._video_conn:
            self._video_conn.close()
            self._video_conn = None
            
        if self._audio_conn:
            self._audio_conn.close()
            self._audio_conn = None
            
        logger.info(f"Stopped recording: {self.output}")

    def _flush_stream(self, stream):
        if stream:
            try:
                packets = stream.encode(None)
                with self._mux_lock:
                    for p in packets:
                        try:
                            self._container.mux(p)
                        except Exception as e:
                            logger.warning(f"Mux flush packet failed: {e}")
            except Exception as e:
                logger.warning(f"Error flushing stream: {e}")

    def _video_worker(self):
        decoder = av.CodecContext.create("h264", "r")
        # Scrcpy PTS 单位是微秒 (us)
        time_base = fractions.Fraction(1, 1000000)

        # 记录上一帧的PTS，用于检查单调性
        last_pts = -1

        while not self._stop_event.is_set():
            try:
                if self.duration and (time.time() - self._started_at > self.duration):
                    self.stop()
                    break

                # 1. Read
                frame = self._video_conn.read_video_frame()
                
                # 2. Decode
                packets = decoder.parse(frame.Payload)
                for pkt in packets:
                    decoded_frames = decoder.decode(pkt)
                    for df in decoded_frames:
                        # 3. Sync & Timestamp
                        if self._base_pts_video is None:
                            self._base_pts_video = frame.Pts
                        
                        # 计算相对时间戳
                        pts = frame.Pts - self._base_pts_video
                        
                        if pts <= last_pts:
                            # 强制递增
                            pts = last_pts + 1
                        last_pts = pts

                        df.pts = pts
                        df.time_base = time_base
                        
                        # 4. Encode
                        # 确保格式为 yuv420p (MP4/H.264最兼容的格式)
                        if df.format.name != 'yuv420p':
                            df = df.reformat(format='yuv420p')
                        
                        # 确保 stream width/height 已设置 (虽然 PyAV 通常会自动处理，但有时候首帧很重要)
                        if self._v_stream.width == 0:
                            self._v_stream.width = df.width
                            self._v_stream.height = df.height

                        try:
                            out_packets = self._v_stream.encode(df)
                        except Exception as e:
                            logger.warning(f"Encode video frame error: {e}")
                            continue
                        
                        # 5. Mux
                        with self._mux_lock:
                            for p in out_packets:
                                if p.dts is None:
                                    continue
                                try:
                                    self._container.mux(p)
                                except ValueError as e:
                                    # PyAV raises ValueError for muxing errors
                                    logger.warning(f"Mux video frame error: {e}")
                                except Exception as e:
                                    # Catch other errors like OSError
                                    logger.warning(f"Mux video frame failed: {e}")

            except Exception as e:
                if not self._stop_event.is_set():
                    logger.error(f"Video worker error: {e}")
                break

    def _audio_worker(self):
        if not self._audio_conn:
            return

        decoder = None
        if self._audio_conn.codec_name == "aac":
            decoder = av.CodecContext.create("aac", "r")
            
        time_base = fractions.Fraction(1, 1000000)
        current_pts = 0 # For RAW audio manual PTS calculation

        while not self._stop_event.is_set():
            try:
                if self.duration and (time.time() - self._started_at > self.duration):
                    break

                # 1. Read
                data, pts, is_config = self._audio_conn.read_raw_audio_packet()
                
                if not data and not is_config:
                    continue

                if is_config and decoder:
                    decoder.extradata = data
                    continue

                decoded_frames = []

                # 2. Decode
                if self._audio_conn.codec_name == "aac":
                    packet = av.Packet(data)
                    decoded_frames = decoder.decode(packet)
                    if self._base_pts_audio is None and pts > 0:
                        self._base_pts_audio = pts
                
                elif self._audio_conn.codec_name == "raw":
                    # Raw PCM (s16le)
                    # 手动构建 AudioFrame
                    # data is bytes, need to convert to AudioFrame
                    # scrcpy raw is s16le, interleaved
                    pcm = np.frombuffer(data, dtype=np.int16)
                    # pcm = pcm.reshape(-1, CHANNELS) # PyAV expects flat or planar depending on format, but from_ndarray usually takes (samples, channels) or (channels, samples)
                    
                    samples = len(pcm) // CHANNELS
                    pcm = pcm.reshape(1, -1) # (planes, samples) for planar? or (1, samples*channels) for packed? 
                    # av.AudioFrame.from_ndarray 比较挑剔，不如直接用 from_buffer
                    
                    # 简单点：创建空frame并填充
                    layout = 'stereo'
                    fmt = 's16'
                    
                    df = av.AudioFrame(format=fmt, layout=layout, samples=samples)
                    df.planes[0].update(data)
                    df.sample_rate = RATE
                    
                    # Manual PTS
                    if self._base_pts_audio is None:
                        self._base_pts_audio = 0 # Raw starts at 0 relative
                        current_pts = 0
                    
                    # 计算 duration (us)
                    duration_us = int((samples / RATE) * 1000000)
                    df.pts = current_pts
                    df.time_base = time_base
                    current_pts += duration_us
                    
                    decoded_frames = [df]

                # 3. Encode & Mux
                for df in decoded_frames:
                    if self._audio_conn.codec_name == "aac":
                         # 使用 scrcpy 提供的 PTS
                         if self._base_pts_audio is not None:
                             df.pts = pts - self._base_pts_audio
                         df.time_base = time_base

                    out_packets = self._a_stream.encode(df)
                    with self._mux_lock:
                        for p in out_packets:
                            try:
                                self._container.mux(p)
                            except Exception as e:
                                logger.warning(f"Mux audio frame failed: {e}")

            except Exception as e:
                if not self._stop_event.is_set():
                    logger.error(f"Audio worker error: {e}")
                break
