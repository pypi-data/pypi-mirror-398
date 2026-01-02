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
import time
from pymata_aio.pymata3 import PyMata3        # type: ignore
from pymata_aio.constants import Constants    # type: ignore
from PIL import Image

# matrix led

MAX7219_REG_NOOP        = 0x00
MAX7219_REG_DIGIT0      = 0x01
MAX7219_REG_DIGIT1      = 0x02
MAX7219_REG_DIGIT2      = 0x03
MAX7219_REG_DIGIT3      = 0x04
MAX7219_REG_DIGIT4      = 0x05
MAX7219_REG_DIGIT5      = 0x06
MAX7219_REG_DIGIT6      = 0x07
MAX7219_REG_DIGIT7      = 0x08
MAX7219_REG_DECODEMODE  = 0x09
MAX7219_REG_INTENSITY   = 0x0a
MAX7219_REG_SCANLIMIT   = 0x0b
MAX7219_REG_SHUTDOWN    = 0x0c
MAX7219_REG_DISPLAYTEST = 0x0f

LOW, HIGH = 0, 1
LSBFIRST, MSBFIRST = 0, 1

# Following bit shifting functons adapted from https://wiki.python.org/moin/BitManipulation


def test_bit(value: int, offset: int) -> int:
    " Returns a 1, if the bit at 'offset' is one, else 0"
    mask = 1 << offset
    return 1 if (value & mask) else 0


def set_bit(value: int, offset: int) -> int:
    " Returns an integer with the bit at 'offset' set to 1"
    mask = 1 << offset
    return (value | mask)


def clear_bit(value: int, offset: int) -> int:
    " Returns an integer with the bit at 'offset' cleared "
    mask = ~(1 << offset)
    return (value & mask)


def toggle_bit(value: int, offset: int) -> int:
    " Returns an integer with the bit at 'offset' inverted, 0 -> 1 and 1 -> 0 "
    mask = 1 << offset
    return (value ^ mask)


def write_bit(value: int, offset: int, bit: int) -> int:
    if bit == HIGH:
        return set_bit(value, offset)
    elif bit == LOW:
        return clear_bit(value, offset)
    else:
        raise Exception("bit must be high or low")


class MaxMatrix:
    def __init__(self, board, data_pin: int, load_pin: int, clock_pin: int):
        self.board = board
        self.data_pin = data_pin
        self.load_pin = load_pin
        self.clock_pin = clock_pin
        self.buffer = bytearray(80)

        # initialise the LED display
        self.board.set_pin_mode(self.data_pin,  Constants.OUTPUT)
        self.board.set_pin_mode(self.clock_pin,  Constants.OUTPUT)
        self.board.set_pin_mode(self.load_pin,  Constants.OUTPUT)

        self.board.digital_write(self.clock_pin, HIGH)

        self.set_command(MAX7219_REG_SCANLIMIT, 0x07)
        self.set_command(MAX7219_REG_DECODEMODE, 0x00)   # using an led matrix (not digits)
        self.set_command(MAX7219_REG_SHUTDOWN, 0x01)     # not in shutdown mode
        self.set_command(MAX7219_REG_DISPLAYTEST, 0x00)  # no display test

        # empty registers, turn all LEDs off
        self.clear()
        self.set_intensity(0x0f)  # the first 0x0f is the value you can set

    def reload(self) -> None:
        for col in range(8):
            self.board.digital_write(self.load_pin, LOW)
            self.shift_out(col + 1)
            self.shift_out(self.buffer[col])
            self.board.digital_write(self.load_pin, LOW)
            self.board.digital_write(self.load_pin, HIGH)

    def clear(self):
        self.buffer = bytearray(80)
        self.reload()

    def set_command(self, command: int, value: int):
        self.board.digital_write(self.load_pin, LOW)

        self.shift_out(command)
        self.shift_out(value)

        self.board.digital_write(self.load_pin, LOW)
        self.board.digital_write(self.load_pin, HIGH)

    def shift_out(self, value: int, bit_order: int=MSBFIRST):
        # Adapted from hardware/arduino/avr/cores/arduino/wiring_shift.c
        for i in range(8):
            if bit_order == LSBFIRST:
                b = HIGH if ~~(value & (1 << i)) else LOW
            else:
                b = HIGH if ~~(value & (1 << (7 - i))) else LOW
            self.board.digital_write(self.data_pin, b)
            self.board.digital_write(self.clock_pin, HIGH)
            self.board.digital_write(self.clock_pin, LOW)

    def set_intensity(self, intensity: int):
        self.set_command(MAX7219_REG_INTENSITY, intensity)

    def set_column(self, col: int, value: int):
        """
        set the column to the value, for example:
        #>>> mm.set_column(0, 0b11011001)
        """
        self.board.digital_write(self.load_pin, LOW)
        self.shift_out(col + 1)
        self.shift_out(value)
        self.board.digital_write(self.load_pin, LOW)
        self.board.digital_write(self.load_pin, HIGH)
        self.buffer[col] = value

    def set_row(self, row: int, value: int):
        """
        set the row to the value, for example:
        #>>> mm.set_row(0, 0b11011001)
        """
        for i in range(8):
            b = test_bit(value, i)
            self.buffer[i] = write_bit(self.buffer[i], row, b)
        self.reload()

    def set_dot(self, col: int, row: int, value: int):
        self.buffer[col] = write_bit(self.buffer[col], row, value)
        self.board.digital_write(self.load_pin, LOW)
        self.shift_out(col + 1)
        self.shift_out(self.buffer[col])
        self.board.digital_write(self.load_pin, LOW)
        self.board.digital_write(self.load_pin, HIGH)

    def shift_left(self, fill_zero: bool = False):
        if fill_zero:
            self.buffer = self.buffer[-1:] + bytearray(1)
        else:
            self.buffer = self.buffer[-1:] + self.buffer[:-1]
        self.reload()

    def shift_right(self, fill_zero: bool = False):
        if fill_zero:
            self.buffer = self.buffer[1:] + bytearray(1)
        else:
            self.buffer = self.buffer[1:] + self.buffer[:1]
        self.reload()

    def shift_up(self, fill_zero: bool = False):
        for i in range(len(self.buffer)):
            if fill_zero:
                self.buffer[i] = self.buffer[i] << 1
            else:
                self.buffer[i] = ((self.buffer[i] << 1) & 0xff) | test_bit(self.buffer[i], 7)
        self.reload()

    def shift_down(self, fill_zero = False):
        for i in range(len(self.buffer)):
            if fill_zero:
                self.buffer[i] = self.buffer[i] >> 1
            else:
                self.buffer[i] = (self.buffer[i] >> 1) | (test_bit(self.buffer[i], 0) << 7)
        self.reload()

    def write_sprite(self, sprite: bytearray, x: int = 0, y: int = 0):
        if x:
            sprite = sprite[:]
            for i in range(8):
                sprite[i] = sprite[i] >> x
        self.buffer[y:y+8] = sprite
        self.reload()

def get_matrix(data, row, col):
    m = []
    for i in range(8):
        m.append(data[((i+8*col)*128) + (row * 8): ((i+8*col) * 128) + (row * 8) + 8])
    return m


def make_sprite(matrix):
    ba = bytearray(8)
    for r in range(8):
        for c in range(8):
            bit = matrix[r][c]
            ba[7 - c] = write_bit(ba[7 - c], 7 - r, bit)
    return ba

class Tileset:
    def __init__(self, tileset="Potash_8x8.png"):
        im = Image.open(tileset)
        data = list(im.getdata())
        sprites = {}
        for i in range(256):
            x, y = i % 16, i // 16
            m = get_matrix(data, x, y)
            sprites[i] = make_sprite(m)
        self.sprites = sprites

    def get_sprite(self, ch):
        return self.sprites[ord(ch)]

#----------------------------------------------------------------------------------------------------------------------

class StepperMotor5:
    def __init__(self, board, motor_pins):
        self.board = board
        self.motor_pins = motor_pins
        self.steps_sequence = [
            [1, 0, 1, 0, 1],  # Step 0: 01101
            [1, 0, 0, 0, 1],  # Step 1: 01001
            [1, 0, 1, 1, 1],  # Step 2: 01011
            [1, 0, 0, 1, 0],  # Step 3: 01010
            [1, 1, 0, 1, 0],  # Step 4: 11010
            [1, 0, 0, 1, 0],  # Step 5: 10010
            [1, 1, 1, 1, 0],  # Step 6: 10110
            [1, 0, 1, 0, 0],  # Step 7: 10100
            [1, 0, 1, 0, 1],  # Step 8: 10101
            [0, 0, 1, 0, 1]   # Step 9: 00101
        ]
        self.number_of_steps = len(self.steps_sequence)
        self.step_delay = 0
        self.set_speed(60)

        # Set up pins for output
        for pin in self.motor_pins:
            self.board.digital[pin].mode = 1

    def set_speed(self, speed):
        self.step_delay = 60 * 1000 / self.number_of_steps / speed

    def step(self, steps_to_move):
        steps_left = abs(steps_to_move)
        direction = 1 if steps_to_move > 0 else 0

        while steps_left > 0:
            for step in range(self.number_of_steps):
                for i, pin in enumerate(self.motor_pins):
                    self.board.digital[pin].write(self.steps_sequence[step][i])
                time.sleep(self.step_delay / 1000.0)  # delay is in milliseconds
            steps_left -= 1

class StepperMotor4:
    def __init__(self, board, step_pin, direction_pin):
        self.board = board
        self.step_pin = step_pin
        self.direction_pin = direction_pin

        self.board.digital[self.step_pin].mode = 1
        self.board.digital[self.direction_pin].mode = 1

        self.step_delay = 0
        self.set_speed(60)

    def set_speed(self, speed):
        self.step_delay = 60 * 1000 / speed

    def step(self, steps_to_move):
        direction = 1 if steps_to_move > 0 else 0
        steps_left = abs(steps_to_move)

        self.board.digital[self.direction_pin].write(direction)

        while steps_left > 0:
            self.board.digital[self.step_pin].write(1)
            time.sleep(self.step_delay / 1000.0)
            self.board.digital[self.step_pin].write(0)
            time.sleep(self.step_delay / 1000.0)
            steps_left -= 1