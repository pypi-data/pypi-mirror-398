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

import colorsys
from .media import PIL2CV2, CV22PIL
import cv2
import numpy

def HighPass(pil_array, radius=10):
    cv2_array = PIL2CV2(pil_array)
    hpf = cv2_array - cv2.GaussianBlur(cv2_array, ((radius * 10) +1, (radius * 10) +1), 1)+(9*20)
    return CV22PIL(hpf)

def LowPass(pil_array, hamming=700, radius=50):
    cv2_array = PIL2CV2(pil_array)[:,:,0]
    ham = numpy.hamming(hamming)
    ham2d = numpy.sqrt(numpy.dot(ham, ham.T)) ** radius
    f = cv2.dft(cv2_array.astype(numpy.float32), flags=cv2.DFT_COMPLEX_OUTPUT)
    f_shifted = numpy.fft.fftshift(f)
    f_complex = f_shifted[:, :, 0] * 1j + f_shifted[:, :, 1]
    f_filtered = ham2d * f_complex
    f_filtered_shifted = numpy.fft.fftshift(f_filtered)
    inv_img = numpy.fft.ifft2(f_filtered_shifted)  # inverse F.T.
    filtered_img = numpy.abs(inv_img)
    filtered_img -= filtered_img.min()
    filtered_img = filtered_img * 255 / filtered_img.max()
    filtered_img = filtered_img.astype(numpy.uint8)
    return CV22PIL(filtered_img)

def Levels(pil_array, minv=0, maxv=255, gamma=1.0):
    """
        Level the brightness of image (a PIL.Image instance)
        All values ≤ minv will become 0
        All values ≥ maxv will become 255
        gamma controls the curve for all values between minv and maxv
    """
    class Level(object):
        def __init__(self, minv, maxv, gamma):
            self.minv= minv/255.0
            self.maxv= maxv/255.0
            self._interval= self.maxv - self.minv
            self._invgamma= 1.0/gamma

        def new_level(self, value):
            if value <= self.minv: return 0.0
            if value >= self.maxv: return 1.0
            return ((value - self.minv)/self._interval)**self._invgamma

        def convert_and_level(self, band_values):
            h, s, v= colorsys.rgb_to_hsv(*(i/255.0 for i in band_values))
            new_v= self.new_level(v)
            return tuple(int(255*i)
                         for i
                         in colorsys.hsv_to_rgb(h, s, new_v))

    if pil_array.mode != "RGB":
        raise ValueError("this works with RGB images only")

    new_pil_array = pil_array.copy()

    leveller = Level(minv, maxv, gamma)
    levelled_data = [
        leveller.convert_and_level(data)
        for data in pil_array.getdata()
    ]
    new_pil_array.putdata(levelled_data)
    return new_pil_array

def BlackAndWhite(pil_array, weights):
    """
        To use can read more on https://stackoverflow.com/a/55233732/15608162
    """
    r_w, y_w, g_w, c_w, b_w, m_w = [w/100 for w in weights]
    pil_array = pil_array.convert('RGB')
    pix = pil_array.load()
    for y in range(pil_array.size[1]):
        for x in range(pil_array.size[0]):
            r, g, b = pix[x, y]
            gray = min([r, g, b])
            r -= gray
            g -= gray
            b -= gray
            if r == 0:
                cyan = min(g, b)
                g -= cyan
                b -= cyan
                gray += cyan * c_w + g * g_w + b * b_w
            elif g == 0:
                magenta = min(r, b)
                r -= magenta
                b -= magenta
                gray += magenta * m_w + r * r_w + b * b_w
            else:
                yellow = min(r, g)
                r -= yellow
                g -= yellow
                gray += yellow * y_w + r * r_w + g * g_w
            gray = max(0, min(255, int(round(gray))))
            pix[x, y] = (gray, gray, gray)
    return pil_array