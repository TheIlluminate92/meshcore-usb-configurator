"""Qualitative hints, not measured runtime or an automatic configuration preset."""
import tkinter as tk
from tkinter import ttk
from model import parse_input

ADVICE = {
 'name': 'Use a unique, recognizable name.',
 'frequency': 'Match your mesh. No direct saving.',
 'bandwidth': 'Match mesh. Narrower = longer airtime.',
 'spreading_factor': 'Match mesh. Higher = slower packets.',
 'coding_rate': 'Match mesh. Higher = more airtime.',
 'tx_power': 'Use lowest reliable power; range falls too.',
 'path_hash_mode': 'Keep mesh default; larger adds bytes.',
 'multi_acks': 'Start at 0; extra replies use more energy.',
 'gps': 'On for trackers; off for fixed stations.',
 'gps_interval': 'If supported: longer saves, fixes lag.',
 'latitude': 'Fixed site only; no direct battery cost.',
 'longitude': 'Fixed site only; no direct battery cost.',
 'advert_location_policy': 'Share if needed; small packet cost.',
 'manual_add_contacts': 'Selected types keeps discovery tidy.',
 'overwrite_oldest': 'Off preserves contacts; little power effect.',
 'auto_add_chat': 'On if wanted; little direct power effect.',
 'auto_add_repeater': 'On for route discovery; little direct cost.',
 'auto_add_room_server': 'Enable if used; little direct power cost.',
 'auto_add_sensor': 'Enable if used; little direct power cost.',
 'auto_add_max_hops': 'Limit clutter if needed; not a sleep mode.',
 'telemetry_mode_base': 'Allowed contacts if needed; replies cost.',
 'telemetry_mode_loc': 'Allow if needed; base access required.',
 'telemetry_mode_env': 'Allow if needed; base access required.',
}

def impact(key, value):
    """Relative impact within each setting only: None means unquantified."""
    try: v = float(parse_input(key, value))
    except (TypeError, ValueError): return None
    if key == 'gps': return 5 if v else 0
    if key == 'tx_power': return 1 if v <= 0 else 2 if v <= 10 else 3 if v <= 17 else 4 if v <= 20 else 5
    if key == 'spreading_factor': return max(1, min(5, int(v)-6))
    if key == 'bandwidth': return 1 if v >= 250 else 2 if v >= 125 else 3 if v >= 62.5 else 4 if v >= 31.25 else 5
    if key == 'coding_rate': return max(1,min(5,int(v)-4))
    if key == 'multi_acks': return min(5,int(v)+1) if v else 0
    # Actual request frequency, sensors and receiver duty cycle are unknown.
    return None

class BatteryHint(ttk.Frame):
    def __init__(self, parent, key):
        super().__init__(parent)
        self.key = key
        self.canvas = tk.Canvas(self, width=77, height=28, background='white', highlightthickness=0)
        self.canvas.pack(side='left', padx=(8, 5))
        ttk.Label(self, text=ADVICE[key], wraplength=215, font=('Segoe UI', 9), style='Muted.TLabel').pack(side='left')
        self.update_value('')

    def update_value(self, value, available=True):
        self.canvas.delete('all')
        level = impact(self.key, value) if available else None
        if level is None:
            self.canvas.create_text(38,14,text='—',fill='#8291a0')
            return
        color = '#b45e36' if level >= 4 else '#007f79'
        for i in range(5):
            x = i*15+1
            self.canvas.create_rectangle(x,7,x+11,21,outline='#96a7b6',fill=color if i<level else 'white')
            self.canvas.create_rectangle(x+3,4,x+8,7,outline='#96a7b6',fill='#96a7b6')
