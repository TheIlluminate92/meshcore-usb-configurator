"""Atomic portable-data backup with a consistent SQLite copy."""
import json
import os
import sqlite3
import tempfile
from contextlib import closing
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from app_version import VERSION

FOLDERS = ('profiles','data','snapshots','reports','logs')
FILES = ('preferences.json','startup-error.log')


def create_backup(destination, data_root, executable=None):
    destination=Path(destination).resolve();root=Path(data_root).resolve()
    # Keep the backup outside live data, avoiding recursive backups and source replacement.
    if destination == root or root in destination.parents:
        raise ValueError('Save the backup outside the User Data folder (or outside the project folder when running from source).')
    if executable and destination == Path(executable).resolve():
        raise ValueError('Choose a ZIP file, not the running executable.')
    if destination.suffix.lower()!='.zip':raise ValueError('Choose a .zip filename.')
    destination.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='meshcore-backup-') as scratch:
        temp=destination.parent / ('.'+destination.name+'.'+__import__('uuid').uuid4().hex+'.tmp')
        count=0
        try:
            with zipfile.ZipFile(temp,'w',compression=zipfile.ZIP_DEFLATED) as archive:
                candidates=[root/name for name in FILES if (root/name).is_file()]
                for name in FOLDERS:
                    base=root/name
                    if base.exists():candidates.extend(p for p in base.rglob('*') if p.is_file())
                for path in candidates:
                    if path.is_symlink() or not path.resolve().is_relative_to(root):
                        raise ValueError('A saved-data link points outside the portable data folder.')
                    if path.name.endswith(('-wal','-shm','-journal')):continue
                    target='MeshCore Configurator/User Data/'+path.relative_to(root).as_posix()
                    if path == root/'data'/'history.sqlite3':
                        copy=Path(scratch)/'history.sqlite3'
                        with closing(sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)) as source,closing(sqlite3.connect(copy)) as backup:
                            source.backup(backup)
                        archive.write(copy,target)
                    else:archive.write(path,target)
                    count+=1
                if executable:
                    archive.write(executable,'MeshCore Configurator/! MeshCore Configurator.exe');count+=1
                archive.writestr('BACKUP.json',json.dumps({'format':'meshcore-portable-backup','version':VERSION,'created':datetime.now(timezone.utc).isoformat(),'files':count,'includes_executable':bool(executable),'excludes':['downloaded update installers','old executable update backups'],'restore':'Close the app. Extract into a separate folder. If no EXE is included, put a compatible portable EXE beside User Data. Do not merge over an app that is running.','private':'Contains private local profiles, channel keys and saved device data. Do not attach this backup to public support issues.'},indent=2))
            with zipfile.ZipFile(temp) as archive:
                if archive.testzip():raise ValueError('Backup verification failed.')
            os.replace(temp,destination)
        finally:
            temp.unlink(missing_ok=True)
    return count
