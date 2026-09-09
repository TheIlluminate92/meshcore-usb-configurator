"""Versioned profiles; browser exports use kHz/Hz, commands use MHz/kHz."""
import json
import math

FIELDS = {
    'name': ('Device name', str, None, None),
    'frequency': ('Frequency (MHz)', float, 150, 2500),
    'bandwidth': ('Bandwidth (kHz)', float, 7.8, 500),
    'spreading_factor': ('Spreading factor', int, 5, 12),
    'coding_rate': ('Coding rate', int, 5, 8),
    'tx_power': ('Transmit power (dBm)', int, 0, 22),
    'latitude': ('Latitude', float, -90, 90),
    'longitude': ('Longitude', float, -180, 180),
}
RADIO = ('frequency', 'bandwidth', 'spreading_factor', 'coding_rate')
COORDS = ('latitude', 'longitude')

def validate(settings, maximum_power=22):
    if not isinstance(settings, dict):
        raise ValueError('Settings must be a JSON object.')
    result = {}
    for key, value in settings.items():
        if key not in FIELDS:
            raise ValueError(f'Unsupported editable option: {key}')
        label, kind, low, high = FIELDS[key]
        if kind is str:
            if not isinstance(value, str) or not value.strip() or '\x00' in value or len(value.encode('utf-8')) > 31:
                raise ValueError('Name must contain 1–31 UTF-8 bytes and no null characters.')
            result[key] = value
            continue
        if isinstance(value, bool):
            raise ValueError(f'{label} must be a number.')
        try:
            number = float(value)
        except (ValueError, TypeError):
            raise ValueError(f'{label} must be a number.') from None
        if key == 'tx_power':
            high = min(high, maximum_power)
        if not math.isfinite(number) or not low <= number <= high or (kind is int and not number.is_integer()):
            raise ValueError(f'{label} must be {low} to {high}' + (' (whole number).' if kind is int else '.'))
        result[key] = kind(number)
    return result

def load_profile(path):
    data = json.loads(path.read_text(encoding='utf-8-sig'))
    if not isinstance(data, dict):
        raise ValueError('Profile must be a JSON object.')
    if 'schema_version' in data:
        if data['schema_version'] != 1 or data.get('format') != 'meshcore-usb-profile':
            raise ValueError('Unrecognized profile format or version.')
        return validate(data['settings'])
    if not {'name', 'radio_settings', 'position_settings'} <= data.keys():
        raise ValueError('Expected a MeshCore browser export or configurator profile.')
    radio = data['radio_settings']
    values = {'name': data['name']}
    for key in RADIO + ('tx_power',):
        if key in radio:
            values[key] = radio[key] / (1000 if key in ('frequency', 'bandwidth') else 1)
    values.update({k: v for k, v in data['position_settings'].items() if k in COORDS})
    return validate(values)

def profile(settings):
    return {'format': 'meshcore-usb-profile', 'schema_version': 1,
            'units': {'frequency': 'MHz', 'bandwidth': 'kHz', 'tx_power': 'dBm'},
            'settings': validate(settings)}

def equal(key, a, b):
    if key in ('frequency', 'bandwidth'):
        return abs(float(a) - float(b)) < .0011
    if key in COORDS:
        return abs(float(a) - float(b)) < .0000011
    return a == b

def changes(current, desired):
    return {k: v for k, v in desired.items() if k not in current or not equal(k, current[k], v)}
