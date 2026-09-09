"""Small hover hints with a clickable, keyboard-accessible help alternative."""
import tkinter as tk
from tkinter import ttk, messagebox


class Tooltip:
    active = None

    def __init__(self, widget, title, text):
        self.widget, self.title, self.text = widget, title, text
        self.timer = self.window = None
        widget.bind('<Enter>', self.schedule, add='+')
        widget.bind('<Leave>', self.hide, add='+')
        widget.bind('<FocusOut>', self.hide, add='+')
        widget.bind('<ButtonPress>', self.hide, add='+')
        widget.bind('<Escape>', self.hide, add='+')
        widget.bind('<Destroy>', self.hide, add='+')
        widget.help_tooltip = self

    def schedule(self, event=None):
        self.hide()
        self.timer = self.widget.after(450, self.show)

    def show(self):
        self.timer = None
        if not self.widget.winfo_exists() or not self.widget.winfo_viewable():
            return
        if Tooltip.active is not None:
            Tooltip.active.hide()
        Tooltip.active = self
        self.window = tk.Toplevel(self.widget)
        self.window.withdraw()
        self.window.overrideredirect(True)
        self.window.attributes('-topmost', True)
        box = tk.Frame(self.window, background='#fffbe6', borderwidth=1, relief='solid')
        box.pack()
        for text, font in ((self.title, ('Segoe UI', 10, 'bold')), (self.text, ('Segoe UI', 10))):
            tk.Label(box, text=text, font=font, background='#fffbe6', foreground='#202020',
                     justify='left', wraplength=360, padx=10, pady=5).pack(anchor='w')
        self.window.update_idletasks()
        w, h = self.window.winfo_reqwidth(), self.window.winfo_reqheight()
        left, top = self.widget.winfo_vrootx(), self.widget.winfo_vrooty()
        right = left + self.widget.winfo_vrootwidth()
        bottom = top + self.widget.winfo_vrootheight()
        x = max(left, min(self.widget.winfo_rootx(), right-w-8))
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        if y + h > bottom:
            y = max(top, self.widget.winfo_rooty()-h-6)
        self.window.geometry(f'{x:+d}{y:+d}')
        self.window.deiconify()

    def hide(self, event=None):
        if self.timer is not None:
            try:
                self.widget.after_cancel(self.timer)
            except tk.TclError:
                pass
            self.timer = None
        if self.window is not None:
            try:
                self.window.destroy()
            except tk.TclError:
                pass
            self.window = None
        if Tooltip.active is self:
            Tooltip.active = None

    def explain(self):
        self.hide()
        messagebox.showinfo(self.title, self.text, parent=self.widget.winfo_toplevel())


def help_label(parent, title, text):
    frame = ttk.Frame(parent)
    label = ttk.Label(frame, text=title, wraplength=240)
    label.pack(side='left')
    Tooltip(label, title, text)
    button = ttk.Button(frame, text='?', width=2, takefocus=True, style='Help.TButton')
    button.pack(side='left', padx=(5, 0))
    hint = Tooltip(button, title, text)
    button.configure(command=hint.explain)
    button.bind('<Return>', lambda e: hint.explain())
    return frame
