import re
import os
from setuptools import setup, find_packages

VERSION = "1.8.78"
long_desc = open("README.en.md", encoding="utf-8").read()


def replaceFile(filename, pattern, repl):
    with open(filename, "rt", encoding="utf-8") as f:
        content = f.read()
    if isinstance(pattern, tuple):
        s = content.find(pattern[0])
        e = content.find(pattern[1], s) + len(pattern[1])
        content = content[:s] + repl + content[e:]
    else:
        content = re.sub(pattern, repl, content)
    with open(filename, "wt", encoding="utf-8") as f:
        f.write(content)
    return content


# 切换目录
os.chdir(os.path.dirname(__file__))

# 更新版本号
replaceFile("nbcmdio/__init__.py", r'__version__ = ".*"', f'__version__ = "{VERSION}"')
content = replaceFile(
    "nbcmdio/output.py", r'__version__ = ".*"', f'__version__ = "{VERSION}"'
)

setup(
    name="nbcmdio",
    version=VERSION,
    author="Cipen",
    author_email="faithyxp@foxmail.com",
    description="一个在终端中输出色彩斑斓、颜色多样内容以及快捷输入的强大工具。"
    "A powerful tool for outputting colorful content and enabling quick input in the terminal.",
    long_description=long_desc,
    long_description_content_type="text/markdown",
    url="https://github.com/YXPHOPE/NbCmdIO",
    packages=find_packages(),  # 自动发现包
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    entry_points={
        'console_scripts': [
            'prt=nbcmdio.cli:cli',
        ],
    }
)
