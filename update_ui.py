"""User initiated updates, outside radio operations."""
import os
import sys
import queue
import threading
import tkinter as tk
from tkinter import ttk,messagebox
from app_version import VERSION
from app_paths import DATA_ROOT
import updater

class UpdateWindow:
    def __init__(self,app):
        self.app=app;self.busy=False;self.release=None;self.results=queue.Queue()
        app.update_window=self
        self.window=tk.Toplevel(app.root);self.window.title('App updates');self.window.geometry('700x540');self.window.transient(app.root);self.window.grab_set()
        frame=ttk.Frame(self.window,padding=18);frame.pack(fill='both',expand=True)
        ttk.Label(frame,text='MeshCore Configurator '+VERSION,font=('Segoe UI',15,'bold')).pack(anchor='w')
        ttk.Label(frame,text='Updates replace only the app. Your portable User Data folder stays intact.',wraplength=560).pack(anchor='w',pady=10)
        ttk.Label(frame,text='Public GitHub releases — no sign-in required.').pack(anchor='w',pady=6)
        self.status=tk.StringVar(value='Check for a published release when you are ready.')
        ttk.Label(frame,textvariable=self.status,wraplength=560).pack(anchor='w',pady=12)
        ttk.Label(frame,text='What changed').pack(anchor='w')
        note_frame=ttk.Frame(frame);note_frame.pack(fill='both',expand=True,pady=8)
        self.notes=tk.Text(note_frame,height=10,wrap='word',state='disabled')
        note_scroll=ttk.Scrollbar(note_frame,command=self.notes.yview);note_scroll.pack(side='right',fill='y');self.notes.configure(yscrollcommand=note_scroll.set);self.notes.pack(fill='both',expand=True)
        bar=ttk.Frame(frame);bar.pack(fill='x')
        self.check_button=ttk.Button(bar,text='Check for updates',command=self.check);self.check_button.pack(side='left',padx=(0,8))
        self.install_button=ttk.Button(bar,text='Install & restart',command=self.install,state='disabled');self.install_button.pack(side='left')
        self.window.protocol('WM_DELETE_WINDOW',self.close);self.poll_id=self.window.after(100,self.poll)
    def work(self,fn):
        self.busy=True;self.check_button.configure(state='disabled');self.install_button.configure(state='disabled')
        def worker():
            try:self.results.put((fn(),None))
            except Exception as exc:
                from diagnostics import record_error
                record_error('update',exc)
                self.results.put((None,str(exc)))
        threading.Thread(target=worker,daemon=True).start()
    def check(self):
        if self.busy:return
        self.notes.configure(state='normal');self.notes.delete('1.0','end');self.notes.configure(state='disabled')
        self.release=None;self.status.set('Checking GitHub…');self.work(lambda:('check',updater.check()))
    def install(self):
        if self.busy or not self.release:return
        if not getattr(sys,'frozen',False):self.status.set('Run the portable EXE to install updates.');return
        if not self.app.confirm_discard():return
        if not messagebox.askokcancel('Install update?',f"Download {self.release['version']} and restart the app?",parent=self.window):return
        release=self.release;self.status.set('Downloading and verifying…')
        self.work(lambda:('install',updater.download(release,DATA_ROOT/'Updates')))
    def poll(self):
        try:
            result,error=self.results.get_nowait();self.busy=False;self.check_button.configure(state='normal')
            if error:
                self.status.set(error)
                if self.release:self.install_button.configure(state='normal')
            elif result[0]=='check':
                self.release=result[1];self.status.set('You have the latest release.' if not self.release else 'Available: '+self.release['version'])
                self.notes.configure(state='normal');self.notes.delete('1.0','end');self.notes.insert('1.0',self.release.get('notes','No release notes provided.') if self.release else 'No newer release available.');self.notes.configure(state='disabled')
                if self.release:self.install_button.configure(state='normal')
            else:
                try:updater.schedule_install(result[1],sys.executable,os.getpid(),self.release['asset']['digest'])
                except Exception as exc:self.status.set(str(exc))
                else:
                    self.close();self.app.pending_count=0;self.app.close();return
        except queue.Empty:pass
        self.poll_id=self.window.after(100,self.poll)
    def close(self):
        if self.busy:return
        self.window.after_cancel(self.poll_id);self.window.destroy();self.app.update_window=None
