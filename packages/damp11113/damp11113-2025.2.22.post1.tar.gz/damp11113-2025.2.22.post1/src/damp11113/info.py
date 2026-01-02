"""
damp11113-library - A Utils library and Easy to use. For more info visit https://github.com/damp11113/damp11113-library/wiki
Copyright (C) 2021-present damp11113 (MIT)

Visit https://github.com/damp11113/damp11113-library

MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import sys
import platform
import os
import time
import psutil
import cpuinfo
import GPUtil
from .utils import get_format_time3, TextFormatter

__version__ = '2025.2.22' # 2025 | 2 revisions in year | 22 file (no __init__.py count)

def pyversion(fullpython=False, fullversion=False, tags=False, date=False, compiler=False, implementation=False, revision=False):
    if fullpython:
        return f'Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} {sys.version_info.releaselevel} {platform.python_build()[0]} {platform.python_build()[1]} {platform.python_compiler()} {platform.python_implementation()} {platform.python_revision()}'
    if fullversion:
        return f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}'
    if tags:
        return platform.python_build()[0]
    if date:
        return platform.python_build()[1]
    if compiler:
        return platform.python_compiler()
    if implementation:
        return platform.python_implementation()
    if revision:
        return platform.python_revision()
    return f'{sys.version_info.major}.{sys.version_info.minor}'

def osversion(fullos=False, fullversion=False, type=False, cuser=False, hostname=False, uptime=False, kernel=False):
    if fullos:
        return f'{os.getlogin()}@{platform.node()} on {platform.platform()} {platform.machine()} {platform.architecture()[0]}'
    elif fullversion:
        return f'{platform.system()} {platform.version()}'
    elif type:
        return platform.architecture()[0]
    elif hostname:
        return platform.node()
    elif cuser:
        return os.getlogin()
    elif uptime:
        boot_time_seconds = psutil.boot_time()
        uptime_seconds = time.time() - boot_time_seconds
        return get_format_time3(int(uptime_seconds))
    elif kernel:
        return os.name
    else:
        return platform.release()

def hardwareinfo(cpu=False, gpu=False, ram=False):
    if cpu:
        return (cpuinfo.get_cpu_info()["brand_raw"], cpuinfo.get_cpu_info()["arch"], cpuinfo.get_cpu_info()["bits"])
    elif gpu:
        gpus = GPUtil.getGPUs()
        return (gpus[0].name, gpus[0].memoryTotal, gpus[0].load)
    elif ram:
        memory = psutil.virtual_memory()
        return (memory.total / (1024 * 1024 * 1024), memory.available / (1024 * 1024 * 1024), memory.used / (1024 * 1024 * 1024))

class pyofetch:
    def __init__(self):
        RESET = TextFormatter.RESET
        BOLD = TextFormatter.TEXT_ATTRIBUTES["bold"]

        BLACK = TextFormatter.TEXT_COLORS["black"]
        RED = TextFormatter.TEXT_COLORS["red"]
        GREEN = TextFormatter.TEXT_COLORS["green"]
        YELLOW = TextFormatter.TEXT_COLORS["yellow"]
        BLUE = TextFormatter.TEXT_COLORS["blue"]
        MAGENTA = TextFormatter.TEXT_COLORS["magenta"]
        CYAN = TextFormatter.TEXT_COLORS["cyan"]
        WHITE = TextFormatter.TEXT_COLORS["white"]

        self.ASCII_LOGO = [
            "                ",
            "    {}████████{}    ".format(YELLOW+BOLD, RESET),
            "  {}██{}{}████████{}{}██{}  ".format(WHITE, RESET, YELLOW+BOLD, RESET, WHITE, RESET),
            "{}████{}{}████████{}{}████{}".format(YELLOW+BOLD, RESET, YELLOW, RESET, YELLOW+BOLD, RESET),
            "{}██{}{}██{}{}██{}{}████████{}{}██{}".format(YELLOW+BOLD, RESET, YELLOW, RESET, BLACK+BOLD, RESET, YELLOW, RESET, YELLOW+BOLD, RESET),
            "{}██{}██{}  {}██{}{}██{}  {}██{}██{}".format(YELLOW, WHITE, RESET, BLACK+BOLD, RESET, YELLOW, RESET, WHITE, YELLOW, RESET),
            "{}██{}██{}  {}████{}  {}██{}██{}".format(YELLOW, WHITE, RESET, BLACK+BOLD, RESET, WHITE, YELLOW, RESET),
            "{}████████████████{}".format(BLACK+BOLD, RESET),
            "{}████████████████{}".format(BLACK+BOLD, RESET),
            "                ",
        ]

        D_COLORS = [BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE]
        B_COLORS = [c[:-1] + ";1m" for c in D_COLORS]

        self.bright_colors = [color + "███" for color in B_COLORS]
        self.dark_colors = [color + "███" for color in D_COLORS]
        self.RESET = RESET

    def render(self, info, ascii_logo):
        combined_lines = []

        # Adjust lengths of lists to match
        if len(ascii_logo) < len(info):
            for _ in range(len(info) - len(ascii_logo)):
                ascii_logo.append(" " * len(ascii_logo[0]))
        elif len(ascii_logo) > len(info):
            for _ in range(len(ascii_logo) - len(info)):
                info.append(" ")

        # Combine lines of ascii_logo and info
        for (art_line, info_line) in zip(ascii_logo, info):
            combined_lines.append("{} {}".format(art_line, info_line))

        return combined_lines

    def info(self, moreinfo="", Itext_theme="yellow", text_theme="cyan", logo=None):
        userhost = TextFormatter.format_text(osversion(cuser=True), color=text_theme) + TextFormatter.format_text("@", color=Itext_theme) + TextFormatter.format_text(osversion(hostname=True), color=text_theme)
        unformatuserhost = osversion(cuser=True) + "@" + osversion(hostname=True)
        CPU, _, _ = hardwareinfo(cpu=True)
        GPU, _, _ = hardwareinfo(gpu=True)
        ram, _, ramuse = hardwareinfo(ram=True)

        allinfo = [
            f"{userhost}",
            f"{TextFormatter.format_text('-'*len(unformatuserhost), color=text_theme)}",
            f"{TextFormatter.format_text('OS', color=Itext_theme)}: {TextFormatter.format_text(osversion(fullversion=True), color=text_theme)}",
            f"{TextFormatter.format_text('Kernel', color=Itext_theme)}: {TextFormatter.format_text(osversion(kernel=True), color=text_theme)}",
            f"{TextFormatter.format_text('Uptime', color=Itext_theme)}: {TextFormatter.format_text(osversion(uptime=True), color=text_theme)}",
            f"{TextFormatter.format_text('CPU', color=Itext_theme)}: {TextFormatter.format_text(CPU, color=text_theme)}",
            f"{TextFormatter.format_text('GPU', color=Itext_theme)}: {TextFormatter.format_text(GPU, color=text_theme)}",
            f"{TextFormatter.format_text('Memory', color=Itext_theme)}: {TextFormatter.format_text(f'{ramuse:.2f} GB / {ram:.2f} GB', color=text_theme)}",
            f"{TextFormatter.format_text('-'*len(unformatuserhost), color=text_theme)}",
            f"{TextFormatter.format_text('Runtime', color=Itext_theme)}: {TextFormatter.format_text('Python ' + pyversion(fullversion=True), color=text_theme)}",
            f"{TextFormatter.format_text('Library Version', color=Itext_theme)}: {TextFormatter.format_text(__version__, color=text_theme)}",
            moreinfo,
            " ",
            "".join(self.dark_colors) + self.RESET,
            "".join(self.bright_colors) + self.RESET,
        ]
        if logo is None:
            return self.render(allinfo, self.ASCII_LOGO)
        else:
            return self.render(allinfo, logo)
