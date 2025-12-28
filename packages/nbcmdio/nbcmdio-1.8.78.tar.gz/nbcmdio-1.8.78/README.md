# NbCmdIO: 终端色彩与交互的强大工具

<div align="center">

[![English](https://img.shields.io/badge/Readme-English-blue?style=for-the-badge&logo=googledocs&logoColor=white)](https://github.com/YXPHOPE/NbCmdIO/blob/main/README.en.md)
[![PyPI Version](https://img.shields.io/pypi/v/nbcmdio?style=for-the-badge&logo=pypi)](https://pypi.org/project/nbcmdio/)
[![License](https://img.shields.io/pypi/l/nbcmdio?style=for-the-badge&logo=opensourceinitiative)](https://github.com/YXPHOPE/NbCmdIO/blob/main/LICENSE)

[![Downloads](https://img.shields.io/pypi/dm/nbcmdio?style=for-the-badge&logo=hono)](https://pypi.org/project/nbcmdio/)
[![Python Versions](https://img.shields.io/pypi/pyversions/nbcmdio?style=for-the-badge&logo=python)](https://www.python.org/)

![Terminal Art](./assets/NbCmdIO.png)

</div>

**NbCmdIO** 是一个强大的Python库，将普通的命令行终端转变为充满活力的视觉画布和强大的交互平台！告别单调的黑白输出，迎接RGB真彩世界；告别笨重的文本界面，迎接精准的光标控制和输入捕获能力。

**关键字**：Terminal, CSI escape sequence, print, colorful, input, cursor, draw, Image, Gif

## 🌟 核心功能亮点

### ⚡ 支持链式调用

- 随时随地，设置光标位置、样式，方便快捷、清晰易读！

```python
prt[row, col].bold().fg_red("text")
```

### 🎨 真彩RGB终端着色

- 支持以24位RGB、HEX格式设定前景色、背景色
- 支持默认颜色：Black、Red、Green等
- 支持Bold、Underline、Italics等效果
- 真彩显示图片，单字符显示两个像素点大大提升分辨率
  ![nbcmdio.prt.drawIMG](./assets/drawDoraemon.png)
- 显示ASCII灰度图片

### 🖱️ 字符级光标控制

- 精确到字符的光标定位
- 保存/恢复光标位置
- 获取光标位置

### 📦 动态区域管理

- 创建独立更新区域
- 嵌套区域支持

### ⌨️ 输入捕获（...ing）

- 单键无缓冲读取
- 快捷键组合检测

## 🚀 快速入门

### 安装

```bash
pip install nbcmdio
```

### 基础使用

- 命令行用法:

```bash
# 清屏然后 绘制图片
prt cls drawImage "path/to/image/file"

# 前景#CCF粗体居中打印
prt fg_hex CCF bold alignCenter "Hello!"

# 列出所有可用函数
prt list

# 获取function的帮助信息
prt help <function>
```

- Python:

```python
from nbcmdio import prt

def NbCmdIO():
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
    prt.gotoCenterOffset(50)
    # 画一条渐变带，然后下移2行，测试终端对颜色效果的支持情况
    prt.drawHGrad((51, 101, 211), (190, 240, 72), 50).end(2)
    prt.test().end()

NbCmdIO()
```

## 🔮 未来路线图

| 版本 | 功能                  | 状态        |
| ---- | --------------------- | ----------- |
| v1.0 | RGB色彩支持、区域管理 | ✅ 已发布   |
| v1.9 | Progress进度条        | ⏳  进行中 |
| v2.0 | 输入捕获系统          | 📅 规划中   |
| v3.0 | 终端UI组件库          | 💡  构思中 |

**近期计划**

* [ ] Progress bar
* [ ] Customized Exception info
* [ ] Async operation

## 🌍 社区贡献

我们欢迎各种形式的贡献！无论您是：

- 发现并报告问题
- 提交功能请求
- 贡献代码
- 创作文档
- 分享创意用例

## 📜 开源协议

NbCmdIO采用**MIT许可证** - 您可以自由地在商业和个人项目中使用它！

## ✨ 立即体验终端魔法！

```bash
pip install nbcmdio
```

准备好将您的命令行体验提升到全新维度了吗？NbCmdIO正在等待为您的终端注入生命！

---

## 📜 更新日志

- 1.8.1 完成Output的所有基本功能，一次性更新
- 1.8.2 初开Input的单键无缓冲读取功能
- 1.8.3 修复部分问题，添加快捷ps1批处理文件，分离style
- 1.8.4 添加多行区域打印，分离utils
- 1.8.5 feat: drawHGrad(渐变), drawIMG(终端显示图片)
- 1.8.6 improve: 增加 loc, size 的有效性验证；
  feat: drawImageStr ASCII绘制灰度图
- 1.8.63 feat: Output.playGif, 播放gif动画
- 1.8.64 fix: Output.valSize, 高度溢出
- 1.8.7 big change: 许多函数把height参数提到width前了；
  add: Area, Output.clearRegion 清除区域；
  fix: 一些小问题
- 1.8.71 feat: FrameTimer, 用于Output.playGif
- 1.8.72 add: utils.getIMG支持url；
  improve: utils.FrameTimer支持特定帧时长; Output.playGif使用gif帧时长.
- 1.8.73 fix: Output.gotoCenterOffset; 高度溢出;
- 1.8.74 fix: Output.drawImageStr的返回值；
  add: Output.setFile: file=None, flush；
  fix: Output.print: 分块写入；
  update: 系统类型配置
- 1.8.75 improve: 性能提升2.31倍（相较于1.8.74，提供474x474的RGB格式Image对象，Output.drawImage直接输出该大小图像时）
- 1.8.76 add: 提供命令行工具prt
- 1.8.77 fix: 改进prt参数解析
- 1.8.78 add: playVideo 播放视频

## 🙏 致谢

- **[colorama](https://github.com/tartley/colorama)** 借鉴CSI设置终端标题的方法
- **[timg](https://github.com/adzierzanowski/timg)** 借鉴ASCII方法绘制灰度图片，并指出修复[问题#4](https://github.com/adzierzanowski/timg/issues/4)
- **[curses](https://github.com/zephyrproject-rtos/windows-curses)** 借鉴hline、vline、rectangle方法
