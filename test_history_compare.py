import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch,AsyncMock
from history_store import HistoryStore
from comparison import rows,verify_expected,profile_text
from profile_library import ProfileLibrary
from model import validate_naming,load_document
from batch import plan_many,apply_many
from restart_check import check_restart
from test_profiles_batch import radio

class Storage(unittest.TestCase):
    def test_same_identity_new_port_keeps_device_record(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'history.sqlite3';store=HistoryStore(path)
            self.assertIsNone(store.remember(radio('COM4','a')))
            previous=HistoryStore(path).remember(radio('COM9','a'))
            self.assertEqual(previous['last_port'],'COM4')
            self.assertEqual(len(store.radios()),1)
            self.assertEqual(store.radios()[0]['last_port'],'COM9')
            store.remember(radio('COM9','b'))
            self.assertEqual(len(store.radios()),2)

    def test_pending_progress_survives_reopen_without_resuming(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'history.sqlite3';store=HistoryStore(path)
            plans=plan_many([radio('COM4','a'),radio('COM5','b')],{'settings':{'bandwidth':125}})
            run=store.start(plans,'Team','report.json')
            store.result(run,plans[0],'Writing and verifying…')
            reopened=HistoryStore(path)
            results,_=reopened.details(run)
            self.assertEqual([r['status'] for r in results],['Writing and verifying…','Pending'])
            self.assertEqual(reopened.runs()[0]['status'],'Running')

    def test_naming_metadata_survives_update_rename_and_export(self):
        with tempfile.TemporaryDirectory() as folder:
            lib=ProfileLibrary(folder);template={'prefix':'Truck','start':10}
            ident=lib.save('Trucks',{'bandwidth':125},[],naming=template)
            lib.save('Renamed',{'bandwidth':62.5},[],ident)
            entry=lib.entries()[0][0]
            self.assertEqual(entry['naming'],template)
            self.assertEqual(json.loads(lib.path(ident).read_text())['naming'],template)
            self.assertEqual(load_document(lib.path(ident))[0],{'bandwidth':62.5})

    def test_bad_template_rejected(self):
        for value in [{'prefix':'','start':1},{'prefix':'x','start':True},{'prefix':'x','start':0},{'prefix':'é'*20,'start':1}]:
            with self.assertRaises(ValueError):validate_naming(value)

class Compare(unittest.TestCase):
    def test_comparison_marks_missing_differences_and_keeps_keys_hidden(self):
        a=radio('COM4','a');b=radio('COM5','b');b['settings']['bandwidth']=125
        del b['settings']['tx_power'];b['channels'][0]['secret']='ab'*16
        result=rows([a,b],{'settings':{'bandwidth':62.5},'channels':a['channels']})
        by_name={r[0]:r for r in result}
        self.assertEqual(by_name['Bandwidth (kHz)'][1],'Profile mismatch')
        self.assertEqual(by_name['Transmit power (dBm)'][1],'Not reported')
        self.assertEqual(by_name['Channel 0 key'][1],'Profile mismatch')
        self.assertNotIn('ab'*16,str(result));self.assertNotIn('11'*16,str(result))

    def test_expected_checks_include_missing_channels_and_exact_precision(self):
        s=radio();expected={'settings':{'frequency':s['settings']['frequency']+.001},'channels':[{'index':9,'name':'X','secret':'00'*16}]}
        self.assertEqual(verify_expected(s,expected),['frequency','channel 9'])

    def test_profile_preview_values_and_template_without_keys(self):
        doc={'name':'Team','settings':{'bandwidth':125},'channels':radio()['channels'],'naming':{'prefix':'Van','start':7}}
        text=profile_text(doc)
        self.assertIn('Van-07',text);self.assertIn('125',text);self.assertNotIn('11'*16,text)

class RecordedRuns(unittest.IsolatedAsyncioTestCase):
    async def test_failed_batch_retains_all_device_results(self):
        with tempfile.TemporaryDirectory() as folder:
            store=HistoryStore(Path(folder)/'history.sqlite3')
            plans=plan_many([radio('COM4','a'),radio('COM5','b'),radio('COM6','c')],{'settings':{'bandwidth':125}})
            with patch('batch.apply_device',AsyncMock(side_effect=[radio('COM4','a'),RuntimeError('Rejected')])):
                report,_=await apply_many(plans,folder,history=store,profile_name='Team')
            saved,_=store.details(report['run_id'])
            self.assertEqual([r['status'] for r in saved],['Verified','Failed — reread required','Not attempted'])
            self.assertEqual(store.runs()[0]['status'],'Stopped')

    async def test_restart_uses_identity_on_new_port_and_records_mismatch(self):
        with tempfile.TemporaryDirectory() as folder:
            store=HistoryStore(Path(folder)/'history.sqlite3')
            plan=plan_many([radio('COM4','a')],{'settings':{'bandwidth':125}})[0]
            run=store.start([plan],'Team','report.json');store.result(run,plan,'Verified');store.finish(run,'Complete')
            fresh=radio('COM9','a');fresh['settings']['bandwidth']=125
            with patch('restart_check.read_device',AsyncMock(return_value=fresh)):
                _,status,_=await check_restart(store,run,'COM9',True)
            self.assertEqual(status,'Matches after reported restart')
            fresh['settings']['bandwidth']=62.5
            with patch('restart_check.read_device',AsyncMock(return_value=fresh)):
                _,status,_=await check_restart(store,run,'COM9',True)
            self.assertEqual(status,'Mismatch after reported restart')
            checks=store.details(run)[1];self.assertEqual(len(checks),2)
            self.assertTrue(all(c['restart_attested']==1 for c in checks))

    async def test_wrong_radio_or_no_restart_cannot_get_verified(self):
        with tempfile.TemporaryDirectory() as folder:
            store=HistoryStore(Path(folder)/'history.sqlite3');plan=plan_many([radio()],{'settings':{'bandwidth':125}})[0]
            run=store.start([plan],'Team','report');store.result(run,plan,'Verified')
            reader=AsyncMock(return_value=radio('COM4','different'))
            with patch('restart_check.read_device',reader):
                with self.assertRaises(ValueError):await check_restart(store,run,'COM4',False)
                reader.assert_not_awaited()
                with self.assertRaises(ValueError):await check_restart(store,run,'COM4',True)
            self.assertEqual(store.details(run)[1],[])

if __name__=='__main__':unittest.main()
