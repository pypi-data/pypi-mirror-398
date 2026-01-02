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
import gc; gc.enable()
import os
import platform

from .info import __version__

try:
    os.environ["damp11113_load_all_module"]
except:
    os.environ["damp11113_load_all_module"] = "YES"

try:
    os.environ["damp11113_check_update"]
except:
    os.environ["damp11113_check_update"] = "YES"

if os.environ["damp11113_load_all_module"] == "YES":
    if platform.system() == "Windows":
        from .pywindows import *

    from .info import *
    from .file import *
    from .randoms import *
    from .processbar import *
    from .convert import *
    from .utils import *
    from .plusmata import *
    from .logic import *
    from .PyserHTTP import *
    from .format import *
    from .imageps import *
    from .minecraft import *
    from .media import *
    from .network import *
    from .DSP import *
    from .codec import *

    from .OPFONMW.dearpygui_animate import *
    from .OPFONMW.StepperLib import *

if os.environ["damp11113_check_update"] == "YES":
    import threading
    import time
    def check_for_update():
        from pygments import console
        import requests
        if os.name == 'nt':
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

        print(console.colorize("yellow", "Checking for damp11113-library update..."))
        try:
            # Attempt to fetch version info with a timeout and retry logic
            retries = 3
            for attempt in range(retries):
                try:
                    response = requests.get("https://cdn.damp11113.xyz/file/text/damp11113libver.txt", timeout=5)
                    if response.status_code == 200:
                        # Compare versions and display results
                        if response.text == __version__:
                            print(console.colorize("green", f"No update available for damp11113-library."))
                            print(console.colorize("green", f"damp11113-library version: {__version__}"))
                        else:
                            print(console.colorize("yellow", "Update available!"))
                            print(console.colorize("green", f"Current version: {__version__}"))
                            print(console.colorize("green", f"New version: {response.text}"))
                        break  # Exit after handling the response
                    else:
                        print(console.colorize("red", f"Error {response.status_code}: Update check failed."))
                        break
                except requests.exceptions.RequestException as e:
                    if attempt < retries - 1:
                        print(console.colorize("yellow", f"Retrying... ({attempt + 1}/{retries})"))
                        time.sleep(2)  # Wait before retrying
                    else:
                        print(console.colorize("red", f"Failed to check for update: {e}"))
        except Exception as e:
            print(console.colorize("red", f"Unexpected error: {e}"))


    # Create and start the thread for the update check
    update_thread = threading.Thread(target=check_for_update)
    update_thread.start()