# LLE_plotter

Utility program to create LLE ternary plots from tabular data.  
It is mainly distributed as a portable Windows executable, but you may also run the source code locally, then refer to [this document](./CONTRIBUTING.md).

The program can be run intuitively by drag & dropping your file on it in Explorer.

The data is expected to be a tab-separated values file in a certain format:
- In Microsfot Excel, you must save your worksheet as `Text (Tab delimited) (\*.txt)` (language may differ)
  - File extension does not matter.
  - But `.xls` or `.xlsx` is **not** supported.
- The first row may or may not contain the headers – exactly 3 compound names (otherwise A,B,C).
- Equilibrium curves & sets of tie lines should be in groups, separated by any number of empty rows.
  - A row with 3 values is considered an equilibrium curve point.
  - A row with 6 values is considered a tie line.
  - Both eq. curves & tie line sets will be labeled by their order.
    - _Eq. curves & tie lines are numbered independently, i.e. the counts don't need to match._
  - It is possible to provide only eq. curve(s), or only tie line(s).
- [Simple .tsv example](dev/water-acetone-toluene.tsv?plain=1)
- [Example .tsv with multiple datasets](dev/water-acetone-toluene-2.tsv?plain=1)
- [Example .tsv with only eq. curve](dev/water-ethanol-NaCl.tsv?plain=1)
- [Example .svg output](./example.svg)

### Running in terminal

You may run `LLE_plotter.exe` in cmd or powershell, with only the file path as argument, and will interactively prompt you for additional options.

Alternatively, you may specify the arguments _(helpful for many files)_:
```
.\LLE_plotter.exe --help
.\LLE_plotter.exe dev\water-acetone-toluene.tsv
.\LLE_plotter.exe dev\water-acetone-toluene-2.tsv --silent --grayscale --legend
.\LLE_plotter.exe dev\water-ethanol-NaCl.tsv --silent --ticks --numbers --percent
```

## References

Example data was sourced from:

- water-acetone-toluene: [Aspen Plus V14.5](https://www.aspentech.com/en/products/engineering/aspen-plus)
- water-ethanol-NaCl: [A. Marcilla et. al. 1995](https://doi.org/10.1016/0378-3812(94)02595-R)
