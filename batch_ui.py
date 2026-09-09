"""Modal fleet workspace; only one device operation can run at a time."""
import asyncio
import copy
import queue
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from device import serial_ports, bluetooth_devices, read_device, save_json
from model import FIELDS, display
from batch import plan_many, apply_many

class BatchWindow:
    def __init__(self, app, document):
        self.app=app;self.document=copy.deepcopy(document)
        self.window=tk.Toplevel(app.root);self.window.title('Multiple devices — '+document['name'])
        self.window.geometry('1050x720');self.window.minsize(900,650)
        self.window.transient(app.root);self.window.grab_set()
        self.busy=False;self.cancel=threading.Event();self.queue=queue.Queue()
        app.batch_window=self
        self.targets={};self.snapshots={};self.plans=None;self.controls=[]
        self.window.protocol('WM_DELETE_WINDOW',self.close)
        f=ttk.Frame(self.window,padding=16);f.pack(fill='both',expand=True)
        ttk.Label(f,text='Profile: '+document['name'],font=('Segoe UI',16,'bold')).pack(anchor='w')
        ttk.Label(f,text='Select devices → Read selected → Review changes → Apply reviewed. USB and BLE use the same checks.').pack(anchor='w',pady=8)
        bar=ttk.Frame(f);bar.pack(fill='x')
        for title,fn in [('Find USB',self.find_usb),('Find Bluetooth',self.find_ble),('Select all',self.select_all),('Read selected',self.read_selected),('Review changes',self.review),('Apply reviewed',self.apply)]:
            b=ttk.Button(bar,text=title,command=lambda action=fn:self.guard(action));b.pack(side='left',padx=(0,5));self.controls.append(b)
            if title=='Apply reviewed':self.apply_button=b;b.configure(state='disabled')
        self.tree=ttk.Treeview(f,columns=('port','name','status'),show='headings',selectmode='extended',height=8)
        for key,label,width in [('port','Connection',200),('name','Device',220),('status','Status',480)]:
            self.tree.heading(key,text=label);self.tree.column(key,width=width)
        self.tree.pack(fill='both',expand=True,pady=12)
        self.tree.bind('<<TreeviewSelect>>',lambda _:self.invalidate_review())
        ttk.Label(f,text='Use Ctrl/Shift to select devices. Every selected device must pass review. A failed write stops the batch.').pack(anchor='w')
        details=ttk.Frame(f);details.pack(fill='both',expand=True,pady=8)
        self.details=tk.Text(details,height=10,wrap='word',font=('Consolas',10),state='disabled')
        scroll=ttk.Scrollbar(details,command=self.details.yview);self.details.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right',fill='y');self.details.pack(fill='both',expand=True)
        self.status=tk.StringVar(value='Find and select the devices you want to configure.')
        ttk.Label(f,textvariable=self.status,wraplength=980).pack(anchor='w')
        self.stop=ttk.Button(f,text='Stop after current device',command=self.cancel.set,state='disabled');self.stop.pack(anchor='e',pady=(8,0))
        self.poll_id=self.window.after(100,self.poll)
        self.find_usb()

    def guard(self,action):
        if self.busy:return
        try:action()
        except Exception as exc:messagebox.showerror('Multiple devices',str(exc),parent=self.window)

    def invalidate_review(self):
        self.plans=None
        self.apply_button.configure(state='disabled')

    def add_targets(self,targets):
        self.invalidate_review()
        for port,name in targets:
            if port in self.targets:continue
            ident=str(len(self.targets));self.targets[port]=ident
            self.tree.insert('','end',iid=ident,values=(port,name,'Not read'))

    def find_usb(self):self.add_targets(serial_ports())
    def find_ble(self):self.run(bluetooth_devices(),self.add_targets,'Scanning Bluetooth…')
    def select_all(self):self.tree.selection_set(self.tree.get_children())
    def selected(self):
        ports=[self.tree.item(i,'values')[0] for i in self.tree.selection()]
        if not ports:raise ValueError('Select at least one device.')
        return ports

    def update(self,port,status,name=None):
        i=self.targets[port];values=list(self.tree.item(i,'values'));values[2]=status
        if name is not None:values[1]=name
        self.tree.item(i,values=values)

    def run(self,operation,callback,status):
        self.busy=True;self.cancel.clear();self.status.set(status)
        for b in self.controls:b.configure(state='disabled')
        self.stop.configure(state='normal')
        def worker():
            try:self.queue.put(('done',callback,asyncio.run(operation),None))
            except Exception as exc:self.queue.put(('done',callback,None,str(exc)))
        threading.Thread(target=worker,daemon=True).start()

    def read_selected(self):
        ports=self.selected();self.invalidate_review()
        for p in ports:self.snapshots.pop(p,None)
        async def read():
            results={}
            for port in ports:
                if self.cancel.is_set():self.queue.put(('progress',port,'Not read — stopped'));continue
                self.queue.put(('progress',port,'Reading…'))
                try:
                    snapshot=await read_device(port)
                    save_json(self.app.profile_page.library.folder.parent/'snapshots'/('fleet-'+datetime.now().strftime('%Y%m%d-%H%M%S-%f')+'.json'),snapshot)
                    results[port]=snapshot
                    self.queue.put(('progress',port,'Read complete'))
                except Exception as exc:self.queue.put(('progress',port,'Read failed: '+str(exc)))
            return results
        def done(results):
            self.snapshots.update(results)
            for p,s in results.items():self.update(p,'Read complete',s['settings'].get('name','?'))
            self.status.set(f'{len(results)} of {len(ports)} devices read. Review the selected devices next.')
        self.run(read(),done,'Reading selected devices…')

    def set_details(self,text):
        self.details.configure(state='normal');self.details.delete('1.0','end');self.details.insert('1.0',text);self.details.configure(state='disabled')

    def review(self):
        self.invalidate_review();ports=self.selected()
        missing=[p for p in ports if p not in self.snapshots]
        if missing:raise ValueError('Read these devices first: '+', '.join(missing))
        errors=[]
        from batch import plan_device
        for p in ports:
            try:plan_device(self.snapshots[p],self.document);self.update(p,'Compatible')
            except Exception as exc:errors.append(p+': '+str(exc));self.update(p,'Blocked: '+str(exc))
        if errors:self.set_details('\n'.join(errors));return
        plans=plan_many([self.snapshots[p] for p in ports],self.document)
        lines=[]
        for plan in plans:
            s=plan['baseline'];lines.append(f"{s['settings'].get('name','?')} — {plan['port']}")
            for k,v in plan['settings'].items():lines.append(f"  {FIELDS[k][0]}: {display(k,s['settings'][k])} → {display(k,v)}")
            before={c['index']:c for c in s.get('channels',[])}
            for c in plan['channels']:
                old=before[c['index']]
                lines.append(f"  Channel {c['index']}: {old['name'] or '(empty)'} → {c['name'] or '(empty)'}"+(' [key changes]' if c['secret']!=old['secret'] else ''))
            if not plan['settings'] and not plan['channels']:lines.append('  No changes')
            lines.append('')
        self.plans=plans;self.set_details('\n'.join(lines));self.apply_button.configure(state='normal' if any(p['settings'] or p['channels'] for p in plans) else 'disabled')
        self.status.set('Review every device above. Names and coordinates change only if explicitly included in the saved profile.')

    def apply(self):
        if not self.plans:raise ValueError('Review the selected devices first.')
        plans=copy.deepcopy(self.plans)
        if not messagebox.askokcancel('Apply reviewed batch?',f"Apply {self.document['name']} to {len(plans)} reviewed devices?\nEach changed device will be reread and verified. A failure stops the batch; completed devices are not rolled back.",parent=self.window):return
        self.invalidate_review()
        async def work():
            return await apply_many(plans,self.app.profile_page.library.folder.parent/'reports',self.cancel.is_set,lambda p,s:self.queue.put(('progress',p,s)))
        def done(result):
            report,path=result
            for p in plans:self.snapshots.pop(p['port'],None)
            self.set_details('\n'.join(f"{d['name']} — {d['port']}: {d['status']}"+ ('\n'+d['error'] if 'error' in d else '') for d in report['devices']))
            self.status.set(f'Batch finished. Report: {path}. Read again before another batch.')
            self.app.invalidate()
        self.run(work(),done,'Applying reviewed changes…')

    def poll(self):
        try:
            while True:
                message=self.queue.get_nowait()
                if message[0]=='progress':self.update(message[1],message[2]);continue
                _,callback,result,error=message;self.busy=False
                for b in self.controls:b.configure(state='normal')
                self.stop.configure(state='disabled');self.invalidate_review()
                if error:
                    self.snapshots.clear();self.app.invalidate();self.status.set(error)
                    messagebox.showerror('Batch operation failed',error,parent=self.window)
                else:
                    try:callback(result)
                    except Exception as exc:self.status.set(str(exc));messagebox.showerror('Batch result',str(exc),parent=self.window)
        except queue.Empty:pass
        self.poll_id=self.window.after(100,self.poll)

    def close(self):
        if self.busy:
            self.cancel.set();self.status.set('Stopping after the current device. Wait for its operation to finish.');return
        self.window.after_cancel(self.poll_id);self.window.destroy();self.app.batch_window=None
