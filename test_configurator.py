import asyncio
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace
from model import load_profile, validate, profile, changes
import device

BASE = {'port': 'COM4', 'device': {'ver': '1.17.1'},
        'self_info': {'public_key': 'abc', 'max_tx_power': 22},
        'settings': {'name': 'Test', 'frequency': 910.525, 'bandwidth': 62.5,
                     'spreading_factor': 7, 'coding_rate': 5, 'tx_power': 22,
                     'latitude': 0., 'longitude': 0.}}

class Profiles(unittest.TestCase):
    def test_browser_units(self):
        # Synthetic fixture: tests must never depend on private device exports.
        export = {'name': 'Example', 'radio_settings': {'frequency': 869618,
                  'bandwidth': 62500, 'spreading_factor': 8, 'coding_rate': 5,
                  'tx_power': 22}, 'position_settings': {'latitude': '0', 'longitude': '0'}}
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'export.json'
            path.write_text(json.dumps(export), encoding='utf-8')
            values = load_profile(path)
        self.assertEqual(values['frequency'], 869.618)
        self.assertEqual(values['bandwidth'], 62.5)

    def test_profile_roundtrip(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'p.json'
            path.write_text(json.dumps(profile(BASE['settings'])))
            self.assertEqual(load_profile(path), BASE['settings'])

    def test_bad_values(self):
        for values in [{'name': 'é' * 16}, {'frequency': float('nan')},
                       {'tx_power': 23}, {'spreading_factor': 7.5},
                       {'frequency': True}, {'private_key': 'abc'}]:
            with self.subTest(values=values), self.assertRaises(ValueError):
                validate(values)

    def test_hardware_max(self):
        with self.assertRaises(ValueError):
            validate({'tx_power': 20}, maximum_power=14)

    def test_precision(self):
        self.assertTrue(changes({'latitude': 1.000001}, {'latitude': 1.000002}))
        self.assertFalse(changes({'latitude': 1.000001}, {'latitude': 1.00000100001}))
        self.assertTrue(changes({'frequency': 910.525}, {'frequency': 910.526}))
        self.assertTrue(changes({'frequency': 910.525}, {'frequency': 910.527}))

class Writes(unittest.IsolatedAsyncioTestCase):
    async def test_radio_preserves_repeat(self):
        current = copy.deepcopy(BASE)
        current['device'].update({'fw ver': 9, 'repeat': True})
        baseline = copy.deepcopy(current)
        calls = []
        async def send(packet, expected):
            import struct
            _, freq, bw, sf, cr, repeat = struct.unpack('<BIIBBB', packet)
            calls.append(repeat)
            current['settings'].update(frequency=freq / 1000, bandwidth=bw / 1000, spreading_factor=sf, coding_rate=cr)
            current['device']['repeat'] = bool(repeat)
            return SimpleNamespace(type=SimpleNamespace(name='OK'), payload={})
        mc = SimpleNamespace(commands=SimpleNamespace(send=send))
        async def operate(port, action):
            return await action(mc)
        async def basic(*args):
            return copy.deepcopy(current)
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(device, 'operate', operate), patch.object(device, 'basic', basic):
                await device.apply_device('COM4', baseline, {'spreading_factor': 8}, folder)
        self.assertEqual(calls, [1])

    async def test_radio_without_reported_repeat_blocked(self):
        altered = copy.deepcopy(BASE)
        altered['device']['fw ver'] = 9
        _, error, writes, _ = await self.exercise({'spreading_factor': 8}, altered=altered)
        self.assertIn('did not report repeat', str(error))
        self.assertFalse(writes)

    async def exercise(self, desired, *, altered=None, reject=False, mismatch=False):
        current = copy.deepcopy(altered or BASE)
        writes = []
        async def set_name(value):
            writes.append(value)
            if not mismatch:
                current['settings']['name'] = value
            return SimpleNamespace(type=SimpleNamespace(name='ERROR' if reject else 'OK'), payload={})
        mc = SimpleNamespace(commands=SimpleNamespace(set_name=set_name))
        async def operate(port, action):
            return await action(mc)
        async def basic(*args):
            return copy.deepcopy(current)
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(device, 'operate', operate), patch.object(device, 'basic', basic):
                try:
                    result = await device.apply_device('COM4', BASE, desired, folder)
                    error = None
                except Exception as exc:
                    result, error = None, exc
            reports = [json.loads(p.read_text()) for p in Path(folder).glob('*.json')]
        return result, error, writes, reports

    async def test_success_verified(self):
        result, error, writes, reports = await self.exercise({'name': 'New'})
        self.assertIsNone(error)
        self.assertEqual(writes, ['New'])
        self.assertTrue(reports[0]['verified'])
        self.assertEqual(result['settings']['name'], 'New')

    async def test_wrong_device_no_write(self):
        altered = copy.deepcopy(BASE)
        altered['self_info']['public_key'] = 'other'
        _, error, writes, _ = await self.exercise({'name': 'New'}, altered=altered)
        self.assertIsNotNone(error)
        self.assertFalse(writes)

    async def test_stale_no_write(self):
        altered = copy.deepcopy(BASE)
        altered['settings']['name'] = 'Changed elsewhere'
        _, error, writes, _ = await self.exercise({'name': 'New'}, altered=altered)
        self.assertIsNotNone(error)
        self.assertFalse(writes)

    async def test_rejected_write_not_verified(self):
        _, error, _, reports = await self.exercise({'name': 'New'}, reject=True)
        self.assertIsNotNone(error)
        self.assertFalse(reports[0]['verified'])

    async def test_mismatch_not_verified(self):
        _, error, _, reports = await self.exercise({'name': 'New'}, mismatch=True)
        self.assertIsNotNone(error)
        self.assertFalse(reports[0]['verified'])

    async def test_invalid_profile_no_write(self):
        _, error, writes, _ = await self.exercise({'tx_power': 99})
        self.assertIsNotNone(error)
        self.assertFalse(writes)

    async def test_noop(self):
        _, error, writes, reports = await self.exercise({'name': 'Test'})
        self.assertIsNone(error)
        self.assertFalse(writes)
        self.assertTrue(reports[0]['verified'])

if __name__ == '__main__':
    unittest.main()
