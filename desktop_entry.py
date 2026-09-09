"""Windowed executable entry point."""
import sys
import os
import json
import traceback
from pathlib import Path
original_directory = Path.cwd()
try:
    if getattr(sys, 'frozen', False):
        os.chdir(sys._MEIPASS)
        os.environ['TCL_LIBRARY'] = '_tcl_data'
        os.environ['TK_LIBRARY'] = '_tk_data'
    import tkinter as tk
    from app import App
    root = tk.Tk()
    os.chdir(original_directory)
    app = App(root)
    if len(sys.argv) == 3 and sys.argv[1] == '--smoke-test':
        root.withdraw()
        root.update()
        Path(sys.argv[2]).write_text(json.dumps({'started': True, 'settings': len(app.entries), 'history': bool(app.history)}))
        app.close()
    else:
        root.mainloop()
except Exception:
    log_directory=Path(sys.executable).resolve().parent/'User Data' if getattr(sys,'frozen',False) else original_directory
    log_directory.mkdir(parents=True,exist_ok=True)
    (log_directory/'startup-error.log').write_text(traceback.format_exc(), encoding='utf-8')
    raise
