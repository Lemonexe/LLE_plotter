import json
from copy import deepcopy

import pytest
from PySide6.QtGui import QUndoStack

from lle_plotter.app import MainWindow
from lle_plotter.data import blank_dataset, defaults, number, validate
from lle_plotter.plot import render
from lle_plotter.storage import load, save
from lle_plotter.table import CompositionModel, CompositionTable


def example():
    state = defaults()
    state["datasets"][0]["rows"] = [["0.8", "0.1", "0.1", "0.1", "0.2", "0.7"]]
    state["datasets"][1]["rows"] = [["0.8", "0.1", "0.1"], ["0.1", "0.2", "0.7"]]
    return state


def test_validation_normalizes_only_copy_and_rejects_bad_cells():
    state = example()
    state["datasets"][1]["rows"][0] = ["0.8", "0.1", "0.0999"]
    before = deepcopy(state)
    result = validate(state)
    assert not result.errors
    assert sum(result.datasets[1]["values"][0]) == pytest.approx(1)
    assert state == before
    state["datasets"][0]["rows"][0][3] = "-0.1"
    assert validate(state).errors[0][:3] == (0, 0, 3)
    state["datasets"][1]["rows"] = [["0.5", "", "0.5"]]
    assert any(error[:3] == (1, 0, 1) for error in validate(state).errors)


def test_numbers_and_percentage():
    assert number("1,25e-2") == 0.0125
    for text in ("nan", "inf", "1,234.5", "1 000", "50%", "1e999"):
        with pytest.raises(ValueError):
            number(text)
    state = defaults()
    state["options"]["percent"] = True
    state["datasets"][1]["rows"] = [["50", "30", "19.99"]]
    assert not validate(state).errors
    state["options"]["percent"] = False
    assert validate(state).errors


def test_clipboard_growth_undo_and_atomic_rejection(qtbot):
    stack = QUndoStack()
    model = CompositionModel(blank_dataset("curve"), ["A", "B", "C"], stack)
    table = CompositionTable(model)
    qtbot.addWidget(table)
    data = "\n".join(["0.2\t0.3\t0.5"] * 15)
    table.paste(data)
    assert len(model.rows) == 16
    assert model.rows[14] == ["0.2", "0.3", "0.5"]
    stack.undo()
    assert len(model.rows) == 10
    stack.redo()
    before = deepcopy(model.rows)
    with qtbot.waitSignal(table.problem):
        table.paste("1\t2\t3\t4")
    assert model.rows == before
    model.setData(model.index(15, 0), "0.1")
    assert len(model.rows) == 17


def test_cache_recovers_invalid_text_and_quarantines_damage(tmp_path):
    path = tmp_path / "session.json"
    state = defaults()
    state["datasets"][0]["rows"][0][0] = "unfinished -"
    save(path, state)
    assert load(path) == (state, "")
    path.write_text('{"version": 999}')
    recovered, warning = load(path)
    assert recovered == defaults() and warning
    assert list(tmp_path.glob("session-damaged-*.json"))
    assert not path.exists()


def test_render_order_orientation_and_export(tmp_path):
    state = example()
    figure = render(state, validate(state).datasets)
    axis = figure.axes[0]
    assert len(axis.lines) == 2
    # Matplotlib sees the exact user order, permuted A/B/C -> B/C/A.
    assert list(axis.lines[1].get_ydata()) == pytest.approx([0.1, 0.2])
    assert axis.lines[1].get_xdata()[0] > axis.lines[1].get_xdata()[1]
    assert [text.get_text() for text in axis.texts] == ["A", "B", "C"]
    for fmt in ("png", "svg", "pdf"):
        path = tmp_path / f"chart.{fmt}"
        figure.savefig(path, dpi=150, format=fmt)
        assert path.stat().st_size > 1000
    from PIL import Image

    with Image.open(tmp_path / "chart.png") as image:
        assert image.size == (1062, 944)


def test_window_generate_validation_recovery_dataset_undo(qtbot, tmp_path):
    path = tmp_path / "session.json"
    save(path, example())
    window = MainWindow(path)
    qtbot.addWidget(window)
    window.show()
    window.generate()
    assert window.export_button.isEnabled()
    assert window.plot_window.figure is not None
    window.cards[0].model.setData(window.cards[0].model.index(0, 0), "bad")
    assert "Inputs changed" in window.preview_status.text()
    window.generate()
    assert "invalid cells" in window.banner.text()
    window.undo_stack.undo()
    assert window.cards[0].model.rows[0][0] == "0.8"
    card = window.cards[0]
    window.remove_dataset(card)
    assert len(window.cards) == 1
    window.undo_stack.undo()
    assert window.cards[0] is card
    window.add_dataset("curve")
    assert len(window.cards) == 3
    window.undo_stack.undo()
    assert len(window.cards) == 2
    window.persist()
    assert json.loads(path.read_text())["datasets"] == window.snapshot()["datasets"]
    window.close()


def test_independent_tick_toggles_and_hidden_sets():
    state = example()
    state["options"].update(ticks=False, numbers=True, grid=False)
    state["datasets"][0].update(marker="None", line="None")
    figure = render(state, validate(state).datasets)
    from matplotlib.backends.backend_agg import FigureCanvasAgg

    FigureCanvasAgg(figure).draw()
    axis = figure.axes[0]
    assert len(axis.lines) == 1
    assert axis.taxis.get_major_ticks()[0].tick1line.get_markersize() == 0
    assert axis.taxis.get_major_ticks()[0].label1.get_visible()
    assert not any(line.get_visible() for line in axis.taxis.get_gridlines())


def test_footer_export_keeps_fixed_dimensions_after_preview_resize(qtbot, tmp_path, monkeypatch):
    from PIL import Image
    from PySide6.QtWidgets import QFileDialog

    path = tmp_path / "session.json"
    save(path, example())
    window = MainWindow(path)
    qtbot.addWidget(window)
    window.show()
    window.generate()
    window.plot_window.resize(1100, 600)
    qtbot.wait(30)
    figure = window.plot_window.figure
    before = figure.get_size_inches().copy()
    window.dpi.setCurrentText("150")
    output = tmp_path / "resized.png"
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *a, **kw: (str(output), ""))
    window.export()
    with Image.open(output) as image:
        assert image.size == (1062, 944)
    assert figure.get_size_inches() == pytest.approx(before)
    window.format.setCurrentText("PDF")
    assert not window.dpi.isEnabled()
    window.close()


def test_warning_and_reset_session(qtbot, tmp_path, monkeypatch):
    from PySide6.QtWidgets import QMessageBox

    window = MainWindow(tmp_path / "session.json")
    qtbot.addWidget(window)
    window.show()
    window.cards[1].table.paste("0.1\t0.2\t0.7")
    window.generate()
    assert "one-point curve" in window.banner.text()
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **kw: QMessageBox.StandardButton.Yes)
    window.reset_session()
    assert len(window.cards) == 2
    assert not window.export_button.isEnabled()
    assert not window.undo_stack.canUndo()
    window.generate()
    assert window.export_button.isEnabled()
    assert not window.banner.isVisible()
    window.close()


def test_keyboard_edit_tab_preserves_spreadsheet_navigation(qtbot):
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QLineEdit

    stack = QUndoStack()
    model = CompositionModel(blank_dataset("curve"), ["A", "B", "C"], stack)
    table = CompositionTable(model)
    qtbot.addWidget(table)
    table.show()
    table.setCurrentIndex(model.index(0, 0))
    table.edit(model.index(0, 0))
    editor = table.findChild(QLineEdit)
    assert isinstance(editor, QLineEdit)
    qtbot.keyClicks(editor, "0.2")
    qtbot.keyClick(editor, Qt.Key.Key_Tab)
    assert model.rows[0][0] == "0.2"
    assert table.currentIndex().column() == 1
