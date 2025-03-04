import win32api
import ctypes
from ctypes import wintypes
import sys
from datetime import datetime

import obs
import config

# Windows hook constants
WH_KEYBOARD_LL = 13  # Low-level keyboard hook
WM_KEYDOWN = 0x0100  # Key press event
WM_SYSKEYDOWN = 0x0104  # System key press event

# Define the HOOKPROC callback function type
HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_void_p))

# Load user32.dll for Windows API functions
user32 = ctypes.WinDLL('user32', use_last_error=True)

# Configure GetKeyNameTextW function for translating virtual keys to names
user32.GetKeyNameTextW.argtypes = [
    ctypes.c_long,  # lParam (scan code and flags)
    ctypes.c_wchar_p,  # buffer for key name
    ctypes.c_int  # buffer size
]
user32.GetKeyNameTextW.restype = ctypes.c_int

# Configure MapVirtualKeyW function for virtual-to-scan code conversion
user32.MapVirtualKeyW.argtypes = [ctypes.c_uint, ctypes.c_uint]
user32.MapVirtualKeyW.restype = ctypes.c_uint

# Constants for MapVirtualKey function
MAPVK_VK_TO_VSC = 0  # Convert virtual key to scan code


def get_key_name(vk_code):
    """
    Convert a virtual key code to its corresponding key name.

    Args:
        vk_code (int): Virtual key code.

    Returns:
        str: Readable key name or 'Unknown' if not found.
    """
    scan_code = user32.MapVirtualKeyW(vk_code, MAPVK_VK_TO_VSC)
    buf = ctypes.create_unicode_buffer(64)  # Buffer to store the key name
    lParam = scan_code << 16  # Encode scan code in lParam
    user32.GetKeyNameTextW(lParam, buf, ctypes.sizeof(buf))
    return buf.value


# Global flag to control the message loop
exit_flag = False


def low_level_keyboard_handler(nCode, wParam, lParam):
    """
    Callback function for processing low-level keyboard events.
    Detects key presses and triggers scene changes if configured.

    Args:
        nCode (int): Hook code.
        wParam (int): Event type (key press, system key press, etc.).
        lParam (ctypes.POINTER): Pointer to event data.

    Returns:
        int: CallNextHookEx result to pass event to the next hook.
    """
    global exit_flag
    if nCode >= 0:
        if wParam in (WM_KEYDOWN, WM_SYSKEYDOWN):
            vk_code = lParam[0]  # Extract virtual key code
            try:
                key_name = get_key_name(vk_code) or f"Unknown (VK: {vk_code})"
                scene = ""

                with config.lock:
                    if key_name in config.setup["key"]:
                        scene = config.setup["scene"][config.setup["key"].index(key_name)]

                data = {
                    "success": False,
                    "key": key_name,
                    "scene": scene,
                }

                if scene:
                    obs.set_active_scene(scene)
                    data["success"] = True

                with config.log_condition:
                    config.key_log = data
                    print(data)
                    config.log_condition.notify_all()
            except Exception as e:
                print(f"Error: {e}")

    return ctypes.windll.user32.CallNextHookEx(None, nCode, wParam, lParam)


def main():
    """
    Main function to set up the low-level keyboard hook and start the message loop.
    """
    hook_proc = HOOKPROC(low_level_keyboard_handler)  # Define hook procedure
    module_handle = ctypes.c_void_p(win32api.GetModuleHandle(None))  # Get module handle

    # Install the low-level keyboard hook
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

    # Message loop to keep the hook active
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
    """
    Entry point for the script. Ensures administrator privileges before execution.
    """
    if ctypes.windll.shell32.IsUserAnAdmin() == 0:
        print("Error: Run this script as Administrator.")
        sys.exit(1)
    main()
