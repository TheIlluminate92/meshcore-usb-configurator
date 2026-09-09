"""A consistent light desktop theme with clear editable and pending states."""
from tkinter import ttk

BG = '#edf2f7'
INK = '#142b43'
MUTED = '#52667c'
ACCENT = '#007f79'

def apply_light(root):
    root.configure(background=BG)
    root.option_add('*Font', ('Segoe UI', 10))
    root.option_add('*TCombobox*Listbox.font', ('Segoe UI', 10))
    style = ttk.Style(root)
    style.theme_use('clam')
    style.configure('.', font=('Segoe UI', 10), foreground=INK, background='white')
    style.configure('TFrame', background='white')
    style.configure('Root.TFrame', background=BG)
    style.configure('Header.TFrame', background=INK)
    style.configure('Title.TLabel', background=INK, foreground='white', font=('Segoe UI', 22, 'bold'))
    style.configure('Subtitle.TLabel', background=INK, foreground='#bcd1e1', font=('Segoe UI', 10))
    style.configure('TLabel', background='white', foreground=INK)
    style.configure('Muted.TLabel', foreground=MUTED)
    style.configure('Caption.TLabel', foreground=MUTED, font=('Segoe UI', 9, 'bold'))
    style.configure('Note.TLabel', foreground=MUTED, padding=(0, 6))
    style.configure('Status.TLabel', background=BG, foreground=MUTED, font=('Segoe UI', 9))
    style.configure('Pending.TLabel', background=BG, foreground=ACCENT, font=('Segoe UI', 10, 'bold'))
    style.configure('TButton', padding=(12, 8), background='#f0f5fa', bordercolor='#d8e2ec', relief='flat')
    style.map('TButton', background=[('active', '#e1ebf3')], foreground=[('disabled', '#92a0ae')])
    style.configure('Primary.TButton', background=ACCENT, foreground='white', bordercolor=ACCENT, font=('Segoe UI', 10, 'bold'))
    style.map('Primary.TButton', background=[('disabled', '#a4bdbb'), ('active', '#00665f')], foreground=[('disabled', '#f1f7f6'), ('!disabled', 'white')])
    style.configure('Help.TButton', padding=0, background='#edf4f8', foreground='#326b89', font=('Segoe UI', 9, 'bold'), borderwidth=0)
    style.configure('TEntry', padding=(8, 4), fieldbackground='#f8fafc', bordercolor='#cbd8e5', lightcolor='#cbd8e5', darkcolor='#cbd8e5')
    style.configure('TCombobox', padding=(8, 4), fieldbackground='#f8fafc', background='#f0f5fa', bordercolor='#cbd8e5', arrowsize=14)
    for name in ('TEntry', 'TCombobox'):
        style.map(name, fieldbackground=[('disabled', '#eff3f6'), ('readonly', '#f8fafc')], foreground=[('disabled', '#8391a0'), ('readonly', INK)], bordercolor=[('focus', ACCENT)])
        style.configure('Changed.'+name, fieldbackground='#fff5d8', bordercolor='#c38a26')
        style.map('Changed.'+name, fieldbackground=[('disabled', '#f4eddf'), ('readonly', '#fff5d8'), ('!disabled', '#fff5d8')])
    style.configure('TNotebook', background=BG, borderwidth=0, tabmargins=(0, 0, 0, 0))
    style.configure('TNotebook.Tab', padding=(12, 9), background='#dfe8f0', foreground=MUTED, font=('Segoe UI', 10))
    style.map('TNotebook.Tab', background=[('selected', 'white'), ('active', '#e8eff5')], foreground=[('selected', ACCENT)])
    style.configure('TSeparator', background='#e1e9f1')
    return style


def system_dark():
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Software\Microsoft\Windows\CurrentVersion\Themes\Personalize') as key:
            return winreg.QueryValueEx(key,'AppsUseLightTheme')[0]==0
    except (ImportError,OSError):return False

def apply_theme(root,mode='Light'):
    import tkinter as tk
    dark=mode=='Dark' or (mode=='System' and system_dark())
    style=apply_light(root)
    bg='#111922' if dark else BG
    panel='#1b2633' if dark else 'white'
    field='#243344' if dark else '#f8fafc'
    ink='#e5edf5' if dark else INK
    muted='#b2c0cf' if dark else MUTED
    border='#46586b' if dark else '#cbd8e5'
    for name in ('TLabelframe','TLabelframe.Label','TCheckbutton','TRadiobutton','TMenubutton'):
        style.configure(name,background=panel,foreground=ink)
        style.map(name,background=[('active',field)],foreground=[('disabled',muted)])
    style.configure('TSpinbox',fieldbackground=field,background=field,foreground=ink,arrowcolor=ink)
    style.map('TSpinbox',fieldbackground=[('disabled',field),('readonly',field)],foreground=[('disabled',muted),('readonly',ink)])
    for name in ('TEntry','TCombobox'):
        style.configure(name,foreground=ink,insertcolor=ink,arrowcolor=ink)
        style.configure('Changed.'+name,foreground=ink)
    if dark:
        style.configure('.',background=panel,foreground=ink)
        for name in ('TFrame','TLabel','TLabelframe','TLabelframe.Label','TCheckbutton','TRadiobutton','TMenubutton'):
            style.configure(name,background=panel,foreground=ink)
        style.configure('Root.TFrame',background=bg)
        for name in ('Muted.TLabel','Caption.TLabel','Note.TLabel'):style.configure(name,foreground=muted)
        style.configure('Status.TLabel',background=bg,foreground=muted)
        style.configure('Pending.TLabel',background=bg,foreground='#6dd8cb')
        style.configure('TButton',background=field,foreground=ink,bordercolor=border)
        style.map('TButton',background=[('active','#364c62')],foreground=[('disabled','#8395a6')])
        style.configure('Help.TButton',background=field,foreground='#8dd7ed')
        for name in ('TEntry','TCombobox','TSpinbox'):
            style.configure(name,fieldbackground=field,background=field,foreground=ink,bordercolor=border,insertcolor=ink,arrowcolor=ink)
            style.map(name,fieldbackground=[('disabled','#202b37'),('readonly',field)],foreground=[('disabled','#91a1b2'),('readonly',ink)])
            style.configure('Changed.'+name,fieldbackground='#53472d',foreground='#ffedb0')
            style.map('Changed.'+name,fieldbackground=[('disabled','#3d382d'),('readonly','#53472d'),('!disabled','#53472d')])
        style.configure('TNotebook',background=bg)
        style.configure('TNotebook.Tab',background=field,foreground=muted)
        style.map('TNotebook.Tab',background=[('selected',panel),('active','#364c62')],foreground=[('selected','#6dd8cb')])
        for name in ('TCheckbutton','TRadiobutton','TMenubutton'):
            style.map(name,background=[('active',field)],foreground=[('disabled','#91a1b2')])
    style.configure('Treeview',background=panel,fieldbackground=panel,foreground=ink,rowheight=26,bordercolor=border)
    style.configure('Treeview.Heading',background=field,foreground=ink,relief='flat')
    style.map('Treeview',background=[('selected','#28556b')],foreground=[('selected','white')])
    for option,value in [('background',field),('foreground',ink),('selectBackground','#28556b'),('selectForeground','white')]:
        root.option_add('*TCombobox*Listbox.'+option,value)
    def visit(widget):
        try:
            if isinstance(widget,(tk.Tk,tk.Toplevel)):widget.configure(background=bg)
            elif isinstance(widget,tk.Text):widget.configure(background=panel,foreground=ink,insertbackground=ink,selectbackground='#28556b',selectforeground='white')
            elif isinstance(widget,tk.Canvas):
                old=widget.cget('background');widget.configure(background=panel)
                for item in widget.find_all():
                    if widget.type(item)=='rectangle' and widget.itemcget(item,'fill') in ('white',old):widget.itemconfigure(item,fill=panel)
            elif isinstance(widget,tk.Menu):widget.configure(background=panel,foreground=ink,activebackground=field,activeforeground=ink)
            elif isinstance(widget,ttk.Treeview):
                widget.tag_configure('different',background='#55472a' if dark else '#fff0cb',foreground=ink)
                widget.tag_configure('missing',background='#57333a' if dark else '#f9dede',foreground=ink)
            for child in widget.winfo_children():visit(child)
        except tk.TclError:pass
    visit(root)
    return style
