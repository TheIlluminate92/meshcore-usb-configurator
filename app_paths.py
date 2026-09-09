"""Portable builds keep all persistent files beside the executable."""
import sys
from pathlib import Path
APP_DIR = Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent
DATA_ROOT = APP_DIR / 'User Data' if getattr(sys, 'frozen', False) else APP_DIR
DATA_ROOT.mkdir(parents=True, exist_ok=True)

# Explorer normally shows folders first. Hide the supporting data folder so the
# portable folder opens on the EXE; moving the parent folder still includes it.
if getattr(sys, 'frozen', False) and sys.platform=='win32':
    import ctypes
    attributes=ctypes.windll.kernel32.GetFileAttributesW(str(DATA_ROOT))
    if attributes != -1:ctypes.windll.kernel32.SetFileAttributesW(str(DATA_ROOT),attributes | 2)
