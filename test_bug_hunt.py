import json
import tempfile
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch, AsyncMock
from guidance import impact
from profile_library import ProfileLibrary
from batch import plan_many, apply_many
from test_profiles_batch import radio

class Regressions(unittest.IsolatedAsyncioTestCase):
    def test_nonfinite_typed_values_do_not_crash_hints(self):
        for key in ('spreading_factor','coding_rate','multi_acks','tx_power','bandwidth'):
            for value in ('nan','inf','-inf','1e999'):
                self.assertIsNone(impact(key,value))

    def test_invalid_profile_metadata_does_not_break_library(self):
        with tempfile.TemporaryDirectory() as folder:
            lib=ProfileLibrary(folder)
            good=lib.save('Good',{'bandwidth':125},[])
            bad=lib.save('Bad',{'bandwidth':125},[])
            path=lib.path(bad);data=json.loads(path.read_text());data['profile_name']=42
            path.write_text(json.dumps(data))
            entries,errors=lib.entries()
            self.assertEqual([e['id'] for e in entries],[good])
            self.assertEqual(errors,[path.name])

    async def test_batch_checks_unchanged_profile_channels_before_writing(self):
        s=radio()
        plans=plan_many([s],{'settings':{'bandwidth':125},'channels':s['channels']})
        self.assertEqual(plans[0]['channels'],[])
        writer=AsyncMock(return_value=s)
        with tempfile.TemporaryDirectory() as folder,patch('batch.apply_device',writer):
            await apply_many(plans,folder)
        self.assertEqual(writer.await_args.args[4],s['channels'])

class SharedScope(unittest.TestCase):
    def test_profile_update_keeps_original_channel_scope(self):
        from library_ui import LibraryPage
        from types import SimpleNamespace
        s=radio();s['channels'].append({'index':1,'name':'Other','secret':'22'*16})
        app=SimpleNamespace(snapshot=s,desired=lambda:s['settings'],desired_channels=lambda:s['channels'])
        page=SimpleNamespace(app=app,choose_scope=unittest.mock.Mock())
        saved={'name':'Settings only','settings':{'bandwidth':125},'channels':[]}
        LibraryPage.save_editor(page,saved)
        self.assertEqual(page.choose_scope.call_args.args[1],[])
        saved['channels']=[s['channels'][0]]
        LibraryPage.save_editor(page,saved)
        self.assertEqual(page.choose_scope.call_args.args[1],[s['channels'][0]])
        saved['settings']['gps_interval']=60
        with self.assertRaisesRegex(ValueError,'every field/slot'):LibraryPage.save_editor(page,saved)

    def test_channel_only_profile_and_empty_selection_do_not_expand_scope(self):
        from app import App
        from batch_ui import BatchWindow
        from batch_editor import SharedEditor
        try:r=tk.Tk()
        except tk.TclError as exc:self.skipTest(str(exc))
        with patch('app.serial_ports',return_value=[]):app=App(r)
        self.addCleanup(app.close)
        s=radio()
        with patch('batch_ui.serial_ports',return_value=[]):owner=BatchWindow(app,{'name':'Channels only','settings':{},'channels':s['channels']})
        editor=SharedEditor(owner,[s]);r.update()
        self.assertFalse(any(v.get() for v in editor.include.values()))
        editor.close()
        owner.document={'name':'Intentionally empty','settings':{},'channels':[]}
        editor=SharedEditor(owner,[s]);r.update()
        self.assertFalse(any(v.get() for v in editor.include.values()))
        editor.close()

    def test_dropdown_typing_preserves_modal_grab(self):
        from setting_box import SettingBox
        try:r=tk.Tk()
        except tk.TclError as exc:self.skipTest(str(exc))
        self.addCleanup(r.destroy)
        dialog=tk.Toplevel(r);dialog.grab_set()
        value=tk.StringVar(value='Off');box=SettingBox(dialog,textvariable=value,values=['Off','On'],state='normal');box.pack();r.update()
        box.event_generate('<Button-1>',x=10,y=10);r.update()
        popup=str(box.tk.call('ttk::combobox::PopdownWindow',box._w))
        box.tk.call('event','generate',popup+'.f.l','<KeyPress>','-keysym','o');r.update()
        self.assertEqual(value.get(),'o')
        self.assertEqual(str(r.grab_current()),str(dialog))

if __name__=='__main__':unittest.main()
