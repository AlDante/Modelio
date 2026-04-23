from pathlib import Path
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

STAGED_DIR = Path('/Users/david/IdeaProjects/Modelio/dev-platform/rcp-target/rcp-eclipse/eclipse-2026-03')
ARTIFACTS_XML = STAGED_DIR / 'artifacts.xml'
SOURCE_URL = 'https://download.eclipse.org/releases/2026-03/202603111000/'
PREFIXES = (
    'ch.qos.',
    'com.github.',
    'com.ibm.',
    'com.sun.',
    'jakarta.',
    'jcl.over.slf4j',
    'org.apache.',
    'org.eclipse.',
    'org.objectweb.asm',
    'org.osgi.',
    'slf4j.',
)
SUPPORTED_CLASSIFIERS = {
    'osgi.bundle': 'plugins',
    'org.eclipse.update.feature': 'features',
}


def iter_candidate_paths() -> list[str]:
    paths: set[str] = set()
    for _, element in ET.iterparse(ARTIFACTS_XML, events=('end',)):
        if element.tag != 'artifact':
            continue
        classifier = element.get('classifier')
        folder = SUPPORTED_CLASSIFIERS.get(classifier or '')
        artifact_id = element.get('id')
        version = element.get('version')
        if folder and artifact_id and version and artifact_id.startswith(PREFIXES):
            paths.add(f'{folder}/{artifact_id}_{version}.jar')
        element.clear()
    return sorted(paths, key=lambda path: (0 if path.startswith('plugins/') else 1, path))


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

