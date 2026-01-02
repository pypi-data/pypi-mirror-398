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
import operator
import time
import sys
from functools import reduce
from inspect import getmembers, isfunction
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from shutil import get_terminal_size
from decimal import Decimal, getcontext

textt = """Unhandled exception has occurred in your application.If you click\nContinue,the application will ignore this error and attempt to continue.\nIf you click Quit,the application will close immediately.\n"""

def emb(info, details=None, text=textt, title='python', standalone=True):
    if standalone:
        app = QApplication(sys.argv)

    msg = QMessageBox()

    msg.setEscapeButton(QMessageBox.Close)
    msg.setIcon(QMessageBox.Critical)

    msg.setText(text)
    msg.setInformativeText(info)
    msg.setWindowTitle(title)

    if details is not None:
        msg.setDetailedText(details)

    msg.addButton(QPushButton('Continue'), QMessageBox.YesRole)
    msg.addButton(QPushButton('Quit'), QMessageBox.NoRole)

    retval = msg.exec_()

    if retval == 0:
        return True
    else:
        exit()

def get_size_unit(bytes):
    for unit in ['', 'K', 'M', 'G', 'T', 'P']:
        if bytes < 1024:
            return f"{bytes:.2f} {unit}B/s"
        bytes /= 1024

def get_size_unit2(number, unitp, persec=True, unitsize=1024, decimal=True, space=" "):
    for unit in ['', 'K', 'M', 'G', 'T', 'P']:
        if number < unitsize:
            if decimal:
                num = f"{number:.2f}"
            else:
                num = int(number)

            if persec:
                return f"{num}{space}{unit}{unitp}/s"
            else:
                return f"{num}{space}{unit}{unitp}"
        number /= unitsize

def get_percent_completed(current, total):
    return round((current * 100) / total)

def textonumber(text):
    l = []
    tl = list(text)
    for i in tl:
        l.append(ord(i))
    return ''.join(str(v) for v in l)

def numbertotext(numbers):
    l = []
    for i in range(0, len(numbers), 2):
        l.append(chr(int(numbers[i:i+2])))
    return ''.join(l)

def Amap(x, in_min, in_max, out_min, out_max):
    try:
        return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
    except:
        return 0

def get_remaining_time(current, total):
    if total == 0:
        return None
    else:
        totalMin = 1440 - 60 * current - total
        hoursRemaining = totalMin // 60
        minRemaining = totalMin % 60
        return (hoursRemaining, minRemaining)

def isAscii(string):
    return reduce(operator.and_, [ord(x) < 256 for x in string], True)

def get_all_func_in_module(module):
    func = []
    for i in getmembers(module, isfunction):
        func.append(i[0])
    return func
    
def get_format_time(sec):
    if sec >= 31557600: # years
        m, s = divmod(sec, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        y, d = divmod(d, 365)
        return f"{y}y {d}d {h}h {m}m {s}s"
    elif sec >= 2628002: # months
        m, s = divmod(sec, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        mo, d = divmod(d, 30)
        return f"{mo}mo {d}d {h}h {m}m {s}s"
    elif sec >= 604800:# weeks
        m, s = divmod(sec, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        w, d = divmod(d, 7)
        return f"{w}w {d}d {h}h {m}m {s}s"
    elif sec >= 86400: # days
        m, s = divmod(sec, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        return f"{d}d {h}h {m}m {s}s"
    elif sec >= 3600:# hours
        m, s = divmod(sec, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        return f"{h}h {m}m {s}s"
    elif sec >= 60: # minutes
        m, s = divmod(sec, 60)
        h, m = divmod(m, 60)
        return f"{m}m {s}s"
    else:
        return f"{sec}s"

def get_format_time2(sec):
    if sec >= 31557600: # years
        m, s = divmod(sec, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        y, d = divmod(d, 365)
        return f"{y}y {d}d {str(h).zfill(2)}:{str(m).zfill(2)}:{str(sec).zfill(2)}"
    elif sec >= 2628002: # months
        m, s = divmod(sec, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        mo, d = divmod(d, 30)
        return f"{mo}mo {d}d {str(h).zfill(2)}:{str(m).zfill(2)}:{str(sec).zfill(2)}"
    elif sec >= 604800:# weeks
        m, s = divmod(sec, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        w, d = divmod(d, 7)
        return f"{w}w {d}d {str(h).zfill(2)}:{str(m).zfill(2)}:{str(sec).zfill(2)}"
    elif sec >= 86400: # days
        m, s = divmod(sec, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        return f"{d}d {str(h).zfill(2)}:{str(m).zfill(2)}:{str(sec).zfill(2)}"
    elif sec >= 3600:# hours
        m, s = divmod(sec, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        return f"{str(h).zfill(2)}:{str(m).zfill(2)}:{str(sec).zfill(2)}"
    elif sec >= 60: # minutes
        m, s = divmod(sec, 60)
        h, m = divmod(m, 60)
        return f"{str(m).zfill(2)}:{str(sec).zfill(2)}"
    else:
        return f"00:{str(sec).zfill(2)}"

def get_format_time3(sec):
    if sec >= 31557600: # years
        m, s = divmod(sec, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        y, d = divmod(d, 365)
        return f"{y} years, {d} days, {h} hour, {m} minutes, {s} seconds"
    elif sec >= 2628002: # months
        m, s = divmod(sec, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        mo, d = divmod(d, 30)
        return f"{mo} months, {d} days, {h} hour, {m} minutes, {s} seconds"
    elif sec >= 604800:# weeks
        m, s = divmod(sec, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        w, d = divmod(d, 7)
        return f"{w} weeks, {d} days, {h} hour, {m} minutes, {s} seconds"
    elif sec >= 86400: # days
        m, s = divmod(sec, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        return f"{d} days, {h} hour, {m} minutes, {s} seconds"
    elif sec >= 3600:# hours
        m, s = divmod(sec, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        return f"{h} hour, {m} minutes, {s} seconds"
    elif sec >= 60: # minutes
        m, s = divmod(sec, 60)
        h, m = divmod(m, 60)
        return f"{m} minutes, {s} seconds"
    else:
        return f"{sec} seconds"

def addStringEveryN(original_string, add_string, n):
    # Input validation
    if not isinstance(original_string, str) or not isinstance(add_string, str):
        raise TypeError("Both original_string and add_string must be strings.")
    if not isinstance(n, int) or n <= 0:
        raise ValueError("n must be a positive integer.")

    chunks = [original_string[i:i+n] for i in range(0, len(original_string), n)]
    result = add_string.join(chunks)
    return result

def findStringDifferencesInList(list1, list2):
    # Find the differences between the sets
    return list(set(list1).symmetric_difference(set(list2)))

def replaceEnterWithCrlf(input_string):
    if '\n' in input_string:
        input_string = input_string.replace('\n', '\r\n')
    return input_string

def scrollTextBySteps(text, scrollstep, scrollspace=10):
    if len(text) < scrollspace:
        raise ValueError("text is shorter than scroll space")
    if len(text) < scrollstep:
        raise ValueError("text is shorter than scroll step")

    scrolled_text = text
    scrolled = ""

    for _ in range(0, scrollstep+1):
        scrolled = f"{scrolled_text[:scrollspace]:<{scrollspace}}"

        # Shift the text by one character to the right
        scrolled_text = scrolled_text[1:] + scrolled_text[0]

        # Add a space at the end if the text length is less than 8 characters
        if len(scrolled_text) < scrollspace:
            scrolled_text += " "

    return scrolled

def scrollTextBySteps_yield(text, scrollspace=10, max_loops=None, clearspace=False):
    if len(text) < scrollspace:
        raise ValueError("text is shorter than scroll space")
    if clearspace:
        text = text + " " * scrollspace

    scrolled_text = text
    text_length = len(text)
    loop_count = 0
    scroll_length = text_length  # Full scroll loop when text has shifted completely

    while True:
        # Prepare the scrolled text
        scrolled = f"{scrolled_text[:scrollspace]:<{scrollspace}}"
        yield scrolled  # Yield the current scrolled text

        # Shift the text by one character to the right
        scrolled_text = scrolled_text[1:] + scrolled_text[0]

        # If max_loops is set, stop when loop_count reaches max_loops
        if max_loops is not None and loop_count >= max_loops:
            break

        # Increment the loop count if we return to the original text position
        scroll_length -= 1
        if scroll_length == 0:
            loop_count += 1
            scroll_length = text_length  # Reset the scroll length for the next loop

def calculate_pi(n):
    getcontext().prec = 50  # Set precision to 50 decimal places
    pi = Decimal(0)
    for k in range(n):
        pi += Decimal(1) / (16 ** k) * (
            Decimal(4) / (8 * k + 1) - Decimal(2) / (8 * k + 4) - Decimal(1) / (8 * k + 5) - Decimal(1) / (8 * k + 6)
        )
    return pi

def findMedian(list_numbers: list):
    list_numbers.sort()
    length = len(list_numbers)
    if length % 2 == 0:
        return (list_numbers[length // 2 - 1] + list_numbers[length // 2]) / 2
    else:
        return list_numbers[length // 2]

def stemLeafPlot(data):
    stems = {}
    result = ""

    for num in data:
        stem = num // 10
        leaf = num % 10
        if stem not in stems:
            stems[stem] = []
        stems[stem].append(leaf)

    for stem, leaves in sorted(stems.items()):
        result += f"{stem} | {' '.join(map(str, sorted(leaves)))}\n"

    return result

def dotPlot(data, dot=". ", showlable=True):
    max_value = max(data)
    dot_plot = ''

    for i in range(max_value, 0, -1):
        row = ''
        for value in data:
            if value >= i:
                row += dot  # Use a dot to represent the value
            else:
                row += ' ' * len(dot)  # Use empty space if the value is lower
        dot_plot += row + '\n'

    if showlable:
        x_axis_labels = ' '.join(str(i) for i in range(1, len(data) + 1))
        dot_plot += x_axis_labels + '\n'

    return dot_plot

def texttable(data):
    table_str = ""

    # Calculate the width of each column based on the maximum length of data in each column
    col_width = [max(len(str(row[i])) for row in data) for i in range(len(data[0]))]

    # Create table header
    for i in range(len(data[0])):
        table_str += str(data[0][i]).ljust(col_width[i]) + ' '
    table_str += '\n'

    # Create separator
    for width in col_width:
        table_str += '-' * width + ' '
    table_str += '\n'

    # Create table content
    for row in data[1:]:
        for i in range(len(row)):
            table_str += str(row[i]).ljust(col_width[i]) + ' '
        table_str += '\n'

    return table_str

class TextFormatter:
    RESET = "\033[0m"
    TEXT_COLORS = {
        "black": "\033[30m",
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "magenta": "\033[35m",
        "cyan": "\033[36m",
        "white": "\033[37m"
    }
    TEXT_COLOR_LEVELS = {
        "light": "\033[1;{}m",  # Light color prefix
        "dark": "\033[2;{}m"  # Dark color prefix
    }
    BACKGROUND_COLORS = {
        "black": "\033[40m",
        "red": "\033[41m",
        "green": "\033[42m",
        "yellow": "\033[43m",
        "blue": "\033[44m",
        "magenta": "\033[45m",
        "cyan": "\033[46m",
        "white": "\033[47m"
    }
    TEXT_ATTRIBUTES = {
        "bold": "\033[1m",
        "italic": "\033[3m",
        "underline": "\033[4m",
        "blink": "\033[5m",
        "reverse": "\033[7m",
        "strikethrough": "\033[9m"
    }

    @staticmethod
    def format_text(text, color=None, color_level=None, background=None, attributes=None, target_text=''):
        formatted_text = ""
        start_index = text.find(target_text)
        end_index = start_index + len(target_text) if start_index != -1 else len(text)

        if color in TextFormatter.TEXT_COLORS:
            if color_level in TextFormatter.TEXT_COLOR_LEVELS:
                color_code = TextFormatter.TEXT_COLORS[color]
                color_format = TextFormatter.TEXT_COLOR_LEVELS[color_level].format(color_code)
                formatted_text += color_format
            else:
                formatted_text += TextFormatter.TEXT_COLORS[color]

        if background in TextFormatter.BACKGROUND_COLORS:
            formatted_text += TextFormatter.BACKGROUND_COLORS[background]

        if attributes in TextFormatter.TEXT_ATTRIBUTES:
            formatted_text += TextFormatter.TEXT_ATTRIBUTES[attributes]

        if target_text == "":
            formatted_text += text + TextFormatter.RESET
        else:
            formatted_text += text[:start_index] + text[start_index:end_index] + TextFormatter.RESET + text[end_index:]

        return formatted_text

    @staticmethod
    def format_text_truecolor(text, color=None, background=None, attributes=None, target_text=''):
        formatted_text = ""
        start_index = text.find(target_text)
        end_index = start_index + len(target_text) if start_index != -1 else len(text)

        if color:
            formatted_text += f"\033[38;2;{color}m"

        if background:
            formatted_text += f"\033[48;2;{background}m"

        if attributes in TextFormatter.TEXT_ATTRIBUTES:
            formatted_text += TextFormatter.TEXT_ATTRIBUTES[attributes]

        if target_text == "":
            formatted_text += text + TextFormatter.RESET
        else:
            formatted_text += text[:start_index] + text[start_index:end_index] + TextFormatter.RESET + text[end_index:]

        return formatted_text

    @staticmethod
    def interpolate_color(color1, color2, ratio):
        """
        Interpolates between two RGB colors.
        """
        r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
        g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
        b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
        return f"{r};{g};{b}"

    @staticmethod
    def format_gradient_text(text, color1, color2, attributes=None):
        formatted_text = ""
        gradient_length = len(text)
        for i in range(gradient_length):
            ratio = i / (gradient_length - 1)
            interpolated_color = TextFormatter.interpolate_color(color1, color2, ratio)
            formatted_text += f"\033[38;2;{interpolated_color}m{text[i]}"
        formatted_text += TextFormatter.RESET

        if attributes:
            formatted_text = f"{TextFormatter.TEXT_ATTRIBUTES[attributes]}{formatted_text}"

        return formatted_text

def center_string(main_string, replacement_string):
    # Find the center index of the main string
    center_index = len(main_string) // 2

    # Calculate the start and end indices for replacing
    start_index = center_index - len(replacement_string) // 2
    end_index = start_index + len(replacement_string)

    # Replace the substring at the center
    new_string = main_string[:start_index] + replacement_string + main_string[end_index:]

    return new_string

def insert_string(base, inserted, position=0):
    return base[:position] + inserted + base[position + len(inserted):]

def find_quartiles(data):
    data.sort()
    mid = len(data) // 2

    q2 = data[mid] if len(data) % 2 != 0 else (data[mid - 1] + data[mid]) / 2

    lower_half = data[:mid]
    upper_half = data[mid + 1:] if len(data) % 2 != 0 else data[mid:]

    mid_lower = len(lower_half) // 2
    mid_upper = len(upper_half) // 2

    q1 = lower_half[mid_lower] if len(lower_half) % 2 != 0 else (lower_half[mid_lower - 1] + lower_half[mid_lower]) / 2
    q3 = upper_half[mid_upper] if len(upper_half) % 2 != 0 else (upper_half[mid_upper - 1] + upper_half[mid_upper]) / 2

    return min(data), q1, q2, q3, max(data)

def limit_string_in_line(text, limit):
    lines = text.split('\n')
    new_lines = []

    for line in lines:
        words = line.split()
        new_line = ''

        for word in words:
            if len(new_line) + len(word) <= limit:
                new_line += word + ' '
            else:
                new_lines.append(new_line.strip())
                new_line = word + ' '

        if new_line:
            new_lines.append(new_line.strip())

    return '\n'.join(new_lines)

def split_string_at_intervals(input_string, interval):
    return [input_string[i:i+interval] for i in range(0, len(input_string), interval)]

def bytesfiller(byte_sequence: bytes, bit_length):
    # Calculate the current length in bits
    current_bit_length = len(byte_sequence) * 8

    # Check if padding is necessary
    if current_bit_length >= bit_length:
        return byte_sequence[:bit_length // 8]

    # Calculate the number of zero bits to add
    additional_bits = bit_length - current_bit_length

    # Create the padding bytes
    additional_bytes = ((additional_bits + 7) // 8) # Round up to the nearest byte
    padding = b"\\xsb" # start fill
    padding += b'\x00' * additional_bytes

    # Combine the original bytes with the padding
    padded_bytes = byte_sequence + padding

    # Return only the necessary number of bytes
    return padded_bytes[:bit_length // 8]

def bytesdefiller(padded_bytes: bytes):
    return padded_bytes.split(b"\\xsb")[0]

def karaoke_print(text, delay=0.1, ln=True):
    printed_text = ""
    for i, char in enumerate(text):
        # Print already printed text normally
        print(printed_text + char, end='', flush=True)

        # Calculate not yet printed text to dim
        not_printed_text = text[i + 1:]
        dimmed_text = ''.join([f"\033[2m{char}\033[0m" for char in not_printed_text])

        # Print dimmed text
        print(dimmed_text, end='', flush=True)

        # Wait before printing the next character
        time.sleep(delay)

        # Clear the line for the next iteration
        print('\r', end='', flush=True)

        # Prepare the updated printed_text for the next iteration
        printed_text += char

    if ln:
        print("")

def split_integer_with_percentage(value, percentage):
    # Convert the percentage from 0-100 range to 0-1 range
    percentage_decimal = percentage / 100
    part1 = round(value * percentage_decimal)
    part2 = value - part1
    return part1, part2

def frange(start, stop, step=1):
    while start < stop:
        yield start
        start += step