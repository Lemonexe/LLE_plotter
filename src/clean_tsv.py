def clean_row(raw_row):
    row = [cell.strip() for cell in raw_row if len(cell.strip()) > 0]
    try:
        return [float(cell) for cell in row]
    except ValueError:
        return row


def clean_tsv(raw_table):
    """
    Open a path with .tsv file and return it as list of lists, while filtering out empty rows.

    raw_table (list of lists of strings)
    return (list of lists)
    """
    return [clean_row(raw_row) for raw_row in raw_table]
