from enum import Enum, IntEnum

# .core._const 有部分按键没有迁移，待之后扩充


class Action(IntEnum):

    DOWN = 0
    UP = 1
    MOVE = 2


class KeyCode(IntEnum):

    UNKNOWN = 0
    SOFT_LEFT = 1
    SOFT_RIGHT = 2
    HOME = 3
    BACK = 4
    CALL = 5
    ENDCALL = 6

    NUM_0 = 7
    NUM_1 = 8
    NUM_2 = 9
    NUM_3 = 10
    NUM_4 = 11
    NUM_5 = 12
    NUM_6 = 13
    NUM_7 = 14
    NUM_8 = 15
    NUM_9 = 16

    STAR = 17
    POUND = 18

    DPAD_UP = 19
    DPAD_DOWN = 20
    DPAD_LEFT = 21
    DPAD_RIGHT = 22
    DPAD_CENTER = 23

    VOLUME_UP = 24
    VOLUME_DOWN = 25
    VOLUME_MUTE = 164

    POWER = 26
    CAMERA = 27
    CLEAR = 28

    A = 29
    B = 30
    C = 31
    D = 32
    E = 33
    F = 34
    G = 35
    H = 36
    I = 37
    J = 38
    K = 39
    L = 40
    M = 41
    N = 42
    O = 43
    P = 44
    Q = 45
    R = 46
    S = 47
    T = 48
    U = 49
    V = 50
    W = 51
    X = 52
    Y = 53
    Z = 54

    COMMA = 55
    PERIOD = 56

    ALT_LEFT = 57
    ALT_RIGHT = 58
    SHIFT_LEFT = 59
    SHIFT_RIGHT = 60
    TAB = 61
    SPACE = 62
    ENTER = 66
    DEL = 67

    F1 = 131
    F2 = 132
    F3 = 133
    F4 = 134
    F5 = 135
    F6 = 136
    F7 = 137
    F8 = 138
    F9 = 139
    F10 = 140
    F11 = 141
    F12 = 142

    MEDIA_PLAY_PAUSE = 85
    MEDIA_STOP = 86
    MEDIA_NEXT = 87
    MEDIA_PREVIOUS = 88

    PAGE_UP = 92
    PAGE_DOWN = 93
    ESCAPE = 111
    MENU = 82

    CUT = 277
    COPY = 278


class CopyKey(IntEnum):
    NONE = 0
    COPY = 1
    CUT = 2


class ControlType(IntEnum):

    INJECT_KEYCODE = 0
    INJECT_TEXT = 1
    INJECT_TOUCH_EVENT = 2
    INJECT_SCROLL_EVENT = 3
    BACK_OR_SCREEN_ON = 4
    EXPAND_NOTIFICATION_PANEL = 5
    EXPAND_SETTINGS_PANEL = 6
    COLLAPSE_PANELS = 7
    GET_CLIPBOARD = 8
    SET_CLIPBOARD = 9
    SET_SCREEN_POWER_MODE = 10
    ROTATE_DEVICE = 11


class Orientation(IntEnum):

    UNLOCKED = -1
    INITIAL = -2
    PORTRAIT = 0
    LANDSCAPE = 1
    PORTRAIT_REVERSE = 2
    LANDSCAPE_REVERSE = 3


class PowerMode(IntEnum):

    OFF = 0
    NORMAL = 2


class Event(str, Enum):

    INIT = "init"
    FRAME = "frame"
    DISCONNECT = "disconnect"


class ControlMessageType(IntEnum):

    REQ_IDR = 100
    SET_BITRATE = 101
    HEARTBEAT = 102
    CAPTURE = 103
    PAUSE_VIDEO = 104
    RESUME_VIDEO = 105
    GET_LOCALE = 106
    SET_LOCALE = 107
    GET_APPS = 108
    GET_ROTATION = 109
    GET_SCREENINFO = 110


class DeviceMessageType(IntEnum):

    CLIPBOARD = 0
    ACK_CLIPBOARD = 1
    HEARTBEAT = 102
    CAPTURE = 103
    GET_LOCALE = 104
    GET_APPS = 105
    GET_ROTATION = 106
    GET_SCREENINFO = 110


class Buttons(IntEnum):
    BACK = 4
    MENU = 82
    HOME = 3
    VOLUME_UP = 24
    VOLUME_DOWN = 25
    VOLUME_MUTE = 164
    POWER = 26
    CAMERA = 27
    CLEAR = 28
