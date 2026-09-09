"""Regression cases from the Companion 1.17.1 protocol audit."""
import copy
import json
import struct
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import device
from model import validate, load_profile
from test_configurator import BASE

class Audit(unittest.IsolatedAsyncioTestCase):
    async def test_signed_power_read(self):
        def response(name, payload):
            return SimpleNamespace(type=SimpleNamespace(name=name), payload=payload)
        async def query(): return response('DEVICE_INFO', {})
        async def own(): return response('SELF_INFO', {'tx_power': 247})
        async def custom(): return response('CUSTOM_VARS', {})
        async def auto(): return response('AUTOADD_CONFIG', {})
        commands=SimpleNamespace(send_device_query=query, send_appstart=own,
                                 get_custom_vars=custom, get_autoadd_config=auto)
        result=await device.basic(SimpleNamespace(commands=commands), 'TEST')
        self.assertEqual(result['settings']['tx_power'], -9)

    async def test_signed_power_and_coordinates_write_and_verify(self):
        state=copy.deepcopy(BASE)
        baseline=copy.deepcopy(state)
        sent=[]
        async def basic(*args): return copy.deepcopy(state)
        async def send(packet, expected):
            sent.append(packet)
            if packet[0]==12:
                state['settings']['tx_power']=struct.unpack('<Bb',packet)[1]
            elif packet[0]==14:
                _,lat,lon,alt=struct.unpack('<Biii',packet)
                self.assertEqual(alt,0)
                state['settings'].update(latitude=lat/1e6,longitude=lon/1e6)
            return SimpleNamespace(type=SimpleNamespace(name='OK'),payload={})
        async def operate(port, action):
            return await action(SimpleNamespace(commands=SimpleNamespace(send=send)))
        with tempfile.TemporaryDirectory() as folder, patch.object(device,'operate',operate), patch.object(device,'basic',basic):
            result=await device.apply_device('TEST',baseline,{'tx_power':-9,'latitude':-12.345678,'longitude':34.000001},folder)
        self.assertEqual(sent[0],bytes([12,247]))
        self.assertEqual(result['settings']['latitude'],-12.345678)
        self.assertEqual(result['snapshot_scope']['kind'],'apply_verification')

    def test_radio_avoids_float_truncation(self):
        values=BASE['settings'] | {'frequency':910.001,'bandwidth':62.501}
        self.assertEqual(struct.unpack('<BIIBB',device.radio_packet(values)),(11,910001,62501,7,5))

    def test_conflicting_profile_units_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'profile.json'
            path.write_text(json.dumps({'format':'meshcore-usb-profile','schema_version':2,
                                        'units':{'frequency':'kHz'},'settings':{'frequency':910.525}}))
            with self.assertRaisesRegex(ValueError,'units'):
                load_profile(path)

    def test_negative_power_bounds(self):
        self.assertEqual(validate({'tx_power':-9}),{'tx_power':-9})
        with self.assertRaises(ValueError): validate({'tx_power':-10})

if __name__=='__main__': unittest.main()
