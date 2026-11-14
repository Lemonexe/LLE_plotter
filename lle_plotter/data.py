"""Composition validation, independent of Qt and plotting."""

import base64
import math
import re
from dataclasses import dataclass

COLORS = {
    "Blue": "#0072b2",
    "Orange": "#d55e00",
    "Green": "#009e73",
    "Purple": "#cc79a7",
    "Gold": "#b38b00",
    "Black": "#222222",
}
MARKERS = {
    "None": "",
    "Circle": "o",
    "Square": "s",
    "Triangle": "^",
    "Diamond": "D",
    "Plus": "+",
    "Cross": "x",
}
LINES = {"None": "", "Solid": "-", "Dashed": "--", "Dotted": ":", "Dash-dot": "-."}
NUMBER = re.compile(r"^[+-]?(?:\d+(?:[.,]\d*)?|[.,]\d+)(?:[eE][+-]?\d+)?$")


def number(text):
    text = text.strip()
    if not NUMBER.fullmatch(text):
        raise ValueError("Enter a number without thousands separators or a % sign")
    value = float(text.replace(",", "."))
    if not math.isfinite(value):
        raise ValueError("Enter a finite number")
    return value


def blank_dataset(kind, index=0):
    return {
        "kind": kind,
        "label": f"{'Tie lines' if kind == 'tie' else 'Curve'} {index + 1}",
        "color": list(COLORS)[index % len(COLORS)],
        "marker": "Circle" if kind == "tie" else "None",
        "line": "Solid",
        "rows": [[""] * (6 if kind == "tie" else 3) for _ in range(10)],
    }


def defaults():
    return {
        "version": 1,
        "names": ["A", "B", "C"],
        "title": "",
        "options": {
            "percent": False,
            "color": True,
            "ticks": True,
            "numbers": True,
            "grid": True,
            "legend": True,
        },
        "datasets": [blank_dataset("tie"), blank_dataset("curve")],
        "format": "PNG",
        "dpi": "300",
    }


@dataclass
class Validation:
    datasets: list
    errors: list  # (dataset index, row index, column index, message)
    warnings: list


def validate(state):
    total = 100.0 if state["options"]["percent"] else 1.0
    tolerance = total * 0.0001
    errors, warnings, datasets = [], [], []
    for di, dataset in enumerate(state["datasets"]):
        parsed = []
        for ri, row in enumerate(dataset["rows"]):
            if not any(cell.strip() for cell in row):
                continue
            values = []
            for ci, cell in enumerate(row):
                try:
                    value = number(cell)
                    if not 0 <= value <= total:
                        raise ValueError(f"Value must be between 0 and {total:g}")
                    values.append(value)
                except ValueError as exc:
                    errors.append((di, ri, ci, str(exc)))
            if len(values) != len(row):
                continue
            normalized = []
            for start in range(0, len(row), 3):
                composition = values[start : start + 3]
                actual = sum(composition)
                if actual == 0 or abs(actual - total) > tolerance + total * 1e-12:
                    message = f"Composition totals {actual:g}; expected {total:g} ± {tolerance:g}"
                    errors.extend((di, ri, ci, message) for ci in range(start, start + 3))
                else:
                    normalized.extend(value * total / actual for value in composition)
            if len(normalized) == len(row):
                parsed.append(normalized)
        datasets.append({**dataset, "values": parsed})
        if (
            dataset["kind"] == "curve"
            and len(parsed) == 1
            and dataset["marker"] == "None"
            and dataset["line"] != "None"
        ):
            warnings.append(f"{dataset['label']}: a one-point curve without a marker is invisible.")
    return Validation(datasets, errors, warnings)


def check_state(state):
    """Reject malformed cache structures before constructing any widgets."""
    if not isinstance(state, dict) or state.get("version") != 1:
        raise ValueError("Unsupported session format")
    if len(state["names"]) != 3 or not all(isinstance(n, str) for n in state["names"]):
        raise ValueError("Invalid component names")
    if not isinstance(state["title"], str):
        raise ValueError("Invalid title")
    for key in defaults()["options"]:
        if not isinstance(state["options"][key], bool):
            raise ValueError("Invalid option")
    if state["format"] not in ("PNG", "SVG", "PDF") or state["dpi"] not in (
        "150",
        "300",
        "600",
        "1200",
    ):
        raise ValueError("Invalid export options")
    if not isinstance(state["datasets"], list):
        raise ValueError("Invalid datasets")
    for dataset in state["datasets"]:
        if dataset["kind"] not in ("tie", "curve") or not isinstance(dataset["label"], str):
            raise ValueError("Invalid dataset")
        for key, choices in (("color", COLORS), ("marker", MARKERS), ("line", LINES)):
            if dataset[key] not in choices:
                raise ValueError("Invalid style")
        columns = 6 if dataset["kind"] == "tie" else 3
        if not isinstance(dataset["rows"], list):
            raise ValueError("Invalid rows")
        for row in dataset["rows"]:
            if (
                not isinstance(row, list)
                or len(row) != columns
                or not all(isinstance(c, str) for c in row)
            ):
                raise ValueError("Invalid cells")
    if "geometry" in state:
        if not isinstance(state["geometry"], str):
            raise ValueError("Invalid window geometry")
        base64.b64decode(state["geometry"], validate=True)
    return state
