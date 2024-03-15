import time
import pandas as pd
import os

#This function reads all the columns from the csv and returns as individual list
def read_from_csv(csv_file_path, log_file):
    """Read csv file and return columns as lists"""
    try:
        df = pd.read_csv(csv_file_path)
        if df.empty:
            print(f'Empty csv for read_from_csv function | {csv_file_path}\n')
            log_file.write(f'{time.strftime("%Y-%m-%d %H:%M:%S")} | csv does not have any data | ({csv_file_path}) \n')
            return []
        else:
            return df.values.tolist()
    except IOError as e:
        print(f'IOError for read_from_csv function | {csv_file_path}')
        log_file.write(f'{time.strftime("%Y-%m-%d %H:%M:%S")} | error while opening csv at ({csv_file_path}) |  {str(e)} \n')



#This function writes data to csv
def write_to_csv(data, csv_file_path, log_file):
    
    """Write data to csv file as new rows"""

    fields = ["AppID", "PhoneNumber", "AppName", "WabaId", "PhoneId", "status_code", "Response"]
    
    try:
        if not os.path.isfile(csv_file_path):
            df = pd.DataFrame([data])
            df.to_csv(csv_file_path, header=fields, index=False)
        else:
            df = pd.DataFrame([data])
            df.to_csv(csv_file_path, mode='a', header=False, index=False)
    
    except IOError as e:
        print(f'IOError for write_to_csv function | {csv_file_path}')
        log_file.write(f'{time.strftime("%Y-%m-%d %H:%M:%S")} | error while writing data to csv at ({csv_file_path}) |  {str(e)} \n')