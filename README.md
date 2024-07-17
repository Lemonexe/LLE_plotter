# LLE_plotter
Utility program to create LLE ternary plots from tabular data

## Setup
```
pip install --user pipenv
pipenv install --dev
```

## Local run
```
pipenv run prettier
pipenv run plot_LLE --help
```

## Build exe
```
pipenv shell
pyinstaller --onefile --name LLE_plotter plot_LLE.py
exit
```
