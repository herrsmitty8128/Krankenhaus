
from pandas import DataFrame
from datetime import timedelta
import os
import pandas as pd
import openpyxl
import numpy as np
import scipy.signal as sig

one_hour = timedelta(seconds=3600)


def list_csv_files_in(directory_path: str) -> list:
    data_dir = os.path.abspath(directory_path)
    adt_file_list = [os.path.join(data_dir, file) for file in os.listdir(data_dir) if file.endswith('.csv')]
    return adt_file_list


def add_to_multimap(multimap: dict, key, value) -> None:
    array = multimap.get(key, None)
    if array:
        array.append(value)
    else:
        multimap[key] = [value]


def insert_smoothed_data(df: DataFrame, columnName: str, window_length: int, polyorder: int, index: int = 0) -> None:
    smoothed = sig.savgol_filter(df[columnName], window_length, polyorder)
    df.insert(index, columnName + ' - Smoothed', smoothed, True)


def create_xlsx_with_tables(file_name: str, descriptors: list) -> None:
    '''
    Creates a new xlsx file with multiple tables in separate sheets, each built from a different pandas DataFrame.

    file_name:  The path to the new xlsx file.
                The file will be over-written if it already exists

    descriptor: A list of dicts describing each table.
                For example: [{'sheet_name': 'sheetname1',
                               'data_frame': df,
                               'display_name': 'displayname1'
                               },
                              {'sheet_name': 'sheetname2',
                               'data_frame': df2,
                               'display_name': 'displayname2'
                               }]
    '''

    file_name = os.path.abspath(file_name)

    with pd.ExcelWriter(file_name) as writer:
        for desc in descriptors:
            df = desc['data_frame']
            if not df.index.name:
                df.index.name = 'Id'
            df.to_excel(writer, sheet_name=desc['sheet_name'])

    wb = openpyxl.load_workbook(filename=file_name)

    for desc in descriptors:
        df = desc['data_frame']
        xlscols = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
                   'AA', 'AB', 'AC', 'AD', 'AE', 'AF', 'AG', 'AH', 'AI', 'AJ', 'AK', 'AL', 'AM', 'AN', 'AO', 'AP', 'AQ', 'AR', 'AS', 'AT', 'AU', 'AV', 'AW', 'AX', 'AY', 'AZ',
                   'BA', 'BB', 'BC', 'BD', 'BE', 'BF', 'BG', 'BH', 'BI', 'BJ', 'BK', 'BL', 'BM', 'BN', 'BO', 'BP', 'BQ', 'BR', 'BS', 'BT', 'BU', 'BV', 'BW', 'BX', 'BY', 'BZ']
        rows = df.shape[0] + 1
        cols = xlscols[df.shape[1]]
        refs = f'A1:{cols}{rows}'
        tab = openpyxl.worksheet.table.Table(displayName=desc['display_name'], ref=refs)
        wb[desc['sheet_name']].add_table(tab)

    wb.save(file_name)
