import numpy as np
from .config import max_datasets

is_numerical = lambda np_arr: np.issubdtype(np.array(np_arr).dtype, np.number)


def parse_LLE(table):
    eq_curves = [[]]
    tie_line_sets = [[]]
    compound_names = None

    for row in table:
        curr_eq_curve = eq_curves[-1]
        curr_tie_line = tie_line_sets[-1]

        # empty row will end current dataset & start an empty one; multiple empty rows are considered as one
        if len(row) == 0:
            if len(curr_eq_curve) > 0: eq_curves.append([])
            if len(curr_tie_line) > 0: tie_line_sets.append([])
            continue

        np_row = np.array(row)
        if is_numerical(np_row):
            if len(np_row) == 3: curr_eq_curve.append(np_row)
            elif len(np_row) == 6: curr_tie_line.append(np_row)
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

    # can't make a np matrix, because the row length is not homogeneous. Also, remove empty datasets
    eq_curves = [np.array(ec) for ec in eq_curves if len(ec) > 0]
    tie_line_sets = [np.array(tl) for tl in tie_line_sets if len(tl) > 0]

    n_datasets = max(len(eq_curves), len(tie_line_sets))
    if n_datasets > max_datasets: raise ValueError(f'Too many datasets, maximum is {max_datasets}, got {n_datasets}')

    return eq_curves, tie_line_sets, compound_names
