from pathlib import Path
import zipfile

ROOT = Path('/Users/david/IdeaProjects/Modelio')
ECLIPSE_TARGET = ROOT / 'dev-platform/rcp-target/rcp-eclipse/eclipse'
BINARY_DIR = ECLIPSE_TARGET / 'binary'
FEATURE_DIR = ECLIPSE_TARGET / 'features/org.eclipse.equinox.executable_3.8.1000.v20200915-1508'
FEATURE_JAR = ECLIPSE_TARGET / 'features/org.eclipse.equinox.executable_3.8.1000.v20200915-1508.jar'
PRESERVED_ARM = ROOT / 'products/preserved-macos/eclipse-arm64-rootfiles/Eclipse.app/Contents'
X86_EQ_INFO = FEATURE_DIR / 'bin/cocoa/macosx/x86_64/Eclipse.app/Contents/Info.plist'
ARM_TOP_INFO = PRESERVED_ARM / 'Info.plist'
ARM_TOP_ICON = PRESERVED_ARM / 'Resources/Eclipse.icns'
ARM_EXE = PRESERVED_ARM / 'MacOS/eclipse'
ARM_EQ_LAUNCHER = FEATURE_DIR / 'bin/cocoa/macosx/aarch64/Eclipse.app/Contents/MacOS/launcher'


def add_file(zf: zipfile.ZipFile, src: Path, arcname: str, mode: int) -> None:
    info = zipfile.ZipInfo(arcname)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = mode << 16
    info.date_time = (2026, 4, 13, 12, 0, 0)
    zf.writestr(info, src.read_bytes())


def add_dir(zf: zipfile.ZipFile, arcname: str, mode: int = 0o755) -> None:
    if not arcname.endswith('/'):
        arcname += '/'
    info = zipfile.ZipInfo(arcname)
    info.external_attr = (mode << 16) | 0x10
    info.date_time = (2026, 4, 13, 12, 0, 0)
    zf.writestr(info, b'')


def make_zip(zip_path: Path, entries):
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'w') as zf:
        made_dirs = set()
        for src, arcname, mode in entries:
            parts = arcname.split('/')[:-1]
            current = []
            for part in parts:
                current.append(part)
                dirname = '/'.join(current) + '/'
                if dirname not in made_dirs:
                    add_dir(zf, dirname)
                    made_dirs.add(dirname)
            add_file(zf, src, arcname, mode)


def repack_feature_jar() -> None:
    with zipfile.ZipFile(FEATURE_JAR, 'w') as zf:
        for path in sorted(FEATURE_DIR.rglob('*')):
            rel = path.relative_to(FEATURE_DIR).as_posix()
            if rel in {'META-INF/ECLIPSE_.SF', 'META-INF/ECLIPSE_.RSA'}:
                continue
            if path.is_dir():
                add_dir(zf, rel)
                continue
            mode = 0o755 if path.name in {'launcher', 'launcher.exe', 'eclipsec.exe'} else 0o644
            add_file(zf, path, rel, mode)


def main() -> None:
    make_zip(
        BINARY_DIR / 'org.eclipse.equinox.executable_root.cocoa.macosx.aarch64_3.8.1000.v20200915-1508',
        [
            (X86_EQ_INFO, 'Eclipse.app/Contents/Info.plist', 0o644),
            (ARM_EQ_LAUNCHER, 'Eclipse.app/Contents/MacOS/launcher', 0o755),
        ],
    )
    make_zip(
        BINARY_DIR / 'org.eclipse.platform.ide.executable.cocoa.macosx.aarch64_4.18.0.I20201202-1800',
        [
            (ARM_TOP_INFO, 'Info.plist', 0o644),
            (ARM_EXE, 'MacOS/eclipse', 0o755),
            (ARM_TOP_ICON, 'Resources/Eclipse.icns', 0o644),
        ],
    )
    make_zip(
        BINARY_DIR / 'org.eclipse.rcp.configuration_root.cocoa.macosx.aarch64_1.1.1100.v20201202-1800',
        [
            (ARM_EXE, 'Eclipse.app/Contents/MacOS/eclipse', 0o755),
        ],
    )
    repack_feature_jar()


if __name__ == '__main__':
    main()

