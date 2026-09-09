"""One-click choices; typing from the open list switches to text editing."""
from tkinter import ttk

class SettingBox(ttk.Combobox):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._typing_command=self.register(self._type_from_list)
        self.configure(postcommand=self._prepare_list)
        self.bind('<Button-1>',self._open_choices)

    def _prepare_list(self):
        popup=self.tk.call('ttk::combobox::PopdownWindow',self._w)
        script=f'if {{[{self._typing_command} %A %K %s] == "break"}} break'
        self.tk.call('bind',str(popup)+'.f.l','<KeyPress>',script)

    def _open_choices(self, event):
        if self.instate(['disabled']):return 'break'
        self.focus_set()
        self.selection_range(0,'end')
        self.tk.call('ttk::combobox::Post',self._w)
        return 'break'

    def _type_from_list(self, char, key, modifiers):
        if self.instate(['disabled']):return 'break'
        if self.instate(['readonly']):return ''
        control=int(modifiers)&4
        if control and key.lower()=='v':
            try:text=self.clipboard_get()
            except Exception:return 'break'
        elif key in ('BackSpace','Delete'):text=''
        elif char and char.isprintable() and not control:text=char
        else:return ''
        self.tk.call('ttk::combobox::Unpost',self._w)
        self.focus_set()
        self.delete(0,'end')
        self.insert(0,text)
        self.icursor('end')
        return 'break'
