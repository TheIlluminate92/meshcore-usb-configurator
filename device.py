"""Read/write adapter for supported MeshCore Companion commands over USB."""
import asyncio
from datetime import datetime, timezone
from pathlib import Path
import json
from model import RADIO, COORDS, validate, changes

MAP = {'name': 'name', 'frequency': 'radio_freq', 'bandwidth': 'radio_bw',
       'spreading_factor': 'radio_sf', 'coding_rate': 'radio_cr',
       'tx_power': 'tx_power', 'latitude': 'adv_lat', 'longitude': 'adv_lon'}

def serial_ports():
    from serial.tools import list_ports
    return [(p.device, p.description) for p in list_ports.comports()]

def save_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=lambda x: x.hex() if isinstance(x, bytes) else str(x)), encoding='utf-8')

async def event(call, expected):
    reply = await asyncio.wait_for(call, 15)
    if reply is None or reply.type.name != expected:
        raise RuntimeError(f'Expected {expected}: {getattr(reply, "payload", "no reply")}')
    return reply.payload

async def basic(mc, port):
    info = await event(mc.commands.send_device_query(), 'DEVICE_INFO')
    own = await event(mc.commands.send_appstart(), 'SELF_INFO')
    return {'captured_at': datetime.now(timezone.utc).isoformat(), 'port': port,
            'device': info, 'self_info': own,
            'settings': {k: own[v] for k, v in MAP.items() if v in own}}

async def operate(port, action):
    from meshcore import MeshCore
    from serial_connection import ClosingSerialConnection
    connection = ClosingSerialConnection(port, 115200)
    mc = MeshCore(connection, only_error=True, default_timeout=5, auto_reconnect=False)
    try:
        try:
            response = await asyncio.wait_for(mc.connect(), 15)
        except Exception as exc:
            if isinstance(exc, PermissionError) or 'Access is denied' in str(exc):
                raise RuntimeError(f'{port} is busy or Windows denied access. Close other browser/app connections to this port. If an older configurator is open, close it and reopen the updated version. No configuration commands were sent by this operation.') from exc
            raise
        if response is None:
            raise RuntimeError('No Companion USB response. Check firmware and close other apps using this port.')
        return await action(mc)
    finally:
        try:
            await mc.disconnect()
        finally:
            # Also clean up a partially established connection that the
            # connection manager did not yet mark as connected.
            await connection.disconnect()

async def read_device(port):
    async def read(mc):
        snapshot = await basic(mc, port)
        snapshot['read_errors'] = {}
        for name, method, expected in [('custom_vars', mc.commands.get_custom_vars, 'CUSTOM_VARS'),
                                        ('contacts', mc.commands.get_contacts, 'CONTACTS')]:
            try:
                snapshot[name] = await event(method(), expected)
            except Exception as exc:
                snapshot['read_errors'][name] = str(exc)
        snapshot['channels'] = []
        count = snapshot['device'].get('max_channels', 0)
        for index in range(min(count, 64)):
            try:
                payload = await event(mc.commands.get_channel(index), 'CHANNEL_INFO')
                snapshot['channels'].append({'index': index, **payload})
            except Exception as exc:
                snapshot['read_errors'][f'channel_{index}'] = str(exc)
                break
        return snapshot
    return await operate(port, read)

async def apply_device(port, baseline, desired, report_dir):
    """One device per transaction; no retries or rollback after uncertain writes."""
    async def apply(mc):
        current = await basic(mc, port)
        if current['self_info']['public_key'] != baseline['self_info']['public_key']:
            raise ValueError('A different device is connected. Read it before applying.')
        if changes(current['settings'], baseline['settings']):
            raise ValueError('Device settings changed since the last read. Read and review again.')
        values = validate(desired, current['self_info'].get('max_tx_power', 0))
        if set(values) - set(current['settings']):
            raise ValueError('Profile contains settings this device did not report.')
        delta = changes(current['settings'], values)
        merged = current['settings'] | values
        for group in (RADIO, COORDS):
            if set(group) & delta.keys() and not set(group) <= merged.keys():
                raise ValueError('Device did not report all fields needed by this command.')
        report = {'before': current, 'requested': delta, 'acknowledged': [], 'verified': False}
        stamp = datetime.now().strftime('%Y%m%d-%H%M%S-%f')
        report_path = Path(report_dir) / f'apply-{port}-{stamp}.json'
        save_json(report_path, report)
        try:
            jobs = []
            if 'name' in delta:
                jobs.append(('name', lambda: mc.commands.set_name(merged['name'])))
            if set(RADIO) & delta.keys():
                jobs.append(('radio', lambda: mc.commands.set_radio(*(merged[k] for k in RADIO))))
            if 'tx_power' in delta:
                jobs.append(('tx_power', lambda: mc.commands.set_tx_power(merged['tx_power'])))
            if set(COORDS) & delta.keys():
                jobs.append(('coordinates', lambda: mc.commands.set_coords(*(merged[k] for k in COORDS))))
            for label, command in jobs:
                await event(command(), 'OK')
                report['acknowledged'].append(label)
                save_json(report_path, report)
            after = await basic(mc, port)
            report['after'] = after
            mismatch = changes(after['settings'], values)
            if mismatch:
                raise RuntimeError(f'Read-back mismatch in: {", ".join(mismatch)}')
            report['verified'] = True
            return after
        except Exception as exc:
            report['error'] = str(exc)
            raise RuntimeError(f'{exc}\nSome settings may have changed. Read the device again.\nReport: {report_path}') from exc
        finally:
            save_json(report_path, report)
    return await operate(port, apply)
