"""Named profile library and explicit field-selection dialog."""
from diagnostics import record_error
import tkinter as tk
import json
from tkinter import ttk, messagebox, filedialog, simpledialog
from pathlib import Path
from model import FIELDS, display, load_document, profile, validate_naming
from device import save_json
from profile_library import ProfileLibrary, PERSONAL

class LibraryPage(ttk.Frame):
    def __init__(self, parent, app, folder):
        super().__init__(parent,padding=16)
        self.app=app
        self.library=ProfileLibrary(folder, include_builtin=True)
        ttk.Label(self,text='Saved profiles',font=('Segoe UI',16,'bold')).pack(anchor='w')
        ttk.Label(self,text='Reusable settings saved on this PC. Loading fills the editor; applying always requires review.').pack(anchor='w',pady=(6,12))
        self.list=ttk.Treeview(self,columns=('name','settings','channels'),show='headings',height=7,selectmode='browse')
        for key,label,width in [('name','Profile',380),('settings','Settings',100),('channels','Channel slots',110)]:
            self.list.heading(key,text=label);self.list.column(key,width=width)
        self.list.pack(fill='both',expand=True)
        self.list.bind('<<TreeviewSelect>>',lambda _:self.describe())
        self.list.bind('<Double-1>',lambda _:self.guarded(self.preview))
        self.info=tk.StringVar()
        ttk.Label(self,textvariable=self.info,wraplength=1020,style='Muted.TLabel').pack(anchor='w',pady=8)
        row=ttk.Frame(self);row.pack(fill='x',pady=8)
        for index,(title,fn) in enumerate([('Preview',self.preview),('Notes…',self.edit_notes),('Compatibility',self.compatibility),('Save editor…',self.save_editor),('Update…',self.update_editor),('Load into editor',self.load_editor),('Import…',self.import_file),('Export…',self.export),('Rename',self.rename),('Remove',self.remove)]):
            ttk.Button(row,text=title,command=lambda f=fn:self.guarded(f)).grid(row=index//5,column=index%5,sticky='w',padx=(0,6),pady=3)
        ttk.Button(self,text='Apply profile to multiple devices…',style='Primary.TButton',command=lambda:self.guarded(self.batch)).pack(anchor='w',pady=(4,0))
        self.refresh()

    def guarded(self, action):
        if self.app.busy:
            messagebox.showinfo('Operation in progress','Wait for the current device operation to finish.');return
        try: action()
        except Exception as exc: record_error('profiles',exc);messagebox.showerror('Saved profiles',str(exc))

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
        self.info.set(e.get('description','')+(' Notes: '+e['notes'][:200] if e.get('notes') else '')+' Includes: '+', '.join(FIELDS[k][0] for k in e['settings'])+f". Channel slots: {[c['index'] for c in e['channels']]}. Keys stay hidden.")

    def edit_notes(self):
        e=self.selected();self.editable(e)
        window=tk.Toplevel(self);window.title('Profile notes');window.transient(self.app.root);window.grab_set()
        frame=ttk.Frame(window,padding=16);frame.pack(fill='both',expand=True)
        ttk.Label(frame,text='Your notes: network, intended use, hardware, or anything useful. Up to 4000 characters.').pack(anchor='w')
        box=tk.Text(frame,width=75,height=9,wrap='word');box.pack(fill='both',expand=True,pady=8);box.insert('1.0',e.get('notes',''))
        def save():
            try:ident=self.library.save(e['name'],e['settings'],e['channels'],e['id'],notes=box.get('1.0','end-1c'))
            except Exception as exc:messagebox.showerror('Profile notes',str(exc),parent=window);return
            self.refresh(ident);window.destroy()
        ttk.Button(frame,text='Save notes',command=save).pack(anchor='e')

    def preview(self):
        from compare_ui import preview
        preview(self.app.root,self.selected())

    def compare(self):
        if self.app.snapshot is None:raise ValueError('Read a radio before comparing it with a profile.')
        from compare_ui import compare
        compare(self.app.root,[self.app.snapshot],self.selected())

    def compatibility(self):
        if self.app.snapshot is None:raise ValueError('Read a radio before checking compatibility.')
        from compatibility import show
        show(self.app.root,[self.app.snapshot],self.selected())

    def editable(self, entry):
        if entry.get('builtin'):raise ValueError('Built-in profiles are read-only. Load the Companion preset and use Save editor to make your own copy; server presets are setup references.')

    def choose_scope(self, settings, channels, suggested='', existing=None, naming=None, notes=None):
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
        template=validate_naming(existing.get('naming') if existing else naming)
        prefix=tk.StringVar(value=template['prefix']);start=tk.StringVar(value=str(template['start']))
        naming_row=ttk.Frame(frame);naming_row.grid(row=row+2,column=0,columnspan=3,sticky='w',pady=8)
        ttk.Label(naming_row,text='Naming prefix:').pack(side='left')
        ttk.Entry(naming_row,textvariable=prefix,width=20).pack(side='left',padx=8)
        ttk.Label(naming_row,text='Start at:').pack(side='left')
        ttk.Spinbox(naming_row,from_=1,to=999999,textvariable=start,width=7).pack(side='left',padx=8)
        ttk.Label(frame,text='Your notes (network, purpose, hardware; 4000 characters)').grid(row=row+3,column=0,columnspan=3,sticky='w')
        notes_box=tk.Text(frame,height=3,width=70,wrap='word');notes_box.grid(row=row+4,column=0,columnspan=3,sticky='ew')
        notes_box.insert('1.0',existing.get('notes','') if existing else notes or '')
        def save():
            try: ident=self.library.save(name.get(),{k:v for k,v in settings.items() if fields[k].get()},channels if include.get() else [],existing['id'] if existing else None,{'prefix':prefix.get(),'start':int(start.get())},notes=notes_box.get('1.0','end-1c'))
            except Exception as exc:record_error('profiles',exc);messagebox.showerror('Could not save',str(exc),parent=dialog);return
            self.refresh(ident);dialog.destroy()
        ttk.Button(frame,text='Save profile',command=save).grid(row=row+5,column=2,sticky='e',pady=(12,0))

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
        entry=self.selected();self.editable(entry);self.save_editor(entry)

    def import_file(self):
        path=filedialog.askopenfilename(filetypes=[('JSON profiles','*.json')])
        if not path:return
        settings,channels,warnings=load_document(Path(path))
        if warnings:messagebox.showinfo('Import notes','\n'.join(warnings))
        data=json.loads(Path(path).read_text(encoding='utf-8-sig'))
        self.choose_scope(settings,channels,data.get('profile_name',Path(path).stem[:80]),naming=validate_naming(data.get('naming')),notes=data.get('notes',''))

    def load_editor(self):
        if self.app.snapshot is None:raise ValueError('Read a device before loading the editor.')
        if not self.app.confirm_discard():return
        from batch import plan_device
        e=self.selected();plan_device(self.app.snapshot,e)
        self.app.show(self.app.snapshot)
        for k,v in e['settings'].items():self.app.variables[k].set(display(k,v))
        for c in e['channels']:
            n,s=self.app.channel_vars[c['index']];n.set(c['name']);s.set(c['secret'])
        self.app.status.set('Saved profile loaded. Review the editor before applying.')
        self.master.select(0)

    def export(self):
        e=self.selected();path=filedialog.asksaveasfilename(defaultextension='.json',filetypes=[('JSON profiles','*.json')])
        if path:
            data=profile(e['settings'],e['channels']);data.update(naming=e['naming'],profile_name=e['name'],target_role=e.get('target_role','companion'))
            for key in ('description','cli_settings','advice','source','notes'):
                if key in e:data[key]=e[key]
            save_json(path,data)

    def rename(self):
        e=self.selected();self.editable(e);name=simpledialog.askstring('Rename profile','Profile name:',initialvalue=e['name'],parent=self)
        if name is not None:self.refresh(self.library.save(name,e['settings'],e['channels'],e['id']))

    def remove(self):
        e=self.selected();self.editable(e)
        if messagebox.askyesno('Remove saved profile',f"Remove {e['name']} from the library? A local archive copy will be kept."):
            self.library.archive(e['id']);self.refresh()

    def batch(self):
        if not self.app.confirm_discard():return
        if self.app.snapshot is not None:self.app.show(self.app.snapshot)
        from batch_ui import BatchWindow
        BatchWindow(self.app,self.selected())
