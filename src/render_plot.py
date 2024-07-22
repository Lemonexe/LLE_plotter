import ternary
from matplotlib import pyplot as plt
# not explicitly used, pipenv runs fine without it, but it's needed so that svg export works in the executable
import matplotlib.backends.backend_svg
from .config import plot_colors


def render_tie_line_set(tax, tie_line_set, color, label):
    for i, line in enumerate(tie_line_set):
        curr_label = label if i == 0 else None
        p1 = line[:3]
        p2 = line[3:]
        tax.line(p1, p2, color=color, linewidth=0.5, marker='o', markersize=4, linestyle='-', label=curr_label)


def render_plot(eq_curves, tie_line_sets, compound_names, do_grid, do_ticks, do_legend, is_percentage):
    scale = 100 if is_percentage else 1
    figure, tax = ternary.figure(scale=scale)

    tax.set_background_color('white')

    tax.boundary(linewidth=1.0)
    if do_grid:
        grid_multiple = 10 if is_percentage else 0.1
        tax.gridlines(color="gray", multiple=grid_multiple)

    tax.top_corner_label(compound_names[0], fontsize=11, offset=0.22)
    tax.left_corner_label(compound_names[1], fontsize=11, offset=0.22)
    tax.right_corner_label(compound_names[2], fontsize=11)

    for i, eq_curve in enumerate(eq_curves):
        tax.plot(eq_curve, color=plot_colors[i], linewidth=1.0, linestyle='--', label=f'Curve {i+1}')

    for i, tie_line_set in enumerate(tie_line_sets):
        render_tie_line_set(tax, tie_line_set, color=plot_colors[i], label=f'Tie lines {i+1}')

    if do_ticks:
        tick_multiple = 20 if is_percentage else 0.2
        tick_formats = '%.0f%%' if is_percentage else '%.1f'
        tax.ticks(axis='lbr', multiple=tick_multiple, linewidth=1, offset=0.025, tick_formats=tick_formats)

    if do_legend: tax.legend()

    # removes rectangular axis & ticks from matplotlib
    tax.get_axes().axis('off')
    tax.clear_matplotlib_ticks()

    # normally this is a hack to ensure square aspect ratio, see https://stackoverflow.com/a/57249253/19120862
    # but in case of ternary diagram, the aspect ratio was empirically observed to produce an equilateral triangle
    ax = plt.gca()
    chart_aspect_ratio = 1.1
    x_left, x_right = ax.get_xlim()
    y_bottom, y_top = ax.get_ylim()
    ax.set_aspect(abs((x_right-x_left) / (y_bottom-y_top)) / chart_aspect_ratio)

    tax.show()
