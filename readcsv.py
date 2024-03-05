import time
import pandas as pd

#This function reads all the columns from the csv and returns as individual list
def readFromCSV(csv_file_path, log_file):

    appID, phoneNumber, appName, phoneId, wabaId = [], [], [], [], []

    try:
        df = pd.read_csv(csv_file_path)
        for index, row in df.iterrows():
            appID.append(row["AppID"])
            phoneNumber.append(row["PhoneNumber"])
            appName.append(row["AppName"])
            phoneId.append(row["WabaId"])
            wabaId.append(row["PhoneId"])

        return appID, phoneNumber, appName, phoneId, wabaId

    except IOError as e:
        print(f'IOError for readFromCSV function | {csv_file_path}')
        log_file.write(f'{time.strftime("%Y-%m-%d %H:%M:%S")} | error while opening csv at ({csv_file_path}) |  {str(e)} \n')