"""Spreadsheet-like fixed-column tables with atomic, undoable edits."""

from copy import deepcopy

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, Signal
from PySide6.QtGui import QColor, QKeySequence, QUndoCommand
from PySide6.QtWidgets import QAbstractItemView, QApplication, QHeaderView, QTableView


class RowsCommand(QUndoCommand):
    def __init__(self, model, rows, title):
        super().__init__(title)
        self.model, self.before, self.after = model, deepcopy(model.rows), rows

    def apply(self, rows):
        previous, current = len(self.model.rows), len(rows)
        if current > previous:
            self.model.beginInsertRows(QModelIndex(), previous, current - 1)
        elif current < previous:
            self.model.beginRemoveRows(QModelIndex(), current, previous - 1)
        self.model.rows = deepcopy(rows)
        self.model.errors = {}
        if current > previous:
            self.model.endInsertRows()
        elif current < previous:
            self.model.endRemoveRows()
        self.model.dataChanged.emit(
            self.model.index(0, 0), self.model.index(current - 1, self.model.columns - 1)
        )
        self.model.edited.emit()

    def redo(self):
        self.apply(self.after)

    def undo(self):
        self.apply(self.before)


class CompositionModel(QAbstractTableModel):
    edited = Signal()

    def __init__(self, dataset, names, stack, parent=None):
        super().__init__(parent)
        self.columns = 6 if dataset["kind"] == "tie" else 3
        self.rows = deepcopy(dataset["rows"]) or [[""] * self.columns for _ in range(10)]
        if any(self.rows[-1]):
            self.rows.append([""] * self.columns)
        self.names, self.stack, self.errors = names, stack, {}

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.rows)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else self.columns

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            return self.rows[index.row()][index.column()]
        if role == Qt.ItemDataRole.BackgroundRole and (index.row(), index.column()) in self.errors:
            return QColor("#ffd9d9")
        if role == Qt.ItemDataRole.ToolTipRole:
            return self.errors.get((index.row(), index.column()))
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Vertical:
                return str(section + 1)
            suffix = f" · endpoint {section // 3 + 1}" if self.columns == 6 else ""
            return f"{self.names[section % 3]}{suffix}"
        if role == Qt.ItemDataRole.ToolTipRole and orientation == Qt.Orientation.Horizontal:
            return "Composition of this component. Enter all three components for each endpoint."
        return None

    def flags(self, index):
        return super().flags(index) | Qt.ItemFlag.ItemIsEditable

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if role != Qt.ItemDataRole.EditRole or not index.isValid():
            return False
        rows = deepcopy(self.rows)
        rows[index.row()][index.column()] = str(value)
        self.commit(rows, "Edit cell")
        return True

    def commit(self, rows, title):
        if not rows:
            rows = [[""] * self.columns]
        if any(rows[-1]):
            rows.append([""] * self.columns)
        if rows != self.rows:
            self.stack.push(RowsCommand(self, rows, title))

    def mark_errors(self, errors):
        self.errors = errors
        self.dataChanged.emit(self.index(0, 0), self.index(len(self.rows) - 1, self.columns - 1))


class CompositionTable(QTableView):
    problem = Signal(str)

    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.setModel(model)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.horizontalHeader().setDefaultSectionSize(145)
        self.verticalHeader().setDefaultSectionSize(28)
        self.setMinimumHeight(200)
        self.setMaximumHeight(340)
        self.setAlternatingRowColors(True)
        self.setWordWrap(False)

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.StandardKey.Paste):
            self.paste(QApplication.clipboard().text())
        elif event.matches(QKeySequence.StandardKey.Copy):
            indexes = self.selectedIndexes()
            if indexes:
                selected = {(i.row(), i.column()) for i in indexes}
                rows = range(min(i.row() for i in indexes), max(i.row() for i in indexes) + 1)
                cols = range(min(i.column() for i in indexes), max(i.column() for i in indexes) + 1)
                QApplication.clipboard().setText(
                    "\n".join(
                        "\t".join(
                            self.model().rows[r][c] if (r, c) in selected else "" for c in cols
                        )
                        for r in rows
                    )
                )
        elif event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            rows = deepcopy(self.model().rows)
            for index in self.selectedIndexes():
                rows[index.row()][index.column()] = ""
            self.model().commit(rows, "Clear cells")
        else:
            super().keyPressEvent(event)

    def paste(self, text):
        if not text:
            return
        matrix = [
            line.split("\t")
            for line in text.replace("\r\n", "\n").replace("\r", "\n").rstrip("\n").split("\n")
        ]
        index = self.currentIndex()
        row, column = (index.row(), index.column()) if index.isValid() else (0, 0)
        model = self.model()
        if any(column + len(cells) > model.columns for cells in matrix):
            self.problem.emit(
                f"Paste rejected: this table has exactly {model.columns} columns. Select the first destination cell."
            )
            return
        rows = deepcopy(model.rows)
        while len(rows) < row + len(matrix):
            rows.append([""] * model.columns)
        for offset, cells in enumerate(matrix):
            rows[row + offset][column : column + len(cells)] = cells
        model.commit(rows, "Paste cells")

    def add_rows(self):
        model = self.model()
        model.commit(deepcopy(model.rows) + [[""] * model.columns for _ in range(10)], "Add rows")

    def remove_rows(self):
        selected = {index.row() for index in self.selectedIndexes()}
        if selected:
            self.model().commit(
                [deepcopy(row) for i, row in enumerate(self.model().rows) if i not in selected],
                "Remove rows",
            )
