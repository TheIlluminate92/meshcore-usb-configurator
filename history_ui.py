"""Read-only history browser, report export, and explicit post-restart reread."""
import csv
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from restart_check import check_restart

class HistoryPage(ttk.Frame):
    def __init__(self,parent,app):
        super().__init__(parent,padding=14);self.app=app
        ttk.Label(self,text='History on this PC',font=('Segoe UI',16,'bold')).pack(anchor='w')
        ttk.Label(self,text='Saved runs survive closing the app. No interrupted run resumes writing automatically.').pack(anchor='w',pady=6)
        self.tree=ttk.Treeview(self,columns=('date','profile','status'),show='headings',height=5,selectmode='browse')
        for key,label,width in [('date','Started',230),('profile','Profile / operation',300),('status','Run status',200)]:
            self.tree.heading(key,text=label);self.tree.column(key,width=width)
        self.tree.pack(fill='both',expand=True)
        self.tree.bind('<<TreeviewSelect>>',lambda _:self.describe())
        self.text=tk.Text(self,height=7,wrap='word',font=('Consolas',9),state='disabled');self.text.pack(fill='both',expand=True,pady=8)
        row=ttk.Frame(self);row.pack(fill='x')
        for title,fn in [('Refresh',self.refresh),('Remembered radios',self.radios),('Export results CSV…',self.export),('Verify selected radio after restart…',self.verify)]:
            ttk.Button(row,text=title,command=lambda action=fn:self.guard(action)).pack(side='left',padx=(0,6))
        self.refresh()

    def guard(self,action):
        if self.app.busy:messagebox.showinfo('Operation in progress','Wait for the device operation to finish.');return
        try:action()
        except Exception as exc:messagebox.showerror('History',str(exc))

    def put(self,text):
        self.text.configure(state='normal');self.text.delete('1.0','end');self.text.insert('1.0',text);self.text.configure(state='disabled')

    def refresh(self):
        selection=self.tree.selection();self.tree.delete(*self.tree.get_children())
        for run in self.app.history.runs():self.tree.insert('','end',iid=run['id'],values=(run['started'],run['profile'],'Running / interrupted' if run['status']=='Running' else run['status']))
        if selection and self.tree.exists(selection[0]):self.tree.selection_set(selection)
        elif self.tree.get_children():self.tree.selection_set(self.tree.get_children()[0])
        else:self.put('No recorded runs yet. Device reads appear under Remembered radios.')

    def selected(self):
        selection=self.tree.selection()
        if not selection:raise ValueError('Select a saved run first.')
        return selection[0]

    def describe(self):
        if not self.tree.selection():return
        rows,checks=self.app.history.details(self.selected())
        lines=[f"{r['name']} | {r['port']} | ID {r['identity'][:12]} | {r['status']}"+('\n  '+r['error'] if r['error'] else '') for r in rows]
        lines+=['','Pending/writing entries from an unfinished run are not verified. Reread before retrying.','Restart checks (restart confirmed by user):']
        lines += [f"{v['checked']} | {v['port']} | ID {v['identity'][:12]} | {v['status']} | {v['detail']}" for v in checks]
        self.put('\n'.join(lines))

    def radios(self):
        rows=self.app.history.radios()
        self.put('\n'.join(f"{r['name']} | {r['model']} | last connection {r['last_port']} | ID {r['identity'][:12]}\n  First seen: {r['first_seen']}\n  Last seen: {r['last_seen']}" for r in rows) or 'No identified radios recorded yet.')

    def export(self):
        rows,checks=self.app.history.details(self.selected())
        path=filedialog.asksaveasfilename(defaultextension='.csv',filetypes=[('CSV results','*.csv')])
        if not path:return
        # Escape formula-leading user names for spreadsheet consumers.
        def cell(v):
            text=str(v or '')
            return "'"+text if text[:1] in ('=','+','-','@','\t','\r') else text
        with open(path,'w',newline='',encoding='utf-8-sig') as f:
            writer=csv.writer(f);writer.writerow(['Device','Identity','Connection','Status','Error','Last restart check'])
            for r in rows:
                latest=next((v for v in reversed(checks) if v['identity']==r['identity']),None)
                writer.writerow([cell(x) for x in (r['name'],r['identity'],r['port'],r['status'],r['error'],latest['status'] if latest else 'Not checked')])

    def verify(self):
        if not self.app.confirm_discard():return
        run_id=self.selected();port=self.app.selected_port()
        rows,_=self.app.history.details(run_id)
        expected={r['identity']:r for r in rows if r['status'] in ('Verified','No changes at review')}
        if not expected:raise ValueError('This run has no successfully completed devices to check.')
        if not messagebox.askokcancel('Confirm restart',f'Restart or power-cycle the radio, then select its current connection above.\n\nSelected connection: {port}\n\nHave you restarted it since this run? Continue will reread settings only. A restart is recorded as your confirmation, not detected automatically.'):return
        def done(result):
            snapshot,status,detail=result
            self.app.show(snapshot);self.app.status.set(status+': '+detail)
            self.refresh();self.describe()
        self.app.run(check_restart(self.app.history,run_id,port,True),done,'Rereading after your reported restart…')
