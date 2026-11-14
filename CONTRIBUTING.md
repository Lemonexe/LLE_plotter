# Development and builds

Install [uv](https://docs.astral.sh/uv/). The repository pins Python **3.14.10** in `.python-version`; uv installs/manages Python and dependencies. `uv.lock` fixes the resolved package versions.

```sh
uv sync --locked
uv run --locked python launch.py
```

This launches the same GUI used in production. No separate development application, server or application CLI is needed.

## Checks

```sh
uv run --locked ruff check lle_plotter tests scripts launch.py
uv run --locked ruff format --check lle_plotter tests scripts launch.py
QT_QPA_PLATFORM=offscreen uv run --locked pytest -q
```

On Windows PowerShell set `$env:QT_QPA_PLATFORM = "offscreen"` before pytest. GUI tests isolate their session cache in temporary directories.

## Portable builds

On Linux:

```sh
sh scripts/build-linux.sh
```

On Windows PowerShell:

```powershell
.\scripts\build-windows.ps1
```

Both scripts synchronize locked dependencies and run the shared PyInstaller spec. Alternatively run `uv run --locked scripts/build.py` after syncing. Output: `dist/LLE_plotter/`, including executable, `_internal` dependencies, application license and README. Distribute the **whole directory**. Builds are produced on their target OS, not cross-compiled. Windows execution has no console window. No installer, signing or automatic updating is configured.

PyInstaller retains dependency license files in `_internal`; keep these with distributions. Qt/PySide6 is dynamically linked and distributed under its applicable open-source licenses; the application retains the repository's MIT license.

Linux requires build tools `ldd`, `objdump` and `objcopy`, normally supplied by libc-bin and binutils. The resulting binary bundles Python and Qt but uses the system's glibc and graphics/font/desktop libraries. Build on the oldest supported distribution if targeting an older glibc. The current local target is Debian 13 / GNOME x86-64. Windows scripts/spec are prepared but require testing on a Windows machine. `scripts/build-macos.sh` deliberately reports that macOS packaging is not implemented.

## Structure

- `lle_plotter/data.py`: numeric parsing, composition validation, defaults and cache schema.
- `lle_plotter/table.py`: fixed-column Qt model/view, clipboard and undoable edits.
- `lle_plotter/plot.py`: figure rendering, coordinate mapping and plot styles.
- `lle_plotter/storage.py`: per-user cache and atomic writes.
- `lle_plotter/app.py`: GUI, preview, export, session lifecycle and single-instance activation.
- `packaging/LLE_plotter.spec`: shared Linux/Windows packaging configuration.

Keep scientific transformations independent of UI code. Input rows remain untouched by generation; normalization applies only to validated rendering copies.
