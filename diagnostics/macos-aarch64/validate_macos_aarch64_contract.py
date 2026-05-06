#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys

FORBIDDEN_CONFIG_SNIPPETS = {
    'legacy Eclipse fallback path': 'rcp-target/rcp-eclipse/eclipse/',
    'legacy French localisation fallback path': 'rcp-target/rcp-eclipse/eclipse-fr',
    'legacy JNA fallback path': 'jna/repository',
    'legacy JRE11 target wiring': 'openjdk-jre11',
    'retired preserved macOS wrapper path': 'products/preserved-macos',
    'retired preserved macOS rootfiles path': 'eclipse-arm64-rootfiles',
    'retired launcher-arm64 overlay path': 'rcp-eclipse/launcher-arm64',
    'retired macos-arm64 overlay path': 'rcp-eclipse/macos-arm64',
}

REQUIRED_CONFIG_SNIPPETS = {
    'pom.xml': ('dev-platform/rcp-target/rcp-eclipse/eclipse-2026-03',),
    'maven/modelio-parent/pom.xml': ('dev-platform/rcp-target/rcp-eclipse/eclipse-2026-03',),
    'dev-platform/rcp-target/rcp.target': ('dev-platform/rcp-target/rcp-eclipse/eclipse-2026-03',),
    'products/pom.xml': ('org.eclipse.equinox.launcher.cocoa.macosx.aarch64', 'verify-macos-aarch64-diagram-editor-smoke'),
}

ALLOWED_REMOTE_REPOSITORY_PREFIXES = (
    'file://',
    'https://repository.modelio.org',
)

NATIVE_SUFFIXES = {'.so', '.dylib', '.jnilib'}


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Validate the supported macOS Apple Silicon build contract and the packaged Modelio.app payload.'
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


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True, check=False)


def validate_active_configuration(repo_root: Path, failures: list[str]) -> None:
    for relative_path, snippets in REQUIRED_CONFIG_SNIPPETS.items():
        path = repo_root / relative_path
        if not path.is_file():
            failures.append(f'Missing configuration file: {relative_path}')
            continue

        text = path.read_text(encoding='utf-8')
        for snippet in snippets:
            if snippet not in text:
                failures.append(f'{relative_path}: missing required snippet {snippet!r}')

        for label, forbidden in FORBIDDEN_CONFIG_SNIPPETS.items():
            if forbidden in text:
                failures.append(f'{relative_path}: found forbidden {label} snippet {forbidden!r}')

    for pom_relative in ('pom.xml', 'maven/modelio-parent/pom.xml'):
        pom_text = (repo_root / pom_relative).read_text(encoding='utf-8')
        for line in pom_text.splitlines():
            stripped = line.strip()
            if stripped.startswith('<url>') and stripped.endswith('</url>'):
                url = stripped.removeprefix('<url>').removesuffix('</url>')
                if not url.startswith(ALLOWED_REMOTE_REPOSITORY_PREFIXES):
                    failures.append(f'{pom_relative}: unexpected repository URL {url}')


def validate_required_app_files(app_bundle: Path, failures: list[str]) -> None:
    required_paths = (
        app_bundle / 'Contents/Info.plist',
        app_bundle / 'Contents/MacOS/modelio',
        app_bundle / 'Contents/Resources/modelio.icns',
        app_bundle / 'Contents/Eclipse/modelio.ini',
    )
    for path in required_paths:
        if not path.exists():
            failures.append(f'Missing packaged app path: {path}')


def validate_launcher_architecture(app_bundle: Path, failures: list[str]) -> None:
    launcher = app_bundle / 'Contents/MacOS/modelio'
    if not launcher.is_file():
        return

    result = run_command(['lipo', '-archs', str(launcher)])
    if result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip()
        failures.append(f'lipo failed for {launcher}: {stderr}')
        return

    archs = result.stdout.strip()
    if archs != 'arm64':
        failures.append(f'{launcher}: expected arm64 launcher, got {archs}')


def validate_packaged_plugins(app_bundle: Path, failures: list[str]) -> None:
    plugins_dir = app_bundle / 'Contents/Eclipse/plugins'
    if not plugins_dir.is_dir():
        failures.append(f'Missing packaged plugins directory: {plugins_dir}')
        return

    if not list(plugins_dir.glob('org.eclipse.swt.cocoa.macosx.aarch64_*.jar')):
        failures.append('Missing packaged org.eclipse.swt.cocoa.macosx.aarch64 fragment jar')

    if not list(plugins_dir.glob('org.eclipse.equinox.launcher.cocoa.macosx.aarch64_*')):
        failures.append('Missing packaged org.eclipse.equinox.launcher.cocoa.macosx.aarch64 fragment directory')


def validate_modelio_ini(app_bundle: Path, failures: list[str]) -> None:
    modelio_ini = app_bundle / 'Contents/Eclipse/modelio.ini'
    if not modelio_ini.is_file():
        return

    text = modelio_ini.read_text(encoding='utf-8')
    required_snippets = (
        '-configuration',
        '../Eclipse/configuration',
        '-Dosgi.requiredJavaVersion=21',
    )
    for snippet in required_snippets:
        if snippet not in text:
            failures.append(f'{modelio_ini}: missing required snippet {snippet!r}')

    forbidden_snippets = (
        '-Dapple.awt.graphics.UseQuartz=true',
        '-Dcom.apple.smallTabs=true',
    )
    for snippet in forbidden_snippets:
        if snippet in text:
            failures.append(f'{modelio_ini}: found retired launcher snippet {snippet!r}')


def is_native_candidate(path: Path) -> bool:
    if not path.is_file():
        return False
    if path.suffix in NATIVE_SUFFIXES:
        return True
    if os.access(path, os.X_OK):
        return True
    if path.name.startswith('eclipse_'):
        return True
    return False


def validate_no_x86_64_payloads(app_bundle: Path, failures: list[str]) -> None:
    inspected = 0
    for path in app_bundle.rglob('*'):
        if not is_native_candidate(path):
            continue

        inspected += 1
        result = run_command(['file', str(path)])
        if result.returncode != 0:
            stderr = result.stderr.strip() or result.stdout.strip()
            failures.append(f'file failed for {path}: {stderr}')
            continue

        description = result.stdout.strip()
        if 'x86_64' in description:
            failures.append(f'Unexpected x86_64 payload: {description}')

    if inspected == 0:
        failures.append(f'No native payload candidates were inspected under {app_bundle}')


def validate_quarantine_absent(app_bundle: Path, failures: list[str]) -> None:
    result = run_command(['xattr', '-lr', str(app_bundle)])
    if result.returncode == 0 and 'com.apple.quarantine' in result.stdout:
        failures.append(f'{app_bundle}: com.apple.quarantine attribute is still present')


def main() -> int:
    args = build_argument_parser().parse_args()
    repo_root = args.repo_root.resolve()
    app_bundle = args.app.resolve()
    failures: list[str] = []

    validate_active_configuration(repo_root, failures)

    if not app_bundle.is_dir():
        failures.append(f'Missing app bundle: {app_bundle}')
    else:
        validate_required_app_files(app_bundle, failures)
        validate_launcher_architecture(app_bundle, failures)
        validate_packaged_plugins(app_bundle, failures)
        validate_modelio_ini(app_bundle, failures)
        validate_no_x86_64_payloads(app_bundle, failures)
        validate_quarantine_absent(app_bundle, failures)

    if failures:
        print('MACOS AARCH64 CONTRACT VALIDATION FAILED')
        for failure in failures:
            print(failure)
        return 1

    print('MACOS AARCH64 CONTRACT VALIDATION OK')
    print(f'App bundle: {app_bundle}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

