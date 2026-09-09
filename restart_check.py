"""Read-only comparison after a user-reported restart, never an inferred reboot."""
from history_store import identity
from comparison import verify_expected
from device import read_device

async def check_restart(history,run_id,port,restart_attested):
    if not restart_attested:
        raise ValueError('Confirm a restart before recording a post-restart check.')
    records,_=history.details(run_id)
    eligible={r['identity']:r for r in records if r['status'] in ('Verified','No changes at review')}
    if not eligible:raise ValueError('No successfully completed devices in that run.')
    snapshot=await read_device(port)
    key=identity(snapshot)
    if key not in eligible:
        raise ValueError('This radio is not a successfully completed device from the selected run. Nothing was written.')
    mismatch=verify_expected(snapshot,eligible[key]['expected'])
    status='Mismatch after reported restart' if mismatch else 'Matches after reported restart'
    detail=', '.join(mismatch) if mismatch else 'Expected settings and channel slots match.'
    history.remember(snapshot)
    history.verify(run_id,snapshot,status,detail,True)
    return snapshot,status,detail
