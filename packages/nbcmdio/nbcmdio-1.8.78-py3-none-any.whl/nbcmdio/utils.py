import re
import os
import sys
import time
import io
import cv2
import ctypes
import requests
from typing import Union
from PIL import Image
from unicodedata import east_asian_width
from platform import system as getOS
from threading import Thread
from pyaudio import PyAudio
from pydub import AudioSegment

__os = getOS()
IS_WIN = IS_LINUX = IS_MAC = False
if __os == "Windows":
    IS_WIN = True
elif __os == "Linux":
    IS_LINUX = True
elif __os == "Darwin":
    IS_MAC = True

# ------------------------------字符类处理函数---------------------------------
TabWidth = 4
Tab = " " * TabWidth

CHAR_WIDTH = {
    '—': 1
}

def getCharWidth(c: str):
    """返回字符宽度
    F W A ：全宽，Na、H：半宽，N：0
    """
    if c in CHAR_WIDTH:
        return CHAR_WIDTH[c]
    w = east_asian_width(c)
    if w == "N":
        # \t 应该返回多少宽度？
        return 0
    return 2 if w in ("F", "W", "A") else 1


def getStringWidth(s: str):
    """返回字符串去除CSI转义序列、\n、\t后的显示长度"""
    raw = re.sub(r"\033\[[\d;\?]*[a-zA-Z]", "", s)  # 去除csi转义序列
    return sum(getCharWidth(c) for c in raw)

def getEscapeString(s: str):
    """将一些不可见的控制字符转为可见的转义字符，包括空格32之前的和127 Delete（Oct：177）"""
    res = "".join([i.encode("unicode-escape").decode() if ord(i) < ord(" ") or i == "\177" else i for i in s])
    return res


def padString(s: str, width: int, mode=-1, fillchar=" "):
    """填充字符串s到宽度width （基于占位宽度）
    - mode: -1 左对齐右侧补充字符，0 居中对齐两边补充字符，1右对齐 左侧补充字符"""
    w = getStringWidth(s)
    if w >= width:
        return s
    width_fill_char = getStringWidth(fillchar)
    n = (width - w) // width_fill_char
    if mode == -1:
        s += fillchar * n
    elif mode == 0:
        h = n // 2
        s = f'{fillchar * h}{s}{fillchar * (n - h)}'
    elif mode == 1:
        s = fillchar * n + s
    else:
        raise ValueError(f"Parameter mode must be in -1,0,1 (got {mode}).")
    return s


# textwrap.wrap()的简化版，但是该方法不会解析转义序列，因此不采用
def splitLinesByWidth(s: str, width: int) -> list[str]:
    """按照显示宽度分割字符串，\\n 也会被分割，请不要包含 \\t 等字符，CSI转义序列会被保存但不计入宽度"""
    res, csi = [], []  # 结果，转义序列位置
    line, lwidth, i = [], 0, 0
    for match in re.finditer(r"\033\[[\d;\?]*[a-zA-Z]", s):
        csi.append(match.span())
    while i < len(s):
        chr = s[i]
        if csi and csi[0][0] == i:
            i = csi[0][1]
            line.append(s[csi[0][0] : csi[0][1]])
            csi.pop(0)
            continue
        if chr != "\n":
            line.append(chr)
            lwidth += getCharWidth(chr)
        if lwidth > width: # 最后一个字符是双宽字符导致宽度溢出时，使其换行
            last = line.pop()
            res.append(''.join(line))
            line = [last]
            lwidth = getCharWidth(last)
        elif lwidth == width or chr == "\n":
            res.append(''.join(line))
            line = []
            lwidth = 0
        i += 1
    if line:
        res.append(''.join(line))
    return res


# ------------------------------颜色类处理函数---------------------------------

RGB = Union[list[int], tuple[int, int, int], str]


def hex2RGB(hex: str) -> tuple[int, int, int]:
    """hex color to RGB color"""
    if hex[0] == "#":
        hex = hex[1:]
    hexes = []
    if len(hex) == 6:
        hexes = (hex[:2], hex[2:4], hex[4:])
    elif len(hex) == 3:
        hexes = (hex[:1] * 2, hex[1:2] * 2, hex[2:] * 2)
    else:
        raise ValueError("Hex color should be like #F0F or #00FFFF")
    return (int(hexes[0], 16), int(hexes[1], 16), int(hexes[2], 16))


def genGradient(color_start: RGB, color_end: RGB, num: int):
    """生成两个RGB颜色之间的渐变色列表
    - color_start: 起始颜色，格式为 (r, g, b)
    - color_end: 结束颜色，格式为 (r, g, b)
    - num: 总共要生成的渐变色数量（包括起始和结束颜色）

    Returns:
        包含起始颜色、渐变色和结束颜色的列表"""
    num -= 1
    if isinstance(color_start, str):
        color_start = hex2RGB(color_start)
    if isinstance(color_end, str):
        color_end = hex2RGB(color_end)
    step = [(color_end[i] - color_start[i]) / num for i in range(3)]
    gradient = [(int(color_start[0]+step[0]*i),
                int(color_start[1]+step[1]*i),
                int(color_start[2]+step[2]*i)) for i in range(num+1)]
    return gradient

def toImage(img_path: Union[str, Image.Image]):
    try:
        if isinstance(img_path,str):
            # 使用Path的请先str()转为字符串
            if os.path.exists(img_path):
                img = Image.open(img_path)
            elif img_path.startswith("http"):
                res = requests.get(img_path)
                img = Image.open(io.BytesIO(res.content))
            else:
                raise ValueError(f'Not a vaild path or url: {img_path}.')
        elif isinstance(img_path, Image.Image):
            img = img_path
        else:
            raise TypeError("Invalid type!")
    except Exception as e:
        raise ValueError(f"Parameter img_path({img_path}) is not "
                         "a valid image path or instance of Image.")
    return img

def getIMG(img_path: Union[str, Image.Image], height:int, width:int, resample=1):
    img = toImage(img_path)
    if img.mode != "RGB":
        img = img.convert("RGB")
    # 计算缩放比例
    img_width, img_height = img.size
    ratio_width = width / img_width
    ratio_height = height / img_height
    ratio = min(ratio_width, ratio_height)
    if ratio == 1:
        return img
    new_width = int(img_width * ratio)
    new_height = int(img_height * ratio)
    if new_height % 2:
        new_height += 1
    # 缩放图片
    img = img.resize((new_width, new_height), resample)
    return img

def readVideo2Image(video_path, max_frames=None):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Failed to open {video_path}")
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    frame_index = 0
    while True:
        ret, frame = cap.read()
        if not ret or (max_frames is not None and frame_num >= max_frames):
            break
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_frame)
        yield (pil_image, frame_index, frame_count, fps)
        frame_index += 1
    cap.release()


# ------------------------------时间类处理函数---------------------------------

PRECISE = 0.001

def sleepPrecise(seconds: float):
    start = time.perf_counter()
    n = seconds // PRECISE - 1 # -1 是因为时钟中断，实际暂停时间更久
    if n > 0:
        time.sleep(n * PRECISE)
    while time.perf_counter() - start < seconds:
        pass

# 循环等待的时间小于 2*PRECISE
def __win_sleepPrecise(seconds: float):
    start = time.perf_counter()
    n = seconds // PRECISE - 1
    if n > 0:
        winmm.timeBeginPeriod(1)
        time.sleep(n * PRECISE)
        winmm.timeEndPeriod(1)
    while time.perf_counter() - start < seconds:
        pass


if IS_WIN:
    winmm = ctypes.WinDLL('winmm')
    sleepPrecise = __win_sleepPrecise


# 通过耗时测试性能（本身也耗时，自测耗1μs左右）
class Timer:
    def __init__(self) -> None:
        self.t1 = time.perf_counter()
        self.t2 = 0
        self.span = 0

    def __enter__(self):
        self.t1 = time.perf_counter()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.t2 = time.perf_counter()
        self.span = self.t2 - self.t1
        print(f"{self.span:.9f}")

    def update(self):
        """ 获取与上一次update之间的时间间隔 """
        self.t2 = time.perf_counter()
        self.span = self.t2 - self.t1
        self.t1 = self.t2
        return self.span

TIMER = Timer()


class FrameTimer:
    def __init__(self, num: int=-1, spf: Union[int, float]=0, iterator=None) -> None:
        """ ## 帧计时器 (确保每一帧使用准确间隔)
        - num: 总帧数
        - spf: 每帧用时，等价于 1s / fps。未指定时请通过frameTime(seconds)指定当前帧应该耗费的时间
        - iterator: 可选，迭代器 或 可索引对象，长度必须>=num
        
        for i, v in FrameTimer:
            i = 当前帧数，从0到num-1
            v = None，或iterator迭代到相同次数的值，或对应下标的值"""
        self.__spf = spf
        self.__num = num if num>0 else 0x7fffffff
        self.__cur = 0
        self.__t0 = 0
        self.__total_spent = 0
        self.__last_frame_start = 0
        self.__iterator = iterator
        self.frame_spent = 0
        if self.__iterator == None:
            pass
        elif hasattr(self.__iterator, '__next__'):
            self.__getiter = lambda: self.__iterator.__next__()
        elif hasattr(self.__iterator, '__getitem__'):
            self.__getiter = lambda: self.__iterator[self.__cur - 1]

    def __iter__(self):
        return self
    
    def __next__(self):
        if self.__cur == 0:
            self.__t0 = time.perf_counter()
            self.__last_frame_start = self.__t0
            self.__cur += 1
            return 0, self.__getiter()
        if self.__cur >= self.__num:
            raise StopIteration
        i = self.__cur
        self.__cur += 1
        now = time.perf_counter()
        if self.__spf:
            self.__total_spent = now - self.__t0
            t = i * self.__spf - self.__total_spent
        else:
            self.frame_spent = now - self.__last_frame_start
            t = self.__frametime - self.frame_spent
        if t > 0: sleepPrecise(t)
        self.__last_frame_start = time.perf_counter()
        return i, self.__getiter()
    
    def __getiter(self):
        return None
    
    def frameTime(self, seconds: float):
        self.__frametime = seconds

    def stop(self):
        # Stop iteration (raise StopIteration at next iteration)
        self.__num = self.__cur

class Audio:
    def __init__(self, audio_path) -> None:
        audio = AudioSegment.from_file(audio_path)
        self.p = PyAudio()
        format = self.p.get_format_from_width(audio.sample_width)
        self.stream = self.p.open(
            format=format,
            channels=audio.channels,
            rate=audio.frame_rate,
            output=True,
        )
        self.__raw_data = audio.raw_data

    def __play(self, close=True):
        self.stream.write(self.__raw_data)
        if close:
            self.close()

    def play(self, close=True):
        Thread(target=self.__play, args=(close,), daemon=True).start()
    
    def close(self):
        self.stream.close()
        self.p.terminate()
