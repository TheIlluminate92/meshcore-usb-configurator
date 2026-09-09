import tkinter as tk
from tkinter import ttk
from comparison import rows,profile_text

def preview(parent,document):
    window=tk.Toplevel(parent);window.title('Profile preview — '+document['name']);window.geometry('760x580');window.transient(parent)
    frame=ttk.Frame(window,padding=14);frame.pack(fill='both',expand=True)
    text=tk.Text(frame,wrap='word',font=('Consolas',10));text.pack(fill='both',expand=True)
    text.insert('1.0',profile_text(document));text.configure(state='disabled')
    ttk.Button(frame,text='Close',command=window.destroy).pack(anchor='e',pady=(8,0))

def compare(parent,snapshots,document=None):
    window=tk.Toplevel(parent);window.title('Compare devices and profile');window.geometry('1060x650');window.transient(parent)
    frame=ttk.Frame(window,padding=14);frame.pack(fill='both',expand=True)
    ttk.Label(frame,text='Differences are highlighted. Missing values are not treated as matches. Channel keys stay hidden.').pack(anchor='w',pady=6)
    only=tk.BooleanVar(value=True)
    ttk.Checkbutton(frame,text='Show differences only',variable=only).pack(anchor='w',pady=4)
    summary=tk.StringVar();ttk.Label(frame,textvariable=summary,style='Muted.TLabel').pack(anchor='w',pady=(0,6))
    area=ttk.Frame(frame);area.pack(fill='both',expand=True)
    columns=['field','status','profile']+[f'd{i}' for i in range(len(snapshots))]
    tree=ttk.Treeview(area,columns=columns,show='headings')
    headings=['Setting / channel','Comparison','Profile']+[s['settings'].get('name','?')+' / '+s['port'] for s in snapshots]
    for key,label in zip(columns,headings):tree.heading(key,text=label);tree.column(key,width=210,stretch=False)
    tree.tag_configure('different',background='#fff0cb');tree.tag_configure('missing',background='#f9dede')
    y=ttk.Scrollbar(area,orient='vertical',command=tree.yview);x=ttk.Scrollbar(area,orient='horizontal',command=tree.xview)
    tree.configure(yscrollcommand=y.set,xscrollcommand=x.set)
    y.pack(side='right',fill='y');x.pack(side='bottom',fill='x');tree.pack(fill='both',expand=True)
    def refresh():
        tree.delete(*tree.get_children())
        data=rows(snapshots,document)
        summary.set(f"{sum(row[1]!='Same' for row in data)} differences or missing values across {len(snapshots)} radio(s).")
        for row in data:
            if only.get() and row[1]=='Same':continue
            tree.insert('','end',values=row,tags=('missing' if row[1]=='Not reported' else 'different' if row[1]!='Same' else '',))
    only.trace_add('write',lambda *_:refresh());refresh()
