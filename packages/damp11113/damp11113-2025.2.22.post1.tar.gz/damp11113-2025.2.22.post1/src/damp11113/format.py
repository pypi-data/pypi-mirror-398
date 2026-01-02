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
import queue
import struct
import time
import warnings
import zlib
import bitarray
import random
import xml.etree.ElementTree as ET
from datetime import datetime
import cv2
import matplotlib
import numpy as np
from sklearn.cluster import KMeans

# multiplex4 (m4) format
def m4write(filename, sample_rate, data_format, data_streams):
    with open(filename, 'wb') as file:
        # Write header information
        header = struct.pack('!If', sample_rate, data_format)
        file.write(header)

        # Write data streams
        for stream_data in data_streams:
            metadata = struct.pack('!I', stream_data['id'])  # Example: Stream ID
            file.write(metadata)

            # Write IQ data for each stream
            for iq_sample in stream_data['iq_data']:
                iq_byte = struct.pack('!B', iq_sample)  # Pack the 4-bit IQ sample into a byte
                file.write(iq_byte)

def m4read(file_path):
    with open(file_path, 'rb') as file:
        # Read header information
        header = file.read(8)  # Assuming header is 8 bytes long (4 bytes for sample rate, 4 bytes for format)
        sample_rate, data_format = struct.unpack('!If', header)

        data_streams = []

        # Read data streams
        while True:
            metadata = file.read(4)  # Assuming metadata is 4 bytes long (e.g., stream ID)
            if not metadata:
                break  # Reached the end of the file

            stream_id = struct.unpack('!I', metadata)[0]  # Extract the stream ID

            iq_data = []
            while True:
                iq_byte = file.read(1)  # Assuming each IQ sample is represented by 1 byte (8 bits)
                if not iq_byte:
                    break  # Reached the end of the current data stream

                iq_sample = struct.unpack('!B', iq_byte)[0]  # Unpack the byte as a single 4-bit IQ sample
                iq_data.append(iq_sample)

            data_streams.append({'id': stream_id, 'iq_data': iq_data})

    for stream_data in data_streams:
        iq = '|'.join([str(num) for num in stream_data['iq_data']])
    iqlist = iq.split("|0|0|0")
    iqdi = []
    for id, iqidremove in enumerate(iqlist):
        if id == 0:
            iqdi.append(iqidremove)
        else:
            iqdi.append(iqidremove[3:])
    iqdi2 = []
    for iqreplace in iqdi:
        iqdi2.append(iqreplace.replace('|', ','))
    iqpr = [list(map(int, item.split(','))) for item in iqdi2]
    data_streams = []
    for id, iq in enumerate(iqpr):
        data_streams.append({
            'id': id,
            'iq_data': iq
        })

    return sample_rate, data_format, data_streams

#--------------------------------------------------------------------------------------------------------------

class BrainfuckInterpreter:
    def __init__(self):
        self.memory = [0] * 30000
        self.pointer = 0
        self.output = ""

    def interpret(self, code):
        loop_stack = []
        code_pointer = 0

        while code_pointer < len(code):
            command = code[code_pointer]

            if command == '>':
                self.pointer += 1
            elif command == '<':
                self.pointer -= 1
            elif command == '+':
                self.memory[self.pointer] = (self.memory[self.pointer] + 1) % 256
            elif command == '-':
                self.memory[self.pointer] = (self.memory[self.pointer] - 1) % 256
            elif command == '.':
                self.output += chr(self.memory[self.pointer])
            elif command == ',':
                # Input operation is not implemented in this basic interpreter
                pass
            elif command == '[':
                if self.memory[self.pointer] == 0:
                    loop_depth = 1
                    while loop_depth > 0:
                        code_pointer += 1
                        if code[code_pointer] == '[':
                            loop_depth += 1
                        elif code[code_pointer] == ']':
                            loop_depth -= 1
                else:
                    loop_stack.append(code_pointer)
            elif command == ']':
                if self.memory[self.pointer] != 0:
                    code_pointer = loop_stack[-1] - 1
                else:
                    loop_stack.pop()
            code_pointer += 1

        return self.output

#------------------------------------------------------------------------------------------------------

class RangeEncoder(object):
    def __init__(self, encoding, bits=32):
        """If encoding=True, initialize and support encoding operations. Otherwise,
        support decoding operations. More state bits will give better encoding
        accuracy at the cost of speed."""
        assert encoding in (True, False)
        assert bits > 0
        self.encoding = encoding
        self.finished = False
        # Range state.
        self.bits = bits
        self.norm = 1 << bits
        self.half = self.norm >> 1
        self.low = 0
        self.range = self.norm if encoding else 1
        # Bit queue for data we're ready to input or output.
        qmask = (bits * 4 - 1) | 8
        while qmask & (qmask + 1):
            qmask |= qmask >> 1
        self.qmask = qmask
        self.qcount = [0] * (qmask + 1)
        self.qlen = 0
        self.qpos = 0

    def encode(self, intlow, inthigh, intden):
        """Encode an interval into the range."""
        assert self.encoding and not self.finished
        assert 0 <= intlow < inthigh <= intden <= self.half + 1
        assert self.qlen <= (self.qmask >> 1)
        qmask = self.qmask
        qcount = self.qcount
        qpos = self.qpos
        qlen = self.qlen
        # Shift the range.
        half = self.half
        low = self.low
        range_val = self.range
        while range_val <= half:
            # Push a settled state bit the to queue.
            dif = qpos ^ ((low & half) != 0)
            qpos = (qpos + (dif & 1)) & qmask
            qlen += qcount[qpos] == 0
            qcount[qpos] += 1
            low += low
            range_val += range_val
        norm = self.norm
        low &= norm - 1
        # Scale the range to fit in the interval.
        off = (range_val * intlow) // intden
        low += off
        range_val = (range_val * inthigh) // intden - off
        # If we need to carry.
        if low >= norm:
            # Propagate a carry up our queue. If the previous bits were 0's, flip one to 1.
            # Otherwise, flip all 1's to 0's.
            low -= norm
            # If we're on an odd parity, align us with an even parity.
            odd = qpos & 1
            ones = qcount[qpos] & -odd
            qcount[qpos] -= ones
            qpos -= odd
            # Even parity carry operation.
            qcount[qpos] -= 1
            inc = 1 if qcount[qpos] else -1
            qpos = (qpos + inc) & qmask
            qcount[qpos] += 1
            # Length correction.
            qlen += inc
            qlen += qlen <= odd
            # If we were on an odd parity, add in the 1's-turned-0's.
            qpos = (qpos + odd) & qmask
            qcount[qpos] += ones
        self.low = low
        self.range = range_val
        self.qpos = qpos
        self.qlen = qlen

    def finish(self):
        """Flush the remaining data from the range."""
        if self.finished:
            return
        self.finished = True
        if not self.encoding:
            # We have no more data to decode. Pad the queue with 1's from now on.
            return
        assert self.qlen <= (self.qmask >> 1)
        # We have no more data to encode. Flush out the minimum number of bits necessary
        # to satisfy low <= flush+1's < low+range. Then pad with 1's till we're byte aligned.
        qmask = self.qmask
        qcount = self.qcount
        qpos = self.qpos
        qlen = self.qlen
        low = self.low
        norm = self.norm
        dif = low ^ (low + self.range)
        while dif < norm:
            low += low
            dif += dif
            flip = qpos ^ ((low & norm) != 0)
            qpos = (qpos + (flip & 1)) & qmask
            qlen += qcount[qpos] == 0
            qcount[qpos] += 1
        # Calculate how many bits need to be appended to be byte aligned.
        pad = sum(qcount[(qpos - i) & qmask] for i in range(qlen)) % 8
        # If we're not byte aligned.
        if pad != 0:
            # Align us with an odd parity and add the pad. Add 1 to qlen if qpos & 1 = 0.
            qlen -= qpos
            qpos |= 1
            qlen += qpos
            qcount[qpos] += 8 - pad
        self.qpos = qpos
        self.qlen = qlen

    def hasbyte(self):
        """Is a byte ready to be output?"""
        return self.qlen >= 10 or (self.finished and self.qlen)

    def getbyte(self):
        """If data is ready to be output, returns a bytes object. Otherwise, returns None."""
        assert self.encoding
        qlen = self.qlen
        if qlen < 8 and (not self.finished or qlen == 0):
            return None
        # Go back from the end of the queue and shift bits into ret.
        # If we use all bits at a position, advance the position.
        qmask = self.qmask
        orig = self.qpos + 1
        qpos = orig - qlen
        qcount = self.qcount
        ret = 0
        for i in range(8):
            ret = (ret << 1) | (qpos & 1)
            pos = qpos & qmask
            qcount[pos] -= 1
            qpos += qcount[pos] == 0
        self.qlen = orig - qpos
        return bytes([ret])

    def decode(self, intden):
        """Given an interval denominator, find a value in [0,intden) that will fall
        into some interval. Returns None if more data is needed."""
        assert not self.encoding
        assert intden <= self.half + 1
        qmask = self.qmask
        qpos = self.qpos
        qlen = (self.qlen - qpos) & qmask
        qcount = self.qcount
        if qlen < self.bits:
            # If the input has not signaled it is finished, request more bits.
            if not self.finished:
                return None
            # If we are reading from a finished stream, pad the entire queue with 1's.
            qlen = self.qlen
            while True:
                qcount[qlen] = 1
                qlen = (qlen + 1) & qmask
                if qlen == qpos:
                    break
            self.qlen = (qpos - 1) & qmask
        # Shift the range.
        half = self.half
        low = self.low
        range_val = self.range
        while range_val <= half:
            low += low + qcount[qpos]
            qpos = (qpos + 1) & qmask
            range_val += range_val
        self.qpos = qpos
        self.low = low
        self.range = range_val
        # Scale low to yield our desired code value.
        return (low * intden + intden - 1) // range_val

    def scale(self, intlow, inthigh, intden):
        """Given an interval, scale the range to fit in the interval."""
        assert not self.encoding
        assert 0 <= intlow < inthigh <= intden <= self.half + 1
        range_val = self.range
        off = (range_val * intlow) // intden
        assert self.low >= off
        self.low -= off
        self.range = (range_val * inthigh) // intden - off

    def addbyte(self, byte):
        """Add an input byte to the decoding queue."""
        assert self.encoding and not self.finished
        qmask = self.qmask
        qlen = self.qlen
        qcount = self.qcount
        for i in range(7, -1, -1):
            qcount[qlen] = (byte >> i) & 1
            qlen = (qlen + 1) & qmask
        self.qlen = qlen

"""
import os
import sys
import struct

# Example compressor and decompressor using an adaptive order-0 symbol model.

# Parse arguments.
if len(sys.argv) != 4:
    print("3 arguments expected\npython RangeEncoder.py [-c|-d] infile outfile")
    exit()
mode, infile, outfile = sys.argv[1:]
if mode != "-c" and mode != "-d":
    print("mode must be -c or -d")
    exit()

res = 8
bit = 2 * res
size = 8 * res

# Adaptive order-0 symbol model.
prob = list(range(0, (size + 1) * bit, bit))


def incprob(sym):
    # Increment the probability of a given symbol.
    for i in range(sym + 1, size + 1):
        prob[i] += bit
    if prob[size] >= 65536:
        # Periodically halve all probabilities to help the model forget old symbols.
        for i in range(size, 0, -1):
            prob[i] -= prob[i - 1] - 1
        for i in range(1, size + 1):
            prob[i] = prob[i - 1] + (prob[i] >> 1)


def findsym(code):
    # Find the symbol who's cumulative interval encapsulates the given code.
    for sym in range(1, size + 1):
        if prob[sym] > code:
            return sym - 1


instream = open(infile, "rb")
outstream = open(outfile, "wb")
insize = os.path.getsize(infile)
buf = bytearray(1)

if mode == "-c":
    # Compress a file.
    enc = RangeEncoder(True)
    outstream.write(struct.pack(">i", insize))
    for inpos in range(insize + 1):
        if inpos < insize:
            # Encode a symbol.
            byte = ord(instream.read(1))
            enc.encode(prob[byte], prob[byte + 1], prob[size])
            incprob(byte)
        else:
            enc.finish()
        # While the encoder has bytes to output, output.
        while enc.hasbyte():
            buf[0] = enc.getbyte()
            outstream.write(buf)
else:
    # Decompress a file.
    dec = RangeEncoder(False)
    outsize = struct.unpack(">i", instream.read(4))[0]
    inpos, outpos = 4, 0
    while outpos < outsize:
        decode = dec.decode(prob[size])
        if decode is not None:
            # We are ready to decode a symbol.
            buf[0] = sym = findsym(decode)
            dec.scale(prob[sym], prob[sym + 1], prob[size])
            incprob(sym)
            outstream.write(buf)
            outpos += 1
        elif inpos < insize:
            # We need more input data.
            dec.addbyte(ord(instream.read(1)))
            inpos += 1
        else:
            # Signal that we have no more input data.
            dec.finish()

outstream.close()
instream.close()
"""

#------------------------------------------------------------------------------------------------------

class Packet:
    __slots__ = ['stream_id', 'sequence_number', 'compressed_payload', 'metadata', 'hamming_code']

    def __init__(self, stream_id, sequence_number, compressed_payload, metadata=None):
        self.stream_id = stream_id
        self.sequence_number = sequence_number
        self.compressed_payload = compressed_payload
        self.metadata = metadata if metadata is not None else {}
        self.hamming_code = self.generate_hamming_code()

    def generate_hamming_code(self):
        # Convert payload to bitarray
        payload_bits = bitarray.bitarray()
        payload_bits.frombytes(self.compressed_payload)

        # Calculate the number of parity bits needed
        parity_bits_count = 1
        while (2 ** parity_bits_count) < (len(payload_bits) + parity_bits_count + 1):
            parity_bits_count += 1

        # Initialize Hamming code with all zeros
        hamming_code = bitarray.bitarray(parity_bits_count + len(payload_bits))
        hamming_code.setall(0)

        # Copy payload bits to Hamming code, skipping parity bit positions
        i, j = 0, 0
        while i < len(hamming_code):
            if (i + 1) & i != 0:  # Check if i+1 is a power of 2
                i += 1  # Skip parity bits
                continue
            hamming_code[i] = payload_bits[j]
            i += 1
            j += 1

        # Calculate parity bits
        for i in range(parity_bits_count):
            mask = 1 << i  # bit mask to check corresponding bits
            count = 0
            for j in range(len(hamming_code)):
                if j & mask:  # if jth bit has 1 in its ith significant bit
                    count += hamming_code[j]
            hamming_code[mask - 1] = count % 2  # Set parity bit value

        return hamming_code.tobytes()

class DataMuxer:
    def __init__(self):
        self.streams = {}

    def add_stream(self, stream_id, data, metadata=None):
        compressed_data = self.compress_data(data)
        packets = self.packetize(stream_id, compressed_data, metadata)
        if stream_id not in self.streams:
            self.streams[stream_id] = []
        self.streams[stream_id].extend(packets)

    @staticmethod
    def compress_data(data):
        return zlib.compress(data)

    @staticmethod
    def packetize(stream_id, data, metadata=None, packet_size=100):
        packets = []
        num_packets = (len(data) + packet_size - 1) // packet_size
        for i in range(num_packets):
            start = i * packet_size
            end = min((i + 1) * packet_size, len(data))
            payload = data[start:end]
            packet = Packet(stream_id, i, payload, metadata)
            packets.append(packet)
        return packets

    def multiplex(self, loss_probability=0):
        multiplexed_data = []
        for stream_id, packets in self.streams.items():
            for packet in packets:
                if random.random() > loss_probability:
                    header = (packet.stream_id, len(packet.compressed_payload), packet.metadata)
                    multiplexed_data.append((header, packet.compressed_payload))
        return multiplexed_data

class DataDemuxer:
    def __init__(self):
        self.streams = {}

    def demultiplex(self, multiplexed_data, loss_probability=0):
        for header, compressed_payload in multiplexed_data:
            if random.random() > loss_probability:
                stream_id, compressed_payload_length, metadata = header
                corrected_payload = self.correct_hamming_code(compressed_payload)
                payload = self.decompress_data(corrected_payload)
                packet = Packet(stream_id, None, payload[:compressed_payload_length], metadata)
                self.add_packet(packet)

    @staticmethod
    def decompress_data(compressed_data):
        return zlib.decompress(compressed_data)

    def add_packet(self, packet):
        stream_id = packet.stream_id
        packets = self.streams.get(stream_id)
        if packets is None:
            packets = self.streams[stream_id] = {}
        packets[packet.sequence_number] = packet

    def correct_hamming_code(self, hamming_code):
        # Convert Hamming code to bitarray
        hamming_bits = bitarray.bitarray()
        hamming_bits.frombytes(hamming_code)

        # Detect and correct errors in Hamming code
        error_pos = 0
        for i in range(len(hamming_bits)):
            if (i + 1) & i != 0:  # Check if i+1 is a power of 2 (parity bit)
                parity = 0
                for j in range(len(hamming_bits)):
                    if j & (i + 1):  # If jth bit has 1 in its ith significant bit
                        parity ^= hamming_bits[j]
                if parity != hamming_bits[i]:  # If parity doesn't match, error detected
                    error_pos += i + 1

        if error_pos != 0 and error_pos <= len(hamming_bits):  # If error detected and within range
            hamming_bits.invert(error_pos - 1)  # Correct the error by flipping the bit

        return hamming_bits.tobytes()

    def get_stream_data(self, stream_id):
        packets = self.streams.get(stream_id)
        if packets:
            payload_bits = bitarray.bitarray()
            for packet in sorted(packets.values(), key=lambda pkt: pkt.sequence_number):
                payload_bits.frombytes(packet.compressed_payload)
            return payload_bits.tobytes()
        return b''

    def get_stream_metadata(self, stream_id):
        packets = self.streams.get(stream_id)
        if packets:
            return packets[sorted(packets.keys())[0]].metadata
        return {}

#------------------------------------------------------------------------------------------------------

class RSSFeed:
    def __init__(self, title, link, description, ttl=None, image_url=None, image_title=None, image_link=None, copyright=None):
        self.title = title
        self.link = link
        self.description = description
        self.ttl = ttl
        self.image_url = image_url
        self.image_title = image_title
        self.image_link = image_link
        self.items = []
        self.copyright = copyright
        self.last_build_date = datetime.now()

    def add_item(self, title, link, description, category, guid=None, pubDate=None):
        if pubDate is None:
            pubDate = datetime.now()
        if not guid:
            # Generate a unique identifier if not provided
            guid = str(pubDate.timestamp())
        self.items.append({
            'title': title,
            'link': link,
            'description': description,
            'category': category,
            'guid': guid,
            'pubDate': pubDate
        })

    def generate_feed_xml(self):
        rss = ET.Element("rss", version="2.0")
        channel = ET.SubElement(rss, "channel")

        title = ET.SubElement(channel, "title")
        title.text = self.title

        link = ET.SubElement(channel, "link")
        link.text = self.link

        description = ET.SubElement(channel, "description")
        description.text = self.description

        if self.ttl:
            ttl = ET.SubElement(channel, "ttl")
            ttl.text = str(self.ttl)

        if self.image_url:
            image = ET.SubElement(channel, "image")
            image_url = ET.SubElement(image, "url")
            image_url.text = self.image_url
            if self.image_title:
                image_title = ET.SubElement(image, "title")
                image_title.text = self.image_title
            if self.image_link:
                image_link = ET.SubElement(image, "link")
                image_link.text = self.image_link

        if self.last_build_date:
            last_build_date = ET.SubElement(channel, "lastBuildDate")
            last_build_date.text = self.last_build_date.strftime("%a, %d %b %Y %H:%M:%S %z")

        if self.copyright:
            copy_right = ET.SubElement(channel, "copyright")
            copy_right.text = self.copyright

        for item_data in self.items:
            item = ET.SubElement(channel, "item")

            item_title = ET.SubElement(item, "title")
            item_title.text = item_data['title']

            item_link = ET.SubElement(item, "link")
            item_link.text = item_data['link']

            item_description = ET.SubElement(item, "description")
            item_description.text = item_data['description']

            item_category = ET.SubElement(item, "category")
            item_category.text = item_data['category']

            guid = ET.SubElement(item, "guid")
            guid.text = item_data['guid']
            guid.set("isPermaLink", "false")  # Indicate that the GUID is not a permanent link

            pubDate = ET.SubElement(item, "pubDate")
            pubDate.text = item_data['pubDate'].strftime("%a, %d %b %Y %H:%M:%S %z")

        return ET.tostring(rss, encoding='utf-8').decode('utf-8')

class EPGen:
    def __init__(self, source_info_name="", source_info_url="", generator_info_name="EPGen", generator_info_url="https://damp11113.xyz"):
        """
        https://raw.githubusercontent.com/AlekSi/xmltv/master/xmltv.dtd
        """
        self.root = ET.Element('tv')
        if generator_info_name:
            self.root.set("generator-info-name", generator_info_name)
        if generator_info_url:
            self.root.set("generator-info-url", generator_info_url)
        if source_info_name:
            self.root.set("source-info-name", source_info_name)
        if source_info_url:
            self.root.set("source-info-url", source_info_url)
        self.channels = {}
        self.programs = []

    def add_channel(self, id, name, icon=None):
        channel = ET.SubElement(self.root, 'channel', id=id)
        display_name = ET.SubElement(channel, 'display-name')
        display_name.text = name
        if icon:
            icon_elem = ET.SubElement(channel, 'icon', src=icon)
        self.channels[id] = channel

    def add_program(self, channel_id, title, start_time, end_time, description=None, language=None, episode_num=None, episode_title=None, category=None, country=None, credits=None, video=None, audio=None, previously_shown=None, premiere=None, last_chance=None, new=None, subtitles=None, rating=None, star_rating=None, date=None, sub_title=None, **kwargs):
        """
        @param kwargs: For custom tag only (receiver must be read this)
        """
        program = ET.SubElement(self.root, 'programme', start=start_time.strftime('%Y%m%d%H%M%S %z'),
                                stop=end_time.strftime('%Y%m%d%H%M%S %z'), channel=channel_id)
        title_elem = ET.SubElement(program, 'title')
        title_elem.text = title
        if description:
            desc_elem = ET.SubElement(program, 'desc')
            desc_elem.text = description
        if language:
            lang_elem = ET.SubElement(program, 'language')
            lang_elem.text = language
        if episode_num:
            episode_num_elem = ET.SubElement(program, 'episode-num', system='xmltv_ns')
            episode_num_elem.text = episode_num
        if episode_title:
            episode_title_elem = ET.SubElement(program, 'episode-title')
            episode_title_elem.text = episode_title
        if category:
            category_elem = ET.SubElement(program, 'category')
            category_elem.text = category
        if country:
            country_elem = ET.SubElement(program, 'country')
            country_elem.text = country
        if credits:
            credits_elem = ET.SubElement(program, 'credits')
            for credit in credits:
                credit_elem = ET.SubElement(credits_elem, credit['role'])
                credit_elem.text = credit['name']
        if video:
            video_elem = ET.SubElement(program, 'video')
            present_elem = ET.SubElement(video_elem, 'present')
            present_elem.text = 'yes'  # Assuming every program has video
            for key, value in video.items():
                if value is not None:
                    sub_elem = ET.SubElement(video_elem, key)
                    sub_elem.text = value
        if audio:
            audio_elem = ET.SubElement(program, 'audio')
            present_elem = ET.SubElement(audio_elem, 'present')
            present_elem.text = 'yes'  # Assuming every program has audio
            for key, value in audio.items():
                if value is not None:
                    sub_elem = ET.SubElement(audio_elem, key)
                    sub_elem.text = value
        if previously_shown:
            previously_shown_elem = ET.SubElement(program, 'previously-shown')
            previously_shown_elem.text = previously_shown
        if premiere:
            premiere_elem = ET.SubElement(program, 'premiere')
            premiere_elem.text = premiere
        if last_chance:
            last_chance_elem = ET.SubElement(program, 'last-chance')
            last_chance_elem.text = last_chance
        if new:
            new_elem = ET.SubElement(program, 'new')
            new_elem.text = new
        if subtitles:
            subtitles_elem = ET.SubElement(program, 'subtitles')
            subtitles_elem.text = subtitles
        if rating:
            rating_elem = ET.SubElement(program, 'rating', system=rating['system'])
            value_elem = ET.SubElement(rating_elem, 'value')
            value_elem.text = rating['value']
            if 'advisory' in rating:
                advisory_elem = ET.SubElement(rating_elem, 'advisory')
                advisory_elem.text = rating['advisory']
        if star_rating:
            star_rating_elem = ET.SubElement(program, 'star-rating')
            star_rating_elem.text = star_rating
        if date:
            date_elem = ET.SubElement(program, 'date')
            date_elem.text = date
        if sub_title:
            sub_title_elem = ET.SubElement(program, 'sub-title')
            sub_title_elem.text = sub_title
        # Additional custom tags
        for key, value in kwargs.items():
            if value is not None:
                custom_elem = ET.SubElement(program, key)
                custom_elem.text = value

        self.programs.append(program)

    def generate_xml(self, filename=None):
        xml_content = ET.tostring(self.root, encoding='utf-8', method='xml')
        if filename:
            with open(filename, 'wb') as f:
                f.write(xml_content)
        else:
            return xml_content

#------------------------------------------------------------------------------------------------------

class FileHeader:
    def __init__(self, capture_pattern, version, metadata):
        self.capture_pattern = capture_pattern
        self.version = version
        self.metadata = metadata

    def serialize(self):
        header = struct.pack('<4sB', self.capture_pattern, self.version)
        metadata_bytes = self.serialize_metadata()
        return header + metadata_bytes

    def serialize_metadata(self):
        metadata_bytes = b''
        for key, value in self.metadata.items():
            key_bytes = key.encode('utf-8')
            value_bytes = value.encode('utf-8') if isinstance(value, str) else str(value).encode('utf-8')
            metadata_bytes += struct.pack(f'<I{len(key_bytes)}sI{len(value_bytes)}s', len(key_bytes), key_bytes, len(value_bytes), value_bytes)
        return metadata_bytes

    @classmethod
    def deserialize(cls, data):
        capture_pattern, version = struct.unpack_from('<4sB', data)
        metadata_start = struct.calcsize('<4sB')
        metadata = cls.deserialize_metadata(data[metadata_start:])
        return cls(capture_pattern, version, metadata)

    @staticmethod
    def deserialize_metadata(metadata_bytes):
        metadata = {}
        while metadata_bytes:
            key_length = struct.unpack('<I', metadata_bytes[:4])[0]
            key = struct.unpack(f'<{key_length}s', metadata_bytes[4:4+key_length])[0].decode('utf-8')
            metadata_bytes = metadata_bytes[4+key_length:]
            value_length = struct.unpack('<I', metadata_bytes[:4])[0]
            value = struct.unpack(f'<{value_length}s', metadata_bytes[4:4+value_length])[0].decode('utf-8')
            metadata_bytes = metadata_bytes[4+value_length:]
            metadata[key] = value
        return metadata

#------------------------------------------------------------------------------------------------------

def packqueue(queue: queue.Queue, header: bytes = None, limitblocks=0, timeout=None):
    """if limitblocks 0 = get all blocks in queue"""
    result = bytearray()

    # create header
    if header is not None:
        result.extend(b"\\xsh")  # start header
        result.extend(header)
        result.extend(b"\\xeh")  # end header
    else:
        result.extend(b"\\xnh")  # no header

    result.extend(b"\\xsc")  # start content

    count = 0
    while not queue.empty() and (count < limitblocks or limitblocks == 0):
        queueblock = queue.get(timeout=timeout)
        count += 1

        if isinstance(queueblock, bytes): # check if chunk content is bytes
            result.extend(queueblock)
        else:
            warnings.warn("chunk is not bytes. Skipped!")

        result.extend(b"\\xnc")  # next chunk

    result.extend(b"\\xec")  # end content

    return bytes(result)

def unpackqueue(data: bytes, output_queue: queue.Queue):
    header_start = data.find(b"\\xsh")
    header_end = data.find(b"\\xeh", header_start + 4) if header_start != -1 else -1
    content_start = data.find(b"\\xsc", header_end + 4) if header_end != -1 else data.find(b"\\xsc")
    content_end = data.find(b"\\xec", content_start + 4) if content_start != -1 else -1

    if content_start == -1 or content_end == -1:
        raise ValueError("Invalid packed data format")

    if header_start != -1 and header_end != -1:
        header = data[header_start + 4:header_end]
    else:
        header = None

    content = data[content_start + 4:content_end]

    chunks = content.split(b"\\xnc")[:-1]  # Remove the last empty chunk after split

    for chunk in chunks:
        output_queue.put(chunk)

    return header

#------------------------------------------------------------------------------------------------------

class RCFContentGenerator:
    def __init__(self, id, title, **kwargs):
        # Initialize only with required fields
        self.content = {
            "id": id,
            "title": title,
        }

        # Add optional fields if provided
        optional_fields = ["page_url", "status", "explicit", "rating", "reading_length"]
        for field in optional_fields:
            if field in kwargs:
                self.content[field] = kwargs[field]

    def set_public_date(self, date):
        self.content["public_date"] = date

    def set_modify_date(self, date):
        self.content["modify_date"] = date

    def add_tag(self, tag):
        self.content.setdefault("tags", []).append(tag)

    def set_description(self, description):
        self.content["description"] = description

    def set_summary(self, content, format="text"):
        self.content["summary"] = {
            "format": format,
            "content": content
        }

    def set_image_url(self, image_type, url):
        if image_type in ["banner", "footer"]:
            self.content.setdefault("image", {})[image_type] = url
        else:
            raise TypeError("Image type not supported")

    def add_author(self, name, **kwargs):
        author = {"name": name}
        if kwargs:
            author.update(kwargs)
        self.content.setdefault("authors", []).append(author)

    def set_units(self, **units):
        self.content.setdefault("units", {}).update(units)

    def set_insights(self, score=0, **kwargs):
        self.content.setdefault("insights", {"score": score})
        for key, value in kwargs.items():
            self.content["insights"][key] = value

    def add_custom_data(self, tag, data):
        self.content.setdefault("custom", {})[tag] = data

    def add_reference(self, title, url, date=None):
        refdata = {"title": title, "url": url}
        if date:
            refdata["date"] = date
        self.content.setdefault("reference", []).append(refdata)

    def add_language_sign(self, language):
        self.content.setdefault("language", []).append(language)

    def set_copyright(self, license, date, organ_name):
        self.content["copyright"] = {
            "license": license,
            "date": date,
            "organ_name": organ_name,
        }

    def add_attachments(self, id, url, mine_type, title=None, size=None):
        if "attachments" not in self.content:
            self.content["attachments"] = []

        # Check if the ID already exists
        for existing_feed in self.content["attachments"]:
            if existing_feed.get("id") == id:
                raise ValueError(f"Attachments ID {id} already exists.")

        file = {"id": id, "url": url, "mine_type": mine_type}
        if title:
            file["title"] = title
        if size:
            file["size"] = size

        self.content["attachments"].append(file)


class RCFGenerator:
    def __init__(self, title, home_page_url, feed_url, next_feed_url=None, old_feed_url=None):
        self.data = {
            "version": 1,
            "url": {
                "home_page_url": home_page_url,
                "feed_url": feed_url,
                "next_feed_url": next_feed_url or "",
                "old_feed_url": old_feed_url or ""
            },
            "info": {
                "title": title,
                "authors": [],
                "generator": {
                    "name": "PyRCF",
                    "url": "https://rcf.damp11113.xyz",
                    "last_build": 0
                }
            },
            "feeds": []
        }

    def __setattr__(self, name, value):
        if name == "data":
            super().__setattr__(name, value)
        elif value is not None:
            self.data[name] = value

    def export(self):
        self.data["info"]["generator"]["last_build"] = int(time.time())
        return self.data

    def set_image_url(self, image_type, url):
        if image_type in ["icon", "favicon", "banner", "footer"]:
            if "image" not in self.data:
                self.data["image"] = {}
            self.data["image"][image_type] = url
        else:
            raise TypeError("Image type not supported")

    def set_short_description(self, description):
        if "description" not in self.data["info"]:
            self.data["info"]["description"] = {}
        self.data["info"]["description"]["short"] = description

    def set_long_description(self, content, format="text"):
        if "description" not in self.data["info"]:
            self.data["info"]["description"]["long"] = {}
        self.data["info"]["description"]["long"]["format"] = format
        self.data["info"]["description"]["long"]["content"] = content

    def add_author(self, name, url=None, avatar_url=None, contact=None, social=None):
        author = {"name": name}
        if url: author["url"] = url
        if avatar_url: author["avatar"] = avatar_url
        if contact: author["contact"] = contact
        if social: author["social_media"] = social
        self.data["info"]["authors"].append(author)

    def set_copyright(self, license, date, organ_name):
        if "copyright" not in self.data["info"]:
            self.data["info"]["copyright"] = {}
        self.data["info"]["copyright"]["license"] = license
        self.data["info"]["copyright"]["date"] = date
        self.data["info"]["copyright"]["organ_name"] = organ_name

    def set_subscribe_url(self, type, url):
        if "subscribe" not in self.data["info"]:
            self.data["info"]["subscribe"] = {}
        self.data["info"]["subscribe"]["type"] = type
        self.data["info"]["subscribe"]["url"] = url

    def add_language_sign(self, language):
        if "language" not in self.data["info"]:
            self.data["info"]["language"] = []
        self.data["info"]["language"].append(language)

    def add_categories(self, categories):
        if "categories" not in self.data["info"]:
            self.data["info"]["categories"] = []
        self.data["info"]["categories"].append(categories)

    def add_custom_data(self, tag, data):
        if "custom" not in self.data["info"]:
            self.data["info"]["custom"] = {}
        self.data["info"]["custom"][tag] = data

    def set_custom_html(self, html):
        self.data["info"]["custom_html"] = html

    def set_update_frequency(self, frequency="unknown"):
        self.data["info"]["update_frequency"] = frequency

    def isexpired(self, expired=True):
        self.data["info"]["expired"] = expired

    def istemp(self, temp=True):
        self.data["info"]["temp"] = temp

    def set_current_version(self, version):
        self.data["info"]["versioning"]["current_version"] = version

    def add_previous_versions(self, version, url, release_date):
        if "previous_versions" not in self.data["info"]["versioning"]:
            self.data["info"]["versioning"]["previous_versions"] = []
        self.data["info"]["versioning"]["previous_versions"].append({
            "version": version,
            "url": url,
            "release_date": release_date
        })

    def set_units(self, **units):
        if "units" not in self.data["info"]:
            self.data["info"]["units"] = {}
        self.data["info"]["units"].update(units)

    def add_feed(self, feed: RCFContentGenerator):
        if "feeds" not in self.data:
            self.data["feeds"] = []
        for existing_feed in self.data["feeds"]:
            if existing_feed["id"] == feed.content["id"]:
                raise ValueError(f"Feed ID {feed.content['id']} already exists.")
        self.data["feeds"].append(feed.content)

#------------------------------------------------------------------------------------------------------

def SRTParser(file_path, removeln=True):
    def parse_srt_time(time_str):
        """Convert SRT time format to seconds."""
        hours, minutes, seconds_millis = time_str.split(':')
        seconds, millis = seconds_millis.split(',')
        total_seconds = int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(millis) / 1000
        return total_seconds

    """Parse an SRT file and return a list of subtitle entries."""
    with open(file_path, 'r', encoding='utf-8-sig') as file:
        content = file.read()

    # Split content by double newlines to get subtitle blocks
    blocks = content.strip().split('\n\n')

    subtitles = []

    for i, block in enumerate(blocks):
        lines = block.split('\n')

        # The first line is the index
        index = int(lines[0].strip())

        # The second line is the time range
        time_range = lines[1].strip()
        start_time_str, end_time_str = time_range.split(' --> ')
        start_time = parse_srt_time(start_time_str.strip())
        end_time = parse_srt_time(end_time_str.strip())

        # Calculate duration in seconds
        duration = end_time - start_time

        # The rest is the subtitle text
        if removeln:
            text = ' '.join(line.strip() for line in lines[2:])
        else:
            text = '\n'.join(line.strip() for line in lines[2:])

        # Calculate next text duration in seconds
        if i < len(blocks) - 1:
            next_start_time_str = blocks[i + 1].split('\n')[1].split(' --> ')[0].strip()
            next_start_time = parse_srt_time(next_start_time_str)
            next_text_duration = next_start_time - end_time
        else:
            next_text_duration = None

        subtitles.append({
            'index': index,
            'start_time': start_time,
            'end_time': end_time,
            'duration': duration,
            'text': text,
            'next_text_duration': next_text_duration
        })

    return subtitles

def load_colormap_sdrpp(json_data):
    try:
        # Extract the name and the list of hex colors from the JSON data.
        name = json_data.get("name", "custom_colormap")
        hex_colors = json_data.get("map", [])

        if not hex_colors:
            raise ValueError("The 'map' key in the JSON data is empty or missing.")

        # Convert the list of hex colors to RGB values (0-1 range).
        rgb_colors = [matplotlib.colors.hex2color(hex_val) for hex_val in hex_colors]

        # Create the colormap using the matplotlib.colors.LinearSegmentedColormap.
        # This function interpolates between the provided colors.
        cmap = matplotlib.colors.LinearSegmentedColormap.from_list(name, rgb_colors, N=256)

        return cmap
    except (ValueError, KeyError) as e:
        print(f"Error creating colormap: {e}")
        return None

class SixelEncoder:
    """
    A Sixel encoder for converting OpenCV images to Sixel format
    for display in compatible terminals.
    """

    def __init__(self):
        self.palette = []
        self.width = 0
        self.height = 0

    def quantize_colors(self, img: np.ndarray, n_colors: int = 256):
        """
        Reduce the number of colors in the image using KMeans clustering.

        Args:
            img: Input image (H, W, 3) in RGB format
            n_colors: Maximum number of colors to use

        Returns:
            Quantized image and color palette
        """
        # Reshape image to be a list of pixels
        pixels = img.reshape((-1, 3))

        # Use KMeans to find the most representative colors
        kmeans = KMeans(n_clusters=min(n_colors, len(np.unique(pixels, axis=0))),
                        random_state=42, n_init=10)
        kmeans.fit(pixels)

        # Get the color palette
        palette = kmeans.cluster_centers_.astype(np.uint8)

        # Map each pixel to its nearest color
        labels = kmeans.predict(pixels)
        quantized = palette[labels].reshape(img.shape)

        return quantized, palette

    def build_palette(self, palette: np.ndarray) -> str:
        """
        Build Sixel color palette definition string.

        Args:
            palette: Color palette array

        Returns:
            Sixel palette definition string
        """
        palette_str = ""
        for i, color in enumerate(palette):
            r, g, b = color
            # Convert to 0-100 range for Sixel
            r = int(r * 100 / 255)
            g = int(g * 100 / 255)
            b = int(b * 100 / 255)
            palette_str += f"#{i};2;{r};{g};{b}"
        return palette_str

    def encode_sixel_row(self, row_data: np.ndarray, palette: np.ndarray) -> str:
        """
        Encode a single 6-pixel high row as Sixel data.

        Args:
            row_data: Image data for this row (6, width, 3)
            palette: Color palette

        Returns:
            Sixel encoded string for this row
        """
        output = ""
        width = row_data.shape[1]

        # Create color index map
        color_map = {}
        for y in range(min(6, row_data.shape[0])):
            for x in range(width):
                pixel = tuple(row_data[y, x])
                # Find closest color in palette
                if pixel not in color_map:
                    distances = np.sum((palette - row_data[y, x]) ** 2, axis=1)
                    color_map[pixel] = np.argmin(distances)

        # Group consecutive pixels of the same color
        for color_idx in range(len(palette)):
            output += f"#{color_idx}"

            for x in range(width):
                sixel_char = 0
                for y in range(min(6, row_data.shape[0])):
                    pixel = tuple(row_data[y, x])
                    if color_map[pixel] == color_idx:
                        sixel_char |= (1 << y)

                if sixel_char > 0:
                    output += chr(63 + sixel_char)
                else:
                    output += "?"

            output += "$"  # Carriage return

        output += "-"  # Line feed
        return output

    def encode(self, img: np.ndarray, max_colors: int = 256) -> str:
        """
        Encode an OpenCV image to Sixel format.

        Args:
            img: OpenCV image (BGR format)
            max_colors: Maximum number of colors to use (1-256)
            terminal_width: Maximum width in terminal characters
            terminal_height: Maximum height in terminal lines

        Returns:
            Sixel encoded string
        """
        # Convert BGR to RGB
        if len(img.shape) == 3 and img.shape[2] == 3:
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        else:
            img_rgb = img

        # Quantize colors
        max_colors = max(1, min(256, max_colors))
        img_quantized, palette = self.quantize_colors(img_rgb, max_colors)

        # Start Sixel sequence
        output = "\033Pq"  # Device Control String

        # Add palette definition
        output += self.build_palette(palette)

        # Encode image data row by row (6 pixels per row)
        height = img_quantized.shape[0]
        for y in range(0, height, 6):
            row_end = min(y + 6, height)
            row_data = img_quantized[y:row_end]
            output += self.encode_sixel_row(row_data, palette)

        # End Sixel sequence
        output += "\033\\"

        return output