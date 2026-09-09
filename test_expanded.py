import copy
import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import device
from model import OTHER, AUTO_BITS, validate_channels, load_document, display, parse_input, FIELDS
from test_configurator import BASE


def reply(payload=None):
    return SimpleNamespace(type=SimpleNamespace(name='OK'), payload=payload or {})


class Expanded(unittest.IsolatedAsyncioTestCase):
    async def execute(self, desired, channels=None, mismatch=False, baseline_change=None):
        state = copy.deepcopy(BASE)
        state['self_info'].update({device.MAP[k]: 0 for k in OTHER})
        state['self_info']['multi_acks'] = 2
        state['settings'].update({k: state['self_info'][device.MAP[k]] for k in OTHER})
        state['settings'].update({k: 0 for k in AUTO_BITS})
        state['settings'].update(auto_add_max_hops=3, gps=0, gps_interval=60, path_hash_mode=0)
        state['auto_add'] = {'config': 128, 'max_hops': 3}  # unknown bit must survive
        state['channels'] = [{'index': 0, 'name': 'Original', 'secret': '11'*16}]
        baseline = copy.deepcopy(state)
        if baseline_change:
            baseline_change(baseline)
        sent = []
        async def basic(*args):
            return copy.deepcopy(state)
        async def read_channel(mc, index):
            return copy.deepcopy(state['channels'][index])
        async def shared(values):
            sent.append(('shared', dict(values)))
            state['self_info'].update(values)
            state['settings'].update({k: values[device.MAP[k]] for k in OTHER})
            return reply()
        async def custom(key, value):
            sent.append((key, value))
            state['settings'][key] = int(value)
            return reply()
        async def send(packet, expected):
            sent.append(packet)
            if packet[0] == 58:
                state['auto_add']['config'] = packet[1]
                if len(packet) == 3:
                    state['auto_add']['max_hops'] = packet[2]
                    state['settings']['auto_add_max_hops'] = packet[2]
                state['settings'].update({k: int(bool(packet[1] & bit)) for k, bit in AUTO_BITS.items()})
            elif packet[0] == 32 and not mismatch:
                state['channels'][packet[1]] = {'index': packet[1], 'name': packet[2:34].split(b'\0')[0].decode(), 'secret': packet[34:50].hex()}
            return reply()
        mc = SimpleNamespace(commands=SimpleNamespace(set_other_params_from_infos=shared, send=send, set_custom_var=custom))
        async def operate(port, action):
            return await action(mc)
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(device, 'basic', basic), patch.object(device, 'operate', operate), patch.object(device, 'read_channel', read_channel):
                try:
                    result = await device.apply_device('COM4', baseline, desired, folder, channels)
                    error = None
                except Exception as exc:
                    result, error = None, exc
        return result, error, sent

    async def test_shared_settings_preserve_neighbours(self):
        result, error, sent = await self.execute({'advert_location_policy': 1})
        self.assertIsNone(error)
        self.assertEqual(result['self_info']['multi_acks'], 2)
        self.assertEqual(result['settings']['telemetry_mode_loc'], 0)
        self.assertEqual(sent[0][1]['adv_loc_policy'], 1)

    async def test_auto_flags_preserve_unknown_bits_and_hops(self):
        result, error, sent = await self.execute({'auto_add_repeater': 1})
        self.assertIsNone(error)
        self.assertEqual(sent, [bytes([58, 132, 3])])
        self.assertEqual(result['auto_add'], {'config': 132, 'max_hops': 3})

    async def test_auto_hop_limit(self):
        result, error, sent = await self.execute({'auto_add_max_hops': 64})
        self.assertIsNone(error)
        self.assertEqual(sent, [bytes([58, 128, 64])])

    async def test_hash_channel_preserves_explicit_secret(self):
        channel = {'index': 0, 'name': '#team', 'secret': 'ab'*16}
        result, error, sent = await self.execute({}, [channel])
        self.assertIsNone(error)
        self.assertEqual(sent[0][34:], bytes.fromhex(channel['secret']))
        self.assertEqual(result['channels'], [channel])

    async def test_channel_mismatch_fails(self):
        _, error, _ = await self.execute({}, [{'index': 0, 'name': 'New', 'secret': 'ab'*16}], mismatch=True)
        self.assertIn('Read-back mismatch', str(error))

    async def test_stale_channel_prevents_all_writes(self):
        _, error, sent = await self.execute({'advert_location_policy': 1},
                    [{'index': 0, 'name': 'New', 'secret': 'ab'*16}],
                    baseline_change=lambda b: b['channels'][0].update(name='Stale'))
        self.assertIn('changed since', str(error))
        self.assertFalse(sent)

    async def test_gps_and_fixed_position_conflict_prevents_write(self):
        _, error, sent = await self.execute({'gps': 1, 'latitude': 20.0})
        self.assertIn('Turn GPS off', str(error))
        self.assertFalse(sent)

    async def test_gps_toggle_verifies(self):
        result, error, sent = await self.execute({'gps': 1})
        self.assertIsNone(error)
        self.assertEqual(sent, [('gps', '1')])
        self.assertEqual(result['settings']['gps'], 1)


class ImportAndControls(unittest.TestCase):
    def test_full_browser_mapping_without_identity(self):
        export = {'name': 'Synthetic', 'radio_settings': {}, 'position_settings': {},
                  'other_settings': {'manual_add_contacts': 0, 'advert_location_policy': 1},
                  'auto_add_settings': {'auto_add_chat': True, 'auto_add_max_hops': 1},
                  'private_key': 'not-a-real-key', 'contacts': [{'name': 'Example'}],
                  'channels': [{'name': 'Team', 'secret': 'ab'*16, 'message_retention_duration_seconds': 100}]}
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'export.json'
            path.write_text(json.dumps(export), encoding='utf-8')
            settings, channels, notes = load_document(path)
        self.assertEqual(settings['advert_location_policy'], 1)
        self.assertEqual(settings['auto_add_chat'], 1)
        self.assertNotIn('private_key', settings)
        self.assertEqual(channels, [{'index': 0, 'name': 'Team', 'secret': 'ab'*16}])
        self.assertTrue(notes)

    def test_channel_validation(self):
        for channels in [[{'index': 0, 'name': 'x', 'secret': 'aa'*15}],
                         [{'index': 0, 'name': 'x', 'secret': 'aa'*15+'  '}],
                         [{'index': 0, 'name': 'é'*16, 'secret': 'aa'*16}],
                         [{'index': 0, 'name': 'x', 'secret': 'aa'*16}]*2]:
            with self.assertRaises(ValueError):
                validate_channels(channels)

    def test_control_labels_roundtrip(self):
        from model import CHOICES
        for key, choices in CHOICES.items():
            for value in choices:
                self.assertEqual(parse_input(key, display(key, value)), value)


if __name__ == '__main__':
    unittest.main()
