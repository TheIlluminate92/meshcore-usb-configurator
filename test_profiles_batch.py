import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, AsyncMock
from profile_library import ProfileLibrary
from batch import plan_device, plan_many, apply_many
from test_configurator import BASE

def radio(port='COM4', identity='one'):
    s=copy.deepcopy(BASE);s['port']=port;s['self_info']['public_key']=identity
    s['channels']=[{'index':0,'name':'Old','secret':'11'*16}]
    return s

class Library(unittest.TestCase):
    def test_persist_update_rename_archive(self):
        with tempfile.TemporaryDirectory() as folder:
            lib=ProfileLibrary(folder)
            ident=lib.save('Team',{'bandwidth':62.5},[])
            again=ProfileLibrary(folder)
            self.assertEqual(again.entries()[0][0]['name'],'Team')
            again.save('New team',{'bandwidth':125},[],ident)
            self.assertEqual(again.entries()[0][0]['settings'],{'bandwidth':125})
            again.archive(ident)
            self.assertEqual(again.entries(),([],[]))
            self.assertEqual(len(list((Path(folder)/'archive').glob('*.json'))),1)

    def test_duplicate_names_invalid_data_and_path_injection(self):
        with tempfile.TemporaryDirectory() as folder:
            lib=ProfileLibrary(folder);lib.save('Team',{'bandwidth':62.5},[])
            with self.assertRaises(ValueError):lib.save('team',{'bandwidth':125},[])
            with self.assertRaises(ValueError):lib.save('Empty',{},[])
            with self.assertRaises(ValueError):lib.save('Bad',{'private_key':'x'},[])
            with self.assertRaises(ValueError):lib.archive('../outside')
            ident=lib.save('../name is only a label',{'bandwidth':125},[])
            self.assertTrue(lib.path(ident).is_file())

    def test_malformed_file_not_removed(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'broken.json';path.write_text('{')
            self.assertEqual(ProfileLibrary(folder).entries(),([],['broken.json']))
            self.assertTrue(path.exists())

class Plans(unittest.TestCase):
    def test_shared_profile_preserves_names_locations_and_other_channels(self):
        s=radio();p=plan_device(s,{'settings':{'bandwidth':125},'channels':[]})
        self.assertEqual(p['settings'],{'bandwidth':125})
        self.assertEqual(p['channels'],[])
        s['settings']['name']='Changed externally'
        self.assertEqual(p['baseline']['settings']['name'],'Test')

    def test_mixed_hardware_blocks_unsupported_or_excess_power(self):
        with self.assertRaisesRegex(ValueError,'not supported'):
            plan_device(radio(),{'settings':{'gps_interval':60}})
        s=radio();s['self_info']['max_tx_power']=14
        with self.assertRaises(ValueError):plan_device(s,{'settings':{'tx_power':22}})
        with self.assertRaisesRegex(ValueError,'slot 9'):
            plan_device(radio(),{'settings':{},'channels':[{'index':9,'name':'New','secret':'00'*16}]})

    def test_duplicate_identity_and_gps_conflict(self):
        with self.assertRaisesRegex(ValueError,'same radio'):
            plan_many([radio(),radio('ble:AA:BB')],{'settings':{'bandwidth':125}})
        s=radio();s['settings']['gps']=1
        with self.assertRaisesRegex(ValueError,'GPS'):
            plan_device(s,{'settings':{'latitude':12}})

class BatchRuns(unittest.IsolatedAsyncioTestCase):
    def plans(self):
        return plan_many([radio('COM4','one'),radio('COM5','two'),radio('COM6','three')],{'settings':{'bandwidth':125}})

    async def test_verifies_each_device_and_persists_summary(self):
        mock=AsyncMock(return_value=radio())
        with tempfile.TemporaryDirectory() as folder,patch('batch.apply_device',mock):
            report,path=await apply_many(self.plans(),folder)
            self.assertEqual([r['status'] for r in report['devices']],['Verified']*3)
            self.assertEqual(mock.await_count,3)
            self.assertEqual(json.loads(path.read_text())['devices'][2]['port'],'COM6')

    async def test_partial_failure_stops_remaining_devices(self):
        mock=AsyncMock(side_effect=[radio(),RuntimeError('mismatch')])
        with tempfile.TemporaryDirectory() as folder,patch('batch.apply_device',mock):
            report,_=await apply_many(self.plans(),folder)
        self.assertEqual([r['status'] for r in report['devices']],['Verified','Failed — reread required','Not attempted'])
        self.assertEqual(mock.await_count,2)

    async def test_cancel_between_devices_preserves_completed_result(self):
        cancelled=[False]
        async def apply(*args):cancelled[0]=True;return radio()
        with tempfile.TemporaryDirectory() as folder,patch('batch.apply_device',apply):
            report,_=await apply_many(self.plans(),folder,lambda:cancelled[0])
        self.assertEqual([r['status'] for r in report['devices']],['Verified','Not attempted','Not attempted'])

    async def test_noop_does_not_claim_fresh_verification(self):
        plans=plan_many([radio()],{'settings':{'bandwidth':62.5}})
        mock=AsyncMock()
        with tempfile.TemporaryDirectory() as folder,patch('batch.apply_device',mock):
            report,_=await apply_many(plans,folder)
        self.assertEqual(report['devices'][0]['status'],'No changes at review')
        mock.assert_not_awaited()

if __name__=='__main__':unittest.main()
