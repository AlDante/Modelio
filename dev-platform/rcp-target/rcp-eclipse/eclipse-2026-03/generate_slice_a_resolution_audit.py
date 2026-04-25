from __future__ import annotations

import json
from datetime import date
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

REPO_ROOT = Path('/Users/david/IdeaProjects/Modelio')
BASELINE_LABEL = 'eclipse-2026-03'
REPO_CONTENT = {
    BASELINE_LABEL: REPO_ROOT / 'dev-platform/rcp-target/rcp-eclipse/eclipse-2026-03/content.xml',
}
FEATURE_ROOT = REPO_ROOT / 'features' / 'opensource'
OUTPUT_PATH = REPO_ROOT / 'dev-platform/rcp-target/rcp-eclipse/eclipse-2026-03/slice-a-resolution-audit.json'
SOURCE_URL = 'https://download.eclipse.org/releases/2026-03/202603111000/'


def load_units(content_path: Path) -> dict[str, set[str]]:
    if content_path.suffix == '.jar':
        with zipfile.ZipFile(content_path) as zf:
            root = ET.fromstring(zf.read('content.xml'))
    else:
        root = ET.parse(content_path).getroot()
    units: dict[str, set[str]] = {}
    for unit in root.findall('.//unit'):
        unit_id = unit.get('id')
        version = unit.get('version')
        if unit_id and version:
            units.setdefault(unit_id, set()).add(version)
    return units


def find_sources(tag: str, item_id: str, version: str, repo_units: dict[str, dict[str, set[str]]]) -> dict[str, list[str]]:
    query_ids = [item_id]
    if tag == 'includes' and not item_id.endswith('.feature.group'):
        query_ids.append(f'{item_id}.feature.group')

    result: dict[str, list[str]] = {}
    for repo_name, units in repo_units.items():
        versions: set[str] = set()
        for query_id in query_ids:
            if version and version != '0.0.0':
                if version in units.get(query_id, set()):
                    versions.add(version)
            else:
                versions.update(units.get(query_id, set()))
        if versions:
            result[repo_name] = sorted(versions)
    return result


def iter_feature_entries() -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    for feature_path in sorted(FEATURE_ROOT.glob('*/feature.xml')):
        root = ET.parse(feature_path).getroot()
        feature_id = root.get('id', feature_path.parent.name)
        feature_version = root.get('version', '')
        for tag in ('includes', 'plugin'):
            for node in root.findall(tag):
                item_id = node.get('id', '')
                version = node.get('version', '')
                if not item_id or item_id.startswith('org.modelio.'):
                    continue
                entries.append(
                    {
                        'featureId': feature_id,
                        'featurePath': str(feature_path.relative_to(REPO_ROOT)),
                        'featureVersion': feature_version,
                        'tag': tag,
                        'id': item_id,
                        'version': version,
                    }
                )
    return entries


def is_in_audited_repo_family(tag: str, item_id: str, repo_units: dict[str, dict[str, set[str]]]) -> bool:
    if item_id.startswith('org.eclipse.uml2'):
        return False
    query_ids = [item_id]
    if tag == 'includes' and not item_id.endswith('.feature.group'):
        query_ids.append(f'{item_id}.feature.group')
    for units in repo_units.values():
        for query_id in query_ids:
            if units.get(query_id):
                return True
    return False


def main() -> None:
    repo_units = {label: load_units(path) for label, path in REPO_CONTENT.items()}
    entries = [
        entry
        for entry in iter_feature_entries()
        if is_in_audited_repo_family(entry['tag'], entry['id'], repo_units)
    ]

    baseline_only: list[dict[str, object]] = []
    duplicate_sources: list[dict[str, object]] = []
    fallback_only: list[dict[str, object]] = []
    unresolved: list[dict[str, object]] = []

    for entry in entries:
        sources = find_sources(entry['tag'], entry['id'], entry['version'], repo_units)
        enriched = dict(entry)
        enriched['sources'] = sources
        if not sources:
            unresolved.append(enriched)
            continue
        if set(sources) == {BASELINE_LABEL}:
            baseline_only.append(enriched)
            continue
        if BASELINE_LABEL in sources:
            duplicate_sources.append(enriched)
            continue
        fallback_only.append(enriched)

    payload = {
        'generatedOn': date.today().isoformat(),
        'baseline': {
            'label': BASELINE_LABEL,
            'path': str(REPO_CONTENT[BASELINE_LABEL].relative_to(REPO_ROOT)),
            'sourceUrl': SOURCE_URL,
        },
        'repoInputsAudited': {
            label: str(path.relative_to(REPO_ROOT)) for label, path in REPO_CONTENT.items()
        },
        'featureScope': 'features/opensource/*/feature.xml',
        'scopeRule': 'all non-Modelio feature entries that exist in the active RCP baseline repository',
        'summary': {
            'entriesAudited': len(entries),
            'baselineOnlyCount': len(baseline_only),
            'duplicateSourceCount': len(duplicate_sources),
            'fallbackOnlyCount': len(fallback_only),
            'unresolvedCount': len(unresolved),
        },
        'baselineOnly': baseline_only,
        'duplicateSources': duplicate_sources,
        'fallbackOnly': fallback_only,
        'unresolved': unresolved,
    }

    OUTPUT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=False) + '\n')
    print(f'wrote {OUTPUT_PATH}')
    print(json.dumps(payload['summary'], indent=2, sort_keys=False))


if __name__ == '__main__':
    main()

