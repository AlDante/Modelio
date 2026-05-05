#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from pathlib import Path
import plistlib
import shlex
import shutil
import subprocess
import sys
import tempfile
import time


STARTUP_MARKERS = (
    "Eclipse application started.",
    "Workbench launched",
    "Workspace restored",
    "Application model loaded",
)


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Launch the packaged Modelio payload and verify that this session created a fresh logfile."
    )
    parser.add_argument(
        "--app",
        type=Path,
        required=True,
        help="Path to the built Modelio.app bundle to test.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=45,
        help="Maximum number of seconds to allow the launched payload to run before it is terminated.",
    )
    parser.add_argument(
        "--work-dir",
        type=Path,
        help="Directory to use for the isolated home, workspace, and captured console log. If omitted, a temporary directory is used.",
    )
    parser.add_argument(
        "--launch-mode",
        choices=("native", "java"),
        default="java",
        help="How to launch the packaged app payload. Use 'java' for the default packaged-config smoke or 'native' for direct launcher debugging.",
    )
    return parser


def resolve_java() -> str:
    java_home = os.environ.get("JAVA_HOME")
    if java_home:
        candidate = Path(java_home) / "bin" / "java"
        if candidate.exists():
            return str(candidate)
    return "java"


def parse_eclipse_launcher_args(base_dir: Path, args: list[str]) -> tuple[Path, list[str], list[str]]:
    startup_relative: str | None = None
    program_args: list[str] = []
    vmargs: list[str] = []
    index = 0

    while index < len(args):
        line = args[index].strip()
        if not line:
            index += 1
            continue
        if line == "-vmargs":
            vmargs = [arg.strip() for arg in args[index + 1 :] if arg.strip()]
            break
        if line == "-startup" and index + 1 < len(args):
            startup_relative = args[index + 1].strip()
            index += 2
            continue
        if line == "--launcher.library" and index + 1 < len(args):
            index += 2
            continue
        program_args.append(line)
        index += 1

    if startup_relative is None:
        raise ValueError(f"Unable to locate -startup entry under {base_dir}")

    startup_jar = (base_dir / startup_relative).resolve()
    return startup_jar, program_args, vmargs


def parse_modelio_ini(modelio_ini: Path) -> tuple[Path, list[str], list[str]]:
    lines = [line.strip() for line in modelio_ini.read_text(encoding="utf-8").splitlines() if line.strip()]
    return parse_eclipse_launcher_args(modelio_ini.parent, lines)


def parse_info_plist(launcher_bundle: Path) -> tuple[Path, list[str], list[str]] | None:
    info_plist = launcher_bundle / "Contents" / "Info.plist"
    if not info_plist.is_file():
        return None
    with info_plist.open("rb") as handle:
        plist = plistlib.load(handle)
    eclipse_args = plist.get("Eclipse")
    if not eclipse_args:
        return None
    try:
        return parse_eclipse_launcher_args(launcher_bundle / "Contents", [str(arg) for arg in eclipse_args])
    except ValueError:
        return None


def iter_launcher_candidates(app_bundle: Path) -> list[Path]:
    candidates = [app_bundle]
    nested_apps = [
        app_bundle / "Contents" / "Eclipse" / "modelio.app",
        app_bundle / "Contents" / "Eclipse" / "Modelio.app",
    ]
    for nested_app in nested_apps:
        if nested_app.exists() and nested_app not in candidates:
            candidates.insert(0, nested_app)
    return candidates


def resolve_native_launcher(app_bundle: Path) -> tuple[Path, Path]:
    for candidate in iter_launcher_candidates(app_bundle):
        macos_dir = candidate / "Contents" / "MacOS"
        if not macos_dir.is_dir():
            continue
        preferred = macos_dir / "modelio"
        if preferred.exists() and os.access(preferred, os.X_OK):
            return candidate, preferred
        executables = [
            entry
            for entry in sorted(macos_dir.iterdir())
            if entry.is_file() and os.access(entry, os.X_OK)
        ]
        bundle_named = next(
            (
                entry
                for entry in executables
                if entry.name.lower() == candidate.stem.lower()
            ),
            None,
        )
        if bundle_named is not None:
            return candidate, bundle_named
        if len(executables) == 1:
            return candidate, executables[0]
    fail(f"Missing packaged launcher under {app_bundle}")


def build_native_command(app_bundle: Path, data_dir: Path) -> list[str]:
    launcher = app_bundle / "Contents" / "MacOS" / "modelio"
    if not launcher.is_file():
        raise FileNotFoundError(f"Missing packaged launcher: {launcher}")
    return [str(launcher), "-vm", resolve_java(), "-consoleLog", "-clean", "-data", str(data_dir)]


def build_java_command(app_bundle: Path, home_dir: Path, data_dir: Path) -> list[str]:
    eclipse_dir = app_bundle / "Contents" / "Eclipse"
    configuration_dir = eclipse_dir / "configuration"
    if not configuration_dir.is_dir():
        raise FileNotFoundError(f"Missing configuration directory: {configuration_dir}")

    parsed: tuple[Path, list[str], list[str]] | None = None
    for candidate in iter_launcher_candidates(app_bundle):
        parsed = parse_info_plist(candidate)
        if parsed is not None:
            break
        launcher_ini = candidate / "Contents" / "Eclipse" / "launcher.ini"
        if launcher_ini.is_file():
            parsed = parse_modelio_ini(launcher_ini)
            break
        modelio_ini = candidate / "Contents" / "Eclipse" / "modelio.ini"
        if modelio_ini.is_file():
            parsed = parse_modelio_ini(modelio_ini)
            break
    if parsed is None:
        modelio_ini = eclipse_dir / "modelio.ini"
        if not modelio_ini.is_file():
            raise FileNotFoundError(f"Missing launcher configuration: {modelio_ini}")
        parsed = parse_modelio_ini(modelio_ini)

    startup_jar, program_args, vmargs = parsed
    if not startup_jar.is_file():
        raise FileNotFoundError(f"Missing Equinox launcher jar resolved from packaged launcher metadata: {startup_jar}")

    return [
        resolve_java(),
        *vmargs,
        f"-Duser.home={home_dir}",
        "-jar",
        str(startup_jar),
        *program_args,
        "-consoleLog",
        "-clean",
        "-configuration",
        str(configuration_dir),
        "-data",
        str(data_dir),
    ]


def build_native_launch_command(
    app_bundle: Path,
    data_dir: Path,
    java_executable: str,
) -> tuple[list[str], Path, Path]:
    launcher_bundle, launcher = resolve_native_launcher(app_bundle)
    return [
        str(launcher),
        "-vm",
        java_executable,
        "-consoleLog",
        "-clean",
        "-data",
        str(data_dir),
    ], launcher_bundle, launcher


def prepare_work_dir(work_dir: Path | None) -> tuple[Path, bool]:
    if work_dir is None:
        return Path(tempfile.mkdtemp(prefix="modelio-runtime-logging-smoke-")), True

    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    return work_dir, False


def write_capture_header(output_file: Path, command: list[str], launch_started: float) -> None:
    output_file.write_text(
        "Launch start epoch: "
        + f"{launch_started:.3f}"
        + "\nCMD="
        + shlex.join(command)
        + "\n\n",
        encoding="utf-8",
    )


def append_capture(output_file: Path, label: str, content: str | None) -> None:
    if not content:
        return
    with output_file.open("a", encoding="utf-8") as handle:
        handle.write(label)
        handle.write("\n")
        handle.write(content)
        if not content.endswith("\n"):
            handle.write("\n")


def normalise_output(content: str | bytes | None) -> str:
    if content is None:
        return ""
    if isinstance(content, bytes):
        return content.decode("utf-8", errors="replace")
    return content


def find_latest_session_log(home_dir: Path, launch_started: float) -> Path | None:
    log_root = home_dir / ".modelio"
    candidates = [
        path
        for path in log_root.glob("*/modelio-*.log")
        if path.is_file() and path.stat().st_mtime >= launch_started - 1.0
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def find_native_session_log(home_dir: Path, launch_started: float) -> tuple[Path | None, Path]:
    session_log = find_latest_session_log(home_dir, launch_started)
    if session_log is not None:
        return session_log, home_dir
    real_home = Path.home()
    if real_home != home_dir:
        session_log = find_latest_session_log(real_home, launch_started)
        if session_log is not None:
            return session_log, real_home
    return None, home_dir


def find_first_marker(content: str) -> str | None:
    for marker in STARTUP_MARKERS:
        if marker in content:
            return marker
    return None


def run_smoke_test(app_bundle: Path, timeout_seconds: int, requested_work_dir: Path | None, launch_mode: str) -> int:
    eclipse_dir = app_bundle / "Contents" / "Eclipse"
    work_dir, should_cleanup = prepare_work_dir(requested_work_dir)
    home_dir = work_dir / "home"
    data_dir = work_dir / "workspace"
    console_log = work_dir / "runtime-console.log"
    java_executable = resolve_java()
    home_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    try:
        if launch_mode == "native":
            command, launcher_bundle, launcher = build_native_launch_command(
                app_bundle,
                data_dir,
                java_executable,
            )
            working_directory = launcher.parent
        else:
            command = build_java_command(app_bundle, home_dir, data_dir)
            launcher_bundle = app_bundle
            launcher = Path(java_executable)
            working_directory = app_bundle / "Contents" / "Eclipse"
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        if should_cleanup:
            shutil.rmtree(work_dir)
        return 1

    launch_started = time.time()
    write_capture_header(console_log, command, launch_started)

    environment = os.environ.copy()
    environment["HOME"] = str(home_dir)

    timed_out = False
    stdout_text = ""
    stderr_text = ""
    returncode = 0

    try:
        result = subprocess.run(
            command,
            cwd=working_directory,
            env=environment,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        stdout_text = normalise_output(result.stdout)
        stderr_text = normalise_output(result.stderr)
        returncode = result.returncode
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        stdout_text = normalise_output(exc.stdout)
        stderr_text = normalise_output(exc.stderr)
        returncode = 0

    append_capture(console_log, "[stdout]", stdout_text)
    append_capture(console_log, "[stderr]", stderr_text)
    if timed_out:
        append_capture(console_log, "[status]", f"TIMEOUT after {timeout_seconds}s")

    if returncode != 0:
        print(f"Runtime smoke launch failed with exit code {returncode}.", file=sys.stderr)
        print(f"Captured console log: {console_log}", file=sys.stderr)
        if should_cleanup:
            shutil.rmtree(work_dir)
        return returncode

    if launch_mode == "native":
        session_log, log_home = find_native_session_log(home_dir, launch_started)
    else:
        session_log = find_latest_session_log(home_dir, launch_started)
        log_home = home_dir

    if session_log is None:
        print("No fresh Modelio logfile was created for this session.", file=sys.stderr)
        print(f"Captured console log: {console_log}", file=sys.stderr)
        print(f"Isolated home: {home_dir}", file=sys.stderr)
        if launch_mode == "native":
            print(f"Native-home fallback checked: {Path.home()}", file=sys.stderr)
        if should_cleanup:
            shutil.rmtree(work_dir)
        return 1

    active_log_line = None
    combined_console = stdout_text + "\n" + stderr_text
    for line in combined_console.splitlines():
        if "Active log file name:" in line:
            active_log_line = line.strip()
            break

    log_content = session_log.read_text(encoding="utf-8", errors="replace")
    marker = find_first_marker(log_content)
    if marker is None:
        marker = find_first_marker(combined_console)
    if marker is None:
        print("Fresh logfile was created, but no expected startup marker was found in the logfile or console output.", file=sys.stderr)
        print(f"Captured console log: {console_log}", file=sys.stderr)
        print(f"Session logfile: {session_log}", file=sys.stderr)
        if should_cleanup:
            shutil.rmtree(work_dir)
        return 1

    if session_log.stat().st_size <= 0:
        print(f"Session logfile is empty: {session_log}", file=sys.stderr)
        print(f"Captured console log: {console_log}", file=sys.stderr)
        if should_cleanup:
            shutil.rmtree(work_dir)
        return 1

    print("RUNTIME LOGGING SMOKE OK")
    print(f"Launch mode: {launch_mode}")
    print(f"Work directory: {work_dir}")
    print(f"Captured console log: {console_log}")
    print(f"Session logfile: {session_log}")
    print(f"Log home used: {log_home}")
    if active_log_line:
        print(active_log_line)
    print(f"Verified startup marker: {marker}")
    if timed_out:
        print(f"Launch remained active for at least {timeout_seconds}s before timeout, which is acceptable for this smoke check.")

    if should_cleanup:
        shutil.rmtree(work_dir)
    return 0


def main() -> int:
    args = build_argument_parser().parse_args()
    return run_smoke_test(args.app, args.timeout, args.work_dir, args.launch_mode)


if __name__ == "__main__":
    raise SystemExit(main())
