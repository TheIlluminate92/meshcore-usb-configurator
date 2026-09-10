"""Local named JSON profiles. Filenames never come from user-entered names."""
import json
import uuid
from pathlib import Path
from model import profile, load_document, validate_naming

def validate_notes(value=''):
    if not isinstance(value,str) or len(value)>4000 or '\x00' in value:
        raise ValueError('Profile notes must be text, up to 4000 characters, without null characters.')
    return value

PERSONAL = {'name', 'latitude', 'longitude'}

class ProfileLibrary:
    def __init__(self, folder, include_builtin=False):
        self.folder = Path(folder)
        self.include_builtin = include_builtin

    def entries(self):
        from builtin_profiles import entries as defaults
        entries, errors = (defaults() if self.include_builtin else []), []
        for path in sorted(self.folder.glob('*.json')):
            try:
                settings, channels, _ = load_document(path)
                data = json.loads(path.read_text(encoding='utf-8'))
                if not isinstance(data.get('profile_name'),str) or not data['profile_name'].strip() or len(data['profile_name'])>80:
                    raise ValueError('Invalid profile name')
                if str(uuid.UUID(path.stem))!=path.stem:
                    raise ValueError('Invalid profile identifier')
                entries.append({'id':path.stem, 'name':data['profile_name'], 'settings':settings, 'channels':channels,'notes':validate_notes(data.get('notes','')),'naming':validate_naming(data.get('naming'))})
            except Exception:
                errors.append(path.name)
        return sorted(entries, key=lambda e:e['name'].casefold()), errors

    def path(self, ident):
        return self.folder / (str(uuid.UUID(ident)) + '.json')

    def save(self, name, settings, channels, ident=None, naming=None, notes=None):
        name = name.strip()
        if not name or len(name)>80:
            raise ValueError('Choose a profile name with 1–80 characters.')
        entries, _ = self.entries()
        if any(e['name'].casefold()==name.casefold() and e['id']!=ident for e in entries):
            raise ValueError('That profile name already exists. Choose a different name.')
        data = profile(settings, channels)
        if not data['settings'] and not data.get('channels'):
            raise ValueError('Select at least one setting or channel.')
        data['profile_name'] = name
        if naming is None and ident:
            naming=next((e['naming'] for e in entries if e['id']==ident),None)
        data['naming']=validate_naming(naming)
        if notes is None and ident:
            notes=next((e.get('notes','') for e in entries if e['id']==ident),'')
        data['notes']=validate_notes('' if notes is None else notes)
        ident = ident or str(uuid.uuid4())
        path = self.path(ident)
        self.folder.mkdir(parents=True, exist_ok=True)
        from storage import atomic_text
        atomic_text(path,json.dumps(data, indent=2))
        return ident

    def archive(self, ident):
        path=self.path(ident)
        archive=self.folder/'archive'
        archive.mkdir(parents=True,exist_ok=True)
        path.replace(archive/(path.stem+'-'+uuid.uuid4().hex+'.json'))
