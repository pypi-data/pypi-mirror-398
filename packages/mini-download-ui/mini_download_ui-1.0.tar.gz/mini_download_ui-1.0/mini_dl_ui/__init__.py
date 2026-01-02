import mini_dl_ui._mdu_utils as mu
import sys
import time
import threading
from collections import deque

class DownloadUI:
    def __init__(self, refresh: float = 0.05, fill='#') -> None:
        self.refresh = max(0.02, float(refresh))
        self.fill = fill[0] if fill else "#"
        self._logs = deque(maxlen=2000)
        self._pct = 0.0
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._tty = sys.stdout.isatty()
        if self._tty:
            mu._enable_ansi_windows()
            sys.stdout.write(mu.CSI + "?25l")  # hide cursor
            sys.stdout.flush()
        self._t = threading.Thread(target=self._loop, daemon=True)
        self._t.start()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    def log(self, msg: str) -> None:
        with self._lock:
            for line in str(msg).splitlines() or [""]:
                self._logs.append(line)

    def progress(self, percent: float) -> None:
        p = float(percent)
        if p < 0:
            p = 0.0
        if p > 100:
            p = 100.0
        with self._lock:
            self._pct = p

    def close(self) -> None:
        self._stop.set()
        self._t.join(timeout=1.0)
        if self._tty:
            sys.stdout.write(mu.CSI + "?25h")  # show cursor
            sys.stdout.write("\n")
            sys.stdout.flush()

    def _render(self) -> None:
        cols, rows = mu._term_size()
        log_rows = rows - 1
        with self._lock:
            logs = list(self._logs)[-log_rows:]
            pct = self._pct
        if len(logs) < log_rows:
            logs = logs + [""] * (log_rows - len(logs))
        inner = cols - 2
        filled = int((pct / 100.0) * inner)
        bar = "[" + (self.fill * filled) + (" " * (inner - filled)) + "]"
        right = f" {pct:5.1f}%"
        if len(right) < cols:
            bar = (bar[: max(0, cols - len(right))] + right).ljust(cols)
        else:
            bar = bar[:cols]
        sys.stdout.write(mu.CSI + "H" + mu.CSI + "2J")
        for line in logs:
            sys.stdout.write((line[:cols]).ljust(cols) + "\n")
        sys.stdout.write(bar)
        sys.stdout.flush()

    def _loop(self) -> None:
        if not self._tty:
            while not self._stop.is_set():
                time.sleep(self.refresh)
            return
        while not self._stop.is_set():
            self._render()
            time.sleep(self.refresh)
