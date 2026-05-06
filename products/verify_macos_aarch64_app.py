#!/usr/bin/env python3
import argparse
from pathlib import Path
import subprocess


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser()
	parser.add_argument('--app', type=Path, required=True)
	return parser.parse_args()


def run_checked(command: list[str]) -> None:
	subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def ensure_no_quarantine(app_bundle: Path) -> None:
	result = subprocess.run(
		['xattr', '-lr', str(app_bundle)],
		check=False,
		capture_output=True,
		text=True,
	)
	if result.returncode == 0 and 'com.apple.quarantine' in result.stdout:
		raise SystemExit('macOS aarch64 app still has com.apple.quarantine after patching')


def main() -> int:
	args = parse_args()
	app_bundle = args.app.resolve()
	if not app_bundle.is_dir():
		return 0

	run_checked(['plutil', '-lint', str(app_bundle / 'Contents/Info.plist')])
	run_checked(['codesign', '--verify', '--deep', '--strict', '--verbose=2', str(app_bundle)])
	ensure_no_quarantine(app_bundle)
	return 0


if __name__ == '__main__':
	raise SystemExit(main())

