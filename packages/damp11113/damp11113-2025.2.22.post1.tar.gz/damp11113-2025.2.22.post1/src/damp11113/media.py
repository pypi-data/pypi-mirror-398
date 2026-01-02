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

import libscrc
import cv2
import numpy as np
import qrcode
import barcode
from barcode.writer import ImageWriter
import os
from PIL import Image
from pydub import AudioSegment
from pyzbar import pyzbar
from scipy.signal import resample
import pyaudio
import wave
import threading
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum

from .processbar import LoadingProgress, Steps
from .utils import get_size_unit
from .randoms import rannum
from .file import sizefolder3, allfiles, sort_files
from .codec import DFPWMEncoder, DFPWMDecoder, DFPWMEncoder2, DFPWMEncoderStereo, DFPWMDecoderStereo

def clip2frames(clip_path, frame_path, currentframe=1, filetype='png'):
    progress = LoadingProgress(total=0, unit='frame')
    progress.desc = f'set output to {frame_path}'
    try:
        clip = cv2.VideoCapture(clip_path)
        length = int(clip.get(cv2.CAP_PROP_FRAME_COUNT))
        progress.total = length
        if not os.path.exists(frame_path):
            os.mkdir(frame_path)
            progress.desc = f'create output folder {frame_path}'
        progress.desc = 'converting... '
        while True:
            size = get_size_unit(sizefolder3(frame_path))
            ret, frame = clip.read()
            PILframe = CV22PIL(frame)
            PILframe.save(f'{frame_path}/{str(currentframe)}' + f'.{filetype}')
            progress.desc = f'converting... | filetype .{filetype} | converted {currentframe}/{length} | file {currentframe}.{filetype} | used {size}'
            currentframe += 1
            progress.update(1)
            if currentframe == length:
                progress.desc = f'converted {currentframe} frame | used {size} MB'
                progress.stop()
                break
    except Exception as e:
        progress.fail = f'error: {e}'
        progress.stopfail()

def im2ascii(image, width=None, height=None, new_width=None, chars=None, pixelss=25):
    try:
        try:
            img = Image.open(image)
            img_flag = True
        except:
            print(image, "Unable to find image")

        if width is None:
            width = img.size[0]
        if height is None:
            height = img.size[1]
        if new_width is None:
            new_width = width
        aspect_ratio = int(height)/int(width)
        new_height = aspect_ratio * new_width * 0.55
        img = img.resize((new_width, int(new_height)))

        img = img.convert('L')

        if chars is None:
            chars = ["@", "J", "D", "%", "*", "P", "+", "Y", "$", ",", "."]
            #chars = ['!', '"', '#', '$', '%', '&', "'", '(', ')', '*', '+', ',', '-', '.', '/', ':', ';', '<', '=', '>', '?', '@', '[', '\\', ']', '^', '_', '`', '{', '|', '}', '~']
            #chars = list(string.printable)

        pixels = img.getdata()
        new_pixels = [chars[pixel//pixelss] for pixel in pixels]
        new_pixels = ''.join(new_pixels)
        new_pixels_count = len(new_pixels)
        ascii_image = [new_pixels[index:index + new_width] for index in range(0, new_pixels_count, new_width)]
        ascii_image = "\n".join(ascii_image)
        return ascii_image

    except Exception as e:
        raise e

def im2pixel(image, i_size, output):
    img = Image.open(image)
    small_img = img.resize(i_size, Image.BILINEAR)
    res = small_img.resize(img.size, Image.NEAREST)
    res.save(output)

def repixpil(pilarray, i_size):
    small_img = pilarray.resize(i_size, Image.BILINEAR)
    res = small_img.resize(pilarray.size, Image.NEAREST)
    return res


def resziepil(image, max_width, max_height):
    """
    Resize an image to fit within a bounding box without cropping.

    Args:
    image (PIL.Image): The input image object.
    max_width (int): Maximum width of the bounding box.
    max_height (int): Maximum height of the bounding box.

    Returns:
    PIL.Image: The resized image object.
    """
    # Calculate new dimensions while preserving aspect ratio
    width_ratio = max_width / image.width
    height_ratio = max_height / image.height
    min_ratio = min(width_ratio, height_ratio)
    new_width = int(image.width * min_ratio)
    new_height = int(image.height * min_ratio)

    # Resize the image
    resized_image = image.resize((new_width, new_height), Image.ANTIALIAS)

    # Create a new image of the correct dimensions, with a white background
    new_image = Image.new("RGB", (max_width, max_height), "white")

    # Paste the resized image onto the new image, centered
    x_offset = (max_width - new_width) // 2
    y_offset = (max_height - new_height) // 2
    new_image.paste(resized_image, (x_offset, y_offset))

    # Return the resized image
    return new_image

def qrcodegen(text, showimg=False, save_path='./', filename='qrcode', filetype='png', version=1, box_size=10, border=5, fill_color="black", back_color="white", error_correction=qrcode.constants.ERROR_CORRECT_L, fit=True):
    qr = qrcode.QRCode(
        version=version,
        error_correction=error_correction,
        box_size=box_size,
        border=border,
    )
    qr.add_data(text)
    qr.make(fit=fit)
    img = qr.make_image(fill_color=fill_color, back_color=back_color)
    if showimg:
        img.show()
    else:
        img.save(f'{save_path}{filename}.{filetype}')

def barcodegen(number, type='ean13', showimg=False, save_path='./', filename='barcode', filetype='png', writer=ImageWriter()):
    barcode_img = barcode.get(type, number, writer=writer)
    if showimg:
        img = Image.open(barcode_img.render())
        img.show()
    else:
        barcode_img.save(f'{save_path}{filename}.{filetype}')

def imseq2clip(imseq, path, videoname='video.mp4', fps=30):
    progress = LoadingProgress(total=0, unit='frame')
    progress.desc = f'please wait...'
    simseq = sort_files(allfiles(imseq), reverse=False)
    img = []
    for i in simseq:
        i = path+i
        img.append(i)
    progress.desc = f'converting...'
    progress.total = len(img)
    progress.unit = 'frame'
    cv2_fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video = cv2.VideoWriter(path+videoname, cv2_fourcc, fps)
    for i in range(len(img)):
        progress.desc = f'converting... | frame {i}/{len(img)}'
        frame = cv2.imread(img[i])
        video.write(frame)
        progress.update(1)

    video.release()
    progress.end = f'converted'
    progress.stop()

def readbqrcode(image):
    image = Image.open(image)
    qr_code = pyzbar.decode(image)[0]
    data = qr_code.data.decode("utf-8")
    type = qr_code.type
    return (data, type)

def PIL2CV2(pil_image):
    return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

def CV22PIL(cv2_array):
    return Image.fromarray(cv2.cvtColor(cv2_array, cv2.COLOR_BGR2RGB))

def ranpix(opath, size=(512, 512)):
    im = Image.new("RGB", size=size)
    width, height = im.size
    for x in range(width):
        for y in range(height):
            L = rannum(0, 255)
            R = rannum(0, 255)
            G = rannum(0, 255)
            B = rannum(0, 255)
            LRGB = (L, R, G, B)
            im.putpixel((x, y), LRGB)
    im.save(opath)

def PIL2DPG(pil_image):
    return CV22DPG(PIL2CV2(pil_image))

def CV22DPG(cv2_array):
    try:
        if cv2_array is None or len(cv2_array.shape) < 3:
            print("Invalid or empty array received.")
            return None

        if len(cv2_array.shape) == 2:
            cv2_array = cv2_array[:, :, np.newaxis]

        data = np.flip(cv2_array, 2)
        data = data.ravel()
        data = np.asfarray(data, dtype='f')
        return np.true_divide(data, 255.0)
    except Exception as e:
        print("Error in CV22DPG:", e)
        return None

def PromptPayQRcodeGen(account,one_time=True,country="TH",money="",currency="THB"):
    """
    text_qr(account,one_time=True,country="TH",money="",currency="THB")
    account is phone number or  identification number.
    one_time : if you use once than it's True.
    country : TH
    money : money (if have)
    currency : THB
    """
    Version = "0002"+"01" # เวชั่นของ  PromptPay
    if one_time==True: # one_time คือ ต้องการให้โค้ดนี้ครั้งเดียวหรือไม่
        one_time = "010212" # 12 ใช้ครั้งเดียว
    else:
        one_time = "010211" # 11 ใช้ได้้หลายครั้ง
    merchant_account_information = "2937" # ข้อมูลผู้ขาย
    merchant_account_information += "0016" + "A000000677010111" # หมายเลขแอปพลิเคชั่น PromptPay
    if len(account) != 13: # ใช้บัญชีใช้เป็นเบอร์มือถือหรือไม่ ถ้าใช่ จำนวนจะไม่เท่ากับ 13
        account = list(account)
        merchant_account_information += "011300" # 01 หมายเลขโทรศัพท์ ความยาว 13 ขึ้นต้น 00
        if country == "TH":
            merchant_account_information += "66" # รหัสประเทศ 66 คือประเทศไทย
        del account[0] # ตัดเลข 0 หน้าเบอร์ออก
        merchant_account_information += ''.join(account)
    else:
        merchant_account_information += "02" + account.replace('-', '') # กรณีที่ไม่รับมือถือ แสดงว่าเป็นเลขบัตรประชาชน
    country = "5802" + country # ประเทศ
    if currency == "THB":
        currency = "5303" + "764" # "764"  คือเงินบาทไทย ตาม https://en.wikipedia.org/wiki/ISO_4217
    if money != "": # กรณีกำหนดเงิน
        check_money = money.split('.') # แยกจาก .
        if len(check_money) == 1 or len(check_money[1]) == 1: # กรณีที่ไม่มี . หรือ มีทศนิยมแค่หลักเดียว
            money = "54" + "0" + str(len(str(float(money)))+1) + str(float(money)) + "0"
        else:
            money = "54" + "0" + str(len(str(float(money)))) + str(float(money)) # กรณีที่มีทศนิยมครบ
    check_sum = Version + one_time + merchant_account_information + country + currency + money + "6304" # เช็คค่า check sum
    check_sum1 = hex(libscrc.ccitt(check_sum.encode("ascii"), 0xffff)).replace('0x', '')
    if len(check_sum1) < 4: # # แก้ไขข้อมูล check_sum ไม่ครบ 4 หลัก
        check_sum1 = ("0" * (4 - len(check_sum1))) + check_sum1
    check_sum += check_sum1
    return check_sum.upper() # upper ใช้คืนค่าสตริงเป็นตัวพิมพ์ใหญ่

def change_color_bit(image, output, colorbit=64):
    img = Image.open(image)
    a = img.convert("P", palette=Image.ADAPTIVE, colors=colorbit)
    a.save(output)

#-----------------pyaudio-effect-------------------------

def stretch(snd_array, factor, window_size, h):
    """ Stretches/shortens a sound, by some factor. """
    phase = np.zeros(window_size)
    hanning_window = np.hanning(window_size)
    result = np.zeros(int(len(snd_array) / factor + window_size))
    for i in np.arange(0, len(snd_array) - (window_size + h), h*factor):
        i = int(i)
        # Two potentially overlapping subarrays
        a1 = snd_array[i: i + window_size]
        a2 = snd_array[i + h: i + window_size + h]

        # The spectra of these arrays
        s1 = np.fft.fft(hanning_window * a1)
        s2 = np.fft.fft(hanning_window * a2)

        # Rephase all frequencies
        phase = (phase + np.angle(s2/s1)) % 2*np.pi

        a2_rephased = np.fft.ifft(np.abs(s2)*np.exp(1j*phase))
        i2 = int(i/factor)
        result[i2: i2 + window_size] += hanning_window*a2_rephased.real
    return result.astype('int16')

# --------------------------------------------------------

def EdgeDetection(cvarray):
    # Convert to graycsale
    img_gray = cv2.cvtColor(cvarray, cv2.COLOR_BGR2GRAY)
    # Blur the image for better edge detection
    img_blur = cv2.GaussianBlur(img_gray, (3, 3), 0)
    edges = cv2.Canny(image=img_blur, threshold1=100, threshold2=200)  # Canny Edge Detection
    return edges

class Yolov3Detection:
    def __init__(self, weightsfile, cfgfile, namesfile):
        self.net = cv2.dnn.readNet(weightsfile, cfgfile)
        self.classes = []
        with open(namesfile, "r") as f:
            self.classes = [line.strip() for line in f.readlines()]
        self.input_size = (416, 416)
        self.scale = 1/255.0

    def detect(self, frame, textcolor=None, framecolor=None):
        height, width = frame.shape[:2]

        # Preprocess input image
        blob = cv2.dnn.blobFromImage(frame, self.scale, self.input_size, swapRB=True, crop=False)

        # Set input for YOLOv3 network
        self.net.setInput(blob)

        # Forward pass through YOLOv3 network
        output_layers = self.net.getUnconnectedOutLayersNames()
        layer_outputs = self.net.forward(output_layers)

        # Initialize lists for bounding boxes, confidences, and class IDs
        boxes = []
        confidences = []
        class_ids = []
        info = []

        # Loop over each output layer
        for output in layer_outputs:
            # Loop over each detection
            for detection in output:
                # Extract class ID and confidence
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]

                # Filter out weak detections
                if confidence > 0.5:
                    # Compute bounding box coordinates
                    center_x = int(detection[0] * width)
                    center_y = int(detection[1] * height)
                    w = int(detection[2] * width)
                    h = int(detection[3] * height)
                    x = int(center_x - w / 2)
                    y = int(center_y - h / 2)

                    # Add bounding box, confidence, and class ID to lists
                    boxes.append([x, y, w, h])
                    confidences.append(float(confidence))
                    class_ids.append(class_id)

        # Apply non-maximum suppression to remove overlapping boxes
        indices = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)

        # Draw final bounding boxes on image
        if framecolor is None:
            framecolor = np.random.uniform(0, 255, size=(len(self.classes), 3))
        if textcolor is None:
            textcolor = np.random.uniform(0, 255, size=(len(self.classes), 3))

        if len(indices) > 0:
            for i in indices.flatten():
                box = boxes[i]
                x, y, w, h = box
                fcolor = framecolor[class_ids[i]]
                tcolor = textcolor[class_ids[i]]
                cv2.rectangle(frame, (x, y), (x + w, y + h), fcolor, 2)
                text = f"{self.classes[class_ids[i]]}: {confidences[i]:.2f}"
                cv2.putText(frame, text, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, tcolor, 2)
                info.append([self.classes[class_ids[i]], confidences[i], x, y, w, h])

        return frame, info

def audiofile2pyaudio(file, format, codec, startat=0, convertpyaudio=False, arrayformat=np.int16):
    """
    data, sample_rate, audio_format, channels = audiofile2pyaudio(file_path, format="ogg", codec="opus", convertpyaudio=True)
    """
    # import file
    audio = AudioSegment.from_file(file, format, codec, start_second=startat)
    # read samples to array
    audio_bytes = np.array(audio.get_array_of_samples())
    # convert
    if convertpyaudio:
        audio_bytes = audio_bytes.astype(arrayformat).reshape((-1, audio.channels)).tobytes()

    return audio_bytes, audio.frame_rate, audio.sample_width, audio.channels

class QuickDFPWMEnc:
    def __init__(self, version=1):
        """version: 1 or else = original, 2 = experiment 1, 3 = stereo experiment"""
        self.is_stereo = version == 3
        if version == 2:
            self.encoder = DFPWMEncoder2()
        elif version == 3:
            self.encoder = DFPWMEncoderStereo()
        else:
            self.encoder = DFPWMEncoder()

    def encode(self, pcm_data, one_frame=False):
        pcm_array = np.frombuffer(pcm_data, dtype=np.int16)
        # Convert stereo PCM to mono if necessary
        if not self.is_stereo:
            mono_pcm_array = (pcm_array[0::2] + pcm_array[1::2]) // 2
        else:
            mono_pcm_array = pcm_array
        # Convert 8-bit PCM data to DFPWM
        pcm_8bit = ((mono_pcm_array + 32768) // 256).astype(np.uint8)
        # Convert 8-bit PCM data to DFPWM
        dfpwm_data = self.encoder.encode(pcm_8bit.tobytes(), one_frame)

        return dfpwm_data


class QuickDFPWMDec:
    def __init__(self, sr=48000, stereo=False):
        if stereo:
            self.decoder = DFPWMDecoderStereo()
        else:
            self.decoder = DFPWMDecoder()
        self.sr = sr

    def decode(self, dfpwm_data):
        # Decode DFPWM data back to 8-bit PCM
        dfpwm_data = self.decoder.decode(dfpwm_data)
        pcm_8bit_array = np.frombuffer(dfpwm_data, dtype=np.uint8)
        # Convert 8-bit PCM data back to 16-bit PCM
        pcm_array = (pcm_8bit_array.astype(np.int16) * 256) - 32768
        # Resample back to the original sample rate
        num_samples = int(len(pcm_array) * self.sr / self.sr * 2)
        resampled_data = resample(pcm_array, num_samples)

        return resampled_data.astype(np.int16).tobytes()

class VoiceState(Enum):
    PLAYING = "playing"
    PAUSED = "paused"
    STOPPED = "stopped"


@dataclass
class Voice:
    id: int
    sample_data: np.ndarray
    sample_rate: int
    volume: float = 1.0
    pitch: float = 1.0
    position: int = 0
    state: VoiceState = VoiceState.STOPPED
    loop: bool = False


class AudioManager:
    def __init__(self, sample_rate=44100, chunk_size=1024, channels=1):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.channels = channels
        self.voices: Dict[int, Voice] = {}
        self.next_voice_id = 0
        self.is_running = False
        self.output_buffer = np.zeros(chunk_size, dtype=np.float32)

        # PyAudio setup
        self.pa = pyaudio.PyAudio()
        self.stream = None

        # Threading
        self.lock = threading.Lock()
        self.audio_thread = None

        # Recording for WAV output
        self.recording = False
        self.recorded_data = []

    def load_sample_from_file(self, filename: str) -> tuple:
        """Load audio sample from WAV file"""
        try:
            with wave.open(filename, 'rb') as wf:
                frames = wf.readframes(wf.getnframes())
                sample_rate = wf.getframerate()

                # Convert to numpy array
                if wf.getsampwidth() == 1:
                    dtype = np.int8
                elif wf.getsampwidth() == 2:
                    dtype = np.int16
                elif wf.getsampwidth() == 4:
                    dtype = np.int32
                else:
                    raise ValueError("Unsupported sample width")

                audio_data = np.frombuffer(frames, dtype=dtype)

                # Convert to float32 and normalize
                if dtype == np.int8:
                    audio_data = audio_data.astype(np.float32) / 128.0
                elif dtype == np.int16:
                    audio_data = audio_data.astype(np.float32) / 32768.0
                elif dtype == np.int32:
                    audio_data = audio_data.astype(np.float32) / 2147483648.0

                return audio_data, sample_rate
        except Exception as e:
            print(f"Error loading audio file: {e}")
            return None, None
    def add_voice(self, sample_data: np.ndarray, sample_rate: int = None,
                  volume: float = 1.0, pitch: float = 1.0, loop: bool = False) -> int:
        """Add a new voice to the manager"""
        if sample_rate is None:
            sample_rate = self.sample_rate

        voice_id = self.next_voice_id
        self.next_voice_id += 1

        with self.lock:
            self.voices[voice_id] = Voice(
                id=voice_id,
                sample_data=sample_data,
                sample_rate=sample_rate,
                volume=volume,
                pitch=pitch,
                loop=loop
            )

        return voice_id

    def play_voice(self, voice_id: int):
        """Start playing a voice"""
        with self.lock:
            if voice_id in self.voices:
                self.voices[voice_id].state = VoiceState.PLAYING
                self.voices[voice_id].position = 0

    def stop_voice(self, voice_id: int, destroy: bool = False):
        """Stop a voice"""
        with self.lock:
            if voice_id in self.voices:
                if destroy:
                    del self.voices[voice_id]
                else:
                    self.voices[voice_id].state = VoiceState.STOPPED
                    self.voices[voice_id].position = 0

    def pause_voice(self, voice_id: int):
        """Pause a voice"""
        with self.lock:
            if voice_id in self.voices:
                self.voices[voice_id].state = VoiceState.PAUSED

    def resume_voice(self, voice_id: int):
        """Resume a paused voice"""
        with self.lock:
            if voice_id in self.voices:
                if self.voices[voice_id].state == VoiceState.PAUSED:
                    self.voices[voice_id].state = VoiceState.PLAYING

    def set_voice_volume(self, voice_id: int, volume: float):
        """Set voice volume (0.0 to 1.0+)"""
        with self.lock:
            if voice_id in self.voices:
                self.voices[voice_id].volume = max(0.0, volume)

    def set_voice_pitch(self, voice_id: int, pitch: float):
        """Set voice pitch (1.0 = normal, 2.0 = double speed/pitch)"""
        with self.lock:
            if voice_id in self.voices:
                self.voices[voice_id].pitch = max(0.1, pitch)

    def remove_voice(self, voice_id: int):
        """Remove a voice from the manager"""
        with self.lock:
            if voice_id in self.voices:
                del self.voices[voice_id]

    def set_loop(self, voice_id: int, loop: bool):
        """Set looping for a voice"""
        with self.lock:
            if voice_id in self.voices:
                self.voices[voice_id].loop = loop

    def clear_all_voices(self):
        """Clear all voices from the manager"""
        with self.lock:
            self.voices.clear()
            self.next_voice_id = 0
    def _resample_audio(self, audio_data: np.ndarray, original_rate: int, target_rate: int) -> np.ndarray:
        """Simple resampling using linear interpolation"""
        if original_rate == target_rate:
            return audio_data

        ratio = target_rate / original_rate
        new_length = int(len(audio_data) * ratio)

        old_indices = np.linspace(0, len(audio_data) - 1, new_length)
        new_audio = np.interp(old_indices, np.arange(len(audio_data)), audio_data)

        return new_audio.astype(np.float32)

    def _process_voice(self, voice: Voice, chunk_size: int) -> np.ndarray:
        """Process a single voice and return audio chunk"""
        if voice.state != VoiceState.PLAYING:
            return np.zeros(chunk_size, dtype=np.float32)

        # Calculate effective sample rate with pitch
        effective_rate = voice.sample_rate * voice.pitch

        # Calculate how many samples we need from the original
        samples_needed = int(chunk_size * effective_rate / self.sample_rate)

        # Check if we have enough samples
        remaining_samples = len(voice.sample_data) - voice.position

        if remaining_samples <= 0:
            if voice.loop:
                voice.position = 0
                remaining_samples = len(voice.sample_data)
            else:
                voice.state = VoiceState.STOPPED
                return np.zeros(chunk_size, dtype=np.float32)

        # Get the audio chunk
        end_pos = min(voice.position + samples_needed, len(voice.sample_data))
        audio_chunk = voice.sample_data[voice.position:end_pos]

        # Handle looping if we need more samples
        if len(audio_chunk) < samples_needed and voice.loop:
            remaining_needed = samples_needed - len(audio_chunk)
            loop_chunk = voice.sample_data[:remaining_needed]
            audio_chunk = np.concatenate([audio_chunk, loop_chunk])
            voice.position = remaining_needed
        else:
            voice.position = end_pos

        # Resample to target sample rate if needed
        if effective_rate != self.sample_rate:
            audio_chunk = self._resample_audio(audio_chunk, int(effective_rate), self.sample_rate)

        # Ensure we have the right chunk size
        if len(audio_chunk) > chunk_size:
            audio_chunk = audio_chunk[:chunk_size]
        elif len(audio_chunk) < chunk_size:
            padded = np.zeros(chunk_size, dtype=np.float32)
            padded[:len(audio_chunk)] = audio_chunk
            audio_chunk = padded

        # Apply volume
        audio_chunk *= voice.volume

        return audio_chunk

    def _mix_audio(self) -> np.ndarray:
        """Mix all active voices together"""
        mixed = np.zeros(self.chunk_size, dtype=np.float32)

        with self.lock:
            for voice in self.voices.values():
                voice_audio = self._process_voice(voice, self.chunk_size)
                mixed += voice_audio

        # Simple limiting to prevent clipping
        mixed = np.clip(mixed, -1.0, 1.0)

        return mixed

    def _audio_callback(self, in_data, frame_count, time_info, status):
        """PyAudio callback function"""
        audio_data = self._mix_audio()

        # Record if needed
        if self.recording:
            self.recorded_data.append(audio_data.copy())

        # Convert to bytes
        audio_bytes = (audio_data * 32767).astype(np.int16).tobytes()

        return (audio_bytes, pyaudio.paContinue)

    def start_playback(self):
        """Start real-time audio playback"""
        if self.is_running:
            return

        self.stream = self.pa.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=self.sample_rate,
            output=True,
            frames_per_buffer=self.chunk_size,
            stream_callback=self._audio_callback
        )

        self.stream.start_stream()
        self.is_running = True

    def stop_playback(self):
        """Stop real-time audio playback"""
        if not self.is_running:
            return

        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

        self.is_running = False

    def get_voice_info(self, voice_id: int) -> dict:
        """Get information about a voice"""
        with self.lock:
            if voice_id in self.voices:
                voice = self.voices[voice_id]
                return {
                    'id': voice.id,
                    'state': voice.state.value,
                    'volume': voice.volume,
                    'pitch': voice.pitch,
                    'position': voice.position,
                    'length': len(voice.sample_data),
                    'loop': voice.loop
                }
        return None

    def list_voices(self) -> List[int]:
        """Get list of all voice IDs"""
        with self.lock:
            return list(self.voices.keys())

    def cleanup(self):
        """Clean up resources"""
        self.stop_playback()
        if self.pa:
            self.pa.terminate()

class ChannelState(Enum):
    IDLE = "idle"
    PLAYING = "playing"
    PAUSED = "paused"
    STOPPED = "stopped"

@dataclass
class AudioSample:
    """Represents an audio sample that can be loaded into a channel"""
    data: np.ndarray
    sample_rate: int
    name: str = ""


class AudioChannel:
    """Represents a single audio channel with its own playback state"""

    def __init__(self, channel_id: int, sample_rate: int = 44100):
        self.id = channel_id
        self.sample_rate = sample_rate

        # Playback state
        self.state = ChannelState.IDLE
        self.position = 0
        self.loop = False

        # Audio properties
        self.volume = 1.0
        self.pitch = 1.0
        self.pan = 0.0  # -1.0 (left) to 1.0 (right), 0.0 center
        self.mute = False
        self.solo = False

        # Sample data
        self.sample: Optional[AudioSample] = None

        # Effects
        self.reverb = 0.0
        self.low_pass_cutoff = None  # Hz, None means no filter
        self.high_pass_cutoff = None  # Hz, None means no filter

    def load_sample(self, sample: AudioSample):
        """Load an audio sample into this channel"""
        self.sample = sample
        self.position = 0
        self.state = ChannelState.STOPPED

    def clear_sample(self):
        """Remove the current sample from this channel"""
        self.sample = None
        self.position = 0
        self.state = ChannelState.IDLE

    def play(self):
        """Start playing the loaded sample"""
        if self.sample is not None:
            self.state = ChannelState.PLAYING

    def stop(self):
        """Stop playback and reset position"""
        self.state = ChannelState.STOPPED
        self.position = 0

    def pause(self):
        """Pause playback"""
        if self.state == ChannelState.PLAYING:
            self.state = ChannelState.PAUSED

    def resume(self):
        """Resume playback from paused state"""
        if self.state == ChannelState.PAUSED:
            self.state = ChannelState.PLAYING

    def reset(self):
        """Reset channel to default state"""
        self.stop()
        self.volume = 1.0
        self.pitch = 1.0
        self.pan = 0.0
        self.mute = False
        self.solo = False
        self.loop = False
        self.reverb = 0.0
        self.low_pass_cutoff = None
        self.high_pass_cutoff = None

    def get_info(self) -> dict:
        """Get channel information"""
        return {
            'id': self.id,
            'state': self.state.value,
            'volume': self.volume,
            'pitch': self.pitch,
            'pan': self.pan,
            'mute': self.mute,
            'solo': self.solo,
            'loop': self.loop,
            'position': self.position,
            'sample_loaded': self.sample is not None,
            'sample_name': self.sample.name if self.sample else None,
            'sample_length': len(self.sample.data) if self.sample else 0,
            'reverb': self.reverb,
            'low_pass_cutoff': self.low_pass_cutoff,
            'high_pass_cutoff': self.high_pass_cutoff
        }


class AudioManagerV2:
    """Multi-channel audio manager for mixing and playback"""

    def __init__(self, sample_rate=44100, chunk_size=1024, max_channels=16, audio_channels=2):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.max_channels = max_channels
        self.audio_channels = audio_channels

        # Audio channels
        self.channels: Dict[int, AudioChannel] = {}
        self.master_volume = 1.0
        self.master_mute = False

        # PyAudio setup
        self.pa = pyaudio.PyAudio()
        self.stream = None
        self.is_running = False

        # Threading
        self.lock = threading.Lock()

        # Recording
        self.recording = False
        self.recorded_data = []

        # Sample library
        self.sample_library: Dict[str, AudioSample] = {}

    def create_channel(self, channel_id: int) -> bool:
        """Create a new audio channel"""
        if channel_id < 0 or channel_id >= self.max_channels:
            return False

        with self.lock:
            if channel_id not in self.channels:
                self.channels[channel_id] = AudioChannel(channel_id, self.sample_rate)
                return True
        return False

    def remove_channel(self, channel_id: int) -> bool:
        """Remove an audio channel"""
        with self.lock:
            if channel_id in self.channels:
                del self.channels[channel_id]
                return True
        return False

    def get_channel(self, channel_id: int) -> Optional[AudioChannel]:
        """Get a channel by ID"""
        return self.channels.get(channel_id)

    def list_channels(self) -> List[int]:
        """Get list of all channel IDs"""
        with self.lock:
            return list(self.channels.keys())

    # Sample management
    def load_sample_from_file(self, filename: str, name: str = None) -> Optional[str]:
        """Load audio sample from WAV file into sample library"""
        if name is None:
            name = filename

        try:
            with wave.open(filename, 'rb') as wf:
                frames = wf.readframes(wf.getnframes())
                file_sample_rate = wf.getframerate()

                # Convert to numpy array
                if wf.getsampwidth() == 1:
                    dtype = np.int8
                    divisor = 128.0
                elif wf.getsampwidth() == 2:
                    dtype = np.int16
                    divisor = 32768.0
                elif wf.getsampwidth() == 4:
                    dtype = np.int32
                    divisor = 2147483648.0
                else:
                    raise ValueError("Unsupported sample width")

                audio_data = np.frombuffer(frames, dtype=dtype)
                audio_data = audio_data.astype(np.float32) / divisor

                # make sure the audio data is stereo if needed
                if self.audio_channels == 2 and len(audio_data.shape) == 1:
                    audio_data = np.column_stack((audio_data, audio_data))
                elif self.audio_channels == 1 and len(audio_data.shape) == 2:
                    audio_data = audio_data.mean(axis=1)

                sample = AudioSample(audio_data, file_sample_rate, name)
                self.sample_library[name] = sample
                return name

        except Exception as e:
            print(f"Error loading audio file: {e}")
            return None

    def get_sample(self, name: str) -> Optional[AudioSample]:
        """Get a sample from the library"""
        return self.sample_library.get(name)

    def list_samples(self) -> List[str]:
        """Get list of all sample names in library"""
        return list(self.sample_library.keys())

    def remove_sample(self, name: str) -> bool:
        """Remove a sample from the library"""
        if name in self.sample_library:
            del self.sample_library[name]
            return True
        return False

    # Channel control methods
    def load_sample_to_channel(self, channel_id: int, sample_name: str) -> bool:
        """Load a sample from library to a channel"""
        channel = self.get_channel(channel_id)
        sample = self.get_sample(sample_name)

        if channel and sample:
            with self.lock:
                channel.load_sample(sample)
            return True
        return False

    def play_channel(self, channel_id: int) -> bool:
        """Start playing a channel"""
        channel = self.get_channel(channel_id)
        if channel:
            with self.lock:
                channel.play()
            return True
        return False

    def stop_channel(self, channel_id: int) -> bool:
        """Stop a channel"""
        channel = self.get_channel(channel_id)
        if channel:
            with self.lock:
                channel.stop()
            return True
        return False

    def pause_channel(self, channel_id: int) -> bool:
        """Pause a channel"""
        channel = self.get_channel(channel_id)
        if channel:
            with self.lock:
                channel.pause()
            return True
        return False

    def resume_channel(self, channel_id: int) -> bool:
        """Resume a channel"""
        channel = self.get_channel(channel_id)
        if channel:
            with self.lock:
                channel.resume()
            return True
        return False

    def set_channel_volume(self, channel_id: int, volume: float) -> bool:
        """Set channel volume (0.0 to 1.0+)"""
        channel = self.get_channel(channel_id)
        if channel:
            with self.lock:
                channel.volume = max(0.0, volume)
            return True
        return False

    def set_channel_pitch(self, channel_id: int, pitch: float) -> bool:
        """Set channel pitch (1.0 = normal)"""
        channel = self.get_channel(channel_id)
        if channel:
            with self.lock:
                channel.pitch = max(0.1, pitch)
            return True
        return False

    def set_channel_pan(self, channel_id: int, pan: float) -> bool:
        """Set channel pan (-1.0 left, 0.0 center, 1.0 right)"""
        channel = self.get_channel(channel_id)
        if channel:
            with self.lock:
                channel.pan = np.clip(pan, -1.0, 1.0)
            return True
        return False

    def set_channel_loop(self, channel_id: int, loop: bool) -> bool:
        """Set channel looping"""
        channel = self.get_channel(channel_id)
        if channel:
            with self.lock:
                channel.loop = loop
            return True
        return False

    def mute_channel(self, channel_id: int, mute: bool = True) -> bool:
        """Mute/unmute a channel"""
        channel = self.get_channel(channel_id)
        if channel:
            with self.lock:
                channel.mute = mute
            return True
        return False

    def solo_channel(self, channel_id: int, solo: bool = True) -> bool:
        """Solo a channel (mutes all others)"""
        channel = self.get_channel(channel_id)
        if channel:
            with self.lock:
                channel.solo = solo
            return True
        return False

    def reset_channel(self, channel_id: int) -> bool:
        """Reset channel to default state"""
        channel = self.get_channel(channel_id)
        if channel:
            with self.lock:
                channel.reset()
            return True
        return False

    def clear_channel(self, channel_id: int) -> bool:
        """Clear sample from channel"""
        channel = self.get_channel(channel_id)
        if channel:
            with self.lock:
                channel.clear_sample()
            return True
        return False

    # Global controls
    def set_master_volume(self, volume: float):
        """Set master volume"""
        self.master_volume = max(0.0, volume)

    def set_master_mute(self, mute: bool):
        """Set master mute"""
        self.master_mute = mute

    def stop_all_channels(self):
        """Stop all channels"""
        with self.lock:
            for channel in self.channels.values():
                channel.stop()

    def clear_all_channels(self):
        """Clear samples from all channels"""
        with self.lock:
            for channel in self.channels.values():
                channel.clear_sample()

    def reset_all_channels(self):
        """Reset all channels to default state"""
        with self.lock:
            for channel in self.channels.values():
                channel.reset()

    # Audio processing
    def _resample_audio(self, audio_data: np.ndarray, original_rate: int, target_rate: int) -> np.ndarray:
        """Simple resampling using linear interpolation"""
        if original_rate == target_rate:
            return audio_data

        ratio = target_rate / original_rate
        new_length = int(len(audio_data) * ratio)

        old_indices = np.linspace(0, len(audio_data) - 1, new_length)
        new_audio = np.interp(old_indices, np.arange(len(audio_data)), audio_data)

        return new_audio.astype(np.float32)

    def _process_channel(self, channel: AudioChannel, chunk_size: int) -> np.ndarray:
        """Process a single channel and return audio chunk"""
        if (channel.state != ChannelState.PLAYING or
                channel.sample is None or
                channel.mute):
            return np.zeros(chunk_size, dtype=np.float32)

        # Calculate effective sample rate with pitch
        effective_rate = channel.sample.sample_rate * channel.pitch

        # Calculate how many samples we need from the original
        samples_needed = int(chunk_size * effective_rate / self.sample_rate)

        # Check if we have enough samples
        remaining_samples = len(channel.sample.data) - channel.position

        if remaining_samples <= 0:
            if channel.loop:
                channel.position = 0
                remaining_samples = len(channel.sample.data)
            else:
                channel.state = ChannelState.STOPPED
                return np.zeros(chunk_size, dtype=np.float32)

        # Get the audio chunk
        end_pos = min(channel.position + samples_needed, len(channel.sample.data))
        audio_chunk = channel.sample.data[channel.position:end_pos]

        # Handle looping if we need more samples
        if len(audio_chunk) < samples_needed and channel.loop:
            remaining_needed = samples_needed - len(audio_chunk)
            loop_chunk = channel.sample.data[:remaining_needed]
            audio_chunk = np.concatenate([audio_chunk, loop_chunk])
            channel.position = remaining_needed
        else:
            channel.position = end_pos

        # Resample to target sample rate if needed
        if effective_rate != self.sample_rate:
            audio_chunk = self._resample_audio(audio_chunk, int(effective_rate), self.sample_rate)

        # Ensure we have the right chunk size
        if len(audio_chunk) > chunk_size:
            audio_chunk = audio_chunk[:chunk_size]
        elif len(audio_chunk) < chunk_size:
            padded = np.zeros(chunk_size, dtype=np.float32)
            padded[:len(audio_chunk)] = audio_chunk
            audio_chunk = padded

        # Apply volume
        audio_chunk *= channel.volume

        return audio_chunk

    def _mix_channels(self) -> np.ndarray:
        """Mix all active channels together"""
        mixed = np.zeros(self.chunk_size, dtype=np.float32)

        with self.lock:
            # Check if any channel is soloed
            has_solo = any(ch.solo for ch in self.channels.values())

            for channel in self.channels.values():
                # Skip non-soloed channels if solo is active
                if has_solo and not channel.solo:
                    continue

                channel_audio = self._process_channel(channel, self.chunk_size)
                mixed += channel_audio

        # Apply master volume
        if not self.master_mute:
            mixed *= self.master_volume

        # Simple limiting to prevent clipping
        mixed = np.clip(mixed, -1.0, 1.0)

        return mixed

    def _audio_callback(self, in_data, frame_count, time_info, status):
        """PyAudio callback function"""
        audio_data = self._mix_channels()

        # Record if needed
        if self.recording:
            self.recorded_data.append(audio_data.copy())

        # Convert to bytes
        audio_bytes = (audio_data * 32767).astype(np.int16).tobytes()

        return (audio_bytes, pyaudio.paContinue)

    def start_playback(self):
        """Start real-time audio playback"""
        if self.is_running:
            return

        self.stream = self.pa.open(
            format=pyaudio.paInt16,
            channels=self.audio_channels,
            rate=self.sample_rate,
            output=True,
            frames_per_buffer=self.chunk_size,
            stream_callback=self._audio_callback
        )

        self.stream.start_stream()
        self.is_running = True

    def stop_playback(self):
        """Stop real-time audio playback"""
        if not self.is_running:
            return

        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

        self.is_running = False

    def get_channel_info(self, channel_id: int) -> Optional[dict]:
        """Get information about a channel"""
        channel = self.get_channel(channel_id)
        if channel:
            with self.lock:
                return channel.get_info()
        return None

    def get_all_channel_info(self) -> Dict[int, dict]:
        """Get information about all channels"""
        info = {}
        with self.lock:
            for channel_id, channel in self.channels.items():
                info[channel_id] = channel.get_info()
        return info

    def start_recording(self):
        """Start recording output"""
        self.recording = True
        self.recorded_data = []

    def stop_recording(self) -> np.ndarray:
        """Stop recording and return recorded data"""
        self.recording = False
        if self.recorded_data:
            return np.concatenate(self.recorded_data)
        return np.array([])

    def save_recording(self, filename: str):
        """Save recorded data to WAV file"""
        if not self.recorded_data:
            return False

        try:
            audio_data = np.concatenate(self.recorded_data)

            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(self.sample_rate)

                # Convert to int16
                audio_int16 = (audio_data * 32767).astype(np.int16)
                wf.writeframes(audio_int16.tobytes())

            return True
        except Exception as e:
            print(f"Error saving recording: {e}")
            return False

    def cleanup(self):
        """Clean up resources"""
        self.stop_playback()
        if self.pa:
            self.pa.terminate()