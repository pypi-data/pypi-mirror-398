class ScrcpyError(Exception):
    """Scrcpy基础异常类"""

    def __init__(self, message: str, details: str = None) -> None:
        self.message = message
        self.details = details
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.details:
            return f"{self.message}: {self.details}"
        return self.message


class DeviceError(ScrcpyError):
    """设备相关错误"""

    pass


class SocketError(ScrcpyError):
    """Socket连接相关错误"""

    pass


class FrameError(ScrcpyError):
    """视频流截图帧相关错误"""

    pass


class ProtocolError(ScrcpyError):
    """协议相关错误"""

    pass
