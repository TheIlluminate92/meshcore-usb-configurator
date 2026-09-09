"""Compare reported data without exposing channel secrets in the view."""
from model import FIELDS, display, equal, changes

def rows(snapshots,document=None):
    result=[]
    keys=set().union(*(s['settings'].keys() for s in snapshots))
    if document:keys.update(document.get('settings',{}))
    for key in FIELDS:
        if key not in keys:continue
        values=[s['settings'].get(key) for s in snapshots]
        selected=document is not None and key in document.get('settings',{})
        target=document['settings'][key] if selected else None
        available=all(v is not None for v in values)
        different=not available or any(not equal(key,values[0],v) for v in values[1:])
        mismatch=selected and any(v is None or not equal(key,v,target) for v in values)
        status='Not reported' if not available else 'Profile mismatch' if mismatch else 'Different' if different else 'Same'
        result.append((FIELDS[key][0],status,display(key,target) if selected else '—',*[display(key,v) if v is not None else 'Not reported' for v in values]))
    channels=[{c['index']:c for c in s.get('channels',[])} for s in snapshots]
    desired={c['index']:c for c in document.get('channels',[])} if document else {}
    for index in sorted(set(desired).union(*(set(c) for c in channels))):
        values=[c.get(index) for c in channels]
        for field,label in [('name','name'),('secret','key')]:
            vals=[v[field] if v else None for v in values]
            target=desired.get(index)
            available=all(v is not None for v in vals)
            different=not available or any(v!=vals[0] for v in vals[1:])
            mismatch=target is not None and any(v!=target[field] for v in vals)
            status='Not reported' if not available else 'Profile mismatch' if mismatch else 'Different' if different else 'Same'
            if field=='secret':
                shown=['Not reported' if v is None else ('Matches profile' if v==target[field] else 'Differs from profile') if target else ('Matches first' if v==vals[0] else 'Differs from first') for v in vals]
                wanted='Hidden' if target else '—'
            else:shown=[v or '(empty)' if v is not None else 'Not reported' for v in vals];wanted=(target[field] or '(empty)') if target else '—'
            result.append((f'Channel {index} {label}',status,wanted,*shown))
    return result

def verify_expected(snapshot,expected):
    mismatch=list(changes(snapshot['settings'],expected.get('settings',{})))
    channels={c['index']:c for c in snapshot.get('channels',[])}
    mismatch.extend(f"channel {c['index']}" for c in expected.get('channels',[]) if channels.get(c['index'])!=c)
    return mismatch

def profile_text(document):
    lines=[document.get('name','Profile'),'',document.get('description',''),'']
    if document.get('cli_settings'):
        lines.extend(['SETUP REFERENCE ONLY — not writable with the Companion interface.',document.get('source',''),''])
        lines.extend(f'{k}: {v}' for k,v in document['cli_settings'].items())
        lines.extend(document.get('advice',[]))
    naming=document.get('naming',{})
    lines.append(f"Naming: {naming.get('prefix','Tracker')}-{naming.get('start',1):02d}, … (suggestion only)")
    lines.extend(f'{FIELDS[k][0]}: {display(k,v)}' for k,v in document['settings'].items())
    lines.extend(f"Channel {c['index']}: {c['name'] or '(empty)'} — key hidden" for c in document.get('channels',[]))
    lines.extend(['','Only these fields/slots are included. Other settings stay unchanged.'])
    return '\n'.join(lines)
