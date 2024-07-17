# LLE_plotter
Utility program to create LLE ternary plots from tabular data

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
```

Run code formatter: `pipenv run prettier`

## Build exe
```
pipenv shell
pyinstaller --onefile --name LLE_plotter plot_LLE.py
```
