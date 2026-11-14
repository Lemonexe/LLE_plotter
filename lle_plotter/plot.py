"""Render validated compositions using mpltern's top/left/right convention."""

import mpltern  # noqa: F401 -- registers the ternary projection
from matplotlib.figure import Figure
from matplotlib.ticker import FixedLocator, FuncFormatter

from .data import COLORS, LINES, MARKERS


def render(state, datasets):
    figure = Figure(figsize=(180 / 25.4, 160 / 25.4), dpi=100)
    ax = figure.add_subplot(
        projection="ternary", ternary_sum=100 if state["options"]["percent"] else 1
    )
    figure.subplots_adjust(left=0.13, right=0.87, bottom=0.15, top=0.84)
    options = state["options"]
    total = 100 if options["percent"] else 1
    # Corner labels avoid ambiguity between component axes and triangle vertices.
    a, b, c = state["names"]
    for x, y, text, align in (
        (1, -0.07, a, "right"),
        (0.5, 1.06, b, "center"),
        (0, -0.07, c, "left"),
    ):
        ax.text(x, y, text, transform=ax.transAxes, ha=align, va="center", fontweight="bold")
    for axis in (ax.taxis, ax.laxis, ax.raxis):
        axis.set_major_locator(FixedLocator([total * i / 5 for i in range(6)]))
        axis.set_major_formatter(
            FuncFormatter(lambda value, pos: f"{value:g}%" if options["percent"] else f"{value:g}")
        )
        axis.set_tick_params(
            length=3.5 if options["ticks"] else 0, label1On=options["numbers"], label2On=False
        )
    if options["grid"]:
        ax.grid(True, color="#b8b8b8", linewidth=0.5)
    else:
        ax.grid(False)
    for dataset in datasets:
        rows = dataset["values"]
        if not rows or (dataset["marker"] == "None" and dataset["line"] == "None"):
            continue
        style = {
            "color": COLORS[dataset["color"]] if options["color"] else "black",
            "marker": MARKERS[dataset["marker"]],
            "linestyle": LINES[dataset["line"]] or "None",
            "linewidth": 1,
            "markersize": 4,
        }
        if dataset["kind"] == "curve":
            aa, bb, cc = zip(*rows)
            ax.plot(bb, cc, aa, label=dataset["label"], **style)
        else:
            for i, row in enumerate(rows):
                a1, b1, c1, a2, b2, c2 = row
                ax.plot(
                    [b1, b2],
                    [c1, c2],
                    [a1, a2],
                    label=dataset["label"] if i == 0 else "_nolegend_",
                    **style,
                )
    if options["legend"] and ax.get_legend_handles_labels()[0]:
        ax.legend(loc="upper right", fontsize=8)
    figure.suptitle(state["title"], y=0.98, wrap=True)
    return figure


def export_figure(figure, path, **kwargs):
    """Qt resizes the live figure; exports always use the agreed physical size."""
    original_size = figure.get_size_inches().copy()
    try:
        figure.set_size_inches(180 / 25.4, 160 / 25.4, forward=False)
        figure.savefig(path, **kwargs)
    finally:
        figure.set_size_inches(original_size, forward=False)
        if figure.canvas is not None:
            figure.canvas.draw_idle()
