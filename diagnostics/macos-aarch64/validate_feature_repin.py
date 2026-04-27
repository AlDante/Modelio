import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REPO_ROOT = Path('/Users/david/IdeaProjects/Modelio')
STAGED_CONTENT = REPO_ROOT / 'dev-platform/rcp-target/rcp-eclipse/eclipse-2026-03/content.xml'
FEATURES = {
    'org.modelio.e4.rcp': REPO_ROOT / 'features/opensource/org.modelio.e4.rcp/feature.xml',
    'org.modelio.rcp': REPO_ROOT / 'features/opensource/org.modelio.rcp/feature.xml',
    'org.modelio.platform.feature': REPO_ROOT / 'features/opensource/org.modelio.platform.feature/feature.xml',
}
EXPECTED_FEATURE_VERSIONS = {
    'org.modelio.e4.rcp': '4.39.0.v20260225-1014',
    'org.modelio.rcp': '4.39.0.v20260226-0420',
    'org.modelio.platform.feature': '4.39.0.v20260226-0420',
}
EXPECTED_INCLUDES = {
    ('org.modelio.rcp', 'org.modelio.e4.rcp'): '4.39.0.v20260225-1014',
    ('org.modelio.platform.feature', 'org.modelio.rcp'): '4.39.0.v20260226-0420',
}
PREFIXES = ('org.eclipse.', 'com.sun.jna')


def load_units(path: Path) -> dict[str, set[str]]:
    root = ET.parse(path).getroot()
    units: dict[str, set[str]] = {}
    for unit in root.findall('.//unit'):
        unit_id = unit.get('id')
        version = unit.get('version')
        if unit_id and version:
            units.setdefault(unit_id, set()).add(version)
    return units


def main() -> int:
    units = load_units(STAGED_CONTENT)
    failures: list[str] = []

    for feature_id, feature_path in FEATURES.items():
        root = ET.parse(feature_path).getroot()
        feature_version = root.get('version')
        if feature_version != EXPECTED_FEATURE_VERSIONS[feature_id]:
            failures.append(f'{feature_id}: feature version {feature_version} != {EXPECTED_FEATURE_VERSIONS[feature_id]}')

        for include in root.findall('includes'):
            include_id = include.get('id')
            version = include.get('version')
            if include_id and include_id.startswith(PREFIXES):
                if version not in units.get(f'{include_id}.feature.group', set()):
                    failures.append(f'{feature_id}: include {include_id} {version} not present in staged feature group metadata')
            expected_include = EXPECTED_INCLUDES.get((feature_id, include_id))
            if expected_include and version != expected_include:
                failures.append(f'{feature_id}: include {include_id} {version} != {expected_include}')

        for plugin in root.findall('plugin'):
            plugin_id = plugin.get('id')
            version = plugin.get('version')
            if plugin_id and version and plugin_id.startswith(PREFIXES):
                if version not in units.get(plugin_id, set()):
                    failures.append(f'{feature_id}: plugin {plugin_id} {version} not present in staged metadata')

    if failures:
        print('VALIDATION FAILED')
        for failure in failures:
            print(failure)
        return 1

    print('VALIDATION OK')
    for feature_id in FEATURES:
        print(feature_id)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

