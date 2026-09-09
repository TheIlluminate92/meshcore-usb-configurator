"""Atomic local writes: retain the previous file if writing fails."""
import os
import tempfile
import threading
from pathlib import Path
_write_lock=threading.RLock()

def atomic_text(path,text):
    with _write_lock:_atomic_text(path,text)

def _atomic_text(path,text):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=None
    try:
        with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=path.parent,prefix='.'+path.name+'-',suffix='.tmp',delete=False) as stream:
            temporary=Path(stream.name)
            stream.write(text);stream.flush();os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        if temporary is not None:temporary.unlink(missing_ok=True)
