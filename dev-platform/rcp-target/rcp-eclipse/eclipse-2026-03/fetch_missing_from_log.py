from pathlib import Path
import re
import urllib.request

STAGED_DIR = Path('/Users/david/IdeaProjects/Modelio/dev-platform/rcp-target/rcp-eclipse/eclipse-2026-03')
SOURCE_URL = 'https://download.eclipse.org/releases/2026-03/202603111000/'
LOG_DIR = Path('/Users/david/IdeaProjects/Modelio/tmp/validation-2026-03-logs')
PATTERN = re.compile(r'(dev-platform/rcp-target/rcp-eclipse/eclipse-2026-03/(plugins|features)/[^)\s]+) \(No such file or directory\)')


def find_missing_paths() -> list[str]:
    matches: set[str] = set()
    for log_path in sorted(LOG_DIR.glob('*.log')):
        text = log_path.read_text(errors='replace')
        for match in PATTERN.finditer(text):
            matches.add(match.group(1))
    return sorted(matches)


def main() -> None:
    matches = find_missing_paths()
    if not matches:
        print('no missing staged artifacts found in logs')
        return
    for relative_rooted in matches:
        relative = Path(relative_rooted).relative_to('dev-platform/rcp-target/rcp-eclipse/eclipse-2026-03').as_posix()
        target = STAGED_DIR / relative
        source = SOURCE_URL + relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            print('already present', relative)
            continue
        with urllib.request.urlopen(source) as response:
            target.write_bytes(response.read())
        print('fetched', relative)


if __name__ == '__main__':
    main()

