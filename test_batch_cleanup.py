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

class BatchRegression(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory()
        self.root=tk.Tk();self.app=App(self.root)
        self.app.profile_page.library=ProfileLibrary(Path(self.folder.name))
        with patch('batch_ui.serial_ports',return_value=[('COM4','A'),('COM5','B')]):
            self.batch=BatchWindow(self.app)
        self.root.update()

    def tearDown(self):
        self.batch.busy=False;self.batch.close();self.app.pending_count=0;self.app.close();self.folder.cleanup()

    def test_usb_refresh_drops_stale_snapshot_without_row_collision(self):
        b=self.batch;b.snapshots['COM4']={'old':True}
        b.add_targets([('ble:ABC','Bluetooth')])
        with patch('batch_ui.serial_ports',return_value=[('COM5','B'),('COM6','C')]):b.find_usb()
        self.assertNotIn('COM4',b.targets);self.assertNotIn('COM4',b.snapshots)
        self.assertEqual(set(b.targets),{'COM5','COM6','ble:ABC'})
        self.assertEqual(len(set(b.targets.values())),3)

    def test_saved_profile_refresh_edit_indicator_and_removed_profile(self):
        b=self.batch;b.document['settings']={'bandwidth':125}
        with patch('batch_ui.simpledialog.askstring',return_value='Fresh'):b.save_shared()
        self.assertIn('Fresh',b.profile_box.cget('values'))
        self.assertEqual(b.profile_choice.get(),'Fresh')
        b.shared_edited();self.assertIn('(edited)',b.profile_choice.get())
        b.profile_choice.set('Fresh');b.use_profile()
        self.assertEqual(b.document['settings'],{'bandwidth':125})
        ident=b.profile_choices[0]['id'];self.app.profile_page.library.archive(ident)
        with self.assertRaisesRegex(ValueError,'no longer available'):b.use_profile()

    def test_unchanged_selection_event_preserves_review(self):
        b=self.batch;b.plans=['reviewed'];b.selection_changed()
        self.assertEqual(b.plans,['reviewed'])
        b.tree.focus('0');b.toggle_focused()
        self.assertIsNone(b.plans)

    def test_read_continues_after_failed_port_and_counts_results(self):
        import asyncio
        from unittest.mock import AsyncMock
        from test_history_compare import radio
        b=self.batch
        self.app.history.remember=lambda snapshot:None
        def run(operation,callback,status):callback(asyncio.run(operation))
        reader=AsyncMock(side_effect=[RuntimeError('Port busy'),radio('COM5','b')])
        with patch.object(b,'run',side_effect=run),patch('batch_ui.read_device',reader):b.read_selected()
        self.assertEqual(reader.await_count,2)
        self.assertNotIn('COM4',b.snapshots);self.assertIn('COM5',b.snapshots)
        self.assertIn('1 readable radios',b.device_summary.get())
        self.assertEqual(b.progress_ports,['COM4','COM5'])
