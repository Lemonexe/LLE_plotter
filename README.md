# LLE plotter

A desktop application for entering liquid-liquid equilibrium compositions and generating ternary plots. Built with Qt Widgets (PySide6), Matplotlib and mpltern. No command-line interface or data file import is provided.

Run `LLE_plotter` on Linux or `LLE_plotter.exe` on Windows from the portable application folder. Keep the entire folder together; Python and Qt are bundled. Linux uses system graphics, font and desktop libraries. The Linux build targets Debian 13 / GNOME x86-64; compatibility with older distributions is not guaranteed. Windows binaries must be built and tested on Windows. macOS packaging is a stub.

## Entering compositions

Name the components A (bottom right), B (top), and C (bottom left), and optionally enter a chart title. A curve table contains A/B/C; a tie-line table contains A/B/C for endpoint 1 followed by A/B/C for endpoint 2. Each table represents an independently styled dataset with a legend label. Add or remove tables as needed. Neither dataset type is required; empty input generates a blank ternary diagram.

Paste tab-separated cells from Excel or Calc into the selected starting cell. Rows expand automatically, or use **Add 10 rows**. Ctrl+C copies selections, Ctrl+V pastes, Delete clears cells, Ctrl+Z undoes, and Ctrl+Shift+Z or Ctrl+Y redoes. Row and dataset removal can be undone. Paste exceeding the fixed number of columns is rejected in full. Curve points connect in input order without sorting, smoothing or fitting.

Choose **Fraction** (total 1) or **Percentage** (total 100). This describes your input and changes axis formatting; it never changes entered cells. The app does not distinguish mole and mass compositions or convert between them. Decimal dots or decimal commas and scientific notation are accepted. Thousands separators and literal percent signs are not supported: `1,234` means the decimal number 1.234.

Blank rows and tables are ignored. Partially filled rows, negative/out-of-range numbers and invalid composition totals block generation, with an error banner and highlighted cells. Totals within ±0.0001 (fraction) or ±0.01 percentage points are proportionally normalized **only in the plotting copy**. Duplicate points and coincident tie endpoints are preserved. One-point curves without markers produce a warning banner.

Select color, marker (including None), and line style (including None) per dataset. Grayscale renders all datasets black and preserves their stored color choices. Selecting both marker and line None hides the dataset and its legend entry. Tick marks, axis numbers, grid and legend are independently controlled.

## Preview and export

**Generate** updates a separate reusable interactive chart window. Its Matplotlib navigation toolbar supports inspection and resetting the view. Changes to inputs mark the displayed chart as outdated until Generate is clicked again. Validation errors leave the previous chart available.

The main window footer always contains Generate and export controls. **Save as file** exports the displayed chart (including the current navigation view) as PNG, SVG or PDF. Exports have fixed dimensions of 180 × 160 mm. PNG offers 150/300/600/1200 DPI, default 300; SVG/PDF preserve vector lines and text and disable the DPI selector. There is no printer integration.

## Session recovery

All entered text, including incomplete/invalid cells, labels, styles, options, export settings and main window geometry are cached automatically 300 ms after changes, and on closing. Only one instance runs per user; a second launch requests activation of the existing window. There is no project import/export UI.

Cache locations follow Qt's per-user application data conventions:

- Linux: `$XDG_DATA_HOME/LLE plotter/LLE plotter/session.json`, normally under `~/.local/share`.
- Windows: `%LOCALAPPDATA%\LLE plotter\LLE plotter\session.json`.

Writes replace the previous cache atomically. Caching failures show a banner; damaged cache files are preserved with a timestamp and the app starts with defaults. **Reset session** clears the current session after confirmation. Cache recovery is best effort, not a substitute for retaining source data in your spreadsheet. Undo history and the generated figure are not persisted.

For source setup, testing and builds, see [CONTRIBUTING.md](CONTRIBUTING.md). Previous CLI/file-import code is available in Git history.
