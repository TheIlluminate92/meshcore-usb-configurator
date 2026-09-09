import io
import json
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import updater
from preferences import load_preferences,save_preferences

class UpdateTests(unittest.TestCase):
    def release(self,content=b'MZtest'):
        return {'tag_name':'v99.0.0','assets':[{'name':updater.ASSET,'id':12,'size':len(content),'digest':'sha256:'+hashlib.sha256(content).hexdigest()}]}
    def test_no_downgrade_and_digest_required(self):
        release=self.release();release['tag_name']='v0.0.1'
        with patch('updater.request',return_value=io.BytesIO(json.dumps(release).encode())):self.assertIsNone(updater.check())
        release=self.release();release['assets'][0]['digest']=None
        with patch('updater.request',return_value=io.BytesIO(json.dumps(release).encode())):
            with self.assertRaisesRegex(ValueError,'verified'):updater.check()
    def test_valid_download_and_corrupt_download_does_not_replace_staged(self):
        with tempfile.TemporaryDirectory() as folder:
            asset=self.release()['assets'][0]
            with patch('updater.request',return_value=io.BytesIO(b'MZtest')):
                staged=updater.download({'asset':asset},folder)
            self.assertEqual(staged.read_bytes(),b'MZtest')
            with patch('updater.request',return_value=io.BytesIO(b'badbad')):
                with self.assertRaises(ValueError):updater.download({'asset':asset},folder)
            self.assertEqual(staged.read_bytes(),b'MZtest');self.assertFalse((Path(folder)/'download.tmp').exists())
    def test_redirect_strips_credential_and_blocks_untrusted_host(self):
        from urllib.request import Request
        request=Request(updater.API,headers={'Authorization':'Bearer secret'})
        handler=updater.SafeRedirect()
        redirected=handler.redirect_request(request,None,302,'',{},'https://release-assets.githubusercontent.com/file')
        self.assertIsNone(redirected.get_header('Authorization'))
        with self.assertRaises(ValueError):handler.redirect_request(request,None,302,'',{},'https://example.com/file')
    def test_install_paths_and_encoded_helper(self):
        with tempfile.TemporaryDirectory() as folder:
            exe=Path(folder)/'! app.exe';staged=Path(folder)/'User Data'/'Updates'/'ready.exe'
            with patch('subprocess.Popen') as launch:
                updater.schedule_install(staged,exe,123)
                command=launch.call_args.args[0]
                self.assertIn('-EncodedCommand',command)
                import base64
                script=base64.b64decode(command[-1]).decode('utf-16-le')
                self.assertIn('[IO.File]::Replace',script)
            with self.assertRaises(ValueError):updater.schedule_install(Path(folder)/'ready.exe',exe,123)
    def test_preferences_validate_and_round_trip(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'preferences.json';save_preferences(path,'Dark','1180x820+10+20')
            self.assertEqual(load_preferences(path)['theme'],'Dark')
            path.write_text('[]');self.assertEqual(load_preferences(path),{})

class ThemeTests(unittest.TestCase):
    def test_switches_classic_and_ttk_widgets_and_battery_order(self):
        import tkinter as tk
        from tkinter import ttk
        from theme import apply_theme
        from guidance import BatteryHint
        root=tk.Tk()
        try:
            text=tk.Text(root);text.pack();hint=BatteryHint(root,'tx_power',roomy=True);hint.pack()
            apply_theme(root,'Dark');hint.update_value('22');root.update()
            self.assertEqual(text.cget('background'),'#1b2633')
            self.assertEqual(hint.pack_slaves()[0],hint.canvas)
            self.assertEqual(hint.canvas.cget('background'),'#1b2633')
            apply_theme(root,'Light');root.update()
            self.assertEqual(text.cget('background'),'white')
            self.assertEqual(ttk.Style(root).lookup('TCheckbutton','background'),'white')
        finally:root.destroy()
