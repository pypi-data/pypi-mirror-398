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

import socket
import paho.mqtt.client as mqtt
import time
from .file import *
import re
import requests
from .processbar import LoadingProgress, Steps
import threading
from typing import Dict, Callable, Optional, Any, NamedTuple
import struct


class vc_exception(Exception):
    pass

class line_api_exception(Exception):
    pass

class ip_exeption(Exception):
    pass

class receive_exception(Exception):
    pass

class send_exception(Exception):
    pass

def youtube_search(search, firstresult=True):
    formatUrl = requests.get(f'https://www.youtube.com/results?search_query={search}')
    search_result = re.findall(r'watch\?v=(\S{11})', formatUrl.text)

    if firstresult:
        return f"https://www.youtube.com/watch?v={search_result[0]}"
    else:
        return search_result

#-------------------------download---------------------------

def loadfile(url, filename):
    progress = LoadingProgress(desc=f'loading file from {url}', steps=Steps.steps5, unit="B", shortunitsize=1024, shortnum=True)
    progress.start()
    try:
        progress.desc = f'Downloading {filename} from {url}'
        progress.status = "Connecting..."
        r = requests.get(url, stream=True)
        progress.desc = f'Downloading {filename} from {url}'
        progress.status = "Starting..."
        tsib = int(r.headers.get('content-length', 0))
        bs = 1024
        progress.total = tsib
        progress.desc = f'Downloading {filename} from {url}'
        progress.status = "Downloading..."
        with open(filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=bs):
                progress.update(len(chunk))
                f.write(chunk)
        progress.status = "Downloaded"
        progress.end = f"[ ✔ ] Downloaded {filename} from {url}"
        progress.stop()
    except Exception as e:
        progress.status = "Error"
        progress.faill = f"[ ❌ ] Failed to download {filename} from {url} | " + str(e)
        progress.stopfail()

#-----------------------------send-----------------------------

def mqtt_publish(topic, message, port=1883, host="localhost"):
    try:
        client = mqtt.Client()
        client.connect(host, port, 60)
        client.publish(topic, message)
        client.disconnect()
    except Exception as e:
        raise send_exception(f'send error: {e}')

def tcp_send(host, port, message):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        s.sendall(bytes(message, 'utf-8'))
        s.close()
        print(f"tcp send to {host}:{port}")
    except Exception as e:
        raise send_exception(f'send error: {e}')

def udp_send(host, port, message):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((host, port))
        s.sendall(bytes(message, "utf-8"))
        s.close()
        print(f"udp send to {host}:{port}")
    except Exception as e:
        raise send_exception(f'send error: {e}')

def file_send(host, port, file, buffsize=4096, speed=0.0000001):
    try:
        filesize = sizefile(file)
        s = socket.socket()
        s.connect((host, port))
        s.send(f"{file}{filesize}".encode())
        progress_bar = LoadingProgress(desc=f'Sending {file}', unit="B", total=filesize)
        with open(file, 'rb') as f:
            while True:
                data = f.read(buffsize)
                if not data:
                    break
                s.sendall(data)
                progress_bar.update(len(data))
                time.sleep(speed)
        s.close()
        progress_bar.stop()
    except Exception as e:
        raise send_exception(f'send error: {e}')

#-----------------------------receive--------------------------

def mqtt_subscribe(topic, port=1883, host="localhost"):
    try:
        client = mqtt.Client()
        client.connect(host, port)
        mes = client.subscribe(topic)
        client.disconnect()
        return mes
    except Exception as e:
        raise receive_exception(f'receive error: {e}')

def tcp_receive(host, port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((host, port))
        s.listen(1)
        conn, addr = s.accept()
        data = conn.recv(1024)
        conn.close()
        print(f"tcp receive from {host}:{port}")
        return data.decode('utf-8')
    except Exception as e:
        raise receive_exception(f'receive error: {e}')

def udp_receive(host, port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind((host, port))
        data, addr = s.recvfrom(1024)
        s.close()
        print(f"udp receive from {host}:{port}")
        return data.decode('utf-8')
    except Exception as e:
        raise receive_exception(f'receive error: {e}')

def file_receive(host, port, buffsize=4096, speed=0.0000001):
    try:
        s = socket.socket()
        s.bind((host, port))
        s.listen(5)
        conn, addr = s.accept()
        received = conn.recv(buffsize)
        filename = received.decode()
        filesize = int(conn.recv(1024).decode('utf-16'))
        progress_bar = LoadingProgress(desc=f'Receiving {filename}', unit="B", total=filesize, steps=Steps.receiving)
        with open(filename, 'wb') as f:
            while True:
                data = conn.recv(buffsize)
                if not data:
                    break
                f.write(data)
                progress_bar.update(len(data))
                time.sleep(speed)
        progress_bar.stop()
        conn.close()
    except Exception as e:
        raise receive_exception(f'receive error: {e}')

# ----------------------------------------------------------------------------------------------

class OutGaugeCarFlags(NamedTuple):
    """Car display flags configuration."""
    showTurbo: bool
    showKM: bool
    showBAR: bool


class OutGaugeCarLights(NamedTuple):
    """Car light status indicators."""
    shift_light: bool
    full_beam: bool
    handbrake: bool
    pit_limiter: bool
    tc: bool
    left_turn: bool
    right_turn: bool
    both_turns: bool
    oil_warn: bool
    battery_warn: bool
    abs: bool
    spare_light: bool


class OutGaugeData(NamedTuple):
    """Complete car telemetry data structure."""
    time: int                   # Game time
    carName: str                # Car model name
    flags: OutGaugeCarFlags     # Display flags
    gear: int                   # Current gear (-1=reverse, 0=neutral, 1+=forward)
    PLID: int                   # Player/car ID
    speed: float                # Speed (units depend on flags.showKM)
    rpm: float                  # Engine RPM
    turboPressure: float        # Turbo pressure
    engTemp: float              # Engine temperature
    fuel: float                 # Fuel level (0.0-1.0)
    oilPressure: float          # Oil pressure
    oilTemp: float              # Oil temperature
    lights: OutGaugeCarLights   # Light status
    throttle: float             # Throttle position (0.0-1.0)
    brake: float                # Brake position (0.0-1.0)
    clutch: float               # Clutch position (0.0-1.0)
    misc1: str                  # Miscellaneous data 1
    misc2: str                  # Miscellaneous data 2
    timestamp: float            # Local timestamp when data was received

class BeamNGOutGaugeReceiver:
    """
    A class to receive and decode car telemetry data via UDP in real-time.

    Usage:
        receiver = CarTelemetryReceiver()
        receiver.start_listening()

        # Get latest data
        data = receiver.get_latest_data()

        # Or use callback
        def on_data_received(data):
            print(f"Speed: {data['speed']}, RPM: {data['rpm']}")

        receiver = CarTelemetryReceiver(callback=on_data_received)
        receiver.start_listening()
    """

    def __init__(self, host: str = "0.0.0.0", port: int = 5555, callback: Optional[Callable[[OutGaugeData], None]] = None):
        """
        Initialize the telemetry receiver.

        Args:
            host: IP address to bind to (default: "0.0.0.0" for all interfaces)
            port: Port to listen on (default: 5555)
            callback: Optional callback function to call when new data arrives
        """
        self.host = host
        self.port = port
        self.callback = callback

        self._socket = None
        self._listening = False
        self._thread = None
        self._latest_data: Optional[OutGaugeData] = None
        self._data_lock = threading.Lock()

        # Light names for decoding
        self._light_names = [
            "shift_light", "full_beam", "handbrake", "pit_limiter",
            "tc", "left_turn", "right_turn", "both_turns",
            "oil_warn", "battery_warn", "abs", "spare_light"
        ]

    def _decode_flag(self, flag: int) -> OutGaugeCarFlags:
        """Decode flag bits into CarFlags structure."""
        flag_bin = bin(flag)[2:].zfill(3)  # Ensure at least 3 bits
        return OutGaugeCarFlags(
            showTurbo=flag_bin[-1] == "1",
            showKM=flag_bin[-2] != "1",
            showBAR=flag_bin[-3] != "1"
        )

    def _decode_lights(self, lights_available: int, lights_active: int) -> OutGaugeCarLights:
        """Decode light status from bit flags into CarLights structure."""
        lights_active_bin = bin(lights_active)[2:].zfill(12)[::-1]  # Reverse for correct bit order

        # Extract each light status
        light_values = []
        for i in range(12):
            if i < len(lights_active_bin):
                light_values.append(lights_active_bin[i] == "1")
            else:
                light_values.append(False)

        return OutGaugeCarLights(*light_values)

    def _decode_packet(self, data: bytes) -> Optional[OutGaugeData]:
        """Decode the UDP packet into structured CarTelemetryData."""
        try:
            unpacked = struct.unpack("I4sHBBfffffffIIfff16s16sxxxx", data)

            return OutGaugeData(
                time=unpacked[0],
                carName=unpacked[1].decode("utf-8").rstrip('\x00'),
                flags=self._decode_flag(unpacked[2]),
                gear=unpacked[3],
                PLID=unpacked[4],
                speed=unpacked[5],
                rpm=unpacked[6],
                turboPressure=unpacked[7],
                engTemp=unpacked[8],
                fuel=unpacked[9],
                oilPressure=unpacked[10],
                oilTemp=unpacked[11],
                lights=self._decode_lights(unpacked[12], unpacked[13]),
                throttle=unpacked[14],
                brake=unpacked[15],
                clutch=unpacked[16],
                misc1=unpacked[17].decode("utf-8").rstrip('\x00'),
                misc2=unpacked[18].decode("utf-8").rstrip('\x00'),
                timestamp=time.time()  # Add local timestamp
            )
        except (struct.error, UnicodeDecodeError) as e:
            print(f"Error decoding packet: {e}")
            return None

    def _listen_loop(self):
        """Main listening loop running in separate thread."""
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.settimeout(1.0)  # 1 second timeout for clean shutdown

        try:
            self._socket.bind((self.host, self.port))
            print(f"UDP telemetry server listening on {self.host}:{self.port}")

            while self._listening:
                try:
                    data, addr = self._socket.recvfrom(1024)
                    decoded_data = self._decode_packet(data)

                    if decoded_data:  # Only process if decoding was successful
                        with self._data_lock:
                            self._latest_data = decoded_data

                        # Call callback if provided
                        if self.callback:
                            try:
                                self.callback(decoded_data)
                            except Exception as e:
                                print(f"Error in callback: {e}")

                except socket.timeout:
                    # Timeout is expected for clean shutdown
                    continue
                except Exception as e:
                    if self._listening:  # Only print if we're still supposed to be listening
                        print(f"Error receiving data: {e}")

        except Exception as e:
            print(f"Error setting up socket: {e}")
        finally:
            if self._socket:
                self._socket.close()

    def start_listening(self) -> bool:
        """
        Start listening for telemetry data in a separate thread.

        Returns:
            bool: True if started successfully, False otherwise
        """
        if self._listening:
            print("Already listening!")
            return False

        self._listening = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        return True

    def stop_listening(self):
        """Stop listening for telemetry data."""
        if not self._listening:
            return

        self._listening = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

        print("Telemetry receiver stopped")

    def get_latest_data(self) -> Dict[str, Any]:
        """
        Get the most recently received telemetry data.

        Returns:
            dict: Latest car telemetry data, empty dict if no data received yet
        """
        with self._data_lock:
            return self._latest_data.copy()

    def is_listening(self) -> bool:
        """Check if the receiver is currently listening."""
        return self._listening

    def get_data_as_json(self) -> str:
        """Get the latest data formatted as JSON string."""
        return json.dumps(self.get_latest_data(), indent=2)

    def __enter__(self):
        """Context manager entry."""
        self.start_listening()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop_listening()


class MotionSimData(NamedTuple):
    """Data structure matching the C struct"""
    format: str
    posX: float
    posY: float
    posZ: float
    velX: float
    velY: float
    velZ: float
    accX: float
    accY: float
    accZ: float
    upX: float
    upY: float
    upZ: float
    rollPos: float
    pitchPos: float
    yawPos: float
    rollVel: float
    pitchVel: float
    yawVel: float
    rollAcc: float
    pitchAcc: float
    yawAcc: float

class BeamNGMotionSimReceiver:
    """
    Real-time UDP receiver for vehicle telemetry data.

    Usage:
        receiver = UDPVehicleReceiver(port=12345)
        receiver.start()

        # Get latest data
        data = receiver.get_latest_data()
        if data:
            print(f"Position: {data.posX}, {data.posY}, {data.posZ}")

        receiver.stop()
    """

    def __init__(self, port: int, host: str = "0.0.0.0", buffer_size: int = 1024):
        self.host = host
        self.port = port
        self.buffer_size = buffer_size

        # C struct format: 4 chars + 18 floats = 4 + 72 = 76 bytes
        # Format string: 4s (4-byte string) + 18f (18 floats)
        self.struct_format = "4s18f"
        self.struct_size = struct.calcsize(self.struct_format)

        self.socket = None
        self.running = False
        self.thread = None
        self.latest_data: Optional[MotionSimData] = None
        self.data_lock = threading.Lock()

        # Callback function for real-time processing
        self.data_callback: Optional[Callable[[MotionSimData], None]] = None

        # Statistics
        self.packets_received = 0
        self.invalid_packets = 0
        self.last_packet_time = 0

    def set_data_callback(self, callback: Callable[[MotionSimData], None]):
        """Set a callback function that will be called for each received packet"""
        self.data_callback = callback

    def start(self):
        """Start the UDP receiver in a separate thread"""
        if self.running:
            return

        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.settimeout(1.0)  # 1 second timeout for clean shutdown

            self.running = True
            self.thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.thread.start()

            print(f"UDP Vehicle Receiver started on {self.host}:{self.port}")

        except Exception as e:
            print(f"Failed to start UDP receiver: {e}")
            self.running = False

    def stop(self):
        """Stop the UDP receiver"""
        self.running = False

        if self.thread:
            self.thread.join(timeout=2.0)

        if self.socket:
            self.socket.close()
            self.socket = None

        print("UDP Vehicle Receiver stopped")

    def _receive_loop(self):
        """Main receiving loop running in separate thread"""
        while self.running:
            try:
                data, addr = self.socket.recvfrom(self.buffer_size)
                self._process_packet(data)

            except socket.timeout:
                continue  # Timeout is expected for clean shutdown
            except Exception as e:
                if self.running:  # Only print errors if we're supposed to be running
                    print(f"Error receiving data: {e}")

    def _process_packet(self, data: bytes):
        """Process received packet and extract vehicle data"""
        try:
            # Check if packet size matches expected structure
            if len(data) < self.struct_size:
                self.invalid_packets += 1
                return

            # Unpack the binary data
            unpacked = struct.unpack(self.struct_format, data[:self.struct_size])

            # Decode format string and validate
            format_bytes = unpacked[0]
            format_str = format_bytes.decode('ascii', errors='ignore').rstrip('\x00')

            if format_str != "BNG1":
                self.invalid_packets += 1
                return

            # Create VehicleData object
            vehicle_data = MotionSimData(
                format=format_str,
                posX=unpacked[1], posY=unpacked[2], posZ=unpacked[3],
                velX=unpacked[4], velY=unpacked[5], velZ=unpacked[6],
                accX=unpacked[7], accY=unpacked[8], accZ=unpacked[9],
                upX=unpacked[10], upY=unpacked[11], upZ=unpacked[12],
                rollPos=unpacked[13], pitchPos=unpacked[14], yawPos=unpacked[15],
                rollVel=unpacked[16], pitchVel=unpacked[17], yawVel=unpacked[18],
                rollAcc=unpacked[19], pitchAcc=unpacked[20], yawAcc=unpacked[21]
            )

            # Update latest data thread-safely
            with self.data_lock:
                self.latest_data = vehicle_data
                self.packets_received += 1
                self.last_packet_time = time.time()

            # Call callback if set
            if self.data_callback:
                self.data_callback(vehicle_data)

        except Exception as e:
            print(f"Error processing packet: {e}")
            self.invalid_packets += 1

    def get_latest_data(self) -> Optional[MotionSimData]:
        """Get the most recently received vehicle data"""
        with self.data_lock:
            return self.latest_data

    def get_stats(self) -> dict:
        """Get receiver statistics"""
        with self.data_lock:
            return {
                "packets_received": self.packets_received,
                "invalid_packets": self.invalid_packets,
                "last_packet_time": self.last_packet_time,
                "is_running": self.running
            }

    def wait_for_data(self, timeout: float = 5.0) -> Optional[MotionSimData]:
        """Wait for new data to arrive"""
        start_count = self.packets_received
        start_time = time.time()

        while time.time() - start_time < timeout:
            if self.packets_received > start_count:
                return self.get_latest_data()
            time.sleep(0.01)  # 10ms polling

        return None
