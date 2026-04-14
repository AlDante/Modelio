from pathlib import Path
import subprocess

base = Path("/Users/david/IdeaProjects/Modelio/products/target/products/org.modelio.product/macosx/cocoa/aarch64/Modelio 5.4.1.app/Contents/Eclipse")
log = Path("/Users/david/IdeaProjects/Modelio/.runtime-jar-smoke.log")
data = Path("/Users/david/IdeaProjects/Modelio/.runtime-jar-data")
conf = base / "configuration"
launcher = base / "plugins" / "org.eclipse.equinox.launcher_1.6.0.v20200915-1508.jar"
java = Path("/opt/local/Library/Java/JavaVirtualMachines/openjdk11-temurin/Contents/Home/bin/java")

data.mkdir(exist_ok=True)
cmd = [
    str(java),
    "-Xms512m",
    "-Xmx2048m",
    "-Dpython.console.encoding=UTF-8",
    "-Dosgi.requiredJavaVersion=11",
    "--add-modules=ALL-SYSTEM",
    "-XstartOnFirstThread",
    "-Dorg.eclipse.swt.internal.carbon.smallFonts",
    "-jar",
    str(launcher),
    "-consoleLog",
    "-clean",
    "-configuration",
    str(conf),
    "-data",
    str(data),
]

with log.open("w", encoding="utf-8") as f:
    f.write("CMD=" + " ".join(cmd) + "\n")
    try:
        completed = subprocess.run(
            cmd,
            cwd=str(base),
            stdout=f,
            stderr=subprocess.STDOUT,
            timeout=35,
            check=False,
        )
        f.write(f"\nEXIT={completed.returncode}\n")
    except subprocess.TimeoutExpired:
        f.write("\nTIMEOUT\n")

