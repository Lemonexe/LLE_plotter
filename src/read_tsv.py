import csv


def read_tsv(file_path):
    """
    Open a path with .tsv file and return it as list of lists, while filtering out empty rows.

    file_path (str): exact path to tsv file
    return (list of lists): tsv file content as list of rows, each row is a list of cells for each column
    """
    with open(file_path, encoding='utf-8') as tsv_file:
        reader = csv.reader(tsv_file, delimiter='\t')
        return list(reader)
