"""Desktop entry point. All serial work runs off the Tk event loop."""
import asyncio
from datetime import datetime
from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
from model import FIELDS, CHOICES, EDITABLE_CHOICES, OTHER, AUTO, validate, validate_channels, load_document, profile, changes, display, parse_input
from device import serial_ports, read_device, apply_device, save_json
from help_text import HELP
from tooltips import Tooltip, help_label

ROOT = Path(__file__).resolve().parent

class App:
    def __init__(self, root):
        self.root, self.snapshot, self.busy = root, None, False
        self.results = queue.Queue()
        root.title('MeshCore USB Configurator — Expanded settings')
        root.geometry('1000x740')
        root.minsize(850, 650)
        style = ttk.Style()
        if 'vista' in style.theme_names():
            style.theme_use('vista')
        style.configure('TLabel', font=('Segoe UI', 10))
        outer = ttk.Frame(root, padding=18)
        outer.pack(fill='both', expand=True)
        ttk.Label(outer, text='MeshCore USB Configurator', font=('Segoe UI', 20, 'bold')).pack(anchor='w')
        ttk.Label(outer, text='Read a device • Edit a profile • Review changes • Write and verify').pack(anchor='w', pady=(3, 14))
        row = ttk.Frame(outer)
        row.pack(fill='x')
        self.port = tk.StringVar()
        self.port_box = ttk.Combobox(row, textvariable=self.port, width=43, state='readonly')
        self.port_box.pack(side='left')
        Tooltip(self.port_box, 'USB serial port', HELP['port'])
        help_label(row, 'USB', HELP['port']).pack(side='left')
        self.port_box.bind('<<ComboboxSelected>>', lambda _: self.invalidate())
        self.buttons = []
        self.button(row, 'Refresh ports', self.scan)
        self.button(row, 'Read device', self.read)
        self.identity = tk.StringVar(value='No device read. Connect a Companion USB device, then select its port.')
        ttk.Label(outer, textvariable=self.identity, wraplength=930).pack(anchor='w', pady=12)
        notebook = ttk.Notebook(outer)
        notebook.pack(fill='both', expand=True)
        self.variables, self.entries, self.current = {}, {}, {}
        groups = {
            'Device & radio': ('name', 'frequency', 'bandwidth', 'spreading_factor', 'coding_rate', 'tx_power', 'path_hash_mode', 'multi_acks'),
            'Location & GPS': ('gps', 'gps_interval', 'latitude', 'longitude', 'advert_location_policy'),
            'Contact discovery': ('manual_add_contacts',) + AUTO,
            'Telemetry': ('telemetry_mode_base', 'telemetry_mode_loc', 'telemetry_mode_env'),
        }
        notes = {
            'Device & radio': 'Choose US/Canada or EU/UK frequency suggestions, or type a custom MHz value. Frequency selection changes frequency only; bandwidth, spreading factor and coding rate must also match your network. Bandwidth accepts dropdown choices or custom kHz values. Repeat mode is preserved.',
            'Location & GPS': 'Fixed coordinates require GPS to be off. GPS options depend on the hardware and firmware. Location sharing in adverts and telemetry access are separate settings.',
            'Contact discovery': '“Automatically add all types” overrides the individual type filters. Use selected types/manual mode to apply them. With all type filters off, contacts are added manually. The hop limit still applies.',
            'Telemetry': '“Allowed contacts only” uses each contact’s telemetry permission flags. Allowing location telemetry is separate from including location in adverts.',
        }
        for title, keys in groups.items():
            editor = ttk.Frame(notebook, padding=12)
            notebook.add(editor, text=title)
            for column, label in enumerate(('Setting', 'Device value', 'Profile value')):
                heading = ttk.Label(editor, text=label, font=('Segoe UI', 10, 'bold'))
                heading.grid(row=0, column=column, sticky='w')
                if column:
                    Tooltip(heading, label, HELP['device_value' if column == 1 else 'profile_value'])
            for index, key in enumerate(keys, 1):
                help_label(editor, FIELDS[key][0], HELP[key]).grid(row=index, column=0, sticky='w', padx=(0, 12), pady=8)
                current = tk.StringVar(value='Not read')
                ttk.Label(editor, textvariable=current, width=30).grid(row=index, column=1, sticky='w')
                variable = tk.StringVar()
                if key in CHOICES:
                    entry = ttk.Combobox(editor, textvariable=variable, values=list(CHOICES[key].values()), width=30, state='disabled')
                else:
                    entry = ttk.Entry(editor, textvariable=variable, width=30, state='disabled')
                entry.grid(row=index, column=2, sticky='ew')
                Tooltip(entry, FIELDS[key][0], HELP[key])
                self.variables[key], self.entries[key], self.current[key] = variable, entry, current
            editor.columnconfigure(2, weight=1)
            ttk.Label(editor, text=notes[title], wraplength=890).grid(row=len(keys)+1, column=0, columnspan=3, sticky='w', pady=15)
        self.channel_page = ttk.Frame(notebook, padding=12)
        notebook.add(self.channel_page, text='Channels')
        ttk.Label(self.channel_page, text='Edit existing numbered slots. Keys are hexadecimal and hidden. Empty name with a zero key clears a slot.\nOnly changed slots are written. Browser exports map channels by list order; review the slot assignments.', wraplength=890).pack(anchor='w', pady=(0, 10))
        self.channel_canvas = tk.Canvas(self.channel_page, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.channel_page, orient='vertical', command=self.channel_canvas.yview)
        scrollbar.pack(side='right', fill='y')
        self.channel_canvas.pack(fill='both', expand=True)
        self.channel_canvas.configure(yscrollcommand=scrollbar.set)
        self.channel_rows = ttk.Frame(self.channel_canvas)
        window = self.channel_canvas.create_window((0, 0), window=self.channel_rows, anchor='nw')
        self.channel_canvas.bind('<Configure>', lambda e: self.channel_canvas.itemconfigure(window, width=e.width))
        self.channel_rows.bind('<Configure>', lambda e: self.channel_canvas.configure(scrollregion=self.channel_canvas.bbox('all')))
        self.channel_vars, self.channel_entries = {}, []
        self.variables['gps'].trace_add('write', lambda *_: self.location_state())
        self.details = tk.Text(notebook, wrap='none', font=('Consolas', 10))
        notebook.add(self.details, text='Reported data (read only)')
        actions = ttk.Frame(outer)
        actions.pack(fill='x', pady=12)
        self.button(actions, 'Load JSON profile', self.load)
        self.button(actions, 'Save JSON profile', self.save)
        self.button(actions, 'Save device snapshot', self.save_snapshot)
        self.button(actions, 'Review & apply', self.apply)
        self.status = tk.StringVar(value='Ready. No configuration has been written.')
        ttk.Label(outer, textvariable=self.status, wraplength=930).pack(anchor='w')
        root.protocol('WM_DELETE_WINDOW', self.close)
        root.after(100, self.poll)
        self.scan()

    def button(self, frame, text, command):
        def guarded():
            try:
                command()
            except Exception as exc:
                messagebox.showerror('MeshCore Configurator', str(exc))
        b = ttk.Button(frame, text=text, command=guarded)
        b.pack(side='left', padx=(8, 0))
        self.buttons.append(b)
        if text in HELP:
            Tooltip(b, text, HELP[text])

    def scan(self):
        old = self.port.get()
        ports = [f'{p} | {desc}' for p, desc in serial_ports()]
        self.port_box['values'] = ports
        if old not in ports:
            self.port.set(next((p for p in ports if 'USB' in p.upper()), ports[0] if ports else ''))
            self.invalidate()
        self.status.set(f'{len(ports)} serial port(s) found. Select the USB device and read it.')

    def invalidate(self):
        self.snapshot = None
        self.identity.set('Read this port to identify the device and enable supported settings.')
        for key, entry in self.entries.items():
            entry.configure(state='disabled')
            self.current[key].set('—')
            self.variables[key].set('')
        self.show_channels([])

    def show_channels(self, channels):
        for widget in self.channel_rows.winfo_children():
            widget.destroy()
        self.channel_vars, self.channel_entries = {}, []
        for col, label in enumerate(('Slot', 'Device channel', 'Profile channel name', 'Profile key (hidden)')):
            key = ('channel_slot', 'channel_current', 'channel_name', 'channel_secret')[col]
            help_label(self.channel_rows, label, HELP[key]).grid(row=0, column=col, sticky='w', padx=5)
        for row, channel in enumerate(channels, 1):
            index = channel['index']
            ttk.Label(self.channel_rows, text=str(index)).grid(row=row, column=0, padx=5, pady=7)
            ttk.Label(self.channel_rows, text=channel['name'] or '(empty)', width=22).grid(row=row, column=1, sticky='w')
            name, secret = tk.StringVar(value=channel['name']), tk.StringVar(value=channel['secret'])
            for col, variable in ((2, name), (3, secret)):
                entry = ttk.Entry(self.channel_rows, textvariable=variable, width=28, show='*' if col == 3 else '')
                entry.grid(row=row, column=col, padx=5, sticky='ew')
                Tooltip(entry, 'Channel name' if col == 2 else 'Channel key', HELP['channel_name' if col == 2 else 'channel_secret'])
                self.channel_entries.append(entry)
            self.channel_vars[index] = (name, secret)
        if not channels:
            ttk.Label(self.channel_rows, text='No successfully read channel slots. Read the device to populate this tab.').grid(row=1, column=0, columnspan=4, pady=15)

    def desired_channels(self):
        return validate_channels([{'index': i, 'name': n.get(), 'secret': s.get()} for i, (n, s) in self.channel_vars.items()])

    def location_state(self):
        if self.snapshot is None or self.busy:
            return
        gps_on = parse_input('gps', self.variables['gps'].get()) == 1
        for key in ('latitude', 'longitude'):
            self.entries[key].configure(state='disabled' if gps_on or key not in self.snapshot['settings'] else 'normal')

    def selected_port(self):
        if not self.port.get():
            raise ValueError('No serial port selected. Connect the device and refresh ports.')
        return self.port.get().split(' | ')[0]

    def run(self, operation, callback, label):
        self.busy = True
        for b in self.buttons:
            b.configure(state='disabled')
        self.port_box.configure(state='disabled')
        for e in self.entries.values():
            e.configure(state='disabled')
        for e in self.channel_entries:
            e.configure(state='disabled')
        self.status.set(label)
        def worker():
            try:
                self.results.put((callback, asyncio.run(operation), None))
            except Exception as exc:
                self.results.put((callback, None, str(exc)))
        threading.Thread(target=worker, daemon=True).start()

    def poll(self):
        try:
            callback, result, error = self.results.get_nowait()
        except queue.Empty:
            pass
        else:
            self.busy = False
            for b in self.buttons:
                b.configure(state='normal')
            self.port_box.configure(state='readonly')
            if error:
                self.invalidate()
                self.status.set('Operation failed. Read again before applying changes.')
                messagebox.showerror('Device operation failed', error)
            else:
                try:
                    callback(result)
                except Exception as exc:
                    self.invalidate()
                    messagebox.showerror('Could not save or display result', str(exc))
        self.root.after(100, self.poll)

    def read(self):
        self.run(read_device(self.selected_port()), self.read_done, 'Reading settings, channels and contacts…')

    def show(self, snapshot):
        self.snapshot = snapshot
        info = snapshot['device']
        self.identity.set(f"{snapshot['settings'].get('name', '?')} | {info.get('model', 'Unknown model')} | Firmware {info.get('ver', '?')} | {snapshot['port']}")
        for key, entry in self.entries.items():
            supported = key in snapshot['settings']
            value = display(key, snapshot['settings'][key]) if supported else ''
            self.variables[key].set(value)
            self.current[key].set(value if supported else 'Not reported')
            entry.configure(state=('readonly' if key in CHOICES and key not in EDITABLE_CHOICES else 'normal') if supported else 'disabled')
        self.show_channels(snapshot.get('channels', []))
        self.location_state()
        self.details.configure(state='normal')
        self.details.delete('1.0', 'end')
        self.details.insert('1.0', json.dumps(snapshot, indent=2, default=str))
        self.details.configure(state='disabled')

    def read_done(self, snapshot):
        self.show(snapshot)
        path = ROOT / 'snapshots' / (datetime.now().strftime('%Y%m%d-%H%M%S-%f') + '.json')
        save_json(path, snapshot)
        errors = snapshot.get('read_errors', {})
        self.status.set(f"Read complete; snapshot saved. {'Some optional reads failed; see reported data.' if errors else 'Ready to edit.'}")

    def desired(self):
        if self.snapshot is None:
            raise ValueError('Read the connected device first.')
        return validate({k: parse_input(k, self.variables[k].get()) for k in self.snapshot['settings']},
                        self.snapshot['self_info'].get('max_tx_power', 0))

    def load(self):
        if self.snapshot is None:
            raise ValueError('Read the device first so supported options can be checked.')
        path = filedialog.askopenfilename(filetypes=[('JSON profiles', '*.json')])
        if path:
            settings, channels, warnings = load_document(Path(path))
            unsupported = set(settings) - self.snapshot['settings'].keys()
            if unsupported:
                warnings.append('Unavailable settings skipped: ' + ', '.join(FIELDS[k][0] for k in sorted(unsupported)))
                settings = {k: v for k, v in settings.items() if k not in unsupported}
            unavailable_slots = [c['index'] for c in channels if c['index'] not in self.channel_vars]
            if unavailable_slots:
                raise ValueError(f'Channel slots not reported by this device: {unavailable_slots}')
            validate(settings, self.snapshot['self_info'].get('max_tx_power', 0))
            for key, value in settings.items():
                self.variables[key].set(display(key, value))
            for c in channels:
                n, s = self.channel_vars[c['index']]
                n.set(c['name'])
                s.set(c['secret'])
            self.status.set('Profile loaded into editor. Nothing written. Review device and profile values before applying.')
            if warnings:
                messagebox.showinfo('Profile import notes', '\n\n'.join(warnings))

    def save(self):
        data = profile(self.desired(), self.desired_channels())
        path = filedialog.asksaveasfilename(defaultextension='.json', filetypes=[('JSON profiles', '*.json')])
        if path:
            save_json(path, data)
            self.status.set('JSON profile saved.')

    def save_snapshot(self):
        if self.snapshot is None:
            raise ValueError('Read the device first.')
        path = filedialog.asksaveasfilename(defaultextension='.json', filetypes=[('JSON snapshots', '*.json')])
        if path:
            save_json(path, self.snapshot)

    def apply(self):
        desired = self.desired()
        delta = changes(self.snapshot['settings'], desired)
        previous = {c['index']: c for c in self.snapshot.get('channels', [])}
        channel_delta = [c for c in self.desired_channels() if c != previous[c['index']]]
        if not delta and not channel_delta:
            self.status.set('No changes to apply.')
            return
        review = '\n'.join(f'{FIELDS[k][0]}: {display(k, self.snapshot["settings"][k])} → {display(k, v)}' for k, v in delta.items())
        for c in channel_delta:
            key_changed = c['secret'] != previous[c['index']]['secret']
            review += f"\nChannel {c['index']}: {previous[c['index']]['name'] or '(empty)'} → {c['name'] or '(empty)'}" + (' (key changes)' if key_changed else '')
        if messagebox.askokcancel('Apply these changes?', f'{self.identity.get()}\n\n{review}\n\nWrite these settings and verify by rereading?'):
            def done(result):
                self.show(result)
                self.status.set('Verified: all requested values match the device. Apply report saved.')
            self.run(apply_device(self.selected_port(), self.snapshot, delta, ROOT / 'reports', channel_delta), done, 'Writing settings and verifying…')

    def close(self):
        if self.busy:
            messagebox.showinfo('Operation in progress', 'Wait for the device operation to finish before closing.')
        else:
            self.root.destroy()

if __name__ == '__main__':
    root = tk.Tk()
    App(root)
    root.mainloop()
