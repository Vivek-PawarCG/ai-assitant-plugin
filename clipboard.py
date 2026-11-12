import ctypes
from ctypes import wintypes
import subprocess

CF_UNICODETEXT = 13
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

def get_clipboard_text():
    """Reads current UTF-16 text from the Windows clipboard using ctypes."""
    try:
        if not user32.OpenClipboard(None):
            return ""
        try:
            h_mem = user32.GetClipboardData(CF_UNICODETEXT)
            if not h_mem:
                return ""
            kernel32.GlobalLock.restype = ctypes.c_wchar_p
            data_ptr = kernel32.GlobalLock(h_mem)
            text = str(data_ptr) if data_ptr else ""
            kernel32.GlobalUnlock(h_mem)
            return text
        finally:
            user32.CloseClipboard()
    except Exception:
        # Fallback to powershell if ctypes fails
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", "Get-Clipboard"],
                capture_output=True,
                text=True,
                timeout=2
            )
            return res.stdout.strip()
        except Exception:
            return ""

def set_clipboard_text(text):
    """Sets text in Windows clipboard."""
    try:
        # Standard ctypes clipboard setter
        if not user32.OpenClipboard(None):
            return False
        try:
            user32.EmptyClipboard()
            data = text.encode('utf-16le') + b'\x00\x00'
            h_mem = kernel32.GlobalAlloc(0x0042, len(data)) # GMEM_MOVEABLE | GMEM_ZEROINIT
            if not h_mem:
                return False
            kernel32.GlobalLock.restype = ctypes.c_void_p
            ptr = kernel32.GlobalLock(h_mem)
            ctypes.memmove(ptr, data, len(data))
            kernel32.GlobalUnlock(h_mem)
            user32.SetClipboardData(CF_UNICODETEXT, h_mem)
            return True
        finally:
            user32.CloseClipboard()
    except Exception:
        return False
