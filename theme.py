"""A consistent light desktop theme with clear editable and pending states."""
from tkinter import ttk

BG = '#edf2f7'
INK = '#142b43'
MUTED = '#52667c'
ACCENT = '#007f79'

def apply_theme(root):
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
