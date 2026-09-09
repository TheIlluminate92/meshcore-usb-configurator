"""Project-local SQLite history. Each operation owns its connection/thread."""
import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

def now():return datetime.now(timezone.utc).isoformat()
def identity(snapshot):
    key=snapshot['self_info']['public_key']
    return key.hex() if isinstance(key,bytes) else str(key)

class HistoryStore:
    def __init__(self,path):
        self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.connect() as db:
            if db.execute('PRAGMA user_version').fetchone()[0]>1:
                raise ValueError('History was created by a newer app version. Open it with that version; the database was not changed.')
            db.executescript('''
            CREATE TABLE IF NOT EXISTS radios (
              identity TEXT PRIMARY KEY, name TEXT NOT NULL, model TEXT,
              last_port TEXT, first_seen TEXT NOT NULL, last_seen TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS runs (
              id TEXT PRIMARY KEY, profile TEXT NOT NULL, started TEXT NOT NULL,
              finished TEXT, status TEXT NOT NULL, report_path TEXT);
            CREATE TABLE IF NOT EXISTS results (
              run_id TEXT NOT NULL, identity TEXT NOT NULL, name TEXT NOT NULL,
              port TEXT NOT NULL, status TEXT NOT NULL, expected TEXT NOT NULL,
              error TEXT, PRIMARY KEY(run_id, identity));
            CREATE TABLE IF NOT EXISTS verifications (
              id INTEGER PRIMARY KEY, run_id TEXT NOT NULL, identity TEXT NOT NULL,
              checked TEXT NOT NULL, port TEXT NOT NULL, status TEXT NOT NULL,
              detail TEXT NOT NULL, restart_attested INTEGER NOT NULL);
            PRAGMA user_version=1;
            ''')

    @contextmanager
    def connect(self):
        db=sqlite3.connect(self.path,timeout=10)
        db.row_factory=sqlite3.Row
        try:
            with db:yield db
        finally:db.close()

    def remember(self,snapshot):
        key=identity(snapshot);stamp=now()
        with self.connect() as db:
            old=db.execute('SELECT * FROM radios WHERE identity=?',(key,)).fetchone()
            db.execute('''INSERT INTO radios VALUES (?,?,?,?,?,?) ON CONFLICT(identity)
              DO UPDATE SET name=excluded.name,model=excluded.model,last_port=excluded.last_port,last_seen=excluded.last_seen''',
              (key,snapshot['settings'].get('name','?'),snapshot['device'].get('model','?'),snapshot['port'],stamp,stamp))
        return dict(old) if old else None

    def radios(self):
        with self.connect() as db:return [dict(r) for r in db.execute('SELECT * FROM radios ORDER BY last_seen DESC')]

    def start(self,plans,profile,report_path):
        run_id=uuid.uuid4().hex
        with self.connect() as db:
            db.execute('INSERT INTO runs VALUES (?,?,?,?,?,?)',(run_id,profile,now(),None,'Running',str(report_path)))
            for p in plans:
                expected=p.get('expected',{'settings':p['settings'],'channels':p.get('channel_checks',p['channels'])})
                db.execute('INSERT INTO results VALUES (?,?,?,?,?,?,?)',(run_id,identity(p['baseline']),p['settings'].get('name',p['baseline']['settings'].get('name','?')),p['port'],'Pending',json.dumps(expected),None))
        return run_id

    def result(self,run_id,plan,status,error=None):
        with self.connect() as db:
            db.execute('UPDATE results SET status=?,error=? WHERE run_id=? AND identity=?',(status,error,run_id,identity(plan['baseline'])))

    def finish(self,run_id,status):
        with self.connect() as db:db.execute('UPDATE runs SET status=?,finished=? WHERE id=?',(status,now(),run_id))

    def runs(self):
        with self.connect() as db:return [dict(r) for r in db.execute('SELECT * FROM runs ORDER BY started DESC')]

    def details(self,run_id):
        with self.connect() as db:
            rows=[dict(r) for r in db.execute('SELECT * FROM results WHERE run_id=? ORDER BY port',(run_id,))]
            checks=[dict(r) for r in db.execute('SELECT * FROM verifications WHERE run_id=? ORDER BY id',(run_id,))]
        for row in rows:row['expected']=json.loads(row['expected'])
        return rows,checks

    def verify(self,run_id,snapshot,status,detail,restart_attested):
        with self.connect() as db:db.execute('INSERT INTO verifications(run_id,identity,checked,port,status,detail,restart_attested) VALUES (?,?,?,?,?,?,?)',
                   (run_id,identity(snapshot),now(),snapshot['port'],status,detail,int(restart_attested)))

    def recover_interrupted(self):
        # Called once at application startup, never by a worker connection.
        with self.connect() as db:
            db.execute("UPDATE results SET status='Interrupted — reread required' WHERE run_id IN (SELECT id FROM runs WHERE status='Running') AND status='Writing and verifying…'")
            db.execute("UPDATE results SET status='Not attempted' WHERE run_id IN (SELECT id FROM runs WHERE status='Running') AND status='Pending'")
            db.execute("UPDATE runs SET status='Interrupted',finished=? WHERE status='Running'",(now(),))
