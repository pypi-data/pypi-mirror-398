# Mini Download UI

A minimalist and cross-platform Python module providing a terminal download using ANSI escape sequences.

This project focuses on **simplicity and clarity**:
- No external dependencies
- Pure Python
- Works on Linux, macOS and modern Windows terminals

---

## Features

- APT style progress bar
- Log area displayed above the progress bar
- Progress percentage indicator
- Adaptive to terminal size
- ANSI-based rendering
- Simple and explicit usage

---

## Requirements

- Python **3.8+**
- ANSI-compatible terminal  
  - Linux terminals  
  - macOS Terminal / iTerm2  
  - Windows Terminal, PowerShell 7+, WSL

---

## Installation

No installation step required.
Simply install the lib with `pip`

```bash
pip install mini-download-ui
```

---

## Basic Usage

```python
from mini_dl_ui import DownloadUI
import time

ui = DownloadUI()

for i in range(101):
    ui.progress(i)
    ui.log(f"Downloading package {i}/100")
    time.sleep(0.05)

ui.close()
```

# Alternative Usage

```python
from mini_dl_ui import DownloadUI
import time

with DownloadUI() as ui:
    for i in range(101):
        if i in (10, 40, 70):
            ui.log(f"Downloading package {i}/100")
        ui.progress(i)
        time.sleep(0.03)
    ui.log("Finished.")
    time.sleep(0.5)
```

# Example Terminal Output

```text
[LOG] Downloading package 48/100
[LOG] Downloading package 49/100
[LOG] Downloading package 50/100
--------------------------------------------------
[##########                                  ] 50%
```

---

## Threaded Usage

```python
import threading
import time
from mini_dl_ui import DownloadUI

ui = DownloadUI(fill='=')

def worker():
    for i in range(101):
        ui.progress(i)
        ui.log(f"Chunk {i} received")
        time.sleep(0.03)
    ui.close()

threading.Thread(target=worker).start()
```
# Example Terminal Output

```text
[LOG] Downloading package 48/100
[LOG] Downloading package 49/100
[LOG] Downloading package 50/100
--------------------------------------------------
[=========                                  ] 50%
```
