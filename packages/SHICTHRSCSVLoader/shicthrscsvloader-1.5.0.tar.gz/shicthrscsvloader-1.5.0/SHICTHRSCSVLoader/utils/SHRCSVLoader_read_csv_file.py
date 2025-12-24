
import csv

def read_csv_file(path : str , read_encoding : str) -> dict:
    temp_dict : dict = {}
    with open(path , 'r', encoding = read_encoding , errors = 'replace') as f:
        reader = csv.reader(f)
        headers = next(reader)
        for row_num , row in enumerate(reader):
            row_dict = {}
            for i , value in enumerate(row):
                if i < len(headers):
                    row_dict[headers[i]] = value
                else:
                    row_dict[f"extra_col_{i}"] = value
            temp_dict[row_num] = row_dict
        return temp_dict