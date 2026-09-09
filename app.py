"""Desktop entry point. All serial work runs off the Tk event loop."""
import asyncio
from datetime import datetime
from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
from model import FIELDS, validate, load_profile, profile, changes
from device import serial_ports, read_device, apply_device, save_json

ROOT = Path(__file__).resolve().parent

class App:
    def __init__(self, root):
        self.root, self.snapshot, self.busy = root, None, False
        self.results = queue.Queue()
        root.title('MeshCore USB Configurator')
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
        self.port_box.bind('<<ComboboxSelected>>', lambda _: self.invalidate())
        self.buttons = []
        self.button(row, 'Refresh ports', self.scan)
        self.button(row, 'Read device', self.read)
        self.identity = tk.StringVar(value='No device read. Connect a Companion USB device, then select its port.')
        ttk.Label(outer, textvariable=self.identity, wraplength=930).pack(anchor='w', pady=12)
        notebook = ttk.Notebook(outer)
        notebook.pack(fill='both', expand=True)
        editor = ttk.Frame(notebook, padding=12)
        notebook.add(editor, text='Settings & profiles')
        self.details = tk.Text(notebook, wrap='none', font=('Consolas', 10))
        notebook.add(self.details, text='Reported data (read only)')
        self.variables, self.entries, self.current = {}, {}, {}
        ttk.Label(editor, text='Setting', font=('Segoe UI', 10, 'bold')).grid(row=0, column=0, sticky='w')
        ttk.Label(editor, text='Device value', font=('Segoe UI', 10, 'bold')).grid(row=0, column=1, sticky='w')
        ttk.Label(editor, text='Profile value', font=('Segoe UI', 10, 'bold')).grid(row=0, column=2, sticky='w')
        for index, (key, spec) in enumerate(FIELDS.items(), 1):
            ttk.Label(editor, text=spec[0]).grid(row=index, column=0, sticky='w', padx=(0, 30), pady=8)
            current = tk.StringVar(value='—')
            ttk.Label(editor, textvariable=current, width=24).grid(row=index, column=1, sticky='w')
            variable = tk.StringVar()
            entry = ttk.Entry(editor, textvariable=variable, width=30, state='disabled')
            entry.grid(row=index, column=2, sticky='ew')
            self.variables[key], self.entries[key], self.current[key] = variable, entry, current
        editor.columnconfigure(2, weight=1)
        ttk.Label(editor, text='Only implemented, reported options are editable. Radio values must match your local network.\nChannels, contacts and other settings are snapshot data in this first version.', wraplength=850).grid(row=9, column=0, columnspan=3, sticky='w', pady=12)
        actions = ttk.Frame(outer)
        actions.pack(fill='x', pady=12)
        self.button(actions, 'Load JSON profile', self.load)
        self.button(actions, 'Save JSON profile', self.save)
        self.button(actions, 'Save full snapshot', self.save_snapshot)
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
            value = str(snapshot['settings'].get(key, ''))
            self.variables[key].set(value)
            self.current[key].set(value if supported else 'Not reported')
            entry.configure(state='normal' if supported else 'disabled')
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
        return validate({k: self.variables[k].get() for k in self.snapshot['settings']},
                        self.snapshot['self_info'].get('max_tx_power', 0))

    def load(self):
        if self.snapshot is None:
            raise ValueError('Read the device first so supported options can be checked.')
        path = filedialog.askopenfilename(filetypes=[('JSON profiles', '*.json')])
        if path:
            settings = load_profile(Path(path))
            if set(settings) - self.snapshot['settings'].keys():
                raise ValueError('Profile contains options not reported by this device.')
            validate(settings, self.snapshot['self_info'].get('max_tx_power', 0))
            for key, value in settings.items():
                self.variables[key].set(str(value))
            self.status.set('Profile loaded into editor. Nothing written. Review device and profile values before applying.')

    def save(self):
        data = profile(self.desired())
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
        if not delta:
            self.status.set('No changes to apply.')
            return
        review = '\n'.join(f'{FIELDS[k][0]}: {self.snapshot["settings"][k]} → {v}' for k, v in delta.items())
        if messagebox.askokcancel('Apply these changes?', f'{self.identity.get()}\n\n{review}\n\nWrite these settings and verify by rereading?'):
            def done(result):
                self.show(result)
                self.status.set('Verified: all requested values match the device. Apply report saved.')
            self.run(apply_device(self.selected_port(), self.snapshot, desired, ROOT / 'reports'), done, 'Writing settings and verifying…')

    def close(self):
        if self.busy:
            messagebox.showinfo('Operation in progress', 'Wait for the device operation to finish before closing.')
        else:
            self.root.destroy()

if __name__ == '__main__':
    root = tk.Tk()
    App(root)
    root.mainloop()
