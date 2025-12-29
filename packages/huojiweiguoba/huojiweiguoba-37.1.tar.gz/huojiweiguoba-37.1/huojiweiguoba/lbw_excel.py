import pandas
import openpyxl

def pands_read_excel(file_path):
    '''读取excel'''
    df = pandas.read_excel(file_path).to_dict(orient='records')
    return df

def pandas_write_excel_xlsx(file_path, data):
    '''写入excel'''
    df = pandas.DataFrame(data)
    df.to_excel(file_path, index=False)