import json
from pathlib import Path
import urllib.request
import xml.etree.ElementTree as ET

REPO_ROOT = Path('/Users/david/IdeaProjects/Modelio')
STAGED_DIR = REPO_ROOT / 'dev-platform/rcp-target/rcp-eclipse/eclipse-2026-03'
SOURCE_URL = 'https://download.eclipse.org/releases/2026-03/202603111000/'
CACHE_ROOT = STAGED_DIR / 'slice-cache'
FEATURES = {
    'org.modelio.e4.rcp': REPO_ROOT / 'features/opensource/org.modelio.e4.rcp/feature.xml',
    'org.modelio.rcp': REPO_ROOT / 'features/opensource/org.modelio.rcp/feature.xml',
    'org.modelio.platform.feature': REPO_ROOT / 'features/opensource/org.modelio.platform.feature/feature.xml',
}
ROOT_VERSION_MAP = {
    'org.modelio.e4.rcp': 'org.eclipse.e4.rcp.feature.group',
    'org.modelio.rcp': 'org.eclipse.rcp.feature.group',
    'org.modelio.platform.feature': 'org.eclipse.platform.feature.group',
}
PREFIXES = ('org.eclipse.', 'com.sun.jna')


def load_units() -> dict:
    root = ET.parse(STAGED_DIR / 'content.xml').getroot()
    units = {}
    for unit in root.findall('.//unit'):
        unit_id = unit.get('id')
        version = unit.get('version')
        if unit_id and version:
            units.setdefault(unit_id, []).append(version)
    for unit_id in units:
        units[unit_id] = sorted(set(units[unit_id]))
    return units


def load_artifacts() -> dict:
    root = ET.parse(STAGED_DIR / 'artifacts.xml').getroot()
    artifacts = {}
    for artifact in root.findall('.//artifact'):
        classifier = artifact.get('classifier')
        artifact_id = artifact.get('id')
        version = artifact.get('version')
        if classifier and artifact_id and version:
            artifacts[(classifier, artifact_id, version)] = {
                'classifier': classifier,
                'id': artifact_id,
                'version': version,
            }
    return artifacts


def parse_feature(feature_path: Path) -> tuple[str, list[dict]]:
    root = ET.parse(feature_path).getroot()
    entries = []
    for tag in ('includes', 'plugin'):
        for node in root.findall(tag):
            entry_id = node.get('id')
            version = node.get('version', '')
            if entry_id and version and entry_id.startswith(PREFIXES):
                entries.append({'tag': tag, 'id': entry_id, 'version': version})
    return root.get('version', ''), entries


def resolve_staged_version(entry: dict, units: dict) -> tuple[str | None, str | None]:
    if entry['tag'] == 'includes':
        feature_group_id = f"{entry['id']}.feature.group"
        versions = units.get(feature_group_id, [])
        return (versions[-1], 'org.eclipse.update.feature') if versions else (None, None)
    versions = units.get(entry['id'], [])
    return (versions[-1], 'osgi.bundle') if versions else (None, None)


def cache_artifact(classifier: str, artifact_id: str, version: str) -> dict:
    if classifier == 'osgi.bundle':
        relative_path = f'plugins/{artifact_id}_{version}.jar'
    else:
        relative_path = f'features/{artifact_id}_{version}.jar'
    destination = CACHE_ROOT / relative_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    source = SOURCE_URL + relative_path
    if not destination.exists():
        with urllib.request.urlopen(source) as response:
            destination.write_bytes(response.read())
    return {
        'classifier': classifier,
        'id': artifact_id,
        'version': version,
        'path': str(destination),
        'size': destination.stat().st_size,
        'source': source,
    }


def main() -> None:
    units = load_units()
    artifacts = load_artifacts()
    CACHE_ROOT.mkdir(parents=True, exist_ok=True)

    report = {
        'source_url': SOURCE_URL,
        'staged_dir': str(STAGED_DIR),
        'features': {},
        'cached_artifacts': [],
    }
    cached_keys = set()

    for feature_name, feature_path in FEATURES.items():
        feature_version, entries = parse_feature(feature_path)
        proposed_root_version = units[ROOT_VERSION_MAP[feature_name]][-1]
        feature_report = {
            'current_feature_version': feature_version,
            'proposed_feature_version': proposed_root_version,
            'replace': [],
            'remove': [],
        }
        for entry in entries:
            staged_version, classifier = resolve_staged_version(entry, units)
            if staged_version is None or classifier is None:
                feature_report['remove'].append(entry)
                continue
            suggestion = {
                'tag': entry['tag'],
                'id': entry['id'],
                'current_version': entry['version'],
                'proposed_version': staged_version,
                'classifier': classifier,
            }
            feature_report['replace'].append(suggestion)
            artifact_key = (classifier, entry['id'], staged_version)
            if artifact_key not in cached_keys and artifact_key in artifacts:
                report['cached_artifacts'].append(cache_artifact(classifier, entry['id'], staged_version))
                cached_keys.add(artifact_key)
        report['features'][feature_name] = feature_report

    report_path = STAGED_DIR / 'repin-suggestions.json'
    report_path.write_text(json.dumps(report, indent=2) + '\n')
    print('wrote', report_path)
    print('cached artifacts:', len(report['cached_artifacts']))
    for feature_name, feature_report in report['features'].items():
        print(feature_name, 'replace', len(feature_report['replace']), 'remove', len(feature_report['remove']))


if __name__ == '__main__':
    main()

