import numpy as np

is_numerical = lambda np_arr: np.issubdtype(np.array(np_arr).dtype, np.number)


def parse_LLE(table):
    eq_curve = []
    tie_lines = []
    compound_names = None

    for row in table:
        np_row = np.array(row)
        if is_numerical(np_row):
            if len(np_row) == 3: eq_curve.append(np_row)
            elif len(np_row) == 6: tie_lines.append(np_row)
            else:
                msg = f'Numerical rows must have either 3 cells (eq. curve point) or 6 cells (tie line), got {len(np_row)} columns'
                raise ValueError(msg)
        elif len(row) == 3 and compound_names is None:
            compound_names = row
        elif compound_names is None:
            msg = f'A non-numerical row must have exactly 3 cells, meaning the A,B,C compound names, got {len(np_row)} cells'
            raise ValueError(msg)
        else:
            raise ValueError(f'Only one non-numerical row (with A,B,C compound names) is permitted')

    if compound_names is None: compound_names = ['A', 'B', 'C']

    eq_curve = np.array(eq_curve)
    tie_lines = np.array(tie_lines)

    return eq_curve, tie_lines, compound_names
