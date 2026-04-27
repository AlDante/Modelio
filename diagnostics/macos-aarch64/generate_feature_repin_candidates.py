import json
import re
from pathlib import Path

REPO_ROOT = Path('/Users/david/IdeaProjects/Modelio')
REPORT = json.loads((REPO_ROOT / 'dev-platform/rcp-target/rcp-eclipse/eclipse-2026-03/repin-suggestions.json').read_text())
OUTPUT_DIR = REPO_ROOT / 'diagnostics' / 'macos-aarch64' / 'repin-candidates'
FEATURE_FILES = {
    'org.modelio.e4.rcp': REPO_ROOT / 'features/opensource/org.modelio.e4.rcp/feature.xml',
    'org.modelio.rcp': REPO_ROOT / 'features/opensource/org.modelio.rcp/feature.xml',
    'org.modelio.platform.feature': REPO_ROOT / 'features/opensource/org.modelio.platform.feature/feature.xml',
}
INTER_FEATURE_UPDATES = {
    'org.modelio.rcp': {'org.modelio.e4.rcp': REPORT['features']['org.modelio.e4.rcp']['proposed_feature_version']},
    'org.modelio.platform.feature': {'org.modelio.rcp': REPORT['features']['org.modelio.rcp']['proposed_feature_version']},
}


def update_feature_version(text: str, new_version: str) -> str:
    return re.sub(r'(<feature\s+.*?\bversion=")([^"]+)(")', rf'\g<1>{new_version}\3', text, count=1, flags=re.DOTALL)


def replace_block_version(text: str, tag: str, entry_id: str, old_version: str, new_version: str) -> str:
    pattern = re.compile(
        rf'(<{tag}\b(?:(?!/>).)*?\bid="{re.escape(entry_id)}"(?:(?!/>).)*?\bversion=")'
        rf'{re.escape(old_version)}'
        rf'(")',
        re.DOTALL,
    )
    updated, count = pattern.subn(rf'\g<1>{new_version}\2', text, count=1)
    if count == 1:
        return updated
    already_updated = re.search(
        rf'<{tag}\b(?:(?!/>).)*?\bid="{re.escape(entry_id)}"(?:(?!/>).)*?\bversion="{re.escape(new_version)}"',
        text,
        re.DOTALL,
    )
    if already_updated:
        return text
    raise RuntimeError(f'Failed to update {tag} {entry_id} {old_version} -> {new_version}')



def remove_block(text: str, tag: str, entry_id: str, old_version: str) -> str:
    pattern = re.compile(
        rf'\n\s*<{tag}\b(?:(?!/>).)*?\bid="{re.escape(entry_id)}"(?:(?!/>).)*?\bversion="{re.escape(old_version)}"(?:(?!/>).)*?/>\n?',
        re.DOTALL,
    )
    updated, count = pattern.subn('\n', text, count=1)
    if count == 1:
        return updated
    still_present = re.search(
        rf'<{tag}\b(?:(?!/>).)*?\bid="{re.escape(entry_id)}"(?:(?!/>).)*?\bversion="{re.escape(old_version)}"',
        text,
        re.DOTALL,
    )
    if not still_present:
        return text
    raise RuntimeError(f'Failed to remove {tag} {entry_id} {old_version}')



def fix_e4_swt_block(text: str) -> str:
    broken = re.compile(
        r'\n\s*id="org\.eclipse\.swt"\n\s*download-size="0"\n\s*install-size="0"\n\s*version="3\.120\.0\.v20220530-1036"\n\s*unpack="false"/>\n',
        re.DOTALL,
    )
    replacement = (
        '\n   <plugin\n'
        '         id="org.eclipse.swt"\n'
        '         download-size="0"\n'
        '         install-size="0"\n'
        '         version="3.133.0.v20260225-1014"\n'
        '         unpack="false"/>\n'
    )
    updated, count = broken.subn(replacement, text, count=1)
    if count == 1:
        return updated
    if 'version="3.133.0.v20260225-1014"' in text and 'id="org.eclipse.swt"' in text:
        return text
    raise RuntimeError('Failed to repair org.eclipse.swt block in org.modelio.e4.rcp')


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for feature_name, feature_path in FEATURE_FILES.items():
        text = feature_path.read_text()
        feature_report = REPORT['features'][feature_name]
        text = update_feature_version(text, feature_report['proposed_feature_version'])
        for remove_entry in feature_report['remove']:
            text = remove_block(text, remove_entry['tag'], remove_entry['id'], remove_entry['version'])
        for replace_entry in feature_report['replace']:
            text = replace_block_version(
                text,
                replace_entry['tag'],
                replace_entry['id'],
                replace_entry['current_version'],
                replace_entry['proposed_version'],
            )
        if feature_name in INTER_FEATURE_UPDATES:
            for include_id, new_version in INTER_FEATURE_UPDATES[feature_name].items():
                current = re.search(
                    rf'<includes\b(?:(?!/>).)*?\bid="{re.escape(include_id)}"(?:(?!/>).)*?\bversion="([^"]+)"',
                    text,
                    re.DOTALL,
                )
                if not current:
                    raise RuntimeError(f'Failed to find inter-feature include {include_id} in {feature_name}')
                text = replace_block_version(text, 'includes', include_id, current.group(1), new_version)
        if feature_name == 'org.modelio.e4.rcp':
            text = fix_e4_swt_block(text)
        (OUTPUT_DIR / f'{feature_name}.feature.xml').write_text(text)
        print('wrote', OUTPUT_DIR / f'{feature_name}.feature.xml')


if __name__ == '__main__':
    main()

