"""
Author: Cipen
Date:   2024/05/27
Desc:   提供一个基于控制台输出的任意位置输出RGB色彩文字，只需设置一次Style，即可用于在任意loc的文字输出，直到reset
参见 https://www.man7.org/linux/man-pages/man4/console_codes.4.html
　　 https://learn.microsoft.com/en-us/windows/console/console-virtual-terminal-sequences
　　 https://learn.microsoft.com/zh-cn/windows/console/console-functions
致谢：少部分内容借鉴colorama(setTitle)、curses(textpad,rect)、timg(ascii method)
"""


import re
from io import IOBase
from sys import stdout
from typing import Any, Union
from os import system, get_terminal_size
from .style import Style, fg_rgb, bg_rgb
from .input import inp
from .utils import *

# window cmd 默认禁用 ANSI 转义序列，可通过以下3种方法启用
# 1. cls
# 2. reg add HKCU\Console /v VirtualTerminalLevel /t REG_DWORD /d 1
# 3. kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
"""
┌─┬─┐
│ │ │
├─┼─┤
│ │ │
└─┴─┘
"""


class Area:
    """ 区域：row, col, height, width """
    def __init__(self, row=1, col=1, height=0, width=0) -> None:
        self.row = row
        self.col = col
        self.height = height
        self.width = width
    
    def __str__(self):
        return "{row: %d, col: %d, height: %d, width: %d}" % (self.row, self.col, self.height, self.width)
    

class Output:
    """### 输出类Output()
    - 终端色彩：fg_rgb()、bg_hex() 等设定任意前景、背景色，内置bold()、fg_red()等
    - 光标定位：[row, col] 即可定位到指定位置并供其他函数默认使用该位置，setOrigin()设定新原点，^ | << >> 上下左右
    - 链式调用：bold().fg_red()\\[2,3]("text")
    - 自动重置：所有函数内部样式一致，外部根据auto_reset值决定是否自动重置样式，p()、with上下文不重置样式

    注：许多方法末尾的self.print()不是打印换行，而是根据autoreset自动重置样式"""

    CSI, RESET = "\033[", "\033[0m"
    __cls = "cls"
    __version__ = "1.8.78"
    BUFSIZE = 8192
    CHARSET = {
        'basic': ' .:-=+*#%@',
        'dots': ' ⠂⠢⠴⠶⠾⡾⣷⣿'
    }

    def __init__(self, auto_reset=True, auto_flush=True, file=stdout) -> None:
        self.auto_reset = auto_reset
        self.auto_flush = auto_flush
        self.size_row, self.size_col = 0, 0
        self.origin_row, self.origin_col = 0, 0
        self.height, self.width = 0, 0
        self.getSize()
        self.setFile(file)
        self.__row, self.__col = 1, 1
        """保存[] loc()设定的位置，print后即毁 变为默认值1,1。
        未提供 row,col 的函数使用最近一次的此值，"""
        self.__str = ""
        """用于保存已配置style直至打印内容或reset前"""
        self.__acmlt = "mHG"  # 样式累积类型

        if IS_WIN:
            self.__cls = "cls"
            try:
                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
                # -11 是 stdout 句柄
            except:
                self.cls()
        elif IS_LINUX:
            self.__cls = "clear"
        elif IS_MAC:
            self.__cls = "clear"

    def setTitle(self, title: str):
        self.write(f"\033]2;{title}\a")
        return self
    
    @staticmethod
    def __null(*args):
        pass
    
    def setFile(self, file):
        if isinstance(file, IOBase) and file.writable():
            self.file = file
            self.write = file.write
            self.flush = file.flush
            self.bufwrite = getattr(file, 'buffer', file).write
        elif file == None:
            self.file = None
            self.write = self.__null
            self.flush = self.__null
            self.bufwrite = self.__null
        else:
            raise TypeError("Invalid parameter: file, expected: instance of class based on IOBase.")

    # 清除相关
    def cls(self):
        """调用系统命令清屏"""
        system(self.__cls)
        return self

    def clearAll(self):
        """输出CSI转义序列清屏"""
        return self.loc(0).csi("2J")

    def clearAllBeforeCursor(self):
        """ 光标留在原行 """
        return self.csi("1J")

    def clearAllAfterCursor(self):
        return self.csi("0J")

    def clearLine(self):
        return self.csi("2K")

    def clearLineBefore(self, col=-1):
        if col >= 0:
            self.col(col)
        return self.csi("1K")

    def clearLineAfter(self, col=-1):
        if col >= 0:
            self.col(col)
        return self.csi("K")

    def end(self, nl = 1):
        """重置颜色，并打印换行结尾"""
        self.reset()
        self.write("\n" * nl)
        return self

    def csi(self, s: str, *args):
        s = self.CSI + s
        if s[-1] in self.__acmlt:
            self.__str += s
        else:
            self.__str = ""
        self.bufwrite(s.encode())
        if args:
            self.print(*args)
        return self

    # 打印输出的2种方式：Output(*arg)、Output.print(*arg)
    def __call__(self, *args: Any, **kwds: Any):
        return self.print(*args, **kwds)

    def print(self, *args: Any, sep = " ", end = ""):
        """### 以已加载样式输出所有内容
        - 将会清除self.__str中保存的样式
        - 默认自动reset重置样式"""
        self.__str = ""
        self.__row = self.__col = 1
        s = sep.join([str(i) for i in args])
        for i in range(0, len(s), self.BUFSIZE):
            self.write(s[i:i+self.BUFSIZE])
        self.write(end)
        return self.checkAuto()

    def p(self, s: str):
        """不重置样式的输出"""
        self.write(s)
        return self
    
    def reset(self):
        """重置所有样式"""
        self.__str = self.RESET
        self.__row = self.__col = 1
        self.write(self.RESET)
        return self
    
    def checkAuto(self):
        if self.auto_reset:
            self.reset()
        if self.auto_flush:
            self.flush()
        return self

    def autoResetOn(self):
        self.auto_reset = True
        return self

    def autoResetOff(self):
        """不建议关闭自动重置Style，可以使用with上下文管理器或 p() 来使样式不自动重置"""
        self.auto_reset = False
        return self

    # 光标相对定位：^n|n>n<n>>n<<n
    # 优先级：<<>>  ^ | <>
    # 比较运算符 < > 无法连续运算
    def __xor__(self, n: int):
        return self.up(n)

    def __or__(self, n: int):
        return self.down(n)

    def up(self, n: int, col=-1):
        if n > 0:
            if col >= 0:
                self.csi(f"{n}F").col(col)
            self.csi(f"{n}A")
        elif n == 0:
            if col >= 0:
                self.col(col)
        else:
            return self.down(-n, col=col)
        return self

    def down(self, n: int, col=-1):
        if n > 0:
            if col >= 0:
                self.csi(f"{n}E").col(col)
            self.csi(f"{n}B")
        elif n == 0:
            if col >= 0:
                self.col(col)
        else:
            return self.up(-n, col)
        return self

    def __lt__(self, n: int):
        return self.left(n)

    def __lshift__(self, n: int):
        return self.left(n)

    def left(self, n: int):
        if n == 0:
            return self
        return self.csi(f"{n}D") if n >= 0 else self.right(-n)

    def __gt__(self, n: int):
        return self.right(n)

    def __rshift__(self, n: int):
        return self.right(n)

    def right(self, n: int):
        if n == 0:
            return self
        return self.csi(f"{n}C") if n >= 0 else self.left(-n)

    def __getitem__(self, key: Union[tuple[int, int], int]):
        """光标定位到 [row[,col=0]]"""
        if isinstance(key, tuple) and len(key) == 2:
            row, col = key
            return self.loc(row, col)
        elif isinstance(key, int):
            # col的默认值0、1对原始终端无影响，但对自己设定的origin有影响
            return self.loc(key, 0)
        else:
            raise TypeError("Location index must be [row, col].")

    # 绝对定位
    def loc(self, row: int, col=0):
        """### 光标定位到 row,col\n
        - col: 0 by default
        - 左上角为 1,1
        - 基于set_origin设置的新坐标原点"""
        self.__row, self.__col = row, col
        row += self.origin_row
        col += self.origin_col
        if row<0 or col<0 or row>self.size_row or col>self.size_col:
            raise ValueError(f"Beyond the size: loc of ({row}, {col}) from origin({self.__row}, {self.__col}).")
        return self.csi(f"{row};{col}H")
    
    def __rloc(self, row: int, col=0):
        row += self.origin_row
        col += self.origin_col
        return f"{self.CSI}{row};{col}H"

    def col(self, n: int):
        col = n + self.origin_col
        if col > self.size_col:
            raise ValueError(f"Beyond the size: col {n} from origin({self.__row}, {self.__col}).")
        return self.csi(f"{col}G")
    
    def __rcol(self, n:int):
        n += self.origin_col
        return f'{self.CSI}{n}G'

    def gotoHead(self):
        """回到本行行首（基于坐标原点）"""
        return self.col(0)

    def getLoc(self):
        """获取当前光标位置（相对设定的原点） -> (row, col)"""
        self.write(self.CSI + "6n")
        self.flush()
        res = inp.get_str()
        match = re.match(r"^\x1b\[(\d+);(\d+)R", res)
        if match:
            row = int(match.group(1)) - self.origin_row
            col = int(match.group(2)) - self.origin_col
            return row, col
        else:
            raise ValueError(f"Failed to get the location of cursor : {res!r}")

    # 光标相关
    def saveCursor(self):
        return self.csi("s")

    def restoreCursor(self):
        return self.csi("u")

    def hideCursor(self):
        return self.csi("?25l")

    def showCursor(self):
        return self.csi("?25h")

    # 内置效果（可能没啥效果）
    def bold(self, *args):
        return self.csi("1m", *args)

    def dim(self, *args):
        return self.csi("2m", *args)

    def italics(self, *args):
        return self.csi("3m", *args)

    def underline(self, *args):
        return self.csi("4m", *args)

    def blink(self, *args):
        return self.csi("5m", *args)

    def blinking(self, *args):
        return self.csi("6m", *args)

    def invert(self, *args):
        return self.csi("7m", *args)

    def invisible(self, *args):
        return self.csi("8m", *args)

    def strike(self, *args):
        return self.csi("9m", *args)

    # 内置颜色
    def fg_black(self, *args):
        return self.csi("30m", *args)

    def bg_black(self, *args):
        return self.csi("40m", *args)

    def fg_red(self, *args):
        return self.csi("31m", *args)

    def bg_red(self, *args):
        return self.csi("41m", *args)

    def fg_green(self, *args):
        return self.csi("32m", *args)

    def bg_green(self, *args):
        return self.csi("42m", *args)

    def fg_yellow(self, *args):
        return self.csi("33m", *args)

    def bg_yellow(self, *args):
        return self.csi("43m", *args)

    def fg_blue(self, *args):
        return self.csi("34m", *args)

    def bg_blue(self, *args):
        return self.csi("44m", *args)

    def fg_magenta(self, *args):
        return self.csi("35m", *args)

    def bg_magenta(self, *args):
        return self.csi("45m", *args)

    def fg_cyan(self, *args):
        return self.csi("36m", *args)

    def bg_cyan(self, *args):
        return self.csi("46m", *args)

    def fg_grey(self, *args):
        return self.csi("37m", *args)

    def bg_grey(self, *args):
        return self.csi("47m", *args)

    # 任意颜色
    def fg_rgb(self, rgb: RGB):
        """### 设置前景文字rgb颜色
        rgb: [0,128,255]"""
        if isinstance(rgb, str):
            rgb = hex2RGB(rgb)
        return self.csi(f"38;2;{rgb[0]};{rgb[1]};{rgb[2]}m")

    def bg_rgb(self, rgb: RGB):
        """### 设置背景rgb颜色
        rgb: [0,128,255]"""
        if isinstance(rgb, str):
            rgb = hex2RGB(rgb)
        return self.csi(f"48;2;{rgb[0]};{rgb[1]};{rgb[2]}m")

    def fg_hex(self, hex: str):
        """### 设置前景文字hex颜色
        hex: 0F0, #CCF, 008AFF, #CCCCFF"""
        rgb = hex2RGB(hex)
        return self.csi(f"38;2;{rgb[0]};{rgb[1]};{rgb[2]}m")

    def bg_hex(self, hex: str):
        """### 设置背景hex颜色
        hex: 0F0, #CCF, 008AFF, #CCCCFF"""
        rgb = hex2RGB(hex)
        return self.csi(f"48;2;{rgb[0]};{rgb[1]};{rgb[2]}m")

    def __str__(self):
        """提取出已设置的样式，并重置样式
        - 包括reset后的 位置、颜色、效果 等所有再次reset前累积的样式
        - 连接在字符串中时，请单独定义且先reset，不要在链式调用里直接打印，否则会加上前面链式调用的样式
        - 建议优先使用Style中的常量、方法"""
        s = self.__str
        self.reset()
        return s

    def makeStyle(
        self,
        fg_color: Union[list[int], tuple[int, int, int], str] = "",
        bg_color: Union[list, tuple[int, int, int], str] = "",
        bold=False,
        italics=False,
        underline=False,
        strike=False,
    ) -> Style:
        """
        ### 生成Style样式类
        - fg_color: 前景色，可rgb、hex
        - bg_color: 前景色，可rgb、hex
        - bold: bool=False 是否加粗
        - italics: bool=False 是否斜体
        - underline: bool=False 是否下划线
        - strike: bool=False 是否删除线
        #### 参数无有效样式时使用前面积累的self.__str作为样式
        - 积累包括loc、效果、前景、背景色的样式，建议先reset()
        """
        sty = self.CSI
        if bold: sty += "1;"
        if italics: sty += "3;"
        if underline: sty += "4;"
        if strike: sty += "9;"
        if sty != self.CSI: sty = sty[:-1] + "m"
        else: sty = ""
        if fg_color:
            if type(fg_color) == str:
                self.fg_hex(fg_color)
            elif type(fg_color) == list or type(fg_color) == tuple:
                self.fg_rgb(fg_color)
            sty += self.__str
        if bg_color:
            if type(bg_color) == str:
                self.bg_hex(bg_color)
            elif type(bg_color) == list or type(bg_color) == tuple:
                self.bg_rgb(bg_color)
            sty += self.__str
        if not sty:
            # 没有参数，则使用前面已写入的样式
            sty = self.__str
        self.reset()
        return Style(sty)

    def use(self, style: Style):
        """使用Style样式"""
        self.write(str(style))
        return self

    def getSize(self):
        """更新并返回终端大小（rows，columns）"""
        try:
            size = get_terminal_size()
            rows, columns = size.lines, size.columns
        except OSError:
            rows, columns = 30, 120
        self.size_row = rows
        self.size_col = columns
        self.height = self.size_row - self.origin_row
        self.width = self.size_col - self.origin_col
        return rows, columns

    def gotoCenterOffset(self, len_str: int, row=-1):
        """光标到基于原点、使所给文本长度居中的 offset 位置"""
        width = self.width or self.size_col
        if len_str >= width:
            offset = 0
        else:
            offset = (width - len_str) // 2
        offset += 1 # 前offset个字符均为空格，到下一个字符开始写入
        if row >= 0:
            self[row, offset]
        else:
            self.col(offset)
        return self

    def alignCenter(self, s: str):
        """使文本居中对齐显示
        - 请勿包含 \\t \\n 等特殊字符"""
        s = s.replace("\t", Tab)
        return self.gotoCenterOffset(getStringWidth(s))(s)

    def alignRight(self, s: str, col=-1):
        """使文本右对齐
        - col: -1: 默认方形最右侧对齐，其他：不占用该格，前一格处右对齐"""
        if col < 0 or col > self.width:
            col = self.width + 1
        offset = col - getStringWidth(s)
        if offset < 0:
            offset = 0
        return self.col(offset)(s)
    
    def valLoc(self, row: int, col: int):
        """将上次loc赋给未指定的值，或检查给定row、col是否有效，有效则跳至该位置 """
        if row < 0: row = self.__row
        elif row > self.height: 
            raise ValueError(f"Beyond the region: Row {row} has exceeded!")
        if col < 0: col = self.__col
        elif col > self.width:
            raise ValueError(f"Beyond the region: Col {col} has exceeded!")
        if row != self.__row or col != self.__col:
            self.loc(row, col)
        return (row, col)
    
    def valSize(self, row: int, col: int, height: int, width: int, h_overflow=0):
        """验证并返回合适的大小
        - h_overflow: 0 不允许溢出，1 允许"""
        maxh = self.height - row + 1
        maxw = self.width - col + 1
        # 如果限制换行，则高度限制在终端内
        if h_overflow == 0:
            if height <= 0 or height > maxh:
                height = maxh
            # elif height > maxh:
            #     raise ValueError(f"Beyond the region: Height {height} has exceeded!")
        # 不限制高度，但默认不超过终端高度
        if height <= 0: 
            height = self.height
        if width <= 0: width = maxw
        elif width > maxw:
            raise ValueError(f"Beyond the region: Width {width} has exceeded!")
        return (height, width)

    def setOrigin(self, row: int, col: int, height=0, width=0, base=0):
        """### 设定新的坐标原点与宽高
        - height, width：未设定则使用终端剩余所有大小
        - base: 0基于Terminal左上角，1基于当前origin位置"""
        if base:
            row += self.origin_row
            col += self.origin_col
        if row + height >= self.size_row and col + width >= self.size_col:
            raise ValueError("Given size is bigger than terminal size!")
        self.origin_row = row
        self.origin_col = col
        self.height = height or self.size_row - self.origin_row
        self.width = width or self.size_col - self.origin_col
        self.loc(0,0)
        return self

    def setOriginTerm(self):
        """恢复原点位置为终端左上角"""
        self.origin_row = 0
        self.origin_col = 0
        self.getSize()
        self.height = self.size_row
        self.width = self.size_col
        return self

    def drawNL(self, nline=1):
        """打印 nline=1 个新行"""
        self.write("\n" * nline)
        return self

    def drawHLine(self, length: int, row=-1, col=-1, mark="─"):
        """在给定位置/光标当前位置生成给定长度的**横线**"""
        row, col = self.valLoc(row, col)
        if col + length -1 > self.width:
            raise ValueError(f"Beyond the region: Given length {length} from col {col} > width {self.width}!")
        self.print(mark * length)
        return self

    def drawVLine(self, length: int, row=-1, col=-1, mark="│", overflow=0):
        """在给定位置/之前设定位置生成给定长度的**竖线**
        - mark="|": 画线使用的字符
        - overflow: 0不允许超出，1超出则换行打印"""
        row, col = self.valLoc(row, col)
        if overflow==0 and row + length - 1> self.height:
            raise ValueError(f"Beyond the region: Given length {length} from row {row} > height {self.height}!")
        line = self.__rcol(col)
        line = line + f'\n{line}'.join([mark]*length)
        return self(line)

    def drawRect(self, height: int, width: int, row=-1, col=-1, as_origin=True):
        """产生一个方形，并设定新的坐标原点"""
        row, col = self.valLoc(row, col)
        # ? 4条边占位，实际w+2，h+2，可写区域为w，h，有超过终端边界风险
        height, width = self.valSize(row, col, height, width)
        if as_origin:
            self.setOrigin(row, col, height, width, True)
            row = col = 0
        reset = self.auto_reset
        self.autoResetOff()
        self[row, col].p("┌").drawHLine(width).p("┐")
        self[row + 1, col].drawVLine(height)[row + 1, col + width + 1].drawVLine(height)
        self[row + height + 1, col].p("└").drawHLine(width).p("┘")
        if reset:
            self.reset()
        self.auto_reset = reset
        return self[1, 1]

    def printLines(self, lines: Union[str, list[str]], height=0, width=0, row=-1, col=-1, overflow=1):
        """在给定坐标处左对齐显示多行文本（直接打印多行文本会使后面的行回到终端最左侧）
        - lines: str | list[str], str会自动被splitlines
        - width: lines为str时生效，换行分割宽度（自身换行符处也会被分割，请勿包含\\t）\n
              未指定则按str中的换行符分割
        - row、col: 行、列位置，未给定则使用上一次设定的位置
        - overflow：=0截断，1...省略，其他继续输出

        注：每行宽度请勿超过该位置终端剩余宽度，确保终端剩余高度超过行数"""
        row, col = self.valLoc(row, col)
        height, width = self.valSize(row, col, height, width)
        if isinstance(lines, str):
            if width:
                lines = lines.replace("\t", Tab)
                lines = splitLinesByWidth(lines, width)
            else:
                lines = lines.splitlines()
        else:
            # 处理 宽度 溢出，str时splitLinesByWidth已确保宽度不溢出
            for i in range(len(lines)):
                diff = getStringWidth(lines[i]) - width
                if diff > 0:
                    if overflow == 1: lines[i] = lines[i][:-diff-3]+"..."
                    elif overflow == 0: lines[i] = lines[i][:-diff]
        # 处理 高度 溢出
        if len(lines) > height:
            if overflow == 1:
                lines = lines[:height]
                lastline = lines[height-1]
                lines[height-1] = lastline[:-3]+"..."
            elif overflow == 0:
                lines = lines[:height]
        strcol = self.__rcol(col)
        lines[0] = strcol + lines[0]
        string = f'\n{strcol}'.join(lines)
        return self(string)

    def drawHGrad(self, color_start: RGB, color_end: RGB, length=0, string="", row=-1, col=-1):
        """产生一条给定长度的水平渐变色带
        - 至少提供 length、string 中的一个
        - string中的双宽字符会占据两个宽度，但只有一个色块"""
        string = string.replace("\t", Tab)
        blank = 0
        if not length:
            length = getStringWidth(string)
        if not string:
            blank = 1
            string = " " * length
        string = padString(string, length)
        if not length:
            raise ValueError("Parameter length and string not found.")
        row, col = self.valLoc(row, col)
        if length + col - 1 > self.width:
            raise ValueError(f"Beyond the region: length {length} from col {col} > {self.width}.")
        gradient = genGradient(color_start, color_end, length)
        if blank:
            return self(''.join([f'{bg_rgb(color)} ' for color in gradient]))
        i, n_wc, linelist = 0, 0, []
        while i < length:
            chr = string[i - n_wc]
            linelist.append(f'{bg_rgb(gradient[i])}{chr}')
            if getCharWidth(chr) == 2:
                n_wc += 1
                i += 1
            i += 1
        return self(''.join(linelist))

    def drawVGrad(self, color_start: RGB, color_end: RGB, length=0, row=-1, col=-1, overflow=0):
        """产生一条给定长度的垂直渐变色带
        - overflow: 0不允许超出，1超出则换行打印"""
        if length <= 0:
            raise ValueError("Parameter length are invalid.")
        double = length * 2
        gradient = genGradient(color_start, color_end, double)
        row, col = self.valLoc(row, col)
        if overflow==0 and row + length - 1> self.height:
            raise ValueError(f"Beyond the region: Given length {length} from row {row} > height {self.height}!")
        strcol = self.__rcol(col)
        line = strcol + f'{self.RESET}\n{strcol}'.join([f'{bg_rgb(gradient[i])}{fg_rgb(gradient[i+1])}▄' for i in range(0, double, 2)])
        return self(line)

    def drawImage(self, img_path: Union[str, Image.Image], row=-1, col=-1, height=0, width=0, resample=1, overflow=0, print=1):
        """### 在终端绘制图片
        - img_path: 图片路径 / Image对象
        - row, col: 起始位置(默认使用loc设定的光标位置)
        - height, width: 最大宽度、高度(字符数，0表示自动)
        - resample: 图片重采样方法（向下质量越高，默认1，保留锯齿棱角选0）
            - NEAREST = 0
            - BOX = 4
            - BILINEAR = 2
            - HAMMING = 5
            - BICUBIC = 3
            - LANCZOS = 1
        - overflow=0: 0不允许高度超出，1超出则换行打印 （宽度超出没意义）

        Returns: string, Area 图像转义序列，终端显示图片的位置、大小"""
        row, col = self.valLoc(row, col)
        height, width = self.valSize(row, col, height, width, h_overflow=overflow)
        img = getIMG(img_path, height=height * 2, width=width, resample=resample)
        width, height = img.size # 经过getIMG处理，height一定为偶数
        pixels = img.load()

        ret_nl = self.RESET + "\n"
        prt_nl = ret_nl + self.__rcol(col)
        lines = [''.join(
                [f'{bg_rgb(pixels[c, r])}{fg_rgb(pixels[c, r + 1])}▄' for c in range(width)]
            ) for r in range(0, height, 2)]
        if print: self(prt_nl.join(lines))
        return ret_nl.join(lines), Area(row, col, height // 2, width)
    
    def drawImageStr(self, image: Union[str, Image.Image], row=-1, col=-1, width=0, height=0, chars='basic', resample=1, invert_background=False, overflow=0, print=1):
        """ ### 使用ASCII字符绘制灰度图
        - image: 图片路径 / Image
        - row, col: 绘制起点位置(默认使用loc设定的光标位置)
        - width, height: 最大宽度、高度(字符数，0表示自动)
        - chars：优先使用Output.CHARSET中定义的字符集，如果不存在则使用给定的（由暗至亮排列），默认为basic: ' .:-=+*#%@'
        - resample: 图片重采样方法（向下质量越高，默认1，保留锯齿棱角选0）
        - invert_background=False 反相
        - overflow=0: 0不允许高度超出，1超出则换行打印 
        
        Returns: str 用chars构成的图片灰度图"""
        row, col = self.valLoc(row, col)
        height, width = self.valSize(row, col, height, width, h_overflow=overflow)
        image = getIMG(image, height=height * 2, width=width, resample=resample)
        width, height = image.size
        image = image.convert('L')
        pix = image.getdata()

        if chars in self.CHARSET:
            chars = self.CHARSET[chars]
        if invert_background:
            chars = list(reversed(chars))
        tmp = 255 / len(chars) # 256色分给chars，值越大越亮，字符越密
        div = int(tmp) # 和下句共同构成math.ceil效果
        if div != tmp: div += 1

        ret_nl = "\n"
        prt_nl = ret_nl + self.__rcol(col)
        lines = [''.join([chars[pix[r * width + c]//div] for c in range(width)]) for r in range(0, height, 2)]
        if print: self(prt_nl.join(lines))
        return ret_nl.join(lines), Area(row, col, height//2, width)

    def playGif(self, gif_path, row=-1, col=-1, width=0, height=0, repeat=1):
        """### 播放gif动画
        - 将隐藏光标，播放完毕后恢复
        - Returns: (帧数，播放用时，播放Area) 用时不包准备时间"""
        row, col = self.valLoc(row, col)
        height, width = self.valSize(row, col, height, width)
        gif = toImage(gif_path)
        self.hideCursor()
        frames = int(gif.n_frames)
        t0 = time.perf_counter()
        try:
            for r in range(repeat):
                ft = FrameTimer(frames)
                for i, _ in ft:
                    gif.seek(i)
                    duration = gif.info.get('duration', 0) / 1000
                    s, area = self[row, col].drawImage(gif, row=row, col=col, width=width, height=height, resample=0)
                    ft.frameTime(duration)
            height, width = area.height, area.width
        except Exception as e:
            self.printLines(f'Failed to play "{gif_path}": {e}.', width=width, row=row, col=col)
        total_time = time.perf_counter() - t0
        self.showCursor()
        return frames, total_time, Area(row, col, height, width)

    def playVideo(self, video_path, row=-1, col=-1, width=0, height=0, display_info=False):
        """### 播放视频：使用cv2打开视频获取帧转化为Image呈现
        - 将隐藏光标，播放完毕后恢复
        - display_info: 是否同时显示 视频播放信息
        - Returns: (帧数，播放用时，播放Area) 用时不包准备时间"""
        row, col = self.valLoc(row, col)
        height, width = self.valSize(row, col, height, width)
        self.hideCursor()
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Failed to open {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        duration = 1/fps
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        audio = Audio(video_path) # 解析数据需要时间
        audio.play() # 另开一个线程播放
        t0 = time.perf_counter()
        
        try:
            ft = FrameTimer()
            for i, _ in ft:
                ret, frame = cap.read()
                if not ret:
                    break
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(rgb_frame)
                s, area = self[row, col].drawImage(pil_image, row=row, col=col, width=width, height=height, resample=0)
                if display_info: 
                    self[self.height-2,1](f'time cost/dura frame/total  fps ')
                    self[self.height-1,1](f' {ft.frame_spent:.4f}/{duration:.4f} {i:>5d}/{frame_count:<5d} {fps:3.1f} ')
                ft.frameTime(duration)
            height, width = area.height, area.width
        except Exception as e:
            self.printLines(f'Failed to play "{video_path}": {e}.', width=width, row=row, col=col)
        total_time = time.perf_counter() - t0
        cap.release()
        self.showCursor()
        return frame_count, total_time, Area(row, col, height, width)
    
    def clearRegion(self, height:int, width:int, row=-1, col=-1):
        """### 清除一个区域
        - 用空格清除指定位置大小的内容"""
        row, col = self.valLoc(row, col)
        height, width = self.valSize(row, col, height, width)
        line = self.__rcol(col) + ' ' * width
        lines = '\n'.join([line]*height)
        return self(lines)
        
    # with上下文管理
    def __enter__(self):
        self.__auto_reset = self.auto_reset
        self.autoResetOff()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.reset()
        if self.__auto_reset:
            self.autoResetOn()
        return True

    def test(self):
        """测试终端能显示的指令\\033[0-109m"""
        n = 0
        for i in [0, 2, 3, 4, 9, 10]:
            line = ""
            for j in range(10):
                n = (10 * i) + j
                line += "\033[%dm %3d \033[0m" % (n, n)
            self.alignCenter(line + "\n")
        return self
    
    # 日志记录
    # def log(self):
    #     pass
    # def logError(self, s, time=True, trace=True)


prt = Output()


def NbCmdIO(test=False):
    lavender = "#ccf"
    # 清屏并设置终端标题
    prt.cls().setTitle("NbCmdIO")
    # 在第2行 加粗 文字蓝色 居中显示  背景色渐变
    title = "        NbCmdIO  by  Cipen        "
    prt[2].bold().fg_hex("#00f").gotoCenterOffset(getStringWidth(title), 2)
    prt.drawHGrad((230, 92, 0), (249, 212, 35), string=title)
    WIDTH = 40
    HEIGHT = 10
    center_offset = (prt.size_col - WIDTH) // 2
    # 以前景#CCF 在 3,centerOffset 处 绘制指定大小的方形，并默认设定新区域 为该方形
    prt.fg_hex(lavender)[3, center_offset].drawRect(HEIGHT, WIDTH)
    prt.fg_blue()[0, 3](" NbCmdIO ").bold()[0, WIDTH - 8](prt.__version__)
    b2 = "  "
    # 进入上下文（里面不会自动重置样式），在区域的4个角添加方形色块
    with prt.bg_hex(lavender):
        prt[1, 1](b2)[1, WIDTH - 1](b2)
        prt[HEIGHT, 1](b2)[HEIGHT, WIDTH - 1](b2)
    # 字符串内添加样式（务必：字符单独定义，不要在链式调用里直接打印）
    line1 = f"Welcome to {prt.bold().bg_hex(lavender).fg_hex('#000')} NbCmdIO "
    line2 = "Print your string colorfully!"
    # 保存并使用样式（样式将包括位置、颜色、效果）
    head_style = prt.fg_red().bold().makeStyle()
    prt[1].use(head_style).alignCenter(line1)  # 在新区域第一行使用样式居中显示文本
    prt[2].use(head_style).alignCenter(line2)
    prt[3, 3].fg_grey().drawHLine(WIDTH - 4)

    text = r"""
 _____    _____    _______ 
|  _  \  |  _  \  |__   __|
| |__) | | |__) |    | |   
|  __ /  |  _  <     | |   
| |      | | \ \     | |   
|_|      |_|  \_\    |_|   """[1:]
    lines = text.splitlines()
    chr1 = [l[:8] for l in lines]
    chr2 = [l[8:18] for l in lines]
    chr3 = [l[18:] for l in lines]
    prt.fg_red().bold()[4, 8].printLines(chr1)
    prt.fg_green().bold()[4, 16].printLines(chr2)
    prt.fg_blue().bold()[4, 25].printLines(chr3)

    # 光标跳至本区域下一行，结束
    prt[HEIGHT + 1].setOriginTerm().end()
    if test:
        prt.gotoCenterOffset(50)
        # 画一条渐变带，然后下移2行，测试终端对颜色效果的支持情况
        prt.drawHGrad((51, 101, 211), (190, 240, 72), 50).end(2)
        prt.test().end()
