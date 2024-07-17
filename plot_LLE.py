import click
from src.read_tsv import read_tsv
from src.clean_tsv import clean_tsv
from src.parse_LLE import parse_LLE
from src.render_plot import render_plot


@click.command()
@click.argument('file_name', type=click.Path(exists=True))
def cli_plot_LLE(file_name):
    """Plot LLE ternary plot for a given tsv file."""
    try:
        table = clean_tsv(read_tsv(file_name))
        eq_curve, tie_lines, compound_names = parse_LLE(table)
        do_grid = input('Display grid? (y/n): ').lower() == 'y'
        do_ticks = input('Display ticks with numbers? (y/n): ').lower() == 'y'
        is_percentage = input('Are the values in % ? (y/n): ').lower() == 'y'
        render_plot(eq_curve, tie_lines, compound_names, do_grid, do_ticks, is_percentage)

    except Exception as e:
        print(f'ERROR: {e}')


if __name__ == '__main__':
    cli_plot_LLE()
