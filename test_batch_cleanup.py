import tkinter as tk
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from app import App
from batch_ui import BatchWindow
from profile_library import ProfileLibrary

class BatchCleanup(unittest.TestCase):
    def test_checkboxes_profile_and_footer(self):
        root=tk.Tk();app=App(root)
        try:
            with tempfile.TemporaryDirectory() as folder:
                app.profile_page.library=ProfileLibrary(Path(folder))
                app.profile_page.library.save('Team',{'name':'Personal','bandwidth':125},[],naming={'prefix':'Team','start':10})
                with patch('batch_ui.serial_ports',return_value=[('COM4','Radio'),('COM5','Radio')]):
                    batch=BatchWindow(app)
                batch.window.geometry('900x650');root.update()
                self.assertEqual(batch.selected(),['COM4','COM5'])
                batch.tree.focus('0');batch.toggle_focused();root.update()
                self.assertEqual(batch.selected(),['COM5'])
                self.assertIn('alternate',batch.master_check.state())
                batch.busy=True;batch.toggle_focused()
                self.assertEqual(batch.selected(),['COM5'])
                batch.busy=False;batch.all_checked.set(True);batch.toggle_all();root.update()
                self.assertEqual(len(batch.selected()),2)
                batch.profile_choice.set('Team');batch.use_profile()
                self.assertEqual(batch.document['settings'],{'bandwidth':125})
                self.assertEqual(batch.document['naming']['start'],10)
                self.assertIsNone(batch.plans)
                self.assertTrue(batch.stop.winfo_ismapped())
                self.assertLessEqual(batch.stop.winfo_rooty()+batch.stop.winfo_height(),batch.window.winfo_rooty()+batch.window.winfo_height())
                batch.close()
        finally:
            app.pending_count=0;app.close()
