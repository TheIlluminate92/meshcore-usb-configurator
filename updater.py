"""Explicit GitHub release downloads; never touch profiles or radios."""
import hashlib
import json
import re
import urllib.request
import urllib.error
from pathlib import Path
from app_version import VERSION
REPO = 'TheIlluminate92/meshcore-usb-configurator'
API = 'https://api.github.com/repos/' + REPO
ASSET = 'MeshCore-Configurator.exe'

class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        from urllib.parse import urlsplit
        parsed=urlsplit(newurl)
        if parsed.scheme!='https' or parsed.hostname not in ('api.github.com','release-assets.githubusercontent.com','objects.githubusercontent.com'):
            raise ValueError('Unexpected update download destination.')
        result=super().redirect_request(req,fp,code,msg,headers,newurl)
        if result and parsed.hostname!='api.github.com':result.remove_header('Authorization')
        return result

def request(url, token='', binary=False):
    headers={'Accept':'application/octet-stream' if binary else 'application/vnd.github+json','User-Agent':'MeshCore-Configurator','X-GitHub-Api-Version':'2022-11-28'}
    if token:headers['Authorization']='Bearer '+token.strip()
    return urllib.request.build_opener(SafeRedirect()).open(urllib.request.Request(url,headers=headers),timeout=30)

def version(value):
    if not re.fullmatch(r'v?\d+\.\d+\.\d+',value):raise ValueError('Unsupported release version.')
    return tuple(map(int,value.lstrip('v').split('.')))

def check(token=''):
    try:
        with request(API+'/releases/latest',token) as response:release=json.load(response)
    except urllib.error.HTTPError as exc:
        if exc.code in (401,403,404):
            raise ValueError('No accessible release. This private repository needs a GitHub token with Contents: read access, and a published release.') from None
        raise ValueError('GitHub update check failed. Try again later.') from None
    if release.get('draft') or release.get('prerelease'):raise ValueError('Not a stable published release.')
    if version(release['tag_name'])<=version(VERSION):return None
    asset=next((a for a in release.get('assets',[]) if a['name']==ASSET),None)
    if not asset or not re.fullmatch(r'sha256:[a-f0-9]{64}',asset.get('digest') or ''):raise ValueError('Release has no verified Windows executable yet.')
    if type(asset.get('id')) is not int or not 0<asset.get('size',0)<=150*1024*1024:raise ValueError('Invalid update asset.')
    return {'version':release['tag_name'],'asset':asset}

def download(release,folder,token=''):
    asset=release['asset'];folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    path=folder/'download.tmp';digest=hashlib.sha256();total=0
    try:
        with request(API+'/releases/assets/'+str(asset['id']),token,True) as source,path.open('wb') as out:
            while chunk:=source.read(1024*1024):
                total+=len(chunk)
                if total>asset['size']:raise ValueError('Update exceeds its expected size.')
                digest.update(chunk);out.write(chunk)
        if total!=asset['size'] or 'sha256:'+digest.hexdigest()!=asset['digest']:raise ValueError('Update checksum mismatch. Nothing was installed.')
        with path.open('rb') as stream:
            if stream.read(2)!=b'MZ':raise ValueError('Downloaded file is not a Windows executable.')
        target=folder/'ready.exe';path.replace(target);return target
    finally:path.unlink(missing_ok=True)

def schedule_install(staged,executable,parent_pid):
    """Wait for the app to exit before replacing the EXE, retaining a backup."""
    import base64,subprocess
    staged=Path(staged).resolve();executable=Path(executable).resolve()
    if staged.parent != executable.parent/'User Data'/'Updates' or staged.name!='ready.exe' or executable.suffix.lower()!='.exe':
        raise ValueError('Invalid portable update location.')
    payload=base64.b64encode(json.dumps({'staged':str(staged),'exe':str(executable),'pid':parent_pid}).encode()).decode()
    script="""$ErrorActionPreference='Stop'
$d = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('PAYLOAD')) | ConvertFrom-Json
$log = Join-Path ([IO.Path]::GetDirectoryName($d.staged)) 'update.log'
try {
 $p=Get-Process -Id $d.pid -ErrorAction SilentlyContinue
 if ($p -and !$p.WaitForExit(60000)) { throw 'App still running; update cancelled.' }
 $backup=Join-Path ([IO.Path]::GetDirectoryName($d.staged)) ('previous-'+[guid]::NewGuid().ToString()+'.exe')
 for ($attempt=0; $attempt -lt 30; $attempt++) {
  try { [IO.File]::Replace($d.staged,$d.exe,$backup); break }
  catch { if ($attempt -eq 29) { throw }; Start-Sleep -Seconds 1 }
 }
 Start-Process -FilePath $d.exe -WorkingDirectory ([IO.Path]::GetDirectoryName($d.exe))
 'Update installed.' | Set-Content -LiteralPath $log
} catch { $_.Exception.Message | Set-Content -LiteralPath $log }
""".replace('PAYLOAD',payload)
    encoded=base64.b64encode(script.encode('utf-16-le')).decode()
    subprocess.Popen(['powershell.exe','-NoProfile','-NonInteractive','-WindowStyle','Hidden','-EncodedCommand',encoded],creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),close_fds=True)
