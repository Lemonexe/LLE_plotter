import ternary


def render_plot(eq_curve, tie_lines, compound_names, do_grid, do_ticks, is_percentage):
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

    tax.plot(eq_curve, color='black', linewidth=1.0, linestyle=':', label='curve')

    for i, line in enumerate(tie_lines):
        p1 = line[:3]
        p2 = line[3:]
        tax.line(p1, p2, color='black', linewidth=0.5, marker='o', markersize=4, linestyle='-', label=f'Line {i}')

    if do_ticks:
        tick_multiple = 20 if is_percentage else 0.2
        tick_formats = '%.0f%%' if is_percentage else '%.1f'
        tax.ticks(axis='lbr', multiple=tick_multiple, linewidth=1, offset=0.025, tick_formats=tick_formats)

    # removes rectangular axis & ticks from matplotlib
    tax.get_axes().axis('off')
    tax.clear_matplotlib_ticks()
    tax.show()
