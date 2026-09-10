"""Export an offline preview of current intent, never issue radio operations."""
import copy
from datetime import datetime, timezone
from model import FIELDS,display,equal
from compatibility import review
from device import save_json


def document(snapshots, profile, individual=None, unread=None):
    result={'format':'meshcore-dry-run','created':datetime.now(timezone.utc).isoformat(),'profile':profile.get('name','Editor'),
            'notice':'Preview only from saved reads; not a write or verification. Review again before applying. Names/locations may be present; channel keys are excluded.', 'devices':[]}
    from batch import plan_many
    result['batch_blockers']=[]
    try:plan_many(snapshots,profile,individual)
    except ValueError as exc:result['batch_blockers'].append(str(exc))
    if unread:result['batch_blockers'].append('Some selected devices have not been read.')
    for snapshot in snapshots:
        target=copy.deepcopy(profile)
        identity=snapshot.get('self_info',{}).get('public_key')
        if individual and identity in individual:target['settings'].update(individual[identity])
        statuses,blocked=review(snapshot,target)
        status_map=dict(statuses)
        rows=[]
        for k,v in target['settings'].items():
            old=snapshot['settings'].get(k)
            rows.append({'setting':FIELDS[k][0],'before':display(k,old) if old is not None else 'Not reported','after':display(k,v),'status':status_map[FIELDS[k][0]]})
        old={c['index']:c for c in snapshot.get('channels',[])}
        for c in target.get('channels',[]):
            previous=old.get(c['index'])
            rows.append({'channel':c['index'],'before_name':previous['name'] if previous else 'Not reported','after_name':c['name'],
                         'key_changes':previous is not None and previous['secret']!=c['secret'],'status':status_map[f"Channel {c['index']}"]})
        result['devices'].append({'name':snapshot['settings'].get('name','?'),'connection':snapshot['port'],'read_at':snapshot.get('captured_at'),
                                  'blocked':blocked,'individual_naming_reviewed':individual is not None and identity in individual,'changes':rows})
    for port in unread or []:result['devices'].append({'connection':port,'blocked':'Device has not been read','changes':[]})
    return result


def export(path,snapshots,profile,individual=None,unread=None):
    data=document(snapshots,profile,individual,unread)
    save_json(path,data)
    return data
