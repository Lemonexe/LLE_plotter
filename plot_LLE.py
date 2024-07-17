import click
from src.read_tsv import read_tsv
from src.clean_tsv import clean_tsv
from src.parse_LLE import parse_LLE


@click.command()
@click.argument('file_name', type=click.Path(exists=True))
def cli_plot_LLE(file_name):
    """Plot LLE ternary plot for a given tsv file."""
    try:
        table = clean_tsv(read_tsv(file_name))
        eq_curve, tie_lines, compound_names = parse_LLE(table)
        # print(eq_curve)
        # print(tie_lines)
        # print(compound_names)
    except Exception as e:
        print(f'ERROR: {e}')
        return

    # pause script execution to keep the plot open
    input("Press ENTER to end the program (closes all plots)")


if __name__ == '__main__':
    cli_plot_LLE()
