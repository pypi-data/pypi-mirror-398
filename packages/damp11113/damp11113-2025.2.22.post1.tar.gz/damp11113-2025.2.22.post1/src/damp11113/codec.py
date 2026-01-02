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

import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Optional

class ADPCM:
    step_size_table = [
        7, 8, 9, 10, 11, 12, 13, 14,
        16, 17, 19, 21, 23, 25, 28, 31,
        34, 37, 41, 45, 50, 55, 60, 66,
        73, 80, 88, 97, 107, 118, 130, 143,
        157, 173, 190, 209, 230, 253, 279, 307,
        337, 371, 408, 449, 494, 544, 598, 658,
        724, 796, 876, 963, 1060, 1166, 1282, 1411,
        1552, 1707, 1878, 2066, 2272, 2499, 2749, 3024,
        3327, 3660, 4026, 4428, 4871, 5358, 5894, 6484,
        7132, 7845, 8630, 9493, 10442, 11487, 12635, 13899,
        15289, 16818, 18500, 20350, 22385, 24623, 27086, 29794,
        32767
    ]

    index_table = [
        -1, -1, -1, -1, 2, 4, 6, 8,
        -1, -1, -1, -1, 2, 4, 6, 8
    ]

    def __init__(self, sample_rate=48000, channels=1):
        self.sample_rate = sample_rate
        self.channels = channels
        self.index = np.zeros(channels, dtype=int)
        self.predicted_sample = np.zeros(channels, dtype=int)

    def encode(self, pcm_data):
        pcm_data = pcm_data.reshape(-1, self.channels)
        adpcm_data = []
        for sample_frame in pcm_data:
            for ch in range(self.channels):
                sample = sample_frame[ch]
                delta = sample - self.predicted_sample[ch]
                sign = 0
                if delta < 0:
                    sign = 8
                    delta = -delta

                step_size = self.step_size_table[self.index[ch]]
                delta_q = 0
                if delta >= step_size:
                    delta_q = 4
                    delta -= step_size
                step_size >>= 1
                if delta >= step_size:
                    delta_q |= 2
                    delta -= step_size
                step_size >>= 1
                if delta >= step_size:
                    delta_q |= 1

                delta_q |= sign

                self.index[ch] += self.index_table[delta_q & 0x0F]
                self.index[ch] = max(0, min(len(self.step_size_table) - 1, self.index[ch]))
                self.predicted_sample[ch] += step_size * ((delta_q & 7) - (delta_q & 8))
                self.predicted_sample[ch] = max(-32768, min(32767, self.predicted_sample[ch]))

                adpcm_data.append(delta_q & 0x0F)

        # Pack two 4-bit samples into one byte
        byte_data = bytearray()
        for i in range(0, len(adpcm_data), 2):
            if i + 1 < len(adpcm_data):
                byte = (adpcm_data[i] << 4) | (adpcm_data[i + 1] & 0x0F)
            else:
                byte = adpcm_data[i] << 4
            byte_data.append(byte)

        return bytes(byte_data)

    def decode(self, adpcm_bytes):
        pcm_data = []
        for byte in adpcm_bytes:
            # Extract two 4-bit samples from each byte
            delta_q1 = (byte >> 4) & 0x0F
            delta_q2 = byte & 0x0F

            for delta_q in [delta_q1, delta_q2]:
                step_size = self.step_size_table[self.index[0]]
                delta = step_size * ((delta_q & 7) - (delta_q & 8))

                self.index[0] += self.index_table[delta_q & 0x0F]
                self.index[0] = max(0, min(len(self.step_size_table) - 1, self.index[0]))
                self.predicted_sample[0] += delta
                self.predicted_sample[0] = max(-32768, min(32767, self.predicted_sample[0]))

                pcm_data.append(self.predicted_sample[0])

        return np.array(pcm_data, dtype=np.int16).reshape(-1, self.channels)

# original and information: https://github.com/MCJack123/node-dfpwm
CONST_PREC = 12
CONST_POSTFILT = 140

class DFPWMEncoder:
    def __init__(self, q=0, s=0, lt=-128):
        self.q = q
        self.s = s
        self.lt = lt
        self.pending = None

    def encode(self, buffer, final=False):
        if not isinstance(buffer, (bytes, bytearray)):
            raise TypeError("Argument #1 must be a bytes-like object.")

        buf = buffer
        if self.pending is not None:
            buf = self.pending + buffer

        if len(buf) % 8 < 1:
            final = False

        length = (len(buf) + 7) // 8 if final else len(buf) // 8
        output = bytearray(length)

        for i in range(length):
            d = 0
            for j in range(8 if not (final and i == length - 1) else len(buf) % 8):
                v = buf[i * 8 + j] - 128  # Convert from unsigned to signed
                t = 127 if v > self.q or (v == self.q and v == 127) else -128
                d >>= 1
                if t > 0:
                    d |= 0x80

                nq = self.q + ((self.s * (t - self.q) + (1 << (CONST_PREC - 1))) >> CONST_PREC)
                if nq == self.q and nq != t:
                    nq += 1 if t == 127 else -1
                self.q = nq

                st = 0 if t != self.lt else (1 << CONST_PREC) - 1
                ns = self.s
                if ns != st:
                    ns += 1 if st != 0 else -1
                if CONST_PREC > 8 and ns < (1 << (CONST_PREC - 7)):
                    ns = (1 << (CONST_PREC - 7))
                self.s = ns

                self.lt = t

            if final and i == length - 1:
                d >>= 8 - (len(buf) % 8)
            output[i] = d

        if not final and len(buf) % 8 > 0:
            self.pending = buf[-(len(buf) % 8):]
        else:
            self.pending = None

        return bytes(output)

class DFPWMEncoder2:
    def __init__(self, q=0, s=0, lt=-128):
        self.q = q
        self.s = s
        self.lt = lt
        self.pending = None
        self.prev_samples = []  # Keep track of previous samples for adaptive quantization

    def adaptive_quantization(self, v):
        # Implement adaptive quantization logic based on recent signal
        self.prev_samples.append(v)
        if len(self.prev_samples) > 8:  # Keep the last 8 samples
            self.prev_samples.pop(0)

        avg_signal = sum(self.prev_samples) // len(self.prev_samples)

        if avg_signal > self.q:
            self.q += (avg_signal - self.q) // 8  # Adjust q towards avg_signal
        elif avg_signal < self.q:
            self.q -= (self.q - avg_signal) // 8  # Adjust q towards avg_signal

        # Clamp q to valid range
        self.q = max(-128, min(127, self.q))

        return self.q

    def encode(self, buffer, final=False):
        if not isinstance(buffer, (bytes, bytearray)):
            raise TypeError("Argument #1 must be a bytes-like object.")

        buf = buffer
        if self.pending is not None:
            buf = self.pending + buffer

        if len(buf) % 8 < 1:
            final = False

        length = (len(buf) + 7) // 8 if final else len(buf) // 8
        output = bytearray(length)

        for i in range(length):
            d = 0
            for j in range(8 if not (final and i == length - 1) else len(buf) % 8):
                v = buf[i * 8 + j] - 128  # Convert from unsigned to signed

                # Adaptive quantization
                self.q = self.adaptive_quantization(v)

                t = 127 if v > self.q or (v == self.q and v == 127) else -128
                d >>= 1
                if t > 0:
                    d |= 0x80

                nq = self.q + ((self.s * (t - self.q) + (1 << (CONST_PREC - 1))) >> CONST_PREC)
                if nq == self.q and nq != t:
                    nq += 1 if t == 127 else -1
                self.q = nq

                st = 0 if t != self.lt else (1 << CONST_PREC) - 1
                ns = self.s
                if ns != st:
                    ns += 1 if st != 0 else -1
                if CONST_PREC > 8 and ns < (1 << (CONST_PREC - 7)):
                    ns = (1 << (CONST_PREC - 7))
                self.s = ns

                self.lt = t

            if final and i == length - 1:
                d >>= 8 - (len(buf) % 8)
            output[i] = d

        if not final and len(buf) % 8 > 0:
            self.pending = buf[-(len(buf) % 8):]
        else:
            self.pending = None

        return bytes(output)

class DFPWMEncoderStereo:
    def __init__(self, q_left=0, q_right=0, s_left=0, s_right=0, lt_left=-128, lt_right=-128):
        self.q_left = q_left
        self.q_right = q_right
        self.s_left = s_left
        self.s_right = s_right
        self.lt_left = lt_left
        self.lt_right = lt_right
        self.pending = None

    def encode(self, buffer, final=False):
        if not isinstance(buffer, (bytes, bytearray)):
            raise TypeError("Argument #1 must be a bytes-like object.")

        buf = buffer
        if self.pending is not None:
            buf = self.pending + buffer

        # Ensure the buffer length is even for stereo (left and right)
        if len(buf) % 2 != 0:
            raise ValueError("Input buffer length must be even for stereo encoding.")

        length = len(buf) // 16  # Each 16 bytes produces one output byte
        if final:
            # If final is True, handle the last segment
            if len(buf) % 16 != 0:
                length += 1  # We need one more byte for the remaining data

        output = bytearray(length * 2)  # Allocate space for stereo output

        for i in range(length):
            d_left = 0
            d_right = 0

            # Calculate how many samples to process for this chunk
            num_samples = 8 if not (final and i == length - 1) else (len(buf) - (i * 16)) // 2

            for j in range(num_samples):
                # Left channel processing
                v_left = buf[i * 16 + j * 2] - 128  # Convert from unsigned to signed
                t_left = 127 if v_left > self.q_left or (v_left == self.q_left and v_left == 127) else -128
                d_left >>= 1
                if t_left > 0:
                    d_left |= 0x80

                nq_left = self.q_left + ((self.s_left * (t_left - self.q_left) + (1 << (CONST_PREC - 1))) >> CONST_PREC)
                if nq_left == self.q_left and nq_left != t_left:
                    nq_left += 1 if t_left == 127 else -1
                self.q_left = nq_left

                st_left = 0 if t_left != self.lt_left else (1 << CONST_PREC) - 1
                ns_left = self.s_left
                if ns_left != st_left:
                    ns_left += 1 if st_left != 0 else -1
                if CONST_PREC > 8 and ns_left < (1 << (CONST_PREC - 7)):
                    ns_left = (1 << (CONST_PREC - 7))
                self.s_left = ns_left

                self.lt_left = t_left

                # Right channel processing
                v_right = buf[i * 16 + j * 2 + 1] - 128  # Convert from unsigned to signed
                t_right = 127 if v_right > self.q_right or (v_right == self.q_right and v_right == 127) else -128
                d_right >>= 1
                if t_right > 0:
                    d_right |= 0x80

                nq_right = self.q_right + (
                        (self.s_right * (t_right - self.q_right) + (1 << (CONST_PREC - 1))) >> CONST_PREC)
                if nq_right == self.q_right and nq_right != t_right:
                    nq_right += 1 if t_right == 127 else -1
                self.q_right = nq_right

                st_right = 0 if t_right != self.lt_right else (1 << CONST_PREC) - 1
                ns_right = self.s_right
                if ns_right != st_right:
                    ns_right += 1 if st_right != 0 else -1
                if CONST_PREC > 8 and ns_right < (1 << (CONST_PREC - 7)):
                    ns_right = (1 << (CONST_PREC - 7))
                self.s_right = ns_right

                self.lt_right = t_right

            # Ensure that values fit in byte range
            d_left &= 0xFF
            d_right &= 0xFF

            # Store left and right channel values in separate bytes
            output[i * 2] = d_left
            output[i * 2 + 1] = d_right

        # Handle final adjustments for the last chunk if necessary
        if final and len(buf) % 16 > 0:
            remaining_bytes = len(buf) % 16
            output[-2] >>= 8 - (remaining_bytes // 2)
            output[-1] >>= 8 - (remaining_bytes // 2)

        if not final and len(buf) % 16 > 0:
            self.pending = buf[-(len(buf) % 16):]
        else:
            self.pending = None

        return bytes(output)


class DFPWMDecoder:
    def __init__(self, fq=0, q=0, s=0, lt=-128):
        self.fq = fq
        self.q = q
        self.s = s
        self.lt = lt

    def decode(self, buffer, fs=None):
        if not isinstance(buffer, (bytes, bytearray)):
            raise TypeError("Argument #1 must be a bytes-like object.")

        fs = fs or CONST_POSTFILT
        inpos = 0
        outpos = 0
        output = bytearray(len(buffer) * 8)

        for i in range(len(buffer)):
            d = buffer[inpos]
            inpos += 1
            for j in range(8):
                t = 127 if d & 1 else -128
                d >>= 1

                nq = self.q + ((self.s * (t - self.q) + (1 << (CONST_PREC - 1))) >> CONST_PREC)
                if nq == self.q and nq != t:
                    self.q += 1 if t == 127 else -1
                lq = self.q
                self.q = nq

                st = 0 if t != self.lt else (1 << CONST_PREC) - 1
                ns = self.s
                if ns != st:
                    ns += 1 if st != 0 else -1
                if CONST_PREC > 8 and ns < (1 << (CONST_PREC - 7)):
                    ns = (1 << (CONST_PREC - 7))
                self.s = ns

                # Anti-Jerk filtering
                ov = (nq + lq + 1) >> 1 if t != self.lt else nq

                # Low-pass filtering
                self.fq += (fs * (ov - self.fq) + 0x80) >> 8
                ov = self.fq

                # Output sample
                output[outpos] = int(ov + 128)  # Convert to unsigned
                outpos += 1

                self.lt = t

        return bytes(output)

class DFPWMDecoderStereo:
    def __init__(self, fq_left=0, fq_right=0, q_left=0, q_right=0, s_left=0, s_right=0, lt_left=-128, lt_right=-128):
        self.fq_left = fq_left
        self.fq_right = fq_right
        self.q_left = q_left
        self.q_right = q_right
        self.s_left = s_left
        self.s_right = s_right
        self.lt_left = lt_left
        self.lt_right = lt_right

    def decode(self, buffer, fs=None):
        if not isinstance(buffer, (bytes, bytearray)):
            raise TypeError("Argument #1 must be a bytes-like object.")

        fs = fs or CONST_POSTFILT
        inpos = 0
        outpos = 0
        output_length = len(buffer) * 8
        output = bytearray(output_length)

        for i in range(len(buffer)):
            # Read two channels from the buffer
            d_left = buffer[inpos]  # Left channel byte
            d_right = buffer[inpos + 1] if inpos + 1 < len(buffer) else 0  # Right channel byte (safe access)
            inpos += 2

            # Decode left channel
            for j in range(8):
                t_left = 127 if d_left & 1 else -128
                d_left >>= 1

                nq_left = self.q_left + ((self.s_left * (t_left - self.q_left) + (1 << (CONST_PREC - 1))) >> CONST_PREC)
                if nq_left == self.q_left and nq_left != t_left:
                    self.q_left += 1 if t_left == 127 else -1
                lq_left = self.q_left
                self.q_left = nq_left

                st_left = 0 if t_left != self.lt_left else (1 << CONST_PREC) - 1
                ns_left = self.s_left
                if ns_left != st_left:
                    ns_left += 1 if st_left != 0 else -1
                if CONST_PREC > 8 and ns_left < (1 << (CONST_PREC - 7)):
                    ns_left = (1 << (CONST_PREC - 7))
                self.s_left = ns_left

                # Anti-Jerk filtering for left channel
                ov_left = (nq_left + lq_left + 1) >> 1 if t_left != self.lt_left else nq_left

                # Low-pass filtering for left channel
                self.fq_left += (fs * (ov_left - self.fq_left) + 0x80) >> 8
                ov_left = self.fq_left

                # Output sample for left channel
                output[outpos] = int(ov_left + 128)  # Convert to unsigned
                outpos += 1

                self.lt_left = t_left

            # Decode right channel
            for j in range(8):
                t_right = 127 if d_right & 1 else -128
                d_right >>= 1

                nq_right = self.q_right + ((self.s_right * (t_right - self.q_right) + (1 << (CONST_PREC - 1))) >> CONST_PREC)
                if nq_right == self.q_right and nq_right != t_right:
                    self.q_right += 1 if t_right == 127 else -1
                lq_right = self.q_right
                self.q_right = nq_right

                st_right = 0 if t_right != self.lt_right else (1 << CONST_PREC) - 1
                ns_right = self.s_right
                if ns_right != st_right:
                    ns_right += 1 if st_right != 0 else -1
                if CONST_PREC > 8 and ns_right < (1 << (CONST_PREC - 7)):
                    ns_right = (1 << (CONST_PREC - 7))
                self.s_right = ns_right

                # Anti-Jerk filtering for right channel
                ov_right = (nq_right + lq_right + 1) >> 1 if t_right != self.lt_right else nq_right

                # Low-pass filtering for right channel
                self.fq_right += (fs * (ov_right - self.fq_right) + 0x80) >> 8
                ov_right = self.fq_right

                # Output sample for right channel
                output[outpos] = int(ov_right + 128)  # Convert to unsigned
                outpos += 1

                self.lt_right = t_right

        return bytes(output)

# --------------------------------------------------------------------------------------------------------------------------


# Constants
J17_NTAPS = 81
NICAM_AUDIO_LEN = 733
NICAM_FRAME_BYTES = 732
NICAM_FRAME_BITS = NICAM_FRAME_BYTES * 8
NICAM_SYMBOL_RATE = 364000
NICAM_FAW = 0x07

# Pre-calculated J.17 pre-emphasis filter taps, 32kHz sample rate
J17_TAPS = np.array([
    -1, 0, -1, -1, -1, -1, -1, -1, -1, -1, -2, -2, -3, -3, -3, -3, -5, -5,
    -6, -7, -9, -10, -13, -14, -18, -21, -27, -32, -42, -51, -69, -86, -120,
    -159, -233, -332, -524, -814, -1402, -2372, -4502, 25590, -4502, -2372,
    -1402, -814, -524, -332, -233, -159, -120, -86, -69, -51, -42, -32, -27,
    -21, -18, -14, -13, -10, -9, -7, -6, -5, -5, -3, -3, -3, -3, -2, -2, -1,
    -1, -1, -1, -1, -1, -1, -1, 0, -1
], dtype=np.int32)

INV_J17_TAPS = np.array([
    1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 3, 3, 3, 3, 5, 5,
    6, 7, 9, 10, 13, 14, 18, 21, 27, 32, 42, 51, 69, 86, 120,
    159, 233, 332, 524, 814, 1402, 2372, 4502, -25590, 4502, 2372,
    1402, 814, 524, 332, 233, 159, 120, 86, 69, 51, 42, 32, 27,
    21, 18, 14, 13, 10, 9, 7, 6, 5, 5, 3, 3, 3, 3, 2, 2, 1,
    1, 1, 1, 1, 1, 1, 1, 0, 1
], dtype=np.int32)

# RF symbols
STEP = [0, 3, 1, 2]
SYMS = [0, 1, 3, 2]


@dataclass
class ScaleFactor:
    factor: int
    shift: int
    coding_range: int
    protection_range: int


SCALE_FACTORS = [
    ScaleFactor(0, 2, 5, 7),  # 0b000
    ScaleFactor(1, 2, 5, 7),  # 0b001
    ScaleFactor(2, 2, 5, 6),  # 0b010
    ScaleFactor(4, 2, 5, 5),  # 0b100
    ScaleFactor(3, 3, 4, 4),  # 0b011
    ScaleFactor(5, 4, 3, 3),  # 0b101
    ScaleFactor(6, 5, 2, 2),  # 0b110
    ScaleFactor(7, 6, 1, 1),  # 0b111
]


class NicamEncoder:
    def __init__(self, mode: int, reserve: int):
        self.mode = mode
        self.reserve = reserve
        self.frame_count = 0
        self.fir_l = np.zeros(J17_NTAPS, dtype=np.int16)
        self.fir_r = np.zeros(J17_NTAPS, dtype=np.int16)
        self.fir_p = 0
        self.prn = self._generate_prn()

    def _generate_prn(self) -> np.ndarray:
        """Generate the PRN sequence for a NICAM-728 packet"""
        prn = np.zeros(NICAM_FRAME_BYTES - 1, dtype=np.uint8)
        poly = 0x1FF

        for x in range(NICAM_FRAME_BYTES - 1):
            byte = 0
            for _ in range(8):
                b = poly & 1
                b ^= (poly >> 4) & 1

                poly >>= 1
                poly |= b << 8

                byte = (byte << 1) | b
            prn[x] = byte

        return prn

    def _calculate_scale_factor(self, pcm: np.ndarray, step: int) -> ScaleFactor:
        """Calculate the optimal scale factor for an audio block"""
        b = 1

        for i in range(0, len(pcm), step):
            s = abs(pcm[i])
            while b < 7 and s >> (b + 8):
                b += 1

        return SCALE_FACTORS[b]

    def _parity(self, value: int) -> int:
        """Calculate parity bit"""
        return bin(value).count('1') & 1

    def _process_audio(self, src: np.ndarray) -> np.ndarray:
        """Process audio samples with J.17 pre-emphasis and encoding"""
        # Apply J.17 pre-emphasis filter
        dst = np.zeros(NICAM_AUDIO_LEN * 2, dtype=np.int16)

        for x in range(NICAM_AUDIO_LEN):
            self.fir_l[self.fir_p] = src[x * 2] if src is not None else 0
            self.fir_r[self.fir_p] = src[x * 2 + 1] if src is not None else 0
            self.fir_p = (self.fir_p + 1) % J17_NTAPS

            l = r = 0
            p = self.fir_p
            for tap in J17_TAPS:
                l += int(self.fir_l[p]) * tap
                r += int(self.fir_r[p]) * tap
                p = (p + 1) % J17_NTAPS

            dst[x * 2] = l >> 15
            dst[x * 2 + 1] = r >> 15

        # Calculate scale factors
        scale_l = self._calculate_scale_factor(dst[::2], 1)
        scale_r = self._calculate_scale_factor(dst[1::2], 1)
        scales = [scale_l, scale_r]

        # Scale and append samples
        for x in range(NICAM_AUDIO_LEN * 2):
            # Shift down the selected range
            dst[x] = (dst[x] >> scales[x & 1].shift) & 0x3FF

            # Add parity bit
            dst[x] |= self._parity(dst[x] >> 4) << 10

            # Add scale-factor code if necessary
            if x < 54:
                dst[x] ^= ((scales[x & 1].factor >> (2 - (x // 2 % 3))) & 1) << 10

        return dst

    def encode_frame(self, audio: np.ndarray) -> np.ndarray:
        """Encode a NICAM frame"""
        # Process audio
        j17_audio = self._process_audio(audio)

        # Create frame
        frame = np.zeros(NICAM_FRAME_BYTES, dtype=np.uint8)
        frame[0] = NICAM_FAW

        # Set control bits
        frame[1] = (
                (((~self.frame_count) >> 3) & 1) << 7 |  # C0
                ((self.mode >> 2) & 1) << 6 |  # C1
                ((self.mode >> 1) & 1) << 5 |  # C2
                ((self.mode >> 0) & 1) << 4 |  # C3
                (self.reserve & 1) << 3  # C4
        )

        # Pack encoded audio into frame
        xi = 0
        for x in range(NICAM_AUDIO_LEN * 2):
            for b in range(11):
                if j17_audio[x] & (1 << b):
                    frame[3 + (xi // 8)] |= 1 << (7 - (xi % 8))

                xi += 16
                if xi >= NICAM_FRAME_BITS - 24:
                    xi -= NICAM_FRAME_BITS - 24 - 1

        # Apply PRN
        frame[1:] ^= self.prn

        self.frame_count += 1
        return frame

@dataclass
class DecodedFrame:
    mode: int
    reserve: int
    frame_count: int
    audio_left: np.ndarray
    audio_right: np.ndarray
    error_count: int
    frame_aligned: bool


class NicamDecoder:
    def __init__(self):
        self.frame_count = 0
        self.fir_l = np.zeros(J17_NTAPS, dtype=np.int16)
        self.fir_r = np.zeros(J17_NTAPS, dtype=np.int16)
        self.fir_p = 0
        self.prn = self._generate_prn()
        self.frame_sync = False
        self.last_frame_count = 0

    def _generate_prn(self) -> np.ndarray:
        """Generate the same PRN sequence as encoder for descrambling"""
        prn = np.zeros(NICAM_FRAME_BYTES - 1, dtype=np.uint8)
        poly = 0x1FF

        for x in range(NICAM_FRAME_BYTES - 1):
            byte = 0
            for _ in range(8):
                b = poly & 1
                b ^= (poly >> 4) & 1

                poly >>= 1
                poly |= b << 8

                byte = (byte << 1) | b
            prn[x] = byte

        return prn

    def _parity_check(self, value: int) -> bool:
        """Check if parity is correct for a value"""
        return bin(value).count('1') % 2 == 0

    def _deinterleave_audio(self, frame: np.ndarray) -> Tuple[np.ndarray, int]:
        """Deinterleave audio samples from frame and count errors"""
        audio = np.zeros(NICAM_AUDIO_LEN * 2, dtype=np.int16)
        error_count = 0

        xi = 0
        for x in range(NICAM_AUDIO_LEN * 2):
            sample = 0
            for b in range(11):
                bit_pos = 3 * 8 + xi  # Start after header
                byte_idx = bit_pos // 8
                bit_idx = 7 - (bit_pos % 8)

                if byte_idx < len(frame):
                    bit = (frame[byte_idx] >> bit_idx) & 1
                    sample |= bit << b

                xi += 16
                if xi >= NICAM_FRAME_BITS - 24:
                    xi -= NICAM_FRAME_BITS - 24 - 1

            # Check parity
            expected_parity = (sample >> 10) & 1
            actual_parity = self._parity_check(sample & 0x3FF)
            if expected_parity != actual_parity:
                error_count += 1

            # Store 10-bit audio sample
            audio[x] = sample & 0x3FF

        return audio, error_count

    def _decode_scale_factors(self, audio: np.ndarray) -> List[ScaleFactor]:
        """Decode scale factors from first 54 samples"""
        scale_factors = []
        for channel in range(2):
            factor = 0
            for i in range(3):
                factor |= ((audio[channel + i * 2] >> 10) & 1) << (2 - i)
            scale_factors.append(SCALE_FACTORS[factor])
        return scale_factors

    def _apply_inverse_j17(self, audio: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Apply inverse J.17 filter to recover original audio"""
        left = np.zeros(NICAM_AUDIO_LEN, dtype=np.int16)
        right = np.zeros(NICAM_AUDIO_LEN, dtype=np.int16)

        for x in range(NICAM_AUDIO_LEN):
            # Store filtered samples
            self.fir_l[self.fir_p] = audio[x * 2]
            self.fir_r[self.fir_p] = audio[x * 2 + 1]
            self.fir_p = (self.fir_p + 1) % J17_NTAPS

            # Apply inverse filter
            l = r = 0
            p = self.fir_p
            for tap in INV_J17_TAPS:
                l += int(self.fir_l[p]) * tap
                r += int(self.fir_r[p]) * tap
                p = (p + 1) % J17_NTAPS

            left[x] = l >> 15
            right[x] = r >> 15

        return left, right

    def decode_frame(self, frame: np.ndarray) -> Optional[DecodedFrame]:
        """Decode a complete NICAM frame"""
        # Check frame alignment word
        if frame[0] != NICAM_FAW:
            self.frame_sync = False
            return None

        # Descramble with PRN
        descrambled = frame.copy()
        descrambled[1:] ^= self.prn

        # Extract control bits
        frame_count_bit = (descrambled[1] >> 7) & 1
        mode = ((descrambled[1] >> 4) & 0x7)
        reserve = (descrambled[1] >> 3) & 1

        # Deinterleave audio
        audio, error_count = self._deinterleave_audio(descrambled)

        # Decode scale factors
        scale_factors = self._decode_scale_factors(audio)

        # Apply scale factors
        for x in range(NICAM_AUDIO_LEN * 2):
            sf = scale_factors[x & 1]
            audio[x] = audio[x] << sf.shift

        # Apply inverse J.17 filter
        left, right = self._apply_inverse_j17(audio)

        # Update frame sync status
        if not self.frame_sync:
            self.frame_sync = True
            self.frame_count = 0
        else:
            expected_count_bit = ((~(self.frame_count >> 3)) & 1)
            if frame_count_bit != expected_count_bit:
                self.frame_sync = False
                return None
            self.frame_count += 1

        return DecodedFrame(
            mode=mode,
            reserve=reserve,
            frame_count=self.frame_count,
            audio_left=left,
            audio_right=right,
            error_count=error_count,
            frame_aligned=self.frame_sync
        )

    def reset(self):
        """Reset decoder state"""
        self.frame_count = 0
        self.frame_sync = False
        self.fir_l.fill(0)
        self.fir_r.fill(0)
        self.fir_p = 0