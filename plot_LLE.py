import click
from src.read_tsv import read_tsv
from src.clean_tsv import clean_tsv
from src.parse_LLE import parse_LLE
from src.render_plot import render_plot
from src.set_process_priority import set_process_priority


@click.command()
@click.argument('file_name', type=click.Path(exists=True))
@click.option('--silent', is_flag=True, help='Will only use process arguments and not prompt user for input.')
@click.option('--grid', is_flag=True, help='Display grid.')
@click.option('--ticks', is_flag=True, help='Display axis ticks with numbers.')
@click.option('--legend', is_flag=True, help='Display data legend.')
@click.option('--percent', is_flag=True, help='Values will be considered as %.')
def cli_plot_LLE(file_name, silent, grid, ticks, legend, percent):
    """Plot LLE ternary plot for a given tsv file."""
    try:
        table = clean_tsv(read_tsv(file_name))
        eq_curves, tie_line_sets, compound_names = parse_LLE(table)
        do_grid = grid if silent else input('Display grid? (y/n): ').lower() == 'y'
        do_ticks = ticks if silent else input('Display axis ticks with numbers? (y/n): ').lower() == 'y'
        do_legend = legend if silent else input('Display data legend? (y/n): ').lower() == 'y'
        is_percentage = percent if silent else input('Are the values in % ? (y/n): ').lower() == 'y'
        print('Rendering plot now...')
        print('Closing the plot will also close this window.')
        render_plot(eq_curves, tie_line_sets, compound_names, do_grid, do_ticks, do_legend, is_percentage)

    except Exception as e:
        print(f'ERROR: {e}')


if __name__ == '__main__':
    set_process_priority()
    cli_plot_LLE()
