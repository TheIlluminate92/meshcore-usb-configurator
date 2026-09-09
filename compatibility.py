"""Per-radio compatibility review; unavailable fields block rather than silently skip."""
from model import FIELDS, validate, equal


def check_role(document):
    role = document.get('target_role', 'companion')
    if role != 'companion':
        raise ValueError('Repeater and Room Server setup references require their separate firmware and CLI interface. This version writes Companion firmware only.')


def review(snapshot, document):
    from batch import plan_device
    rows = []
    for key, value in document.get('settings', {}).items():
        label = FIELDS[key][0] if key in FIELDS else 'Unknown setting'
        if key not in snapshot.get('settings', {}):
            status = 'Blocked: not reported'
        else:
            try:
                validate({key:value}, snapshot.get('self_info', {}).get('max_tx_power',0))
                status = 'Unchanged' if equal(key,snapshot['settings'][key],value) else 'Will change'
            except ValueError:
                status = 'Blocked: outside supported limits'
        rows.append((label,status))
    slots = {c['index']:c for c in snapshot.get('channels', [])}
    for c in document.get('channels', []):
        status = 'Blocked: slot not read' if c['index'] not in slots else 'Unchanged' if c == slots[c['index']] else 'Will change (key hidden)'
        rows.append((f"Channel {c['index']}",status))
    try:
        plan_device(snapshot, document)
        blocked = None
    except ValueError as exc:
        blocked = str(exc)
    return rows, blocked


def text(snapshots, document):
    lines = ['Compatibility review', 'Unavailable or invalid items block applying; nothing is silently skipped.', '']
    for s in snapshots:
        rows, blocked = review(s, document)
        d = s.get('device', {})
        lines.append(f"{s.get('settings',{}).get('name','Radio')} / {s.get('port','?')} / {d.get('model','Unknown board')}")
        lines.append('BLOCKED: '+blocked if blocked else 'Compatible with the reported capabilities')
        lines.extend('  '+label+': '+status for label,status in rows)
        lines.append('')
    return '\n'.join(lines)


def show(parent, snapshots, document):
    import tkinter as tk
    from tkinter import ttk
    window = tk.Toplevel(parent); window.title('Profile compatibility'); window.geometry('850x560'); window.transient(parent)
    frame=ttk.Frame(window,padding=14);frame.pack(fill='both',expand=True)
    area=tk.Text(frame,wrap='word',font=('Consolas',10))
    scroll=ttk.Scrollbar(frame,command=area.yview);area.configure(yscrollcommand=scroll.set)
    scroll.pack(side='right',fill='y');area.pack(fill='both',expand=True)
    area.insert('1.0',text(snapshots,document));area.configure(state='disabled')
