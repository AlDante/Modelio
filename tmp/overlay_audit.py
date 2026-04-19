import zipfile
from pathlib import Path

checks = {
    "swt": {
        "path": Path("/Users/david/IdeaProjects/Modelio/dev-platform/rcp-target/rcp-eclipse/swt/content.jar"),
        "needles": [
            "unit id='org.eclipse.swt'",
            "unit id='org.eclipse.swt.cocoa.macosx.aarch64'",
            "unit id='org.eclipse.swt.cocoa.macosx.x86_64'",
        ],
    },
    "launcher-arm64": {
        "path": Path("/Users/david/IdeaProjects/Modelio/dev-platform/rcp-target/rcp-eclipse/launcher-arm64/content.jar"),
        "needles": [
            "unit id='org.eclipse.equinox.launcher.cocoa.macosx'",
            "unit id='org.eclipse.equinox.launcher.cocoa.macosx.aarch64'",
        ],
    },
    "macos-arm64": {
        "path": Path("/Users/david/IdeaProjects/Modelio/dev-platform/rcp-target/rcp-eclipse/macos-arm64/content.jar"),
        "needles": [
            "unit id='org.eclipse.core.filesystem.macosx'",
            "unit id='org.eclipse.equinox.security.macosx'",
        ],
    },
    "jna": {
        "path": Path("/Users/david/IdeaProjects/Modelio/dev-platform/rcp-target/rcp-eclipse/jna/repository/content.jar"),
        "needles": [
            "unit id='com.sun.jna'",
            "unit id='com.sun.jna.platform'",
        ],
    },
}

for label, cfg in checks.items():
    print(label)
    with zipfile.ZipFile(cfg["path"]) as zf:
        content = zf.read("content.xml").decode("utf-8", "replace")
    for needle in cfg["needles"]:
        matches = [line.strip() for line in content.splitlines() if needle in line]
        print(matches[0] if matches else f"MISSING: {needle}")
    print()

