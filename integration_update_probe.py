"""Windows-only disposable EXE replacement test; no radios or app data used.

Run explicitly with Python. Not part of unittest discovery because it compiles
and starts harmless Windows probe executables and an updater helper.
"""
import hashlib
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from updater import schedule_install

def main():
    compiler=Path(os.environ.get('WINDIR','C:/Windows'))/'Microsoft.NET/Framework64/v4.0.30319/csc.exe'
    if sys.platform!='win32' or not compiler.exists():raise RuntimeError('Windows .NET Framework C# compiler required.')
    hidden={'creationflags':subprocess.CREATE_NO_WINDOW}
    with tempfile.TemporaryDirectory(prefix='meshcore-update-probe-') as temporary:
        folder=Path(temporary);updates=folder/'User Data'/'Updates';updates.mkdir(parents=True)
        staged=updates/'ready.exe';target=folder/'! Probe.exe';source=folder/'Probe.cs'
        source.write_text('using System; using System.IO; class Probe { static void Main() { File.WriteAllText(Path.Combine(AppDomain.CurrentDomain.BaseDirectory,"started.txt"),"started"); } }')
        subprocess.run([str(compiler),'/nologo','/target:winexe','/out:'+str(staged),str(source)],check=True,**hidden)
        expected=staged.read_bytes();digest='sha256:'+hashlib.sha256(expected).hexdigest()
        target.write_bytes(b'previous executable');sentinel=folder/'User Data'/'preserve.txt';sentinel.write_text('user data')
        parent=subprocess.Popen([sys.executable,'-c','import time; time.sleep(3)'],**hidden)
        try:
            helper=schedule_install(staged,target,parent.pid,digest)
            time.sleep(0.2)
            assert parent.poll() is None and target.read_bytes()==b'previous executable','Replacement happened before the parent exited.'
            helper.wait(timeout=45);parent.wait(timeout=5)
            deadline=time.monotonic()+10
            while not (folder/'started.txt').exists() and time.monotonic()<deadline:time.sleep(0.1)
            assert target.read_bytes()==expected
            assert (folder/'started.txt').read_text()=='started'
            assert sentinel.read_text()=='user data'
            backups=list(updates.glob('previous-*.exe'))
            assert len(backups)==1 and backups[0].read_bytes()==b'previous executable'
            assert 'Update installed.' in (updates/'update.log').read_text(encoding='utf-8-sig')
            print('PASS: waited for exit; replaced EXE; restarted probe; retained backup and user data.')
            # The probe exits immediately after writing its marker.
            time.sleep(0.3)
        finally:
            if parent.poll() is None:parent.terminate();parent.wait(timeout=5)

if __name__=='__main__':main()
