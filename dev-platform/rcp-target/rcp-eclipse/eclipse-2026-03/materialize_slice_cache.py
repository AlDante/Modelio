from pathlib import Path
import os

STAGED_DIR = Path('/Users/david/IdeaProjects/Modelio/dev-platform/rcp-target/rcp-eclipse/eclipse-2026-03')
SLICE_CACHE = STAGED_DIR / 'slice-cache'


def relink_tree(name: str) -> int:
    source_dir = SLICE_CACHE / name
    target_dir = STAGED_DIR / name
    target_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for source in sorted(source_dir.glob('*.jar')):
        target = target_dir / source.name
        if target.is_symlink() or target.exists():
            target.unlink()
        os.symlink(source, target)
        count += 1
    return count


def main() -> None:
    plugin_count = relink_tree('plugins')
    feature_count = relink_tree('features')
    print('materialized slice cache into staged p2 layout')
    print('plugins:', plugin_count)
    print('features:', feature_count)


if __name__ == '__main__':
    main()

