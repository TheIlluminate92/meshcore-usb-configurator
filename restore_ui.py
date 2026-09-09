"""Explicit, identity-bound restore into the editor, followed by normal review."""
import tkinter as tk
from tkinter import ttk, messagebox
from device import read_device
from restore import backups, restore_document
from model import display


def open_restore(app, folder):
    if app.busy:
        raise ValueError('Wait for the current operation to finish.')
    if app.snapshot is None:
        raise ValueError('Read the radio you want to restore first.')
    found, unreadable = backups(folder, app.snapshot['self_info'].get('public_key'))
    if not found:
        raise ValueError('No previous changes are saved for this radio.' + (' Some report files could not be read.' if unreadable else ''))
    window=tk.Toplevel(app.root);window.title('Restore previous settings');window.geometry('840x450');window.transient(app.root);window.grab_set()
    frame=ttk.Frame(window,padding=16);frame.pack(fill='both',expand=True)
    ttk.Label(frame,text='Choose the operation to undo. The same radio will be reread before its old values fill the editor.',wraplength=790).pack(anchor='w',pady=(0,10))
    tree=ttk.Treeview(frame,columns=('time','fields','channels','result'),show='headings',selectmode='browse',height=9)
    for k,t,w in [('time','Before operation',310),('fields','Settings',80),('channels','Channels',80),('result','Original result',190)]:tree.heading(k,text=t);tree.column(k,width=w)
    tree.pack(fill='both',expand=True)
    for i,(path,data) in enumerate(found):tree.insert('','end',iid=str(i),values=(data['before'].get('captured_at',path.stem),len(data.get('requested',{})),len(data.get('channels_requested',[])),'Verified' if data.get('verified') else 'Incomplete / unverified'))
    tree.selection_set('0')
    ttk.Label(frame,text='Only values changed by that operation are restored. This is not a full flash backup. Review & apply is still required.'+(' Unreadable reports were skipped.' if unreadable else ''),wraplength=790).pack(anchor='w',pady=10)
    def load():
        if not tree.selection():return
        if not app.confirm_discard():return
        report=found[int(tree.selection()[0])][1]
        port=app.selected_port()
        window.destroy()
        def done(snapshot):
            document=restore_document(report,snapshot)
            app.read_done(snapshot)
            for k,v in document['settings'].items():app.variables[k].set(display(k,v))
            for c in document['channels']:
                n,s=app.channel_vars[c['index']];n.set(c['name']);s.set(c['secret'])
            app.profile_page.master.select(0)
            app.status.set('Previous values loaded. Review & apply to restore them; nothing has been written.')
        app.run(read_device(port),done,'Rereading the original radio before restore…')
    ttk.Button(frame,text='Reread & load previous values',command=load).pack(anchor='e')
