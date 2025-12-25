import logging
import struct
import time
import wave
from typing import Generator, Optional

import av
import pyaudio

from ._device import Device
from ._socket import StreamSocket

logger = logging.getLogger(__name__)

# 音频协议标志
PACKET_FLAG_CONFIG = 1 << 63

# 音频参数
CHUNK = 1024
FORMAT_SAMPLE_SIZE = 2  # 16-bit = 2 bytes
CHANNELS = 2
RATE = 48000

# cloudtest 使用 aac，udt 使用 raw，所以暂时只支持这两种编码格式
AUDIO_CODEC_CONFIG = {
    0x6F707573: {"name": "opus", "sample_format": None},  # 暂不支持
    0x00616163: {"name": "aac", "sample_format": pyaudio.paFloat32},
    0x666C6163: {"name": "flac", "sample_format": None},  # 暂不支持
    0x00726177: {"name": "raw", "sample_format": pyaudio.paInt16},
}


class AudioConnection(StreamSocket):

    def __init__(
        self, device: Device, timeout: float = 5, chunk: int = CHUNK, channels: int = CHANNELS, rate: int = RATE
    ):
        self._device = device
        self._timeout = timeout
        self.chunk = chunk
        self.channels = channels
        self.rate = rate

        self._sock = self._device.restart_socket_connection(None, "audio")
        self._sock.settimeout(self._timeout)
        super().__init__(self._sock)

        # 解码器相关属性
        self.codec_name = None
        self.sample_format = None
        self._codec = None

        # 读取音频头部信息
        self._read_audio_header()

    def read(self, size: int) -> bytes:
        """读取指定大小的数据"""
        data = super().read(size)
        return bytes(data)

    def _read_audio_header(self):
        """读取音频头部信息"""
        header_data = self.read(4)
        codec_id = struct.unpack(">I", header_data)[0]
        codec_config = AUDIO_CODEC_CONFIG.get(codec_id, {"name": "unknown", "sample_format": None})
        self.codec_name = codec_config["name"]
        self.sample_format = codec_config["sample_format"]

        logger.info(f"audio codec ID: {codec_id} ({self.codec_name})")

        if self.codec_name == "raw":
            # RAW格式直接返回PCM，无需配置解码器
            pass
        elif self.codec_name == "aac":
            # 初始化AAC解码器
            self._codec = av.CodecContext.create("aac", "r")
            self._codec.sample_rate = RATE
            self._codec.layout = av.AudioLayout("stereo")
            self._codec.channels = CHANNELS
        else:
            raise ValueError(f"unsupported audio codec: {self.codec_name}")

    def read_audio_frame(self) -> Optional[bytes]:
        """读取并解码单个音频帧数据，返回PCM数据"""
        if self.codec_name == "raw":
            # raw没有frameMeta，直接读取数据
            # ref: scrcpy/server/src/main/java/udt/UdtServer.java:307
            packet_size = CHANNELS * FORMAT_SAMPLE_SIZE
            return self.read(packet_size)
        elif self.codec_name == "aac":
            meta_data = self.read(12)
            pts_and_flags = struct.unpack(">Q", meta_data[:8])[0]  # 8字节PTS+flags
            packet_size = struct.unpack(">I", meta_data[8:12])[0]  # 4字节数据包大小

            if bool(pts_and_flags & PACKET_FLAG_CONFIG):
                config_data = self.read(packet_size)
                self._codec.extradata = config_data
                return None

            audio_data = self.read(packet_size)
            packet = av.Packet(audio_data)
            frames = self._codec.decode(packet)
            # 将解码后的音频帧转换为PCM数据
            audio_frames = b"".join(frame.to_ndarray().T.tobytes() for frame in frames)
            return audio_frames

    def audio_frames_generator(self) -> Generator[bytes, None, None]:
        """音频帧生成器，用于流式处理"""
        while True:
            try:
                frame_data = self.read_audio_frame()
                if frame_data:
                    yield frame_data
            except Exception as e:
                logger.exception(f"audio frame generator error: {e}")
                break


# 独立的播放函数
def realtime_playback(audio_conn: AudioConnection, duration: float = 60):
    """实时播放音频数据

    Args:
        audio_conn: AudioConnection实例
        duration: 播放时长（秒）
    """
    # 初始化PyAudio
    pyaudio_instance = pyaudio.PyAudio()
    stream = None

    try:
        # 创建音频流
        stream = pyaudio_instance.open(
            format=audio_conn.sample_format,
            channels=audio_conn.channels,
            rate=audio_conn.rate,
            output=True,
            frames_per_buffer=audio_conn.chunk,
        )

        logger.info(
            f"audio playback started: ({audio_conn.codec_name}, {audio_conn.rate}Hz, {audio_conn.channels} channels)"
        )

        start_time = time.time()
        for audio_data in audio_conn.audio_frames_generator():
            if time.time() - start_time >= duration:
                break
            stream.write(audio_data)

    except Exception as e:
        logger.error(f"play audio error: {e}")
        raise
    finally:
        if stream is not None:
            stream.stop_stream()
            stream.close()
        pyaudio_instance.terminate()
        logger.info("audio playback finished")


# 独立的录制函数
def record_to_file(audio_conn: AudioConnection, output_file: str, duration: float = 60):
    """将音频录制到文件

    Args:
        audio_conn: AudioConnection实例
        output_file: 输出文件路径
        duration: 录制时长（秒）
    """
    try:
        # 统一使用WAV格式，但对AAC数据进行转换
        if not output_file.endswith(".wav"):
            output_file = output_file.rsplit(".", 1)[0] + ".wav"

        with wave.open(output_file, "wb") as wav_file:
            wav_file.setnchannels(audio_conn.channels)
            wav_file.setsampwidth(2)  # 统一使用16位
            wav_file.setframerate(audio_conn.rate)

            logger.info(
                f"record audio to file: {output_file} ({audio_conn.codec_name}, {audio_conn.rate}Hz, {audio_conn.channels} channels)"
            )

            start_time = time.time()
            for audio_data in audio_conn.audio_frames_generator():
                if time.time() - start_time >= duration:
                    break

                # 根据编码格式处理数据
                if audio_conn.codec_name == "aac":
                    # AAC解码后是float32，需要转换为int16
                    import numpy as np

                    float_data = np.frombuffer(audio_data, dtype=np.float32)
                    # 确保数据在[-1.0, 1.0]范围内
                    float_data = np.clip(float_data, -1.0, 1.0)
                    # 转换为int16
                    int16_data = (float_data * 32767).astype(np.int16)
                    audio_data = int16_data.tobytes()
                elif audio_conn.codec_name == "raw":
                    # RAW已经是int16格式，直接使用
                    pass

                wav_file.writeframes(audio_data)
        logger.info(f"audio record finished: {output_file}")

    except Exception as e:
        logger.error(f"record audio to file error: {e}")
        raise
