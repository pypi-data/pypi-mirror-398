import ctypes.wintypes
import time
import sys
from .utils import *
import ctypes
# 在windows终端中可以捕获更多的事件
wintypes = ctypes.wintypes

# 结构体定义
class KEY_EVENT_RECORD(ctypes.Structure):
    _fields_ = [
        ("bKeyDown", wintypes.BOOL),
        ("wRepeatCount", wintypes.WORD),
        ("wVirtualKeyCode", wintypes.WORD),
        ("wVirtualScanCode", wintypes.WORD),
        ("uChar", wintypes.WCHAR),
        ("dwControlKeyState", wintypes.DWORD),
    ]


class MOUSE_EVENT_RECORD(ctypes.Structure):
    _fields_ = [
        ("dwMousePosition", wintypes._COORD),
        ("dwButtonState", wintypes.DWORD),
        ("dwControlKeyState", wintypes.DWORD),
        ("dwEventFlags", wintypes.DWORD),
    ]


class WINDOW_BUFFER_SIZE_RECORD(ctypes.Structure):
    _fields_ = [("dwSize", wintypes._COORD)]


class MENU_EVENT_RECORD(ctypes.Structure):
    _fields_ = [("dwCommandId", wintypes.UINT)]


class FOCUS_EVENT_RECORD(ctypes.Structure):
    _fields_ = [("bSetFocus", wintypes.BOOL)]


class EventUnion(ctypes.Union):
    _fields_ = [
        ("KeyEvent", KEY_EVENT_RECORD),
        ("MouseEvent", MOUSE_EVENT_RECORD),
        ("WindowBufferSizeEvent", WINDOW_BUFFER_SIZE_RECORD),
        ("MenuEvent", MENU_EVENT_RECORD),
        ("FocusEvent", FOCUS_EVENT_RECORD),
    ]


class INPUT_RECORD(ctypes.Structure):
    _fields_ = [
        ("EventType", wintypes.WORD),
        ("Event", EventUnion),
    ]



if IS_WIN:
    import msvcrt
    kernel32 = ctypes.windll.kernel32
else:
    import termios
    import tty


class Input:
    """
    ### 跨平台输入类Input
    - 无缓冲单键输入"""

    WIN_KEY_MAP = {
        8: "BackSpace",
        9: "Tab",
        13: "Enter",
        27: "Esc",
        59: "F1",
        60: "F2",
        61: "F3",
        62: "F4",
        63: "F5",
        64: "F6",
        65: "F7",
        66: "F8",
        67: "F9",
        68: "F10",
        71: "Home",
        72: "ArrowUp",
        73: "PageUp",
        77: "ArrowRight",
        75: "ArrowLeft",
        80: "ArrowDown",
        81: "PageDown",
        82: "Insert",
        83: "Delete",
        133: "F11",
        134: "F12",
    }

    def __init__(self) -> None:
        if IS_WIN:
            self.get_char = self.__win_get_char
            self.get_str = self.__win_get_str

    def get_char(self):
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        char = ""
        try:
            # 设置原始模式（不缓冲输入）
            tty.setraw(fd)
            char = sys.stdin.read(1)
        finally:
            # 恢复终端原始设置
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return char

    def get_str(self, timeout=0.5):
        start_time = time.time()
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        string = ""
        try:
            # 设置原始模式（不缓冲输入）
            tty.setraw(fd)
            # 只要string 或者 时间到 就停止
            while (not string) and time.time() - start_time < timeout:
                string = sys.stdin.read(sys.stdin.seek(0, 2))
        finally:
            # 恢复终端原始设置
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return string

    def __win_get_char(self):
        if msvcrt.kbhit():
            char = msvcrt.getch()
            return char
        return ""

    def __win_get_str(self, timeout=0.5):
        start_time = time.time()
        string = ""
        while time.time() - start_time < timeout:
            if msvcrt.kbhit():  # 检查是否有按键
                char = msvcrt.getch().decode("utf-8", errors="ignore")
                string += char
            elif string:
                break  # 读取完毕
            time.sleep(0.01)
        return string

    def __win_get_key(self, timeout=0.1):
        start_time = time.time()
        key = None

        # 等待按键或超时
        while (time.time() - start_time) < timeout:
            if msvcrt.kbhit():
                first_byte = msvcrt.getch()
                # 检查是否为扩展键（功能键）
                if first_byte in (b"\xe0", b"\x00"):
                    if msvcrt.kbhit():
                        second_byte = msvcrt.getch()
                        key = self.WIN_KEY_MAP.get(
                            ord(second_byte), f"Unknown Key: {ord(second_byte)}"
                        )
                    else:
                        key = str(first_byte)
                else:
                    o = ord(first_byte)
                    key = (
                        self.WIN_KEY_MAP.get(o, None)
                        if o <= 31
                        else first_byte.decode()
                    )
                break
            time.sleep(0.01)  # 减少 CPU 占用

        return key


inp = Input()
