"""Fault injection and persistence checks; never access a physical radio."""
import asyncio
import copy
import hashlib
import io
import json
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock,patch
import device
import updater
from storage import atomic_text
from preferences import save_preferences
from history_store import HistoryStore
from model import validate,load_profile
from test_configurator import BASE

class PersistenceFaults(unittest.TestCase):
    def test_interrupted_save_preserves_previous_json(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'report.json';device.save_json(path,{'verified':False,'acknowledged':['name']})
            before=path.read_bytes()
            with patch('storage.os.fsync',side_effect=OSError('Disk full')):
                with self.assertRaises(OSError):device.save_json(path,{'verified':True})
            self.assertEqual(path.read_bytes(),before)
            self.assertEqual(list(Path(folder).glob('*.tmp')),[])
    def test_concurrent_writers_leave_one_complete_document(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'shared.json'
            with ThreadPoolExecutor(max_workers=4) as pool:
                list(pool.map(lambda n:atomic_text(path,json.dumps({'n':n,'text':str(n)*3000})),range(16)))
            result=json.loads(path.read_text());self.assertEqual(result['text'],str(result['n'])*3000)
            self.assertEqual(list(Path(folder).glob('*.tmp')),[])
    def test_preferences_failure_does_not_raise_on_close(self):
        with patch('storage.atomic_text',side_effect=PermissionError('Read only')):
            self.assertFalse(save_preferences('unused','Dark','1180x820+0+0'))
    def test_future_history_schema_is_not_downgraded(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'history.sqlite3'
            with closing(sqlite3.connect(path)) as db:db.execute('PRAGMA user_version=2')
            with self.assertRaisesRegex(ValueError,'newer app'):HistoryStore(path)
            with closing(sqlite3.connect(path)) as db:self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0],2)
    def test_huge_numeric_and_boolean_schema_rejected(self):
        with self.assertRaises(ValueError):validate({'frequency':10**1000})
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'p.json';path.write_text(json.dumps({'format':'meshcore-usb-profile','schema_version':True,'settings':{}}))
            with self.assertRaises(ValueError):load_profile(path)

class UpdaterFaults(unittest.TestCase):
    def test_downloads_have_independent_staging_files(self):
        data=b'MZverified';asset={'id':12,'size':len(data),'digest':'sha256:'+hashlib.sha256(data).hexdigest()}
        with tempfile.TemporaryDirectory() as folder:
            with patch('updater.request',side_effect=lambda *args,**kwargs:io.BytesIO(data)):
                first=updater.download({'asset':asset},folder);second=updater.download({'asset':asset},folder)
            self.assertNotEqual(first,second);self.assertEqual(first.read_bytes(),second.read_bytes())
    def test_tampered_staging_never_starts_helper(self):
        with tempfile.TemporaryDirectory() as folder:
            staged=Path(folder)/'User Data'/'Updates'/'ready.exe';staged.parent.mkdir(parents=True);staged.write_bytes(b'MZchanged')
            with patch('subprocess.Popen') as launch:
                with self.assertRaisesRegex(ValueError,'changed after'):updater.schedule_install(staged,Path(folder)/'app.exe',123,'sha256:'+hashlib.sha256(b'MZoriginal').hexdigest())
                launch.assert_not_called()
    def test_requests_never_send_credentials(self):
        with patch('urllib.request.build_opener') as builder:
            updater.request(updater.API)
            request=builder.return_value.open.call_args.args[0]
            self.assertIsNone(request.get_header('Authorization'))
    def test_truncated_download_keeps_prior_ready_files(self):
        with tempfile.TemporaryDirectory() as folder:
            previous=Path(folder)/'ready.exe';previous.write_bytes(b'MZprevious')
            with patch('updater.request',return_value=io.BytesIO(b'MZ')):
                with self.assertRaises(ValueError):updater.download({'asset':{'id':12,'size':20,'digest':'sha256:'+'1'*64}},folder)
            self.assertEqual(previous.read_bytes(),b'MZprevious');self.assertEqual(list(Path(folder).glob('*.tmp')),[])

class VerificationFaults(unittest.IsolatedAsyncioTestCase):
    async def apply_case(self,changed_identity=False,changed_channel=False):
        before=copy.deepcopy(BASE);before['channels']=[{'index':0,'name':'Keep','secret':'11'*16}]
        after=copy.deepcopy(before);after['settings']['tx_power']=10
        if changed_identity:after['self_info']['public_key']='different'
        current_channel=copy.deepcopy(before['channels'][0]);late_channel=copy.deepcopy(current_channel)
        if changed_channel:late_channel['secret']='22'*16
        reply=SimpleNamespace(type=SimpleNamespace(name='OK'),payload={})
        commands=SimpleNamespace(send=AsyncMock(return_value=reply))
        async def operate(port,action):return await action(SimpleNamespace(commands=commands))
        with tempfile.TemporaryDirectory() as folder,patch('device.operate',operate),patch('device.basic',AsyncMock(side_effect=[before,after])),patch('device.read_channel',AsyncMock(side_effect=[current_channel,late_channel])) as reader:
            with self.assertRaisesRegex(RuntimeError,'identity mismatch' if changed_identity else 'channel slot'):
                await device.apply_device('FAKE',before,{'tx_power':10},folder,before['channels'])
            report=json.loads(next(Path(folder).glob('apply-*.json')).read_text())
            self.assertFalse(report['verified'])
            if changed_channel:self.assertEqual(reader.await_count,2)
    async def test_identity_is_checked_again_after_writing(self):await self.apply_case(changed_identity=True)
    async def test_unchanged_requested_channel_is_verified_after_writing(self):await self.apply_case(changed_channel=True)
    async def test_cleanup_error_preserves_original_failure(self):
        connection=SimpleNamespace(disconnect=AsyncMock(side_effect=RuntimeError('cleanup also failed')))
        mc=SimpleNamespace(connect=AsyncMock(side_effect=RuntimeError('original connect failure')),disconnect=AsyncMock(side_effect=RuntimeError('manager cleanup failed')))
        with patch('device.make_connection',return_value=connection),patch('meshcore.MeshCore',return_value=mc):
            with self.assertRaisesRegex(RuntimeError,'original connect failure') as caught:await device.operate('FAKE',AsyncMock())
        self.assertIn('Connection cleanup failed',caught.exception.__notes__[0])
        connection.disconnect.assert_awaited_once()

class UpdateLifecycle(unittest.TestCase):
    def test_busy_update_blocks_parent_close_and_duplicate_dialog(self):
        import tkinter as tk
        from app import App
        root=tk.Tk()
        with tempfile.TemporaryDirectory() as folder,patch('app.ROOT',Path(folder)):
            app=App(root)
            try:
                self.assertFalse(app.closing)
                app.theme_choice.set('Dark');app.change_theme();root.update()
                app.open_updates();first=app.update_window
                root.update()
                from tkinter import ttk
                self.assertEqual(ttk.Style(root).lookup('TFrame','background'),'#1b2633')
                app.open_updates();self.assertIs(app.update_window,first)
                first.busy=True
                with patch('app.messagebox.showinfo'):app.close()
                self.assertTrue(root.winfo_exists())
                first.busy=False;first.close();self.assertIsNone(app.update_window)
                with patch('preferences.save_preferences',return_value=False):app.close()
            finally:
                try:root.destroy()
                except tk.TclError:pass
