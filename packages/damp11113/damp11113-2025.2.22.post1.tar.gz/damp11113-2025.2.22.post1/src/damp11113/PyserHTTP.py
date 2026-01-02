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

import os
import logging
import warnings
import socket
import json

logger = logging.getLogger('PyserHTTP')

class HTTPServer:
    def __init__(self):
        warnings.warn("PyserHTTP is experimental and not recommended for production use.", DeprecationWarning)

        self.routes = {}

    def route(self, path, methods=['GET']):
        def decorator(func):
            self.routes[path] = {'handler': func, 'methods': methods}
            return func
        return decorator

    def parse_request(self, request):
        headers_end = request.index("\r\n\r\n")
        headers_raw = request[:headers_end].split("\r\n")[1:]  # Skip the first line (request line)
        headers_dict = {}
        for header_line in headers_raw:
            header_key, header_value = header_line.split(': ', 1)
            headers_dict[header_key] = header_value

        content_type = headers_dict.get('Content-Type', '')

        if 'multipart/form-data' in content_type:
            # Parse form data
            boundary = content_type.split('boundary=')[1]
            body_parts = request.split(f'--{boundary}')
            form_data = {}

            for part in body_parts:
                if 'name=' in part:
                    name_start = part.find('name="') + 6
                    name_end = part.find('"', name_start)
                    name = part[name_start:name_end]
                    value_start = part.find('\r\n\r\n') + 4
                    value = part[value_start:-2]  # Exclude trailing '\r\n'

                    form_data[name] = value

            return form_data, headers_dict

        # Handle other content types (e.g., JSON)
        # ... (as per previous implementation)

        return {}, headers_dict

    def start(self, ip='', port=4000):
        logger.info('Starting PyserHTTP')
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((ip, port))
        server_socket.listen()
        logger.info(f'Started. Running on http://localhost:{port}')

        while True:
            try:
                client_socket, client_address = server_socket.accept()
                logger.info(f"Accepted connection from {client_address}")
                request = client_socket.recv(4096).decode()  # Increased buffer size for POST data
                request_lines = request.split("\r\n")
                request_line = request_lines[0].split(" ")
                method, path, _ = request_line[0], request_line[1], request_line[2]

                if method == 'POST':
                    request_data, headers = self.parse_request(request)
                else:
                    request_data, headers = {}, {}

                if path in self.routes and method in self.routes[path]['methods']:
                    response_body = ""
                    response_status = "HTTP/1.0 200 OK"
                    logger.info(f"HTTP/1.0 200 OK | {path}")
                    result = self.routes[path]['handler'](request_data, headers)
                    if isinstance(result, dict):
                        response_body = json.dumps(result)
                    elif isinstance(result, str):
                        response_body = result
                else:
                    response_status = "HTTP/1.0 404 Not Found"
                    response_body = ""
                    logger.warning(f"HTTP/1.0 404 Not Found | {path}")

                response = f"{response_status}\r\nServer: PyserHTTP/1.0\r\nContent-Length: {len(response_body)}\r\n\r\n{response_body}"

                client_socket.sendall(response.encode())
                client_socket.close()
            except Exception as e:
                logger.error(f"Error accepting connection: {e}")


def render_template(template_name, folder="templates", **context):
    template_path = os.path.join(folder, template_name)
    with open(template_path, 'r') as template_file:
        template_content = template_file.read()
        rendered_template = template_content.format(**context)  # Using string formatting
        # Alternatively, you can use str.format() method:
        # rendered_template = template_content.format_map(context)
    return rendered_template
