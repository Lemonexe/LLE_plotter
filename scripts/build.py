"""Build on the target OS: uv run scripts/build.py."""

import shutil
import subprocess
import sys
from importlib.metadata import distribution
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if sys.platform == "darwin":
    raise SystemExit("macOS packaging is a stub; build and validation require a Mac.")
if sys.platform not in ("linux", "win32"):
    raise SystemExit(f"Unsupported build platform: {sys.platform}")
subprocess.run(
    [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        str(ROOT / "packaging" / "LLE_plotter.spec"),
    ],
    cwd=ROOT,
    check=True,
)
output = ROOT / "dist" / "LLE_plotter"
shutil.copy2(ROOT / "LICENSE", output / "LICENSE")
shutil.copy2(ROOT / "README.md", output / "README.md")
licenses = output / "licenses"
licenses.mkdir(exist_ok=True)
for name in (
    "PySide6",
    "PySide6-Essentials",
    "shiboken6",
    "matplotlib",
    "mpltern",
    "numpy",
    "pillow",
    "contourpy",
    "cycler",
    "fonttools",
    "kiwisolver",
    "packaging",
    "pyparsing",
    "python-dateutil",
    "tzdata",
):
    package = distribution(name)
    destination = licenses / name
    destination.mkdir(exist_ok=True)
    (destination / "METADATA.txt").write_text(package.read_text("METADATA") or "", encoding="utf-8")
    for file in package.files or []:
        if any(word in str(file).lower() for word in ("license", "copying", "notice")):
            source = Path(package.locate_file(file))
            if source.is_file():
                target = destination / file
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
shutil.copytree(ROOT / "packaging" / "licenses", licenses / "Qt", dirs_exist_ok=True)
print(f"Portable application: {output}")
