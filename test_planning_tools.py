import json
import sqlite3
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch, AsyncMock
from profile_library import ProfileLibrary
from firmware_role import parse_cli_role, detect, probe_cli
from portable_backup import create_backup
from dry_run import document
from test_profiles_batch import radio

class NotesTests(unittest.TestCase):
    def test_notes_survive_rename_update_and_clear(self):
        with tempfile.TemporaryDirectory() as tmp:
            lib=ProfileLibrary(tmp)
            ident=lib.save('Team',{'tx_power':14},[],notes='Local mesh\nUser-entered notes')
            lib.save('Renamed',{'tx_power':12},[],ident)
            self.assertEqual(lib.entries()[0][0]['notes'],'Local mesh\nUser-entered notes')
            lib.save('Renamed',{'tx_power':12},[],ident,notes='')
            self.assertEqual(lib.entries()[0][0]['notes'],'')
            for notes in (False,55,'x'*4001):
                with self.assertRaises(ValueError):lib.save('bad',{'tx_power':14},[],notes=notes)

class RolesTests(unittest.IsolatedAsyncioTestCase):
    def test_strict_replies(self):
        self.assertEqual(parse_cli_role('get role\r\n  -> > repeater\r\n'),'repeater')
        self.assertEqual(parse_cli_role('  -> > room_server\r\n'),'room')
        for reply in ('My repeater','> room','> repeater','> repeater-fork\n','> repeater\n> room_server\n'):
            self.assertEqual(parse_cli_role(reply),'unknown')

    async def test_server_does_not_try_companion_commands(self):
        with patch('firmware_role.probe_cli',return_value='room'),patch('device.operate',AsyncMock()) as operate:
            self.assertEqual(await detect('COM4'),'room');operate.assert_not_awaited()

    async def test_companion_and_unknown(self):
        with patch('firmware_role.probe_cli',return_value='unknown'),patch('device.operate',AsyncMock(return_value={})):
            self.assertEqual(await detect('COM4'),'companion')
        with patch('firmware_role.probe_cli',return_value='unknown'),patch('device.operate',AsyncMock(side_effect=TimeoutError())):
            self.assertEqual(await detect('COM4'),'unknown')

    def test_probe_only_get_role_and_always_closes(self):
        from unittest.mock import MagicMock
        port=MagicMock();port.__enter__.return_value=port;port.read.return_value=b'  -> > repeater\r\n'
        with patch('serial.Serial',return_value=port):self.assertEqual(probe_cli('COM4'),'repeater')
        port.write.assert_called_once_with(b'get role\r');port.__exit__.assert_called_once()

class BackupTests(unittest.TestCase):
    def test_sqlite_backup_with_wal_and_private_data_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'User Data';(root/'data').mkdir(parents=True);(root/'profiles').mkdir()
            (root/'profiles'/'profile.json').write_text('private-channel-data')
            db=sqlite3.connect(root/'data'/'history.sqlite3')
            try:
                db.execute('PRAGMA journal_mode=WAL');db.execute('CREATE TABLE test(value)');db.execute('INSERT INTO test VALUES (42)');db.commit()
                dest=Path(tmp)/'backup.zip';create_backup(dest,root)
                with zipfile.ZipFile(dest) as z:
                    self.assertEqual(z.read('MeshCore Configurator/User Data/profiles/profile.json'),b'private-channel-data')
                    self.assertFalse(any(n.endswith('-wal') for n in z.namelist()))
                    copy=Path(tmp)/'copy.sqlite3';copy.write_bytes(z.read('MeshCore Configurator/User Data/data/history.sqlite3'))
                c=sqlite3.connect(copy)
                try:self.assertEqual(c.execute('SELECT value FROM test').fetchone()[0],42)
                finally:c.close()
            finally:db.close()

    def test_prevent_recursive_backup_and_keep_existing_on_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'data';root.mkdir();dest=Path(tmp)/'backup.zip';dest.write_bytes(b'previous')
            with self.assertRaises(ValueError):create_backup(root/'backup.zip',root)
            with self.assertRaises(FileNotFoundError):create_backup(dest,root,root/'missing.exe')
            self.assertEqual(dest.read_bytes(),b'previous')

class DryRunTests(unittest.TestCase):
    def test_keys_excluded_and_individual_changes_included(self):
        d=document([radio()],{'settings':{'tx_power':14},'channels':[{'index':0,'name':'New','secret':'22'*16}]},{'one':{'name':'Team-01'}},['COM9'])
        encoded=json.dumps(d)
        self.assertNotIn('22'*16,encoded);self.assertNotIn('11'*16,encoded)
        self.assertIn('Team-01',encoded);self.assertIn('has not been read',encoded)
        self.assertTrue(d['devices'][0]['changes'][-1]['key_changes'])

    def test_incompatible_still_exports(self):
        d=document([radio()],{'settings':{'gps_interval':30}})
        self.assertTrue(d['devices'][0]['blocked'])


class ReleaseNotesTests(unittest.TestCase):
    def test_current_section_only(self):
        from release_notes import current_notes
        text='# Changelog\n\n## New — 1.2.3\n\nNew changes\n\n## Older — 1.2.2\nOld changes'
        self.assertIn('New changes',current_notes(text,'1.2.3'))
        self.assertNotIn('Old changes',current_notes(text,'1.2.3'))
        with self.assertRaises(ValueError):current_notes(text,'9.0.0')

    def test_updater_returns_notes(self):
        import updater,io
        from test_updates_theme import UpdateTests
        data=UpdateTests().release();data['body']='New features\n- A fix'
        with patch('updater.request',return_value=io.BytesIO(json.dumps(data).encode())):
            self.assertEqual(updater.check()['notes'],data['body'])
