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

import datetime
from iso639 import languages
from typing import Any
import numpy as np

def timestamp2date(timestamp, display='%Y-%m-%d %H:%M:%S'):
    return datetime.fromtimestamp(timestamp).strftime(display)

def str2bin(s):
    return ''.join(format(ord(x), '08b') for x in s)

def str2binnparray(s):
    return np.array([int(bit) for bit in list(''.join(format(ord(x), '08b') for x in s))])

def numpyarray2str(arr):
    # Assuming arr is a NumPy array of binary values
    binary_str = ''.join([str(bit) for bit in arr])
    str_data = ''
    for i in range(0, len(binary_str), 8):
        byte = binary_str[i:i+8]
        str_data += chr(int(byte, 2))
    return str_data

def str2bin2(s):
    binary_strings = [format(num, '08b') for num in s]
    return ''.join(binary_strings)

def bin2str(b):
    return ''.join(chr(int(b[i:i+8], 2)) for i in range(0, len(b), 8))

def bytes2bin(data):
    binary_string = ""
    for byte in data:
        binary_string += format(byte, '08b')  # Convert each byte to its binary representation with 8 bits
    return binary_string

def bin2bytes(binary_string):
    bytes_data = bytearray()
    for i in range(0, len(binary_string), 8):
        byte = binary_string[i:i+8]
        bytes_data.append(int(byte, 2))
    return bytes(bytes_data)

def bin2bool(bin):
    bin = list(bin)
    booll = []
    for i in bin:
        i = int(i)
        if i == 0:
            booll.append(False)
        elif i == 1:
            booll.append(True)
    return booll

def rgb2hex(rgb):
    return '%02x%02x%02x' % rgb

def hex2rgb(value):
    value = value.lstrip('#')
    lv = len(value)
    return tuple(int(value[i:i+lv//3], 16) for i in range(0, lv, lv//3))

def text2morse(text, morselang=None):
    if morselang is None:
        morselang = {
            'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.',
            'G': '--.', 'H': '....', 'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..',
            'M': '--', 'N': '-.', 'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.',
            'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
            'Y': '-.--', 'Z': '--..', ' ': ' ', '0': '-----', '1': '.----', '2': '..---',
            '3': '...--', '4': '....-', '5': '.....', '6': '-....', '7': '--...', '8': '---..',
            '9': '----.', '&': '.-...', "'": '.----.', '@': '.--.-.', ')': '-.--.-', '(': '-.--.',
            ':': '---...', ',': '--..--', '=': '-...-', '!': '-.-.--', '.': '.-.-.-', '-': '-....-',
            '+': '.-.-.', '"': '.-..-.', '?': '..--..', '/': '-..-.'
        }

    morse = ''

    for char in text:
        morse += morselang[char.upper()] + ' '
    return morse

def morse2text(morse, morselang=None):
    if morselang is None:
        morselang = {
            'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.',
            'G': '--.', 'H': '....', 'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..',
            'M': '--', 'N': '-.', 'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.',
            'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
            'Y': '-.--', 'Z': '--..', ' ': ' ', '0': '-----', '1': '.----', '2': '..---',
            '3': '...--', '4': '....-', '5': '.....', '6': '-....', '7': '--...', '8': '---..',
            '9': '----.', '&': '.-...', "'": '.----.', '@': '.--.-.', ')': '-.--.-', '(': '-.--.',
            ':': '---...', ',': '--..--', '=': '-...-', '!': '-.-.--', '.': '.-.-.-', '-': '-....-',
            '+': '.-.-.', '"': '.-..-.', '?': '..--..', '/': '-..-.'
        }

    code_elements = morse.split(' ')
    text = ''

    for code in code_elements:
        text += morselang[code]
    return text

# thank devxpy for this code (ref. https://gist.github.com/devxpy/063968e0a2ef9b6db0bd6af8079dad2a)

INSTRUMENTS = [
    'Acoustic Grand Piano',
    'Bright Acoustic Piano',
    'Electric Grand Piano',
    'Honky-tonk Piano',
    'Electric Piano 1',
    'Electric Piano 2',
    'Harpsichord',
    'Clavi',
    'Celesta',
    'Glockenspiel',
    'Music Box',
    'Vibraphone',
    'Marimba',
    'Xylophone',
    'Tubular Bells',
    'Dulcimer',
    'Drawbar Organ',
    'Percussive Organ',
    'Rock Organ',
    'Church Organ',
    'Reed Organ',
    'Accordion',
    'Harmonica',
    'Tango Accordion',
    'Acoustic Guitar (nylon)',
    'Acoustic Guitar (steel)',
    'Electric Guitar (jazz)',
    'Electric Guitar (clean)',
    'Electric Guitar (muted)',
    'Overdriven Guitar',
    'Distortion Guitar',
    'Guitar harmonics',
    'Acoustic Bass',
    'Electric Bass (finger)',
    'Electric Bass (pick)',
    'Fretless Bass',
    'Slap Bass 1',
    'Slap Bass 2',
    'Synth Bass 1',
    'Synth Bass 2',
    'Violin',
    'Viola',
    'Cello',
    'Contrabass',
    'Tremolo Strings',
    'Pizzicato Strings',
    'Orchestral Harp',
    'Timpani',
    'String Ensemble 1',
    'String Ensemble 2',
    'SynthStrings 1',
    'SynthStrings 2',
    'Choir Aahs',
    'Voice Oohs',
    'Synth Voice',
    'Orchestra Hit',
    'Trumpet',
    'Trombone',
    'Tuba',
    'Muted Trumpet',
    'French Horn',
    'Brass Section',
    'SynthBrass 1',
    'SynthBrass 2',
    'Soprano Sax',
    'Alto Sax',
    'Tenor Sax',
    'Baritone Sax',
    'Oboe',
    'English Horn',
    'Bassoon',
    'Clarinet',
    'Piccolo',
    'Flute',
    'Recorder',
    'Pan Flute',
    'Blown Bottle',
    'Shakuhachi',
    'Whistle',
    'Ocarina',
    'Lead 1 (square)',
    'Lead 2 (sawtooth)',
    'Lead 3 (calliope)',
    'Lead 4 (chiff)',
    'Lead 5 (charang)',
    'Lead 6 (voice)',
    'Lead 7 (fifths)',
    'Lead 8 (bass + lead)',
    'Pad 1 (new age)',
    'Pad 2 (warm)',
    'Pad 3 (polysynth)',
    'Pad 4 (choir)',
    'Pad 5 (bowed)',
    'Pad 6 (metallic)',
    'Pad 7 (halo)',
    'Pad 8 (sweep)',
    'FX 1 (rain)',
    'FX 2 (soundtrack)',
    'FX 3 (crystal)',
    'FX 4 (atmosphere)',
    'FX 5 (brightness)',
    'FX 6 (goblins)',
    'FX 7 (echoes)',
    'FX 8 (sci-fi)',
    'Sitar',
    'Banjo',
    'Shamisen',
    'Koto',
    'Kalimba',
    'Bag pipe',
    'Fiddle',
    'Shanai',
    'Tinkle Bell',
    'Agogo',
    'Steel Drums',
    'Woodblock',
    'Taiko Drum',
    'Melodic Tom',
    'Synth Drum',
    'Reverse Cymbal',
    'Guitar Fret Noise',
    'Breath Noise',
    'Seashore',
    'Bird Tweet',
    'Telephone Ring',
    'Helicopter',
    'Applause',
    'Gunshot'
]
NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
OCTAVES = list(range(11))
NOTES_IN_OCTAVE = len(NOTES)

errors = {
    'program': 'Bad input, please refer this spec-\n'
               'https://www.recordingblogs.com/wiki/midi-program-change-message',
    'notes': 'Bad input, please refer this spec-\n'
             'https://newt.phys.unsw.edu.au/jw/notes.html'
}

def instrument2program(instrument: str) -> int:
    assert instrument in INSTRUMENTS, errors['program']
    return INSTRUMENTS.index(instrument) + 1

def program2instrument(program: int) ->  str:
    assert 1 <= program <= 128, errors['program']
    return INSTRUMENTS[program - 1]

def number2note(number: int) -> list[str | int | Any]:
    octave = number // NOTES_IN_OCTAVE
    assert octave in OCTAVES, errors['notes']
    assert 0 <= number <= 127, errors['notes']
    note = NOTES[number % NOTES_IN_OCTAVE]

    return [note, octave]

def note2number(note: str, octave: int) -> int:
    assert note in NOTES, errors['notes']
    assert octave in OCTAVES, errors['notes']

    note = NOTES.index(note)
    note += (NOTES_IN_OCTAVE * octave)

    assert 0 <= note <= 127, errors['notes']

    return note

#------------------------------------------------------------------------

def number2freq(midi_note: int):
    return 2 ** ((midi_note - 69) / 12) * 440

def langpart12fu(lang):
    return languages.get(part1=lang).name

def SI4713RDSPSMISC(stereo=False, artificialhead=False, compressed=False, dynamicpty=False, tp=False, pty=0, forceb=False, ta=False, ms=False):
    # Construct the 16-bit value
    value = (int(stereo) << 15) | (int(artificialhead) << 14) | (int(compressed) << 13) | (int(dynamicpty) << 12) | (int(forceb) << 11) | \
            (int(tp) << 10) | (pty << 5) | (int(ta) << 4) | (int(ms) << 3)

    # Convert the value to hex
    hex_code = hex(value)[2:].zfill(4).upper()

    return hex_code

def number2roman(number):
    if not isinstance(number, int) or not 0 < number < 1000000000000:
        raise ValueError("Input must be an int only and between 1-999999999999 < 1000000000000")

    roman_numerals = [
        (1000000000000, "M̅"), (900000000000, "C̅M̅"), (500000000000, "D̅"), (400000000000, "C̅D̅"),
        (100000000000, "C̅"), (90000000000, "X̅C̅"), (50000000000, "L̅"), (40000000000, "X̅L̅"),
        (10000000000, "X̅"), (9000000000, "M̅X̅"), (5000000000, "V̅"), (4000000000, "M̅V̅"),
        (1000000000, "M̅"), (900000000, "CM"), (500000000, "D"), (400000000, "CD"),
        (100000000, "C"), (90000000, "XC"), (50000000, "L"), (40000000, "XL"),
        (10000000, "X"), (9000000, "IX"), (5000000, "V"), (4000000, "IV"),
        (1000000, "M"), (900000, "CM"), (500000, "D"), (400000, "CD"),
        (100000, "C"), (90000, "XC"), (50000, "L"), (40000, "XL"),
        (10000, "X"), (9000, "IX"), (5000, "V"), (4000, "IV"),
        (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
        (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
        (10, "X"), (9, "IX"), (5, "V"), (4, "IV"),
        (1, "I")
    ]

    roman_numeral = ""
    for value, symbol in roman_numerals:
        while number >= value:
            roman_numeral += symbol
            number -= value

    return roman_numeral

def hammingEncode(data):
    # Check if the input data is a binary string
    if not all(bit in '01' for bit in data):
        raise ValueError("Input data must be a binary string")

    # Determine the number of parity bits required (m)
    m = 0
    while 2 ** m < len(data) + m + 1:
        m += 1

    # Calculate the number of total bits in the codeword
    n = len(data) + m

    # Initialize the encoded codeword with None for parity bit positions
    codeword = [None] * n

    # Copy data bits to their respective positions in the codeword
    data_index = 0
    for i in range(n):
        if i + 1 not in [2 ** j for j in range(m)]:
            codeword[i] = data[data_index]
            data_index += 1

    # Calculate parity bits using XOR
    for i in range(m):
        parity_bit_index = 2 ** i - 1
        xor_result = 0
        for j in range(parity_bit_index, n, 2 ** (i + 1)):
            if codeword[j] is not None:
                xor_result ^= int(codeword[j])
        codeword[parity_bit_index] = str(xor_result)

    return ''.join(codeword)

def hammingDecode(codeword):
    try:
        # Check if the input codeword is a binary string
        if not all(bit in '01' or bit == 'P' for bit in codeword):
            raise ValueError("Input codeword must be a binary string with 'P' placeholders")

        # Determine the number of parity bits (m)
        m = 0
        while 2 ** m < len(codeword) + 1:
            m += 1

        # Calculate syndrome bits
        syndrome = ''
        for i in range(m):
            parity_bit_index = 2 ** i - 1
            xor_result = 0
            for j in range(parity_bit_index, len(codeword), 2 ** (i + 1)):
                if codeword[j] != 'P':
                    xor_result ^= int(codeword[j])
            syndrome = str(xor_result) + syndrome

        # Convert syndrome to error index
        error_index = int(syndrome, 2)

        if error_index == 0:
            # No error
            data_bits = []
            for i in range(len(codeword)):
                if i + 1 not in [2 ** j for j in range(m)]:
                    data_bits.append(codeword[i])
            data = ''.join(data_bits)
        else:
            # Correct the error
            corrected_bit = '1' if codeword[error_index - 1] == '0' else '0'
            corrected_codeword = codeword[:error_index - 1] + corrected_bit + codeword[error_index:]
            data = hammingDecode(corrected_codeword)

        return data
    except:
        return "0"

def nparray2bin(nparray):
    binary_string = ''.join(str(bit) for bit in nparray)
    return binary_string

# Convert binary string to an array of binary values
def bin2nparray(binary_string):
    binary_array = np.array([int(bit) for bit in binary_string], dtype=np.uint8)
    return binary_array

def sample2bar(sample, sensitivity=2, bar='|'):
    peak = np.average(np.abs(sample)) * sensitivity
    bars = bar * int(50 * peak / 2 ** 16)
    return bars

def calculate_shifted_frequency(center_freq, shift):
    censhift = shift / 2
    tone1 = center_freq - censhift
    tone2 = center_freq + censhift
    return tone1, tone2

# Define dictionaries mapping letters and numbers to their phonetic representations
phonetic_alphabet = {
    'A': 'Alpha', 'B': 'Bravo', 'C': 'Charlie', 'D': 'Delta', 'E': 'Echo',
    'F': 'Foxtrot', 'G': 'Golf', 'H': 'Hotel', 'I': 'India', 'J': 'Juliett',
    'K': 'Kilo', 'L': 'Lima', 'M': 'Mike', 'N': 'November', 'O': 'Oscar',
    'P': 'Papa', 'Q': 'Quebec', 'R': 'Romeo', 'S': 'Sierra', 'T': 'Tango',
    'U': 'Uniform', 'V': 'Victor', 'W': 'Whiskey', 'X': 'X-ray', 'Y': 'Yankee', 'Z': 'Zulu',
    '0': 'Zero', '1': 'One', '2': 'Two', '3': 'Three', '4': 'Four',
    '5': 'Five', '6': 'Six', '7': 'Seven', '8': 'Eight', '9': 'Nine'
}

# Function to translate a word or number into phonetic representation
def str2phonetic(input_string):
    # Convert the input string to uppercase for consistency
    input_string = input_string.upper()
    # Translate each character to phonetic representation and join them
    translated_string = ' '.join(phonetic_alphabet.get(char, char) for char in input_string)
    return translated_string

# Function to translate phonetic representation to a word or number
def phonetic2str(phonetic):
    # Split phonetic representation into words and translate each word back to character or number
    words = phonetic.split()
    translated_string = ''.join([key for word in words for key, value in phonetic_alphabet.items() if value == word])
    return translated_string


def str2bool(s):
    true_values = {'true', 'yes', '1', 'on', 'y', 't'}
    false_values = {'false', 'no', '0', 'off', 'n', 'f'}

    s = s.strip().lower()

    if s in true_values:
        return True
    elif s in false_values:
        return False
    else:
        raise ValueError(f"Invalid boolean string: {s}")


