
import pandas as pd

def insert_header_to_csv(file_path : str , header_row : list , insert_encoding):
    df = pd.read_csv(file_path , encoding = insert_encoding)
    df.columns = header_row
    df.to_csv(file_path , index=False)