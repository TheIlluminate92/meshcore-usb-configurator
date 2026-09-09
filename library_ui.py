"""Named profile library and explicit field-selection dialog."""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from pathlib import Path
from model import FIELDS, display, load_document, profile
from device import save_json
from profile_library import ProfileLibrary, PERSONAL

class LibraryPage(ttk.Frame):
    def __init__(self, parent, app, folder):
        super().__init__(parent,padding=16)
        self.app=app
        self.library=ProfileLibrary(folder)
        ttk.Label(self,text='Saved profiles',font=('Segoe UI',16,'bold')).pack(anchor='w')
        ttk.Label(self,text='Reusable settings saved on this PC. Loading fills the editor; applying always requires review.').pack(anchor='w',pady=(6,12))
        self.list=ttk.Treeview(self,columns=('name','settings','channels'),show='headings',height=7,selectmode='browse')
        for key,label,width in [('name','Profile',380),('settings','Settings',100),('channels','Channel slots',110)]:
            self.list.heading(key,text=label);self.list.column(key,width=width)
        self.list.pack(fill='both',expand=True)
        self.list.bind('<<TreeviewSelect>>',lambda _:self.describe())
        self.info=tk.StringVar()
        ttk.Label(self,textvariable=self.info,wraplength=1020,style='Muted.TLabel').pack(anchor='w',pady=8)
        row=ttk.Frame(self);row.pack(fill='x',pady=8)
        for title,fn in [('Save editor…',self.save_editor),('Update…',self.update_editor),('Load into editor',self.load_editor),('Import…',self.import_file),('Export…',self.export),('Rename',self.rename),('Remove',self.remove)]:
            ttk.Button(row,text=title,command=lambda f=fn:self.guarded(f)).pack(side='left',padx=(0,6))
        ttk.Button(self,text='Apply profile to multiple devices…',style='Primary.TButton',command=lambda:self.guarded(self.batch)).pack(anchor='w',pady=(4,0))
        self.refresh()

    def guarded(self, action):
        if self.app.busy:
            messagebox.showinfo('Operation in progress','Wait for the current device operation to finish.');return
        try: action()
        except Exception as exc: messagebox.showerror('Saved profiles',str(exc))

    def refresh(self, selected=None):
        entries,errors=self.library.entries()
        self.entries={e['id']:e for e in entries}
        self.list.delete(*self.list.get_children())
        for e in entries:self.list.insert('', 'end',iid=e['id'],values=(e['name'],len(e['settings']),len(e['channels'])))
        if selected in self.entries:self.list.selection_set(selected)
        self.info.set('Unreadable profile files left untouched: '+', '.join(errors) if errors else 'Select a profile, or save the current editor as your first profile.')

    def selected(self):
        selection=self.list.selection()
        if not selection:raise ValueError('Select a saved profile first.')
        return self.entries[selection[0]]

    def describe(self):
        if not self.list.selection():return
        e=self.selected()
        self.info.set('Includes: '+', '.join(FIELDS[k][0] for k in e['settings'])+f". Channel slots: {[c['index'] for c in e['channels']]}. Keys stay hidden.")

    def choose_scope(self, settings, channels, suggested='', existing=None):
        dialog=tk.Toplevel(self);dialog.title('Save reusable profile');dialog.transient(self.app.root);dialog.grab_set()
        frame=ttk.Frame(dialog,padding=16);frame.pack(fill='both',expand=True)
        name=tk.StringVar(value=suggested)
        ttk.Label(frame,text='Profile name').grid(row=0,column=0,sticky='w')
        ttk.Entry(frame,textvariable=name,width=42).grid(row=0,column=1,sticky='ew',columnspan=2)
        ttk.Label(frame,text='Choose included settings. Unchecked values stay unchanged on each target.',wraplength=760).grid(row=1,column=0,columnspan=3,sticky='w',pady=10)
        fields={}
        for i,(key,value) in enumerate(settings.items()):
            variable=tk.BooleanVar(value=key in existing['settings'] if existing else key not in PERSONAL);fields[key]=variable
            ttk.Checkbutton(frame,text=FIELDS[key][0],variable=variable).grid(row=2+i//3,column=i%3,sticky='w',padx=(0,12),pady=4)
        row=3+(len(fields)+2)//3
        include=tk.BooleanVar(value=bool(existing['channels']) if existing else bool(channels))
        ttk.Checkbutton(frame,text=f"Include {len(channels)} channel slots (names and keys)",variable=include).grid(row=row,column=0,columnspan=3,sticky='w',pady=8)
        ttk.Label(frame,text='New profiles exclude names and coordinates by default. Saving the editor omits unchanged empty slots.',wraplength=760,style='Muted.TLabel').grid(row=row+1,column=0,columnspan=3,sticky='w')
        def save():
            try: ident=self.library.save(name.get(),{k:v for k,v in settings.items() if fields[k].get()},channels if include.get() else [],existing['id'] if existing else None)
            except Exception as exc:messagebox.showerror('Could not save',str(exc),parent=dialog);return
            self.refresh(ident);dialog.destroy()
        ttk.Button(frame,text='Save profile',command=save).grid(row=row+2,column=2,sticky='e',pady=(12,0))

    def save_editor(self, existing=None):
        settings=self.app.desired()
        old={c['index']:c for c in self.app.snapshot.get('channels',[])}
        desired_channels=self.app.desired_channels()
        if existing:
            missing=set(existing['settings'])-set(settings)
            slots={c['index'] for c in existing['channels']}
            if missing or slots-set(old):
                raise ValueError('This editor did not read every field/slot in the saved profile. Read a compatible device before updating it, or save a new profile.')
            channels=[c for c in desired_channels if c['index'] in slots]
        else:
            channels=[c for c in desired_channels if c['name'] or c['secret']!='00'*16 or c!=old[c['index']]]
        self.choose_scope(settings,channels,existing['name'] if existing else '',existing)

    def update_editor(self):
        self.save_editor(self.selected())

    def import_file(self):
        path=filedialog.askopenfilename(filetypes=[('JSON profiles','*.json')])
        if not path:return
        settings,channels,warnings=load_document(Path(path))
        if warnings:messagebox.showinfo('Import notes','\n'.join(warnings))
        self.choose_scope(settings,channels,Path(path).stem[:80])

    def load_editor(self):
        if self.app.snapshot is None:raise ValueError('Read a device before loading the editor.')
        from batch import plan_device
        e=self.selected();plan_device(self.app.snapshot,e)
        for k,v in e['settings'].items():self.app.variables[k].set(display(k,v))
        for c in e['channels']:
            n,s=self.app.channel_vars[c['index']];n.set(c['name']);s.set(c['secret'])
        self.app.status.set('Saved profile loaded. Review the editor before applying.')
        self.master.select(0)

    def export(self):
        e=self.selected();path=filedialog.asksaveasfilename(defaultextension='.json',filetypes=[('JSON profiles','*.json')])
        if path:save_json(path,profile(e['settings'],e['channels']))

    def rename(self):
        e=self.selected();name=simpledialog.askstring('Rename profile','Profile name:',initialvalue=e['name'],parent=self)
        if name is not None:self.refresh(self.library.save(name,e['settings'],e['channels'],e['id']))

    def remove(self):
        e=self.selected()
        if messagebox.askyesno('Remove saved profile',f"Remove {e['name']} from the library? A local archive copy will be kept."):
            self.library.archive(e['id']);self.refresh()

    def batch(self):
        from batch_ui import BatchWindow
        BatchWindow(self.app,self.selected())
