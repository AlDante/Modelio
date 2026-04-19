import json
from pathlib import Path
import urllib.request
import zipfile

SOURCE_URL = 'https://download.eclipse.org/releases/2026-03/202603111000/'
OUTPUT_DIR = Path('/Users/david/IdeaProjects/Modelio/dev-platform/rcp-target/rcp-eclipse/eclipse-2026-03')
FILES = ['content.jar', 'artifacts.jar']


def download_file(file_name: str) -> dict:
    source = SOURCE_URL + file_name
    destination = OUTPUT_DIR / file_name
    with urllib.request.urlopen(source) as response:
        payload = response.read()
        headers = dict(response.headers.items())
    destination.write_bytes(payload)
    return {
        'file': file_name,
        'source': source,
        'size': len(payload),
        'etag': headers.get('ETag'),
        'last_modified': headers.get('Last-Modified'),
    }


def extract_xml_from_jar(jar_name: str) -> str:
    jar_path = OUTPUT_DIR / jar_name
    xml_name = jar_name.replace('.jar', '.xml')
    with zipfile.ZipFile(jar_path) as archive:
        payload = archive.read(xml_name)
    (OUTPUT_DIR / xml_name).write_bytes(payload)
    return xml_name


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {
        'source_url': SOURCE_URL,
        'files': [],
        'extracted_xml': [],
    }
    for file_name in FILES:
        manifest['files'].append(download_file(file_name))
    for jar_name in FILES:
        manifest['extracted_xml'].append(extract_xml_from_jar(jar_name))
    (OUTPUT_DIR / 'stage-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print('staged metadata to', OUTPUT_DIR)
    for entry in manifest['files']:
        print(f"{entry['file']}: {entry['size']} bytes")


if __name__ == '__main__':
    main()

