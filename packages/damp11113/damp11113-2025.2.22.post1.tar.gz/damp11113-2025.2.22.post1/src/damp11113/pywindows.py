"""
This module will work only in windows
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
import time
import ctypes
from ctypes import wintypes
import comtypes.client
import win32api
import win32con
import win32gui

class ITaskbarList3(comtypes.IUnknown):
    _case_insensitive_ = True
    _iid_ = comtypes.GUID("{ea1afb91-9e28-4b86-90e9-9e9f8a5eefaf}")

    _methods_ = [
        comtypes.STDMETHOD(None, "HrInit"),
        comtypes.STDMETHOD(None, "AddTab", (ctypes.c_ulonglong,)),
        comtypes.STDMETHOD(None, "DeleteTab", (ctypes.c_ulonglong,)),
        comtypes.STDMETHOD(None, "ActivateTab", (ctypes.c_ulonglong,)),
        comtypes.STDMETHOD(None, "SetActiveAlt", (ctypes.c_ulonglong,)),
        comtypes.STDMETHOD(None, "MarkFullscreenWindow", (ctypes.c_ulonglong, ctypes.c_int)),
        comtypes.STDMETHOD(None, "SetProgressValue", (ctypes.c_ulonglong, ctypes.c_ulonglong, ctypes.c_ulonglong)),
        comtypes.STDMETHOD(None, "SetProgressState", (ctypes.c_ulonglong, ctypes.c_ulonglong)),
        comtypes.STDMETHOD(None, "RegisterTab", (ctypes.c_ulonglong,)),
        comtypes.STDMETHOD(None, "UnregisterTab", (ctypes.c_ulonglong,)),
        comtypes.STDMETHOD(None, "SetTabOrder", (ctypes.c_ulonglong, ctypes.c_ulonglong)),
        comtypes.STDMETHOD(None, "SetTabActive", (ctypes.c_ulonglong, ctypes.c_ulonglong, ctypes.c_ulonglong)),
        comtypes.STDMETHOD(None, "ThumbBarAddButtons", (ctypes.c_ulonglong, ctypes.c_ulonglong, ctypes.c_ulonglong, ctypes.POINTER(ctypes.c_ulonglong))),
        comtypes.STDMETHOD(None, "ThumbBarUpdateButtons", (ctypes.c_ulonglong, ctypes.c_ulonglong, ctypes.c_ulonglong, ctypes.POINTER(ctypes.c_ulonglong))),
        comtypes.STDMETHOD(None, "ThumbBarSetImageList", (ctypes.c_ulonglong, ctypes.c_ulonglong)),
        comtypes.STDMETHOD(None, "SetOverlayIcon", (ctypes.c_ulonglong, ctypes.c_char_p, ctypes.c_char_p)),
        comtypes.STDMETHOD(None, "SetThumbnailTooltip", (ctypes.c_ulonglong, ctypes.c_char_p)),
        comtypes.STDMETHOD(None, "SetThumbnailClip", (ctypes.c_ulonglong, ctypes.c_void_p)),
    ]

class WindowsTaskbar:
    def __init__(self, hwnd=ctypes.windll.kernel32.GetConsoleWindow(), maxprogress=100):
        """
        app type has tk, console, pyqt
        """
        self.maxprogress = maxprogress

        comtypes.client.GetModule("shell32.dll")
        self.taskbar_list = comtypes.client.CreateObject(
            comtypes.GUID("{56FDF344-FD6D-11D0-958A-006097C9A090}"), interface=ITaskbarList3
        )

        self.taskbar_list.HrInit()

        self.hwnd = hwnd

    def setProgress(self, current):
        self.taskbar_list.SetProgressValue(self.hwnd, current, self.maxprogress)

    def setState(self, state):
        states = {
            'normal': 2,  # TBPF_NORMAL
            'error': 4,  # TBPF_ERROR
            'paused': 8,  # TBPF_PAUSED
        }

        if state not in states:
            raise ValueError("Invalid state. Supported states: normal, error, paused")

        self.taskbar_list.SetProgressState(self.hwnd, states[state])

    def setIcon(self, icon_path):
        icon_flags = win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
        hicon = win32gui.LoadImage(None, icon_path, win32con.IMAGE_ICON, 0, 0, icon_flags)

        win32gui.SendMessage(self.hwnd, win32con.WM_SETICON, win32con.ICON_SMALL, hicon)
        win32gui.SendMessage(self.hwnd, win32con.WM_SETICON, win32con.ICON_BIG, hicon)

    def setTitle(self, title):
        win32gui.SetWindowText(self.hwnd, title)

    def reset(self):
        # Reset progress and state when done
        self.setProgress(0)
        self.setState('normal')

class WindowsSimpleTray:
    def __init__(self, icon, menu_options, hover_text="Python", onclick=None, ondoubleclick=None, onrightclick=None, default_menu_index=1, window_class_name="SystemTrayIcon"):
        self.icon = icon
        self.hover_text = hover_text
        self.menu_options = menu_options
        self.default_menu_index = default_menu_index
        self.window_class_name = window_class_name
        self.funconclick = onclick
        self.funcondoubleclick = ondoubleclick
        self.funconrightclick = onrightclick

        message_map = {
            win32gui.RegisterWindowMessage("TaskbarCreated"): self.restart,
            win32con.WM_DESTROY: self.destroy,
            win32con.WM_COMMAND: self.command,
            win32con.WM_USER + 20: self.notify,
        }

        wc = win32gui.WNDCLASS()
        hinst = wc.hInstance = win32api.GetModuleHandle(None)
        wc.lpszClassName = self.window_class_name
        wc.style = win32con.CS_VREDRAW | win32con.CS_HREDRAW
        wc.hCursor = win32api.LoadCursor(0, win32con.IDC_ARROW)
        wc.hbrBackground = win32con.COLOR_WINDOW
        wc.lpfnWndProc = message_map
        class_atom = win32gui.RegisterClass(wc)

        style = win32con.WS_OVERLAPPED | win32con.WS_SYSMENU
        self.hwnd = win32gui.CreateWindow(
            class_atom,
            self.window_class_name,
            style,
            0,
            0,
            win32con.CW_USEDEFAULT,
            win32con.CW_USEDEFAULT,
            0,
            0,
            hinst,
            None
        )
        win32gui.UpdateWindow(self.hwnd)
        self.notify_id = None
        self.refresh_icon()

    def refresh_icon(self):
        hinst = win32api.GetModuleHandle(None)
        if self.notify_id:
            message = win32gui.NIM_MODIFY
        else:
            message = win32gui.NIM_ADD
        self.notify_id = (
            self.hwnd,
            0,
            win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP,
            win32con.WM_USER + 20,
            win32gui.LoadImage(hinst, self.icon, win32con.IMAGE_ICON, 0, 0, win32con.LR_LOADFROMFILE),
            self.hover_text
        )
        win32gui.Shell_NotifyIcon(message, self.notify_id)

    def WndProc(self, hwnd, msg, wparam, lparam):
        if msg == 1023:
            self.execute_menu_option(1023)
        elif msg == win32con.WM_DESTROY:
            self.destroy(hwnd, msg, wparam, lparam)
        elif msg == win32con.WM_COMMAND:
            self.command(hwnd, msg, wparam, lparam)
        elif msg == win32con.WM_USER + 20:
            self.notify(hwnd, msg, wparam, lparam)
        else:
            return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)
        return 0

    def restart(self, hwnd, msg, wparam, lparam):
        self.refresh_icon()

    def destroy(self, hwnd, msg, wparam, lparam):
        nid = (self.hwnd, 0)
        win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, nid)
        win32gui.PostQuitMessage(0)

    def command(self, hwnd, msg, wparam, lparam):
        id = win32api.LOWORD(wparam)
        self.execute_menu_option(id)
        return 0

    def notify(self, hwnd, msg, wparam, lparam):
        if lparam == win32con.WM_LBUTTONDBLCLK:
            if self.funcondoubleclick != None:
                self.funcondoubleclick(self)  # Replace with the desired function
        elif lparam == win32con.WM_LBUTTONDOWN:
            if self.funconclick != None:
                self.funconclick(self)  # Replace with the desired function
        elif lparam == win32con.WM_RBUTTONUP:
            if self.funconrightclick != None:
                self.funconrightclick(self)
            else:
                self.show_menu()
        return 0

    def show_menu(self):
        menu = win32gui.CreatePopupMenu()
        for id, (text, _, callback) in enumerate(self.menu_options, 1024):
            if text is None:
                win32gui.InsertMenu(menu, id, win32con.MF_BYPOSITION | win32con.MF_SEPARATOR, id, None)
            else:
                win32gui.InsertMenu(menu, id, win32con.MF_BYPOSITION | win32con.MF_STRING, id, text)

        pos = win32gui.GetCursorPos()
        win32gui.SetForegroundWindow(self.hwnd)
        win32gui.TrackPopupMenu(menu, win32con.TPM_LEFTALIGN, pos[0], pos[1], 0, self.hwnd, None)
        win32gui.PostMessage(self.hwnd, win32con.WM_NULL, 0, 0)

    def execute_menu_option(self, id):
        if id == 1023:
            self.destroy(self.hwnd, 0, 0, 0)
        elif 1024 <= id < 1024 + len(self.menu_options):
            self.menu_options[id - 1024][2](self)

    def loop(self):
        win32gui.PumpMessages()

def size(x, y):
    os.system('mode con: cols={} lines={}'.format(x, y))

def setConsoleTitle(window_title_string, wait_for_change=False):
    os.system("title " + window_title_string)
    if (wait_for_change):
        matched_window = 0
        while (matched_window == 0):
            matched_window = win32gui.FindWindow(None, window_title_string)
            time.sleep(0.025)  # To not flood it too much...

    return window_title_string

def setConsoleIcon(window_title, image_path):
    hwnd = win32gui.FindWindow(None, window_title)
    icon_flags = win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
    hicon = win32gui.LoadImage(None, image_path, win32con.IMAGE_ICON, 0, 0, icon_flags)

    win32gui.SendMessage(hwnd, win32con.WM_SETICON, win32con.ICON_SMALL, hicon)
    win32gui.SendMessage(hwnd, win32con.WM_SETICON, win32con.ICON_BIG, hicon)

def mbox(title, text, style):
    return ctypes.windll.user32.MessageBoxW(0, text, title, style)

def get_hwnd_from_pid(pid: int) -> int | None:
    user32 = ctypes.WinDLL("user32")
    user32.SetWindowPos.restype = wintypes.BOOL
    user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, wintypes.INT, wintypes.INT, wintypes.INT,
                                    wintypes.INT, wintypes.UINT, ]
    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL,
                              wintypes.HWND,
                              wintypes.LPARAM)
    user32.EnumWindows.argtypes = [WNDENUMPROC,
                                   wintypes.LPARAM]

    result = None

    def callback(hwnd, _):
        nonlocal result
        lpdw_PID = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(lpdw_PID))
        hwnd_PID = lpdw_PID.value

        if hwnd_PID == pid:
            result = hwnd
            return False
        return True

    cb_worker = WNDENUMPROC(callback)
    user32.EnumWindows(cb_worker, 0)
    return result
