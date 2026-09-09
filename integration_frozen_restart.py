"""Build as a one-file windowed EXE and run in a disposable folder only.

This probe updates a copy of itself and verifies the restarted process got a
new, existing extraction directory. It does not open or configure any radios.
"""
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path
from updater import schedule_install

def main():
    if not getattr(sys,'frozen',False):raise RuntimeError('Build this probe with PyInstaller first.')
    folder=Path(sys.executable).resolve().parent
    marker=folder/'probe-parent.json'
    if marker.exists():
        previous=json.loads(marker.read_text())
        result={'fresh_runtime':previous['runtime']!=sys._MEIPASS,'runtime_exists':Path(sys._MEIPASS).is_dir()}
        (folder/'probe-result.json').write_text(json.dumps(result))
        return
    marker.write_text(json.dumps({'runtime':sys._MEIPASS}))
    stage=folder/'User Data'/'Updates'/'ready.exe';stage.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(sys.executable,stage)
    schedule_install(stage,sys.executable,os.getpid(),'sha256:'+hashlib.sha256(stage.read_bytes()).hexdigest())

if __name__=='__main__':main()
