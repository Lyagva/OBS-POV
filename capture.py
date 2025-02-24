# capture.py
import win32api
import ctypes
from ctypes import wintypes
import sys
from datetime import datetime

import obs
import config

WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_SYSKEYDOWN = 0x0104

# Define the HOOKPROC type
HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_void_p))

# Define Windows API functions for key name translation
user32 = ctypes.WinDLL('user32', use_last_error=True)

# Define GetKeyNameTextW function
user32.GetKeyNameTextW.argtypes = [
    ctypes.c_long,  # lParam (scan code and flags)
    ctypes.c_wchar_p,  # buffer
    ctypes.c_int  # buffer size
]
user32.GetKeyNameTextW.restype = ctypes.c_int

# Define MapVirtualKeyW for scan code conversion
user32.MapVirtualKeyW.argtypes = [ctypes.c_uint, ctypes.c_uint]
user32.MapVirtualKeyW.restype = ctypes.c_uint

# Constants for MapVirtualKey
MAPVK_VK_TO_VSC = 0


def get_key_name(vk_code):
    # Get scan code from virtual key
    scan_code = user32.MapVirtualKeyW(vk_code, MAPVK_VK_TO_VSC)

    # Create buffer for key name
    buf = ctypes.create_unicode_buffer(64)

    # Format lParam: (scan_code << 16)
    lParam = scan_code << 16

    # Get key name
    user32.GetKeyNameTextW(lParam, buf, ctypes.sizeof(buf))
    return buf.value


# Global flag to control the message loop
exit_flag = False


def low_level_keyboard_handler(nCode, wParam, lParam):
    global exit_flag
    if nCode >= 0:
        if wParam in (WM_KEYDOWN, WM_SYSKEYDOWN):
            vk_code = lParam[0]
            try:
                key_name = get_key_name(vk_code) or f"Unknown (VK: {vk_code})"
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # print(f"Клавиша нажата: {key_name}")

                with config.scene_lock:
                    scene = config.scenes.get(key_name, None)


                if scene:
                    # print(f"Triggering scene: {scene}")
                    obs.set_active_scene(scene)
                    message = f"{timestamp} - Клавиша '{key_name}' нажата - Сцена '{scene}' триггернута"
                else:
                    message = f"{timestamp} - Клавиша '{key_name}' нажата - Сцена не назначена"

                with config.log_condition:
                    config.log_history.append(message)
                    config.log_condition.notify_all()

            except Exception as e:
                print(f"Ошибка: {e}")

    return ctypes.windll.user32.CallNextHookEx(None, nCode, wParam, lParam)


def main():
    # Keep a reference to the hook procedure
    hook_proc = HOOKPROC(low_level_keyboard_handler)

    # Get module handle (64-bit compatible)
    module_handle = ctypes.c_void_p(win32api.GetModuleHandle(None))

    # Install the keyboard hook
    hook_id = ctypes.windll.user32.SetWindowsHookExW(
        WH_KEYBOARD_LL,
        hook_proc,
        module_handle,
        0
    )

    if not hook_id:
        print("Failed to install hook.")
        return

    print("Hook installed. Press Ctrl+C to exit.")

    # Message loop with timeout
    try:
        msg = wintypes.MSG()
        while True:
            has_message = ctypes.windll.user32.PeekMessageW(ctypes.byref(msg), 0, 0, 0, 0x0001)
            if has_message:
                ctypes.windll.user32.GetMessageW(ctypes.byref(msg), 0, 0, 0)
                ctypes.windll.user32.TranslateMessage(ctypes.byref(msg))
                ctypes.windll.user32.DispatchMessageW(ctypes.byref(msg))
            else:
                ctypes.windll.kernel32.Sleep(10)
    except KeyboardInterrupt:
        print("Exiting via Ctrl+C...")
    finally:
        ctypes.windll.user32.UnhookWindowsHookEx(hook_id)
        print("Hook uninstalled.")


def run():
    if ctypes.windll.shell32.IsUserAnAdmin() == 0:
        print("Error: Run this script as Administrator.")
        sys.exit(1)
    main()