import os
from pathlib import Path
import runpy
import sys

base = Path(__file__).resolve().parent
os.chdir(base)
sys.path.insert(0, str(base / 'vendor'))
if (base / 'tcl/tcl8.6/init.tcl').exists():
    os.environ['TCL_LIBRARY'] = 'tcl/tcl8.6'
    os.environ['TK_LIBRARY'] = 'tcl/tk8.6'
runpy.run_path(str(base / 'app.py'), run_name='__main__')
