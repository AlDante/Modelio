from pathlib import Path
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

STAGED_DIR = Path('/Users/david/IdeaProjects/Modelio/dev-platform/rcp-target/rcp-eclipse/eclipse-2026-03')
CONTENT_XML = STAGED_DIR / 'content.xml'
SOURCE_URL = 'https://download.eclipse.org/releases/2026-03/202603111000/'
PREFIXES = (
    'ch.qos.',
    'jakarta.',
    'jcl.over.slf4j',
    'org.apache.',
    'org.eclipse.equinox.',
    'org.eclipse.osgi.',
    'org.eclipse.swt.svg',
    'org.objectweb.asm',
    'org.osgi.',
    'slf4j.',
)


def iter_candidate_paths() -> list[str]:
    root = ET.parse(CONTENT_XML).getroot()
    paths: set[str] = set()
    for unit in root.findall('.//unit'):
        unit_id = unit.get('id')
        version = unit.get('version')
        if not unit_id or not version:
            continue
        if unit_id.endswith('.feature.group'):
            continue
        if unit_id.startswith(PREFIXES):
            paths.add(f'plugins/{unit_id}_{version}.jar')
    return sorted(paths)


def main() -> None:
    fetched = 0
    skipped = 0
    missing_upstream = 0
    for relative in iter_candidate_paths():
        target = STAGED_DIR / relative
        if target.exists():
            skipped += 1
            continue
        source = SOURCE_URL + relative
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            with urllib.request.urlopen(source) as response:
                target.write_bytes(response.read())
        except urllib.error.HTTPError as error:
            if error.code == 404:
                print('missing-upstream', relative)
                missing_upstream += 1
                continue
            raise
        print('fetched', relative)
        fetched += 1
    print('fetched_count', fetched)
    print('skipped_count', skipped)
    print('missing_upstream_count', missing_upstream)


if __name__ == '__main__':
    main()

