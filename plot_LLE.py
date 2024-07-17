import click
from src.read_tsv import read_tsv


@click.command()
@click.argument('file_name')
def cli_plot_LLE(file_name):
    """Plot LLE ternary plot for a given tsv file."""
    read_tsv(file_name)


if __name__ == '__main__':
    cli_plot_LLE()
