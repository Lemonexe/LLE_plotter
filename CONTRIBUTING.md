# Contributing

Pull requests or issues are welcome :)

Instructions for local development:

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
python plot_LLE.py dev\water-acetone-toluene-2.tsv --silent --grid --legend --ticks --numbers
python plot_LLE.py dev\water-ethanol-NaCl.tsv --silent --ticks --numbers --percent
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
.\dist\LLE_plotter.exe dev\water-acetone-toluene-2.tsv --silent --grayscale --legend
.\dist\LLE_plotter.exe dev\water-ethanol-NaCl.tsv --silent --ticks --numbers --percent
```
