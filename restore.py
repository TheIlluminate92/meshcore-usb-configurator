"""Undo only fields changed by a saved apply report, bound to radio identity."""
import json
from pathlib import Path
from model import profile
from batch import plan_device


def restore_document(report, snapshot):
    before = report.get('before', {})
    identity = before.get('self_info', {}).get('public_key')
    if not identity or identity != snapshot.get('self_info', {}).get('public_key'):
        raise ValueError('This backup belongs to a different radio. Read the original radio first.')
    original = before.get('settings', {})
    requested = report.get('requested', {})
    if not isinstance(requested, dict) or set(requested) - set(original):
        raise ValueError('Backup is missing original values; restore is blocked.')
    old_channels = {c['index']: c for c in report.get('channels_before', [])}
    wanted = report.get('channels_requested', [])
    if any(c['index'] not in old_channels for c in wanted):
        raise ValueError('Backup is missing original channel values; restore is blocked.')
    data = profile({k: original[k] for k in requested}, [old_channels[c['index']] for c in wanted])
    if not data['settings'] and not data['channels']:
        raise ValueError('This operation did not request any changes to restore.')
    plan_device(snapshot, data)
    return data


def backups(folder, identity):
    found, unreadable = [], 0
    if not identity:
        return found, unreadable
    for path in sorted(Path(folder).glob('apply-*.json'), reverse=True):
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
            if data.get('before', {}).get('self_info', {}).get('public_key') != identity:
                continue
            if not data.get('requested') and not data.get('channels_requested'):
                continue
            found.append((path, data))
        except (ValueError, OSError, AttributeError, TypeError):
            unreadable += 1
    def captured(item):
        from datetime import datetime
        try:return datetime.fromisoformat(item[1]['before']['captured_at']).timestamp()
        except (KeyError,TypeError,ValueError):return item[0].stat().st_mtime
    found.sort(key=captured, reverse=True)
    return found, unreadable
