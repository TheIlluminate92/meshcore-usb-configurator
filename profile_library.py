"""Local named JSON profiles. Filenames never come from user-entered names."""
import json
import uuid
from pathlib import Path
from model import profile, load_document, validate_naming

PERSONAL = {'name', 'latitude', 'longitude'}

class ProfileLibrary:
    def __init__(self, folder):
        self.folder = Path(folder)

    def entries(self):
        entries, errors = [], []
        for path in sorted(self.folder.glob('*.json')):
            try:
                settings, channels, _ = load_document(path)
                data = json.loads(path.read_text(encoding='utf-8'))
                if not isinstance(data.get('profile_name'),str) or not data['profile_name'].strip() or len(data['profile_name'])>80:
                    raise ValueError('Invalid profile name')
                if str(uuid.UUID(path.stem))!=path.stem:
                    raise ValueError('Invalid profile identifier')
                entries.append({'id':path.stem, 'name':data['profile_name'], 'settings':settings, 'channels':channels,'naming':validate_naming(data.get('naming'))})
            except Exception:
                errors.append(path.name)
        return sorted(entries, key=lambda e:e['name'].casefold()), errors

    def path(self, ident):
        return self.folder / (str(uuid.UUID(ident)) + '.json')

    def save(self, name, settings, channels, ident=None, naming=None):
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
        ident = ident or str(uuid.uuid4())
        path = self.path(ident)
        self.folder.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix('.tmp')
        temporary.write_text(json.dumps(data, indent=2), encoding='utf-8')
        temporary.replace(path)
        return ident

    def archive(self, ident):
        path=self.path(ident)
        archive=self.folder/'archive'
        archive.mkdir(parents=True,exist_ok=True)
        path.replace(archive/(path.stem+'-'+uuid.uuid4().hex+'.json'))
