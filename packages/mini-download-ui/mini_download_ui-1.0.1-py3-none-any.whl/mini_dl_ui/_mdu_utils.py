import os

CSI = "\x1b["

def _enable_ansi_windows() -> None:
    if os.name != "nt":
        return
    try:
        import ctypes
        from ctypes import wintypes

        k32 = ctypes.windll.kernel32
        h = k32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
        mode = wintypes.DWORD()
        if not k32.GetConsoleMode(h, ctypes.byref(mode)):
            return
        k32.SetConsoleMode(h, mode.value | 0x0004)  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
    except Exception:
        pass


def _term_size():
    try:
        s = os.get_terminal_size()
        return max(20, s.columns), max(6, s.lines)
    except OSError:
        return 80, 24
