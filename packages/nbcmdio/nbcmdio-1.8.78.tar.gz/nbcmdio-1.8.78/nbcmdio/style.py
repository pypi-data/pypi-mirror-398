from typing import Union
from .utils import hex2RGB

RGB = Union[list[int], tuple[int, int, int]]


class Style:
    RESET = "\033[0m"
    CSI = "\033["

    def __init__(self, style: str) -> None:
        self.style = style

    def __str__(self) -> str:
        return self.style

    def __add__(self, other):
        return self.style + other

    def __radd__(self, other):
        return other + self.style

    def __call__(self, *args, **kwds):
        if "end" not in kwds:
            kwds["end"] = ""
        print(self.style, end="")
        print(*args, **kwds)
        print(self.RESET, end="")

    def reset(self):
        print(self.RESET, end="")


CSI = "\033["
RESET = Style(CSI + "0m")
BOLD = Style(CSI + "1m")
ITALICS = Style(CSI + "3m")
UNDERLINE = Style(CSI + "4m")
BLINK = Style(CSI + "5m")
VERSE = Style(CSI + "7m")
STRIKE = Style(CSI + "9m")
FG_BLACK = Style(CSI + "30m")
BG_BLACK = Style(CSI + "40m")
FG_RED = Style(CSI + "31m")
BG_RED = Style(CSI + "41m")
FG_GREEN = Style(CSI + "32m")
BG_GREEN = Style(CSI + "42m")
FG_YELLOW = Style(CSI + "33m")
BG_YELLOW = Style(CSI + "43m")
FG_BLUE = Style(CSI + "34m")
BG_BLUE = Style(CSI + "44m")
FG_MAGENTA = Style(CSI + "35m")
BG_MAGENTA = Style(CSI + "45m")
FG_CYAN = Style(CSI + "36m")
BG_CYAN = Style(CSI + "46m")
FG_WHITE = Style(CSI + "37m")
BG_WHITE = Style(CSI + "47m")


# 高频的I/O操作性能影响大，建议先连接所有的转义序列字符串再输出
def fg_rgb(rgb: RGB):
    """设置前景文字rgb颜色
    rgb: [0,128,255]"""
    return f"{CSI}38;2;{rgb[0]};{rgb[1]};{rgb[2]}m"


def bg_rgb(rgb: RGB):
    """设置背景rgb颜色
    rgb: [0,128,255]"""
    return f"{CSI}48;2;{rgb[0]};{rgb[1]};{rgb[2]}m"


def fg_hex(hex: str):
    """设置前景文字hex颜色
    hex: 0F0, #CCF, 008AFF, #CCCCFF"""
    rgb = hex2RGB(hex)
    return f"{CSI}38;2;{rgb[0]};{rgb[1]};{rgb[2]}m"


def bg_hex(hex: str):
    """设置背景hex颜色
    hex: 0F0, #CCF, 008AFF, #CCCCFF"""
    rgb = hex2RGB(hex)
    return f"{CSI}48;2;{rgb[0]};{rgb[1]};{rgb[2]}m"
