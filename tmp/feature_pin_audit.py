from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
import zipfile

REPO_ROOT = Path('/Users/david/IdeaProjects/Modelio')
RCP_REPOS = {
	'eclipse': REPO_ROOT / 'dev-platform/rcp-target/rcp-eclipse/eclipse/content.xml',
	'eclipse-2026-03': REPO_ROOT / 'dev-platform/rcp-target/rcp-eclipse/eclipse-2026-03/content.xml',
	'eclipse-fr': REPO_ROOT / 'dev-platform/rcp-target/rcp-eclipse/eclipse-fr/content.xml',
	'swt': REPO_ROOT / 'dev-platform/rcp-target/rcp-eclipse/swt/content.jar',
	'launcher-arm64': REPO_ROOT / 'dev-platform/rcp-target/rcp-eclipse/launcher-arm64/content.jar',
	'macos-arm64': REPO_ROOT / 'dev-platform/rcp-target/rcp-eclipse/macos-arm64/content.jar',
	'jna': REPO_ROOT / 'dev-platform/rcp-target/rcp-eclipse/jna/repository/content.jar',
}
FEATURES = {
	'org.modelio.e4.rcp': REPO_ROOT / 'features/opensource/org.modelio.e4.rcp/feature.xml',
	'org.modelio.rcp': REPO_ROOT / 'features/opensource/org.modelio.rcp/feature.xml',
	'org.modelio.platform.feature': REPO_ROOT / 'features/opensource/org.modelio.platform.feature/feature.xml',
}
BASELINE_IDS = [
	'org.eclipse.platform.feature.group',
	'org.eclipse.rcp.feature.group',
	'org.eclipse.e4.rcp.feature.group',
	'org.eclipse.platform',
	'org.eclipse.rcp',
	'org.eclipse.swt',
	'org.eclipse.ui.workbench',
	'org.eclipse.core.runtime',
	'org.eclipse.equinox.launcher',
	'org.eclipse.core.filesystem.macosx',
	'org.eclipse.equinox.security.macosx',
	'com.sun.jna',
	'com.sun.jna.platform',
]
OVERLAY_DELTAS = [
	('org.eclipse.swt', 'eclipse', 'swt'),
	('org.eclipse.equinox.launcher.cocoa.macosx.aarch64', 'eclipse', 'launcher-arm64'),
	('org.eclipse.core.filesystem.macosx', 'eclipse', 'macos-arm64'),
	('org.eclipse.equinox.security.macosx', 'eclipse', 'macos-arm64'),
	('com.sun.jna', 'eclipse', 'jna'),
	('com.sun.jna.platform', 'eclipse', 'jna'),
]
REVENDOR_CHECK_IDS = [
	'org.eclipse.platform.feature.group',
	'org.eclipse.rcp.feature.group',
	'org.eclipse.e4.rcp.feature.group',
	'org.eclipse.platform',
	'org.eclipse.rcp',
	'org.eclipse.ui',
	'org.eclipse.ui.workbench',
	'org.eclipse.core.runtime',
	'org.eclipse.equinox.launcher',
	'org.eclipse.equinox.launcher.cocoa.macosx.aarch64',
	'org.eclipse.swt',
	'org.eclipse.swt.cocoa.macosx.aarch64',
	'org.eclipse.core.filesystem.macosx',
	'org.eclipse.equinox.security.macosx',
	'com.sun.jna',
	'com.sun.jna.platform',
]


def load_repo_units(content_path: Path) -> dict[str, set[str]]:
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


def parse_feature(feature_path: Path) -> tuple[str, list[tuple[str, str, str]]]:
	root = ET.parse(feature_path).getroot()
	feature_version = root.get('version', '')
	entries: list[tuple[str, str, str]] = []
	for tag in ('includes', 'plugin'):
		for node in root.findall(tag):
			item_id = node.get('id')
			version = node.get('version', '')
			if item_id and version:
				entries.append((tag, item_id, version))
	return feature_version, entries


def repo_sources(item_id: str, version: str, repo_units: dict[str, dict[str, set[str]]]) -> list[str]:
	hits = []
	for label, units in repo_units.items():
		if version in units.get(item_id, set()):
			hits.append(label)
	return hits


def repo_sources_for_entry(tag: str, item_id: str, version: str, repo_units: dict[str, dict[str, set[str]]]) -> list[str]:
	sources = repo_sources(item_id, version, repo_units)
	if sources or tag != 'includes' or item_id.endswith('.feature.group'):
		return sources
	return repo_sources(f'{item_id}.feature.group', version, repo_units)


def main() -> None:
	repo_units = {label: load_repo_units(path) for label, path in RCP_REPOS.items()}

	print('SELECTED_REPLACEMENT_TRAIN=2026-03')
	print('RATIONALE=repo guidance in MODERNIZATION_PLAN.md, AGENTS.md, and .github/copilot-instructions.md already converges on Eclipse RCP 2026-03')
	print()

	print('CURRENT_BASELINE_UNITS')
	for item_id in BASELINE_IDS:
		versions = sorted(repo_units['eclipse'].get(item_id, set()))
		print(f'{item_id}: {", ".join(versions) if versions else "MISSING_IN_ECLIPSE_BASELINE"}')
	print()

	print('CURRENT_OVERLAY_DELTAS')
	for item_id, baseline_repo, overlay_repo in OVERLAY_DELTAS:
		baseline_versions = sorted(repo_units[baseline_repo].get(item_id, set()))
		overlay_versions = sorted(repo_units[overlay_repo].get(item_id, set()))
		print(
			f'{item_id}: baseline={", ".join(baseline_versions) if baseline_versions else "ABSENT"}; '
			f'{overlay_repo}={", ".join(overlay_versions) if overlay_versions else "ABSENT"}'
		)
	print()

	print('STAGED_2026_03_RELEVANT_UNITS')
	for item_id in REVENDOR_CHECK_IDS:
		current_versions = sorted(repo_units['eclipse'].get(item_id, set()))
		staged_versions = sorted(repo_units['eclipse-2026-03'].get(item_id, set()))
		print(
			f'{item_id}: '
			f'current={", ".join(current_versions) if current_versions else "ABSENT"}; '
			f'staged={", ".join(staged_versions) if staged_versions else "ABSENT"}'
		)
	print()

	for feature_name, feature_path in FEATURES.items():
		feature_version, entries = parse_feature(feature_path)
		print(f'FEATURE {feature_name} version={feature_version}')
		print('repo-source counts:')
		counts: dict[str, int] = {}
		unresolved: list[tuple[str, str, str]] = []
		filtered_entries = [entry for entry in entries if entry[1].startswith('org.eclipse.') or entry[1].startswith('com.sun.jna')]
		for tag, item_id, version in filtered_entries:
			sources = repo_sources_for_entry(tag, item_id, version, repo_units)
			if sources:
				key = '+'.join(sources)
				counts[key] = counts.get(key, 0) + 1
			else:
				unresolved.append((tag, item_id, version))
		for key in sorted(counts):
			print(f'  {key}: {counts[key]}')
		if unresolved:
			print('  unresolved:')
			for tag, item_id, version in unresolved:
				print(f'    {tag} {item_id} {version}')
		missing_from_staged = []
		for tag, item_id, version in filtered_entries:
			staged_sources = repo_sources_for_entry(tag, item_id, version, {'eclipse-2026-03': repo_units['eclipse-2026-03']})
			if not staged_sources and not repo_units['eclipse-2026-03'].get(item_id) and not (tag == 'includes' and repo_units['eclipse-2026-03'].get(f'{item_id}.feature.group')):
				missing_from_staged.append((tag, item_id, version))
		if missing_from_staged:
			print('  missing from staged 2026-03 metadata:')
			for tag, item_id, version in missing_from_staged:
				print(f'    {tag} {item_id} {version}')
		print('overlay/backfill pins:')
		for tag, item_id, version in filtered_entries:
			sources = repo_sources_for_entry(tag, item_id, version, repo_units)
			if not sources:
				continue
			if sources != ['eclipse']:
				print(f'  {tag} {item_id} {version} <- {", ".join(sources)}')
		print()


if __name__ == '__main__':
	main()

