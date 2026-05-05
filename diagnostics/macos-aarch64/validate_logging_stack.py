#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path
import zipfile

REQUIRED_LOGGING_BUNDLES = {
    'slf4j.api': '2.0.17',
    'ch.qos.logback.classic': '1.5.32',
    'ch.qos.logback.core': '1.5.32',
}
REQUIRED_MODELIO_BUNDLES = (
    'org.modelio.platform.utils',
    'org.modelio.platform.logging.logback',
)
LEGACY_REPOSITORY_SNIPPETS = {
    'legacy SLF4J repository': 'dev-platform/rcp-target/org.slf4j/slf4j',
    'legacy Logback repository': 'dev-platform/rcp-target/ch.qos/logback',
}
REQUIRED_SOURCE_SNIPPETS = {
    'features/opensource/org.modelio.platform.libraries/feature.xml': (
        'id="ch.qos.logback.classic"',
        'version="1.5.32"',
        'id="ch.qos.logback.core"',
        'id="slf4j.api"',
        'version="2.0.17"',
    ),
    'features/opensource/org.modelio.application.services/feature.xml': (
        'org.modelio.platform.logging.logback',
    ),
    'modelio/platform/platform.utils/META-INF/MANIFEST.MF': (
        'Import-Package: org.slf4j;version="[2.0.0,3.0.0)"',
    ),
    'modelio/platform/platform.logging.logback/META-INF/MANIFEST.MF': (
        'ch.qos.logback.classic;bundle-version="[1.5.0,2.0.0)"',
        'ch.qos.logback.core;bundle-version="[1.5.0,2.0.0)"',
        'Bundle-Activator: org.modelio.platform.logging.logback.LogbackBackendPlugin',
    ),
}
BUNDLES_INFO_PATH = Path('Contents/Eclipse/configuration/org.eclipse.equinox.simpleconfigurator/bundles.info')
MODELIO_INI_PATH = Path('Contents/Eclipse/modelio.ini')


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Validate that the supported macOS Apple Silicon product resolves the modern SLF4J 2.0 / Logback 1.5 stack only.'
    )
    parser.add_argument(
        '--repo-root',
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help='Path to the repository root. Defaults to the parent of diagnostics/.',
    )
    parser.add_argument(
        '--app',
        type=Path,
        required=True,
        help='Path to the built Modelio.app bundle to validate.',
    )
    return parser


def validate_source_configuration(repo_root: Path, failures: list[str]) -> None:
    for relative_path, snippets in REQUIRED_SOURCE_SNIPPETS.items():
        path = repo_root / relative_path
        if not path.is_file():
            failures.append(f'Missing source file: {relative_path}')
            continue

        text = path.read_text(encoding='utf-8')
        for snippet in snippets:
            if snippet not in text:
                failures.append(f'{relative_path}: missing required snippet {snippet!r}')

    product_file = repo_root / 'products/modelio-os.product'
    if not product_file.is_file():
        failures.append('Missing source file: products/modelio-os.product')
    else:
        provider_flag = '-Dslf4j.provider=ch.qos.logback.classic.spi.LogbackServiceProvider'
        product_text = product_file.read_text(encoding='utf-8')
        if provider_flag in product_text:
            failures.append(
                'products/modelio-os.product: found incompatible explicit SLF4J provider VM argument '
                f'{provider_flag!r}'
            )

    for relative_path in ('pom.xml', 'maven/modelio-parent/pom.xml', 'dev-platform/rcp-target/rcp.target', 'dev-platform/rcp-target/rcp_debug.target'):
        path = repo_root / relative_path
        if not path.is_file():
            failures.append(f'Missing source file: {relative_path}')
            continue

        text = path.read_text(encoding='utf-8')
        for label, snippet in LEGACY_REPOSITORY_SNIPPETS.items():
            if snippet in text:
                failures.append(f'{relative_path}: found forbidden {label} snippet {snippet!r}')


def load_bundles_info(path: Path) -> dict[str, list[dict[str, str]]]:
    entries: dict[str, list[dict[str, str]]] = {}
    with path.open(encoding='utf-8', newline='') as handle:
        reader = csv.reader(handle)
        for row in reader:
            if not row or row[0].startswith('#'):
                continue
            if len(row) < 5:
                continue
            bundle_id, version, relative_bundle_path, start_level, auto_start = row[:5]
            entries.setdefault(bundle_id, []).append(
                {
                    'version': version,
                    'path': relative_bundle_path,
                    'start_level': start_level,
                    'auto_start': auto_start,
                }
            )
    return entries


def validate_packaged_bundles(app_bundle: Path, failures: list[str]) -> None:
    bundles_info = app_bundle / BUNDLES_INFO_PATH
    if not bundles_info.is_file():
        failures.append(f'Missing bundles.info: {bundles_info}')
        return

    entries = load_bundles_info(bundles_info)

    for bundle_id, expected_version in REQUIRED_LOGGING_BUNDLES.items():
        versions = {entry['version'] for entry in entries.get(bundle_id, [])}
        if versions != {expected_version}:
            failures.append(f'{bundle_id}: expected packaged version {expected_version}, got {sorted(versions) or "missing"}')

    for bundle_id in REQUIRED_MODELIO_BUNDLES:
        if bundle_id not in entries:
            failures.append(f'Missing packaged bundle entry for {bundle_id}')

    backend_entries = entries.get('org.modelio.platform.logging.logback', [])
    if len(backend_entries) != 1:
        failures.append(
            'org.modelio.platform.logging.logback: expected exactly one packaged entry, '
            f'got {len(backend_entries)}'
        )
        return

    backend_jar = app_bundle / 'Contents/Eclipse' / backend_entries[0]['path']
    if not backend_jar.is_file():
        failures.append(f'Missing packaged backend bundle jar: {backend_jar}')
        return

    with zipfile.ZipFile(backend_jar) as archive:
        members = set(archive.namelist())
        for member in (
            'config/logback.xml',
            'org/modelio/platform/logging/logback/LogbackBackendPlugin.class',
            'org/modelio/platform/logging/logback/LogbackLoggingBackend.class',
        ):
            if member not in members:
                failures.append(f'{backend_jar.name}: missing required entry {member}')

    packaged_property_files = [
        app_bundle / "Contents" / "Eclipse" / "modelio.ini",
        app_bundle / "Contents" / "Eclipse" / "modelio.app" / "Contents" / "Eclipse" / "launcher.ini",
        app_bundle / "Contents" / "Eclipse" / "modelio.app" / "Contents" / "Info.plist",
        app_bundle / "Contents" / "Eclipse" / "Modelio.app" / "Contents" / "Eclipse" / "launcher.ini",
        app_bundle / "Contents" / "Eclipse" / "Modelio.app" / "Contents" / "Info.plist",
    ]
    existing_property_files = [path for path in packaged_property_files if path.is_file()]
    if not existing_property_files:
        failures.append('Missing packaged launcher metadata files for VM-argument verification')
    else:
        provider_flag = '-Dslf4j.provider=ch.qos.logback.classic.spi.LogbackServiceProvider'
        flagged_files = [
            str(path)
            for path in existing_property_files
            if provider_flag in path.read_text(encoding='utf-8')
        ]
        if flagged_files:
            failures.append(
                'Packaged launcher metadata still contains the incompatible explicit SLF4J provider VM argument '
                f'{provider_flag!r}: ' + ', '.join(flagged_files)
            )


def main() -> int:
    args = build_argument_parser().parse_args()
    repo_root = args.repo_root.resolve()
    app_bundle = args.app.resolve()
    failures: list[str] = []

    validate_source_configuration(repo_root, failures)

    if not app_bundle.is_dir():
        failures.append(f'Missing app bundle: {app_bundle}')
    else:
        validate_packaged_bundles(app_bundle, failures)

    if failures:
        print('LOGGING STACK VALIDATION FAILED')
        for failure in failures:
            print(failure)
        return 1

    print('LOGGING STACK VALIDATION OK')
    print(f'App bundle: {app_bundle}')
    for bundle_id, version in REQUIRED_LOGGING_BUNDLES.items():
        print(f'{bundle_id} {version}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

