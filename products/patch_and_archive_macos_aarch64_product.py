#!/usr/bin/env python3
import argparse
from pathlib import Path
import subprocess
import sys
import tarfile


PRODUCTS_DIR = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('--app', type=Path, required=True)
    parser.add_argument('--patch-script', type=Path, default=PRODUCTS_DIR / 'patch_macos_aarch64_app.py')
    parser.add_argument('--app-name', default='Modelio')
    parser.add_argument('--short-version', default='5.4.1')
    return parser.parse_args()


def build_archive_path(app_bundle: Path) -> Path:
    return app_bundle.parents[3] / 'org.modelio.product-macosx.cocoa.aarch64.tar.gz'


def remove_if_exists(path: Path) -> None:
    if path.exists():
        path.unlink()


def patch_app(app_bundle: Path, patch_script: Path, app_name: str, short_version: str) -> None:
    subprocess.run(
        [
            sys.executable,
            str(patch_script),
            '--app-contents',
            str(app_bundle / 'Contents'),
            '--app-name',
            app_name,
            '--short-version',
            short_version,
        ],
        check=True,
    )


def rebuild_archive(app_bundle: Path, archive_path: Path) -> None:
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive_path, 'w:gz') as handle:
        handle.add(app_bundle, arcname=app_bundle.name)


def main() -> int:
    args = parse_args()
    app_bundle = args.app.resolve()
    if not app_bundle.is_dir():
        return 0

    archive_path = build_archive_path(app_bundle)
    stale_top_level_archive = app_bundle.parents[4] / archive_path.name

    patch_app(app_bundle, args.patch_script.resolve(), args.app_name, args.short_version)
    remove_if_exists(archive_path)
    remove_if_exists(stale_top_level_archive)
    rebuild_archive(app_bundle, archive_path)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

