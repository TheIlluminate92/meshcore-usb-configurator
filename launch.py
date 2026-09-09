import os
from pathlib import Path
import runpy
import sys

base = Path(__file__).resolve().parent
os.chdir(base)
sys.path.insert(0, str(base / 'vendor'))
if (base / 'bluetooth_libs').is_dir():
    sys.path.insert(0, str(base / 'bluetooth_libs'))
if (base / 'tcl/tcl8.6/init.tcl').exists():
    os.environ['TCL_LIBRARY'] = 'tcl/tcl8.6'
    os.environ['TK_LIBRARY'] = 'tcl/tk8.6'
try:
    runpy.run_path(str(base / 'app.py'), run_name='__main__')
except Exception:
    import traceback
    error = traceback.format_exc()
    (base / 'startup-error.log').write_text(error, encoding='utf-8')
    import tkinter as tk
    from tkinter import messagebox
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror('Configurator could not start', 'See startup-error.log in the project folder.\n\n' + error.splitlines()[-1])
    root.destroy()
