import json
from pathlib import Path

report = json.loads(Path('/Users/david/IdeaProjects/Modelio/dev-platform/rcp-target/rcp-eclipse/eclipse-2026-03/repin-suggestions.json').read_text())
for feature_name, feature_report in report['features'].items():
    print(feature_name)
    print('feature version:', feature_report['current_feature_version'], '->', feature_report['proposed_feature_version'])
    print('remove:')
    for entry in feature_report['remove']:
        print(' ', entry['tag'], entry['id'], entry['version'])
    print('replace:')
    for entry in feature_report['replace']:
        if entry['current_version'] != entry['proposed_version']:
            print(' ', entry['tag'], entry['id'], entry['current_version'], '->', entry['proposed_version'])
    print()

