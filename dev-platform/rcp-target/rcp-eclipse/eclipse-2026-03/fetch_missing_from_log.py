from pathlib import Path
import re
import xml.etree.ElementTree as ET
import urllib.request

STAGED_DIR = Path('/Users/david/IdeaProjects/Modelio/dev-platform/rcp-target/rcp-eclipse/eclipse-2026-03')
SOURCE_URL = 'https://download.eclipse.org/releases/2026-03/202603111000/'
LOG_DIR = Path('/Users/david/IdeaProjects/Modelio/tmp/validation-2026-03-logs')
ARTIFACTS_XML = STAGED_DIR / 'artifacts.xml'
MISSING_PATH_PATTERN = re.compile(r'(dev-platform/rcp-target/rcp-eclipse/eclipse-2026-03/(plugins|features)/[^)\s]+) \(No such file or directory\)')
READING_PATTERN = re.compile(r'\bReading ([^\s]+\.jar)\b')
SUPPORTED_CLASSIFIERS = {
    'osgi.bundle': 'plugins',
    'org.eclipse.update.feature': 'features',
}


def build_artifact_index() -> dict[str, str]:
    mapping: dict[str, str] = {}
    for _, element in ET.iterparse(ARTIFACTS_XML, events=('end',)):
        if element.tag != 'artifact':
            continue
        classifier = element.get('classifier')
        folder = SUPPORTED_CLASSIFIERS.get(classifier or '')
        artifact_id = element.get('id')
        version = element.get('version')
        if folder and artifact_id and version:
            relative = f'{folder}/{artifact_id}_{version}.jar'
            mapping[Path(relative).name] = relative
        element.clear()
    return mapping


def find_missing_paths() -> list[str]:
    artifact_index = build_artifact_index()
    matches: set[str] = set()
    unresolved: set[str] = set()
    for log_path in sorted(LOG_DIR.glob('*.log')):
        text = log_path.read_text(errors='replace')
        for match in MISSING_PATH_PATTERN.finditer(text):
            matches.add(match.group(1))
        for match in READING_PATTERN.finditer(text):
            relative = artifact_index.get(match.group(1))
            if relative:
                matches.add(f'dev-platform/rcp-target/rcp-eclipse/eclipse-2026-03/{relative}')
            else:
                unresolved.add(match.group(1))
    for basename in sorted(unresolved):
        print('unresolved-log-artifact', basename)
    return sorted(matches)


def main() -> None:
    matches = find_missing_paths()
    if not matches:
        print('no missing staged artifacts found in logs')
        return
    fetched = 0
    skipped = 0
    for relative_rooted in matches:
        relative = Path(relative_rooted).relative_to('dev-platform/rcp-target/rcp-eclipse/eclipse-2026-03').as_posix()
        target = STAGED_DIR / relative
        source = SOURCE_URL + relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            print('already present', relative)
            skipped += 1
            continue
        with urllib.request.urlopen(source) as response:
            target.write_bytes(response.read())
        print('fetched', relative)
        fetched += 1
    print('fetched_count', fetched)
    print('skipped_count', skipped)


if __name__ == '__main__':
    main()

