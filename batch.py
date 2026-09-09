"""Reviewed per-device plans; sequential writes, stop on failure or cancellation."""
import copy
from datetime import datetime
from pathlib import Path
from model import validate, validate_channels, changes, RADIO, COORDS, OTHER
from device import apply_device, save_json, MAP

def plan_device(snapshot, document):
    settings=validate(document['settings'],snapshot['self_info'].get('max_tx_power',0))
    missing=set(settings)-set(snapshot['settings'])
    if missing:
        raise ValueError('Settings not supported/reported: '+', '.join(sorted(missing)))
    delta=changes(snapshot['settings'],settings)
    merged=snapshot['settings'] | settings
    if set(COORDS)&delta.keys() and merged.get('gps')==1:
        raise ValueError('Fixed coordinates conflict with enabled GPS.')
    for group in (RADIO,COORDS):
        if set(group)&delta.keys() and not set(group)<=merged.keys():
            raise ValueError('Incomplete grouped settings response.')
    if set(OTHER)&delta.keys() and not all(MAP[k] in snapshot['self_info'] for k in OTHER):
        raise ValueError('Incomplete shared contact/telemetry response.')
    if set(RADIO)&delta.keys() and snapshot['device'].get('fw ver',0)>=9 and type(snapshot['device'].get('repeat')) is not bool:
        raise ValueError('Repeat mode was not reported; radio changes blocked.')
    known={c['index']:c for c in snapshot.get('channels',[])}
    channels=[]
    for c in validate_channels(document.get('channels',[])):
        if c['index'] not in known:
            raise ValueError(f"Channel slot {c['index']} was not read on this device.")
        if c!=known[c['index']]: channels.append(c)
    if not snapshot['self_info'].get('public_key'):
        raise ValueError('Device identity was not reported.')
    return copy.deepcopy({'port':snapshot['port'],'baseline':snapshot,'settings':delta,'channels':channels})

def plan_many(snapshots, document, individual=None):
    plans=[]
    seen=set()
    names=set()
    for snapshot in snapshots:
        identity=snapshot['self_info'].get('public_key')
        if identity in seen:
            raise ValueError('The same radio is selected more than once. Select only one connection per radio.')
        seen.add(identity)
        target=copy.deepcopy(document)
        if individual is not None:
            if identity not in individual:
                raise ValueError('Complete the individual-device step for every selected radio.')
            values=validate(individual[identity])
            if set(values)-{'name','latitude','longitude'}:
                raise ValueError('Individual values may only contain name and fixed coordinates.')
            if 'name' not in values:raise ValueError('Every device needs a name.')
            name=values['name'].strip().casefold()
            if name in names:raise ValueError('Each selected device must have a different name.')
            names.add(name)
            target['settings'].update(values)
        plans.append(plan_device(snapshot,target))
    if not plans: raise ValueError('Select and read at least one device.')
    return plans

async def apply_many(plans, folder, cancelled=lambda:False, progress=lambda *args:None):
    report={'started_at':datetime.now().isoformat(),'devices':[]}
    path=Path(folder)/('batch-'+datetime.now().strftime('%Y%m%d-%H%M%S-%f')+'.json')
    stopped=False
    for plan in plans:
        item={'port':plan['port'],'name':plan['baseline']['settings'].get('name','?'),'status':'Not attempted'}
        report['devices'].append(item)
        save_json(path,report)
        if stopped or cancelled():
            stopped=True
            progress(plan['port'],item['status'])
            continue
        if not plan['settings'] and not plan['channels']:
            item['status']='No changes at review'
        else:
            progress(plan['port'],'Writing and verifying…')
            try:
                item['after']=await apply_device(plan['port'],plan['baseline'],plan['settings'],folder,plan['channels'])
                item['status']='Verified'
            except Exception as exc:
                item['status']='Failed — reread required'
                item['error']=str(exc)
                stopped=True
        save_json(path,report)
        progress(plan['port'],item['status'])
    save_json(path,report)
    return report,path
