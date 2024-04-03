import time
import requests
import json
import os
import pandas as pd

def get_ldap_token(username, password, log_file):
    login_url = "https://whatsapp-internal-support.gupshup.io/support/auth/login"
    # login_url = "http://10.80.14.84:8081/support/auth/login"
    login_payload = { "username": username, "password": password }
    login_headers = { "Content-Type": "application/x-www-form-urlencoded" }
    try:
        login_response = requests.post(login_url, headers=login_headers, data=login_payload, timeout=30)
        login_response.raise_for_status()
        print(f'login success for {username}\n')
        log_file.write(f'\n{time.strftime("%Y-%m-%d %H:%M:%S")} | login success for {username}\n')
        return login_response.json()["message"]["token"]
    
    except requests.exceptions.HTTPError as err:
        error_msg = f"error at support login | {err.response.status_code} | {username}  | {err.response.json()['message']}"
        print(f"{error_msg}\n")
        log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} | error at support login ({err.response.status_code}) | {username} | {err.response.json()['message']}\n")
        raise
    except requests.exceptions.RequestException as e:
        print(f"error at support login: ", e)
        log_file.write(f'{time.strftime("%Y-%m-%d %H:%M:%S")} | request exception at support login {str(e)}\n')

def log_message(message, log_file_path):
    with open(log_file_path, "a") as log_file:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_file.write(f"{timestamp} | {message}\n")

    loggerUrl = f"http://10.55.4.254:12346/logger"
    loggerheaders = {"Content-Type": "application/json"}
    loggerPayload = json.dumps({"data": f"{message}"})
    try:
        loggerResponse = requests.post(loggerUrl, headers=loggerheaders, data=loggerPayload, timeout=60)
        loggerResponse.raise_for_status()
    except requests.exceptions.Timeout as err:
        print(f"logger api failing, please check your vpn connection | {err}")
    except requests.exceptions.HTTPError as err:
        print(f"logger api failing, please check your vpn connection | {err}")
    except ConnectionRefusedError:
        print(f"logger api failing, please check your vpn connection | {err}")

def log_csv(message):
    csvUrl = f"http://10.55.4.254:12346/write/csv"
    csvheaders = {"Content-Type": "application/json"}
    try:
        csvResponse = requests.post(csvUrl, headers=csvheaders, data=message, timeout=60)
        csvResponse.raise_for_status()
    except requests.exceptions.Timeout as err:
        print(f"logger api failing, please check your vpn connection | {err}")
    except requests.exceptions.HTTPError as err:
        print(f"logger api failing, please check your vpn connection | {err}")
    except ConnectionRefusedError:
        print(f"logger api failing, please check your vpn connection | {err}")


def parse_env_file(file_path):
    env_vars = {}
    with open(file_path, "r") as file:
        for line in file:
            if "=" in line:
                key, value = line.strip().split("=", 1)
                env_vars[key] = value
    return env_vars


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


def write_to_csv(data, csv_file_path, log_file):
    """Write data to csv file as new rows"""
    fields = ["AppID", "AppName", "PhoneNumber", "WabaId", "PhoneId", "Status_code", "Response"]
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