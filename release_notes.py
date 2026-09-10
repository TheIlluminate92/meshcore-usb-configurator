"""Extract the current changelog section for GitHub release notes."""
from pathlib import Path
from app_version import VERSION


def current_notes(text, version=VERSION):
    sections=text.split('\n## ')
    for section in sections[1:]:
        heading, _, body=section.partition('\n')
        if heading.rstrip().endswith('— '+version):
            return heading+'\n'+body.strip()+'\n'
    raise ValueError('No changelog section for '+version)

if __name__=='__main__':
    Path('release-notes.md').write_text(current_notes(Path('CHANGELOG.md').read_text(encoding='utf-8')),encoding='utf-8')
