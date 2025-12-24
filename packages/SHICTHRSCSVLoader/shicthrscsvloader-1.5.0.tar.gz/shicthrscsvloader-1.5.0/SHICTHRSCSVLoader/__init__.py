# *-* coding: utf-8 *-*
# src\__init__.py
# SHICTHRS CSV LOADER
# AUTHOR : SHICTHRS-JNTMTMTM
# Copyright : © 2025-2026 SHICTHRS, Std. All rights reserved.
# lICENSE : GPL-3.0

import os
from colorama import init
init()
from .utils.SHRCSVLoader_read_csv_file import read_csv_file
from .utils.SHRCSVLoader_write_csv_file import write_csv_file
from .utils.SHRCSVLoader_insert_csv_file import insert_header_to_csv

print('\033[1mWelcome to use SHRCSVLoader - CSV file io System\033[0m\n|  \033[1;34mGithub : https://github.com/JNTMTMTM/SHICTHRS_CSVLoader\033[0m')
print('|  \033[1mAlgorithms = rule ; Questioning = approval\033[0m')
print('|  \033[1mCopyright : © 2025-2026 SHICTHRS, Std. All rights reserved.\033[0m\n')

__all__ = ['SHRCSVLoader_read_csv_file' , 'SHRCSVLoader_write_csv_file' , 'SHRCSVLoader_insert_csv_file']

class SHRCSVLoaderException(Exception):
    def __init__(self , message: str) -> None:
        self.message = message
    
    def __str__(self):
        return self.message

def SHRCSVLoader_read_csv_file(path : str , read_encoding : str = 'GB2312') -> dict:
    try:
        if os.path.exists(path):
            if os.path.isfile(path) and (path.endswith('.csv') or path.endswith('.CSV')):
                return read_csv_file(path , read_encoding)
            else:
                raise SHRCSVLoaderException(f"SHRCSVLoader [ERROR.1017] only csv file is supported not .{path.split('.')[-1]}.")
        else:
            raise SHRCSVLoaderException(f"SHRCSVLoader [ERROR.1018] unable to find csv file. File Path : {path} NOT FOUND")
    except Exception as e:
        raise SHRCSVLoaderException(f"SHRCSVLoader [ERROR.1019] unable to read csv file. File Path : {path} | {e}")

def SHRCSVLoader_write_csv_file(data: dict, path: str, write_encoding: str = 'GB2312') -> bool:
    try:
        if not isinstance(data , dict):
            raise SHRCSVLoaderException("SHRCSVLoader [ERROR.1020] data must be a dictionary")
            
        if not (path.endswith('.csv') or path.endswith('.CSV')):
            raise SHRCSVLoaderException(f"SHRCSVLoader [ERROR.1021] only .csv file is supported not .{path.split('.')[-1]}.")
            
        result = write_csv_file(data, path, write_encoding)
        
        if not result:
            raise SHRCSVLoaderException(f"SHRCSVLoader [ERROR.1022] unable to write csv file. File Path : {path}")
            
    except Exception as e:
        raise SHRCSVLoaderException(f"SHRCSVLoader [ERROR.1023] unable to write csv file. File Path : {path} | {e}")

def SHRCSVLoader_insert_csv_file(path: str , header : dict , insert_encoding: str = 'GB2312') -> bool:
    try:
        if not isinstance(header , list):
            raise SHRCSVLoaderException("SHRCSVLoader [ERROR.1024] data must be a list")
            
        if not (path.endswith('.csv') or path.endswith('.CSV')):
            raise SHRCSVLoaderException(f"SHRCSVLoader [ERROR.1025] only .csv file is supported not .{path.split('.')[-1]}.")
                
        # 写入合并后的数据
        insert_header_to_csv(path , header , insert_encoding)

    except Exception as e:
        raise SHRCSVLoaderException(f"SHRCSVLoader [ERROR.1027] unable to insert data to csv file. File Path : {path} | {e}")

