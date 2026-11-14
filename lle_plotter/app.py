"""Qt desktop application. No command-line interface or data file import."""

import hashlib
import sys
from copy import deepcopy
from pathlib import Path

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from PySide6.QtCore import QByteArray, Qt, QTimer
from PySide6.QtGui import QAction, QColor, QIcon, QKeySequence, QPixmap, QUndoCommand, QUndoStack
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .data import COLORS, LINES, MARKERS, blank_dataset, defaults, validate
from .plot import export_figure, render
from .storage import load, save, state_path
from .table import CompositionModel, CompositionTable


def combo(items, current):
    widget = QComboBox()
    widget.addItems(list(items))
    widget.setCurrentText(current)
    return widget


def button(text, callback):
    widget = QPushButton(text)
    widget.clicked.connect(callback)
    return widget


class DatasetCard(QGroupBox):
    def __init__(self, window, dataset):
        super().__init__("Tie-line set" if dataset["kind"] == "tie" else "Equilibrium curve")
        self.kind = dataset["kind"]
        self.window = window
        layout = QVBoxLayout(self)
        self.label = QLineEdit(dataset["label"])
        self.label.setPlaceholderText("Legend label")
        self.label.setAccessibleName("Dataset legend label")
        layout.addWidget(self.label)
        styles = QHBoxLayout()
        self.color = combo(COLORS, dataset["color"])
        for i, value in enumerate(COLORS.values()):
            pixmap = QPixmap(16, 16)
            pixmap.fill(QColor(value))
            self.color.setItemIcon(i, QIcon(pixmap))
        self.marker = combo(MARKERS, dataset["marker"])
        self.line = combo(LINES, dataset["line"])
        for title, widget in (("Color", self.color), ("Marker", self.marker), ("Line", self.line)):
            widget.setAccessibleName(title)
            styles.addWidget(QLabel(title))
            styles.addWidget(widget)
        layout.addLayout(styles)
        explanation = QLabel(
            "One row = two compositions joined by a tie line."
            if self.kind == "tie"
            else "One row = one composition. Points connect in input order."
        )
        explanation.setWordWrap(True)
        layout.addWidget(explanation)
        self.model = CompositionModel(dataset, window.component_names(), window.undo_stack, self)
        self.table = CompositionTable(self.model)
        self.table.setAccessibleName(self.title() + " composition table")
        self.table.problem.connect(window.input_problem)
        layout.addWidget(self.table)
        actions = QHBoxLayout()
        actions.addWidget(button("Add 10 rows", self.table.add_rows))
        actions.addWidget(button("Remove selected rows", self.table.remove_rows))
        actions.addStretch()
        actions.addWidget(button("Remove set", lambda: window.remove_dataset(self)))
        layout.addLayout(actions)
        self.label.textChanged.connect(window.changed)
        for widget in (self.color, self.marker, self.line):
            widget.currentTextChanged.connect(window.changed)
        self.model.edited.connect(window.changed)

    def snapshot(self):
        return {
            "kind": self.kind,
            "label": self.label.text(),
            "color": self.color.currentText(),
            "marker": self.marker.currentText(),
            "line": self.line.currentText(),
            "rows": deepcopy(self.model.rows),
        }


class DatasetCommand(QUndoCommand):
    def __init__(self, window, card, adding):
        super().__init__("Add dataset" if adding else "Remove dataset")
        self.window, self.card, self.adding = window, card, adding
        self.index = len(window.cards) if adding else window.cards.index(card)

    def attach(self):
        self.window.cards.insert(self.index, self.card)
        self.window.panel_layouts[self.card.kind].insertWidget(
            sum(c.kind == self.card.kind for c in self.window.cards[: self.index]), self.card
        )
        self.card.show()
        self.window.changed()

    def detach(self):
        self.window.cards.remove(self.card)
        self.window.panel_layouts[self.card.kind].removeWidget(self.card)
        self.card.hide()  # Keep the model alive for edits elsewhere in the undo stack.
        self.window.changed()

    def redo(self):
        self.attach() if self.adding else self.detach()

    def undo(self):
        self.detach() if self.adding else self.attach()


class PlotWindow(QMainWindow):
    def __init__(self, parent):
        super().__init__(parent, Qt.WindowType.Window)
        self.setWindowTitle("LLE plotter — chart")
        self.resize(850, 780)
        self.figure = None
        self.canvas = None
        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)
        self.status = QLabel()
        self.status.setWordWrap(True)
        self.layout.addWidget(self.status)
        self.setCentralWidget(self.container)

    def update_figure(self, figure):
        while self.layout.count() > 1:
            item = self.layout.takeAt(1)
            item.widget().deleteLater()
        if self.figure is not None:
            self.figure.clear()
        self.figure = figure
        self.canvas = FigureCanvasQTAgg(figure)
        toolbar = NavigationToolbar2QT(self.canvas, self)
        # Export lives in the main footer with explicit format/DPI controls.
        for action in toolbar.actions():
            if action.text().lower() == "save":
                toolbar.removeAction(action)
        self.layout.addWidget(toolbar)
        self.layout.addWidget(self.canvas, 1)
        self.status.setText(
            "Chart is up to date. Save as file is available in the main window footer."
        )
        self.canvas.draw()


class MainWindow(QMainWindow):
    def __init__(self, path=None):
        super().__init__()
        self.setWindowTitle("LLE plotter")
        self.resize(1280, 900)
        self.path = path if path is not None else state_path()
        state, warning = load(self.path)
        self.loading = True
        self.cards = []
        self.plot_window = PlotWindow(self)
        self.undo_stack = QUndoStack(self)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(300)
        self.timer.timeout.connect(self.persist)
        self.recovery_warning = warning
        root = QWidget()
        self.root_layout = QVBoxLayout(root)
        self.setCentralWidget(root)
        self.build(state)
        self.loading = False
        if state.get("geometry"):
            self.restoreGeometry(QByteArray.fromBase64(state["geometry"].encode("ascii")))
        self.update_colors()
        for text, shortcut, callback in (
            ("Undo", QKeySequence.StandardKey.Undo, self.undo_stack.undo),
            ("Redo", QKeySequence.StandardKey.Redo, self.undo_stack.redo),
        ):
            action = QAction(text, self)
            action.setShortcuts(QKeySequence.keyBindings(shortcut))
            action.triggered.connect(callback)
            self.addAction(action)
        self.cache_banner.setText(warning)
        self.cache_banner.setVisible(bool(warning))

    def build(self, state):
        self.body = QWidget()
        outer = QVBoxLayout(self.body)
        heading = QLabel("LLE plotter")
        heading.setStyleSheet("font-size: 26px; font-weight: 600; padding: 8px")
        self.cache_banner = QLabel()
        self.cache_banner.hide()
        self.cache_banner.setWordWrap(True)
        self.cache_banner.setStyleSheet("background: #fff0c2; color: #493600; padding: 10px")
        self.banner = QLabel()
        self.banner.setWordWrap(True)
        self.banner.hide()
        scroll = QScrollArea()
        self.scroll = scroll
        scroll.setWidgetResizable(True)
        content = QWidget()
        content.setMinimumWidth(1050)
        contents = QVBoxLayout(content)
        contents.addWidget(heading)
        contents.addWidget(self.cache_banner)
        contents.addWidget(self.banner)
        identity = QGroupBox("Chart labels")
        form = QFormLayout(identity)
        names_row = QHBoxLayout()
        self.names = []
        for key, value in zip(("A · bottom right", "B · top", "C · bottom left"), state["names"]):
            names_row.addWidget(QLabel(key))
            entry = QLineEdit(value)
            entry.setAccessibleName(key)
            self.names.append(entry)
            names_row.addWidget(entry)
            entry.textChanged.connect(self.labels_changed)
        form.addRow("Components", names_row)
        self.title = QLineEdit(state["title"])
        self.title.textChanged.connect(self.changed)
        form.addRow("Title (optional)", self.title)
        contents.addWidget(identity)
        panels = QHBoxLayout()
        self.panel_layouts = {}
        for kind, title in (("tie", "Tie lines"), ("curve", "Equilibrium curves")):
            panel = QGroupBox(title)
            panel.setMinimumWidth(500)
            panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            layout = QVBoxLayout(panel)
            self.panel_layouts[kind] = layout
            layout.addStretch()
            layout.addWidget(
                button(
                    "Add tie-line table" if kind == "tie" else "Add equilibrium table",
                    lambda checked=False, k=kind: self.add_dataset(k),
                )
            )
            panels.addWidget(panel)
        contents.addLayout(panels)
        for dataset in state["datasets"]:
            card = DatasetCard(self, dataset)
            self.cards.append(card)
            self.panel_layouts[card.kind].insertWidget(
                self.panel_layouts[card.kind].count() - 2, card
            )
        options = QGroupBox("Plot options")
        opts = QVBoxLayout(options)
        toggle_row = QHBoxLayout()
        self.options = {}
        for key, title in (
            ("ticks", "Axis ticks"),
            ("numbers", "Axis numbers"),
            ("grid", "Grid"),
            ("legend", "Legend"),
            ("color", "Color (off = grayscale)"),
        ):
            check = QCheckBox(title)
            check.setChecked(state["options"][key])
            self.options[key] = check
            check.toggled.connect(self.changed)
            toggle_row.addWidget(check)
        opts.addLayout(toggle_row)
        self.options["color"].toggled.connect(self.update_colors)
        input_row = QHBoxLayout()
        input_row.addWidget(QLabel("Interpret input as"))
        self.scale = combo(
            ["Fraction (total 1)", "Percentage (total 100)"],
            "Percentage (total 100)" if state["options"]["percent"] else "Fraction (total 1)",
        )
        self.scale.currentIndexChanged.connect(self.changed)
        input_row.addWidget(self.scale)
        input_row.addStretch()
        opts.addLayout(input_row)
        help_text = QLabel(
            "All three components are required. Accepted totals: 1 ± 0.0001 or 100 ± 0.01. Within this tolerance, compositions are proportionally normalized for plotting only. Changing the input scale reinterprets cells; it does not convert them.\nPaste tab-separated data from Excel/Calc. Decimal dots or commas and scientific notation are accepted; thousands separators and % signs are not. Ctrl+C copies, Ctrl+V pastes, Delete clears, Ctrl+Z undoes, Ctrl+Shift+Z/Ctrl+Y redoes."
        )
        help_text.setWordWrap(True)
        opts.addWidget(help_text)
        tools = QHBoxLayout()
        tools.addWidget(button("Undo", self.undo_stack.undo))
        tools.addWidget(button("Redo", self.undo_stack.redo))
        tools.addStretch()
        tools.addWidget(button("Reset session…", self.reset_session))
        opts.addLayout(tools)
        contents.addWidget(options)
        contents.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll, 1)
        footer = QFrame()
        footer.setFrameShape(QFrame.Shape.StyledPanel)
        bottom = QHBoxLayout(footer)
        generate = button("Generate", self.generate)
        generate.setDefault(True)
        generate.setShortcut(QKeySequence("Alt+G"))
        generate.setToolTip("Generate chart (Alt+G)")
        bottom.addWidget(generate)
        self.preview_status = QLabel("No chart generated")
        self.preview_status.setWordWrap(True)
        bottom.addWidget(self.preview_status, 1)
        bottom.addWidget(QLabel("Format"))
        self.format = combo(["PNG", "SVG", "PDF"], state["format"])
        self.format.currentTextChanged.connect(self.export_changed)
        bottom.addWidget(self.format)
        bottom.addWidget(QLabel("DPI"))
        self.dpi = combo(["150", "300", "600", "1200"], state["dpi"])
        self.dpi.currentTextChanged.connect(self.export_changed)
        self.dpi.setEnabled(self.format.currentText() == "PNG")
        bottom.addWidget(self.dpi)
        self.export_button = button("Save as file…", self.export)
        self.export_button.setEnabled(False)
        bottom.addWidget(self.export_button)
        outer.addWidget(footer)
        self.root_layout.addWidget(self.body)

    def component_names(self):
        return [entry.text() for entry in self.names]

    def snapshot(self):
        return {
            "version": 1,
            "names": self.component_names(),
            "title": self.title.text(),
            "options": {
                **{key: check.isChecked() for key, check in self.options.items()},
                "percent": self.scale.currentIndex() == 1,
            },
            "datasets": [card.snapshot() for card in self.cards],
            "format": self.format.currentText(),
            "dpi": self.dpi.currentText(),
            "geometry": bytes(self.saveGeometry().toBase64()).decode("ascii"),
        }

    def changed(self, *_):
        if self.loading:
            return
        self.timer.start()
        for card in self.cards:
            card.model.mark_errors({})
        self.banner.hide()
        if self.plot_window.figure is not None:
            self.preview_status.setText("Inputs changed — generate to update")
            self.plot_window.status.setText(
                "Inputs changed — generate to update. Export saves this displayed chart."
            )

    def export_changed(self, *_):
        if self.loading:
            return
        self.dpi.setEnabled(self.format.currentText() == "PNG")
        self.timer.start()

    def labels_changed(self, *_):
        if self.loading:
            return
        for card in self.cards:
            card.model.names = self.component_names()
            card.model.headerDataChanged.emit(Qt.Orientation.Horizontal, 0, card.model.columns - 1)
        self.changed()

    def update_colors(self, *_):
        for card in self.cards:
            card.color.setEnabled(self.options["color"].isChecked())

    def add_dataset(self, kind):
        index = sum(card.kind == kind for card in self.cards)
        card = DatasetCard(self, blank_dataset(kind, index))
        card.color.setEnabled(self.options["color"].isChecked())
        self.undo_stack.push(DatasetCommand(self, card, True))

    def remove_dataset(self, card):
        self.undo_stack.push(DatasetCommand(self, card, False))

    def input_problem(self, text):
        self.banner.setStyleSheet("background: #ffe0df; color: #741c18; padding: 10px")
        self.banner.setText(text)
        self.banner.show()
        QTimer.singleShot(0, lambda: self.scroll.ensureWidgetVisible(self.banner))

    def generate(self):
        state = self.snapshot()
        result = validate(state)
        for di, card in enumerate(self.cards):
            card.model.mark_errors(
                {(r, c): message for d, r, c, message in result.errors if d == di}
            )
        if result.errors:
            di, ri, ci, message = result.errors[0]
            self.input_problem(
                f"{len(result.errors)} invalid cells. {state['datasets'][di]['label']}, row {ri + 1}, column {ci + 1}: {message}. Hover highlighted cells for details."
            )
            return
        try:
            self.plot_window.update_figure(render(state, result.datasets))
        except Exception as exc:
            self.input_problem(f"Could not generate chart: {exc}")
            return
        self.preview_status.setText("Chart is up to date · 180 × 160 mm")
        self.export_button.setEnabled(True)
        self.banner.setText("\n".join(result.warnings))
        self.banner.setStyleSheet("background: #fff0c2; color: #493600; padding: 10px")
        self.banner.setVisible(bool(result.warnings))
        if result.warnings:
            self.plot_window.status.setText("Warning: " + "\n".join(result.warnings))
            QTimer.singleShot(0, lambda: self.scroll.ensureWidgetVisible(self.banner))
        self.plot_window.show()
        self.plot_window.raise_()

    def export(self):
        if self.plot_window.figure is None:
            return
        fmt = self.format.currentText().lower()
        path, _ = QFileDialog.getSaveFileName(
            self, "Save displayed chart", f"LLE-plot.{fmt}", f"{fmt.upper()} files (*.{fmt})"
        )
        if not path:
            return
        if not path.lower().endswith(f".{fmt}"):
            path += f".{fmt}"
            if (
                Path(path).exists()
                and QMessageBox.question(self, "Replace file?", f"Replace {path}?")
                != QMessageBox.StandardButton.Yes
            ):
                return
        try:
            export_figure(
                self.plot_window.figure,
                path,
                format=fmt,
                dpi=int(self.dpi.currentText()),
                facecolor="white",
            )
        except Exception as exc:
            self.input_problem(f"Could not save chart: {exc}")

    def persist(self):
        try:
            save(self.path, self.snapshot())
        except OSError as exc:
            self.cache_banner.setText(
                f"Session could not be cached: {exc}. Keep this window open to retain your work."
            )
            self.cache_banner.show()
            QTimer.singleShot(0, lambda: self.scroll.ensureWidgetVisible(self.cache_banner))
        else:
            self.cache_banner.setText(self.recovery_warning)
            self.cache_banner.setVisible(bool(self.recovery_warning))

    def reset_session(self):
        if (
            QMessageBox.question(
                self,
                "Reset session?",
                "Clear all tables, labels, styles and options? This cannot be undone.",
            )
            != QMessageBox.StandardButton.Yes
        ):
            return
        self.timer.stop()
        self.loading = True
        self.undo_stack.clear()
        self.cards = []
        self.plot_window.hide()
        if self.plot_window.figure is not None:
            self.plot_window.figure.clear()
        self.plot_window.deleteLater()
        self.plot_window = PlotWindow(self)
        old = self.body
        self.root_layout.removeWidget(old)
        old.hide()
        old.deleteLater()
        self.recovery_warning = ""
        self.build(defaults())
        self.loading = False
        self.update_colors()
        self.persist()

    def moveEvent(self, event):
        super().moveEvent(event)
        if hasattr(self, "timer") and not self.loading:
            self.timer.start()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "timer") and not self.loading:
            self.timer.start()

    def closeEvent(self, event):
        self.timer.stop()
        self.persist()
        if self.cache_banner.isVisible() and "could not be cached" in self.cache_banner.text():
            if (
                QMessageBox.question(
                    self,
                    "Session not saved",
                    "Session caching failed. Close and lose uncached changes?",
                )
                != QMessageBox.StandardButton.Yes
            ):
                event.ignore()
                return
        self.plot_window.close()
        event.accept()


def main():
    app = QApplication(sys.argv[:1])
    app.setApplicationName("LLE plotter")
    app.setOrganizationName("LLE plotter")
    app.setWindowIcon(QIcon(str(Path(__file__).resolve().parent / "icon.ico")))
    # The per-user appdata path also identifies the local activation socket.
    identity = str(state_path()).encode("utf-8")
    server_name = "lle-plotter-" + hashlib.sha256(identity).hexdigest()[:24]
    socket = QLocalSocket()
    socket.connectToServer(server_name)
    if socket.waitForConnected(500):
        socket.write(b"activate")
        socket.waitForBytesWritten(500)
        return
    server = QLocalServer()
    server.setSocketOptions(QLocalServer.SocketOption.UserAccessOption)
    # QLockFile prevents two simultaneous launches racing through stale-socket cleanup.
    from PySide6.QtCore import QLockFile

    path = state_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        QMessageBox.critical(
            None, "Cannot start LLE plotter", f"Cannot create application data directory: {exc}"
        )
        return
    lock = QLockFile(str(path.with_suffix(".lock")))
    if not lock.tryLock(1000):
        socket.connectToServer(server_name)
        if socket.waitForConnected(1000):
            socket.write(b"activate")
            socket.waitForBytesWritten(500)
        else:
            QMessageBox.warning(
                None,
                "LLE plotter is running",
                "Another instance is starting or owns the session. Try again shortly.",
            )
        return
    QLocalServer.removeServer(server_name)
    if not server.listen(server_name):
        QMessageBox.critical(None, "Cannot start LLE plotter", server.errorString())
        return
    window = MainWindow()

    def activate():
        while server.hasPendingConnections():
            connection = server.nextPendingConnection()
            connection.disconnectFromServer()
            connection.deleteLater()
        window.showNormal()
        window.raise_()
        window.activateWindow()

    server.newConnection.connect(activate)
    window.show()
    app.exec()
    server.close()
    lock.unlock()
