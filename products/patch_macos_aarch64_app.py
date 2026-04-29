import argparse
import plistlib
from pathlib import Path
import shutil
import stat
import subprocess

PRODUCTS_DIR = Path(__file__).resolve().parent
REPO_DIR = PRODUCTS_DIR.parent
LAUNCHER_SRC = REPO_DIR / 'products/preserved-macos/eclipse-arm64-rootfiles/Eclipse.app/Contents/MacOS/eclipse'
ICON_SRC = REPO_DIR / 'products/icons/modelio.icns'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--app-contents',
        type=Path,
        default=PRODUCTS_DIR / 'target/products/org.modelio.product/macosx/cocoa/aarch64/Modelio.app/Contents',
    )
    parser.add_argument('--app-name', default='Modelio')
    parser.add_argument('--short-version', default='5.4.1')
    return parser.parse_args()


def detect_bundle_version(app_contents: Path, short_version: str) -> str:
    version_plugins = sorted((app_contents / 'Eclipse/plugins').glob('org.modelio.version_*.jar'))
    if not version_plugins:
        return short_version

    plugin_name = version_plugins[-1].name
    return plugin_name.removeprefix('org.modelio.version_').removesuffix('.jar')


def build_info_plist(app_name: str, short_version: str, bundle_version: str) -> dict:
    return {
        'CFBundleExecutable': 'modelio',
        'CFBundleGetInfoString': (
            f'{app_name} {short_version}, '
            'Copyright Modeliosoft and others 2013, 2026. All rights reserved.'
        ),
        'CFBundleIconFile': 'modelio.icns',
        'CFBundleIdentifier': 'org.modelio.product',
        'CFBundleInfoDictionaryVersion': '6.0',
        'CFBundleName': app_name,
        'CFBundlePackageType': 'APPL',
        'CFBundleShortVersionString': short_version,
        'CFBundleSignature': '????',
        'CFBundleVersion': bundle_version,
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': True,
        'CFBundleDevelopmentRegion': 'English',
        'Eclipse': ['-keyring', '~/.eclipse_keyring'],
        'CFBundleDisplayName': app_name,
    }


def write_info_plist(info_dst: Path, app_name: str, short_version: str, bundle_version: str) -> None:
    plist = build_info_plist(app_name, short_version, bundle_version)
    with info_dst.open('wb') as handle:
        plistlib.dump(plist, handle, sort_keys=False)


def upsert_argument_pair(lines: list[str], flag: str, value: str, before_flag: str) -> list[str]:
    updated = list(lines)
    if flag in updated:
        index = updated.index(flag)
        if index + 1 < len(updated):
            updated[index + 1] = value
        else:
            updated.append(value)
        return updated

    insert_at = updated.index(before_flag) if before_flag in updated else len(updated)
    updated[insert_at:insert_at] = [flag, value]
    return updated


def patch_modelio_ini(modelio_ini: Path) -> None:
    lines = modelio_ini.read_text(encoding='utf-8').splitlines()
    lines = upsert_argument_pair(lines, '-configuration', '../Eclipse/configuration', '-vmargs')
    modelio_ini.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def verify_launcher_arch(launcher: Path) -> None:
    result = subprocess.run(
        ['lipo', '-archs', str(launcher)],
        capture_output=True,
        text=True,
        check=True,
    )
    archs = result.stdout.strip()
    if archs != 'arm64':
        raise SystemExit(f'Expected arm64 launcher, got: {archs}')


def clear_quarantine(path: Path) -> None:
    subprocess.run(
        ['xattr', '-dr', 'com.apple.quarantine', str(path)],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def ad_hoc_sign(app_bundle: Path) -> None:
    subprocess.run(
        ['codesign', '--force', '--deep', '--sign', '-', '--timestamp=none', str(app_bundle)],
        check=True,
    )


def main() -> int:
    args = parse_args()
    app_contents = args.app_contents.resolve()
    app_bundle = app_contents.parent
    modelio_ini = app_contents / 'Eclipse/modelio.ini'
    if not modelio_ini.exists():
        return 0

    info_dst = app_contents / 'Info.plist'
    launcher_dst = app_contents / 'MacOS/modelio'
    icon_dst = app_contents / 'Resources/modelio.icns'
    bundle_version = detect_bundle_version(app_contents, args.short_version)

    launcher_dst.parent.mkdir(parents=True, exist_ok=True)
    icon_dst.parent.mkdir(parents=True, exist_ok=True)

    shutil.copy2(LAUNCHER_SRC, launcher_dst)
    shutil.copy2(ICON_SRC, icon_dst)
    write_info_plist(info_dst, args.app_name, args.short_version, bundle_version)
    patch_modelio_ini(modelio_ini)

    launcher_dst.chmod(launcher_dst.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    verify_launcher_arch(launcher_dst)
    clear_quarantine(app_bundle)
    ad_hoc_sign(app_bundle)
    return 0


raise SystemExit(main())
