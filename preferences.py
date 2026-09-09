import json
import re
from pathlib import Path

def load_preferences(path):
    try:
        data=json.loads(Path(path).read_text(encoding='utf-8'))
        if not isinstance(data,dict):return {}
        result={}
        if data.get('theme') in ('Light','Dark','System'):result['theme']=data['theme']
        value=data.get('geometry','')
        match=re.fullmatch(r'(\d+)x(\d+)\+(-?\d+)\+(-?\d+)',value) if isinstance(value,str) else None
        if match:
            w,h,x,y=map(int,match.groups())
            # Keep a moved/removed monitor from stranding the next window.
            if 1100<=w<=7680 and 800<=h<=4320 and x>=0 and y>=0:result['geometry']=value
        return result
    except (OSError,ValueError):return {}

def save_preferences(path,theme,geometry):
    from storage import atomic_text
    try:atomic_text(path,json.dumps({'theme':theme,'geometry':geometry}))
    except OSError:return False
    return True
