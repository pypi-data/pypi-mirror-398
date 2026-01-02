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
import warnings
import json
import requests
from base64 import b64decode as base64decode
import socket
import struct

class mcstatus_exception(Exception):
    pass

class uuid2name_exception(Exception):
    pass

class server_exeption(Exception):
    pass

class install_exception(Exception):
    pass


#------------------get-uuid2name------------------

class uuid2name:
    def __init__(self) -> None:
        pass

    @staticmethod
    def getmcuuid(player_name):
        try:
            r = requests.get(f"https://api.mojang.com/users/profiles/minecraft/{player_name}")
            if r.text == '':
                raise uuid2name_exception(f"{player_name} not found")
            else:
                return json.loads(r.text)['id']
        except Exception as e:
            raise uuid2name_exception(e)

    @staticmethod
    def getmcname(player_uuid):
        try:
            r = requests.get(f"https://api.mojang.com/user/profiles/{player_uuid}/names")
        except Exception as e:
            raise uuid2name_exception(e)
        try:
            o = json.loads(r.text)[0]['name']
            return o
        except KeyError:
            raise uuid2name_exception(f"player not found")

    @staticmethod
    def getmcnamejson(player_uuid):
        try:
            return requests.get(f"https://api.mojang.com/user/profiles/{player_uuid}/names").text
        except Exception as e:
            raise uuid2name_exception(f"get mc name error: {e}")

    @staticmethod
    def getmcuuidjson(player_name):
        try:
            return requests.get(f"https://api.mojang.com/users/profiles/minecraft/{player_name}").text
        except Exception as e:
            raise uuid2name_exception(f"get mc uuid error: {e}")

#----------------other api------------------

def skin_url(uuid):
    try:
        r = requests.get(f"https://sessionserver.mojang.com/session/minecraft/profile/{uuid}")
        base = json.loads(r.text)['properties'][0]['value']
        # base64 to json
        js = base64decode(base)
        # json to dict
        d = json.loads(js)
        # get skin url
        return d['textures']['SKIN']['url']
    except Exception as e:
        raise uuid2name_exception(f"skin url error: {e}")

def mctimestamp(uuid):
    try:
        r = requests.get(f"https://sessionserver.mojang.com/session/minecraft/profile/{uuid}")
        base = json.loads(r.text)['properties'][0]['value']
        # base64 to json
        js = base64decode(base)
        # json to dict
        d = json.loads(js)
        # get skin url
        return d['timestamp']
    except Exception as e:
        raise uuid2name_exception(f"error: {e}")

#----------------------mcstatus------------------------



class mcstatusv2:
    def __init__(self, ip, port=25565):
        """
        To use visit https://chat.openai.com/share/966ad89a-3785-4d94-a4cc-7cb05c73bab3
        """
        warnings.warn("mcstatusv2 is experimental and not fully implemented", Warning)

        self.ip = ip
        self.port = port

    def _send_receive(self, payload):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)

        try:
            sock.connect((self.ip, self.port))
            sock.sendall(payload)
            data = sock.recv(4096)
            return data
        except socket.timeout:
            raise mcstatus_exception("Connection timed out")
        except Exception as e:
            raise mcstatus_exception(f"Error: {e}")
        finally:
            sock.close()

    def _parse_status(self, data):
        length = data[0]
        data = data[1:length+1]
        return json.loads(data.decode('utf-8'))

    def _get_status(self):
        payload = b'\x00\x00'  # Packet for getting status
        payload += bytes([len(self.ip)]) + self.ip.encode('utf-8')  # Append server address
        payload += bytes.fromhex('{:04x}'.format(self.port))  # Append server port
        payload += b'\x01'  # Protocol version

        response = self._send_receive(bytes([len(payload)]) + payload)
        return response

    def status(self):
        try:
            response = self._get_status()
            parsed_status = self._parse_status(response)
            return parsed_status
        except mcstatus_exception as e:
            raise mcstatus_exception(f"Error parsing status: {e}")

#----------------------Rcon-----------------------

class RconV2:
    def __init__(self, host, port, password):
        warnings.warn("RconV2 is experimental and not fully implemented", Warning)
        self.host = host
        self.port = port
        self.password = password
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect()

    def connect(self):
        self.sock.connect((self.host, self.port))
        packet = struct.pack('<iii', 0, 0, 2) + self.password.encode('utf-8') + b'\x00\x00'
        self.sock.send(struct.pack('<i', len(packet)) + packet)
        size, id, type = struct.unpack('<iii', self.sock.recv(12))
        response = self.sock.recv(size - 8).decode('utf-8')
        if id == -1:
            raise RuntimeError(f"Failed to authenticate: {response.strip()}")

    def send_command(self, command):
        command_packet = struct.pack('<iii', 1, 2, 2) + command.encode('utf-8') + b'\x00\x00'
        self.sock.send(struct.pack('<i', len(command_packet)) + command_packet)
        size, id, type = struct.unpack('<iii', self.sock.recv(12))
        response = self.sock.recv(size - 8).decode('utf-8')
        return response.strip()

    def close(self):
        self.sock.close()
