"""Keep packaged application data outside the executable bundle."""
import os
import sys
from pathlib import Path
DATA_ROOT = (Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData' / 'Local')) / 'MeshCore Configurator') if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent
DATA_ROOT.mkdir(parents=True, exist_ok=True)
