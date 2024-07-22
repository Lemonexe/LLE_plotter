# LLE_plotter
Utility program to create LLE ternary plots from tabular data.  
It is designed to be distributed as a portable Windows executable, but you may also run the source code locally.

The data is expected to be a tab-separated values file in a certain format:
- The first row may or may not contain the headers – exactly 3 compound names (otherwise A,B,C).
- Any row with 3 values is considered an equilibrium curve point.
- Any row with 6 values is considered a tie line.
- See `dev\water-acetone-toluene.tsv` for example.
- See [example .svg output](./example.svg).

## Setup
```
pip install --user pipenv
pipenv install --dev
```

## Local run
```
pipenv shell
python plot_LLE.py --help
python plot_LLE.py dev\water-acetone-toluene.tsv
python plot_LLE.py dev\water-acetone-toluene.tsv --silent --grid --ticks
```

Run code formatter: `pipenv run prettier`

## Build exe
```
pipenv shell
pyinstaller --onefile --name LLE_plotter --icon icon.ico plot_LLE.py
```

The executable can be run intuitively by drag & dropping the `.tsv` file on it in Explorer.  
The script will run with only file path as argument, and will prompt user for additional options.

Alternatively, run via terminal to specify arguments:
```
.\dist\LLE_plotter.exe --help
.\dist\LLE_plotter.exe dev\water-acetone-toluene.tsv
.\dist\LLE_plotter.exe dev\water-acetone-toluene.tsv --silent --grid --ticks
```
