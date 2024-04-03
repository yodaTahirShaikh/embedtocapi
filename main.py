import requests
import time
import json
from helper import get_ldap_token, read_from_csv, write_to_csv, parse_env_file, log_message, log_csv
from os.path import join, dirname

def get_file_paths():
    return {
        "log_file_path": join(dirname(__file__), "log.txt"),
        "env_file_path": join(dirname(__file__), ".env"),
        "data_csv_file_path": join(dirname(__file__), "Embed_To_CAPI.csv"),
        "output_file": "CAPI_Migration_result.csv",
        "mismatch_output_file": "Mismatch_Migration_result.csv"
    }

def authenticate():
    env_vars = parse_env_file(get_file_paths()["env_file_path"])
    username = env_vars.get("USERNAME")
    password = env_vars.get("PASSWORD")
    return get_ldap_token(username, password, open(get_file_paths()["log_file_path"], "a"))

env_vars = parse_env_file(get_file_paths()["env_file_path"])
username = env_vars.get("USERNAME")

LDAP =  authenticate()

def process_migration_data():
    try:
        pnSet = set()
        
        csvData = read_from_csv(get_file_paths()["data_csv_file_path"], open(get_file_paths()["log_file_path"], "a"))
        (appID, appName, phoneNumber, wabaId, phoneId) = zip(*csvData)
        for i in range(0, len(phoneNumber)):
            if phoneNumber[i] in pnSet:
                print(f"duplicate phone number or already processed ({phoneNumber[i]}) | ({appName[i]})\n")
                log_message(f'{time.strftime("%Y-%m-%d %H:%M:%S")} | {username} | duplicate phone number or already processed ({phoneNumber[i]}) | ({appName[i]})',get_file_paths()["log_file_path"])
                i += 1
                continue

            else:
                pnSet.add(phoneNumber[i])
                print(f"processing {i} of {len(phoneNumber)} | {appName[i]} | {phoneNumber[i]}\n")
                moveToCAPIUrl = f"https://whatsapp-internal-support.gupshup.io/support/migrate/{appID[i]}/docker/embed"
                # moveToCAPIUrl = f"http://10.80.14.84:8081/support/migrate/{appID[i]}/docker/embed"
                moveToCAPIPayload = f"phone={phoneNumber[i]}&clientName={appName[i]}&phoneId={phoneId[i]}&wabaId={wabaId[i]}&forceMigrate=false"
                moveToCAPIHeaders = {"Authorization": f"{LDAP}","Content-Type": "application/x-www-form-urlencoded",}
                try:
                    
                    time.sleep(1)
                    moveToCAPIResponse = requests.post( moveToCAPIUrl, headers=moveToCAPIHeaders, data=moveToCAPIPayload, timeout=60)
                    moveToCAPIResponse.raise_for_status()
                    write_to_csv([ appID[i], appName[i], phoneNumber[i], wabaId[i], phoneId[i], moveToCAPIResponse.status_code, moveToCAPIResponse.json()], get_file_paths()["output_file"], open(get_file_paths()["log_file_path"], "a"),)
                    print(f"cloud migration success for (status : {moveToCAPIResponse.status_code}) | {appName[i]} | {phoneNumber[i]}\n")
                    log_message(f'{time.strftime("%Y-%m-%d %H:%M:%S")} | {username} | success move to capi (status : {moveToCAPIResponse.status_code}) | {appName[i]} | {phoneNumber[i]} | {moveToCAPIResponse.json()}', get_file_paths()["log_file_path"])
                
                except requests.exceptions.Timeout as err:
                    print("move to CAPI request timed out")
                    log_message(f'{time.strftime("%Y-%m-%d %H:%M:%S")} | {username} | move to CAPI request timed out (status : {err.response.status_code}) | {appName[i]} | {phoneNumber[i]} | {err.response.json()}', get_file_paths()["log_file_path"])
                
                except requests.exceptions.HTTPError as err:
                    if ( err.response.status_code == 400 and err.response.json()["message"] == "Given phone number does not match with app details record" or err.response.json()["message"] == "phone number in meta does not match with phone number in SS"):
                        print(f"phone number mismatch (status : {err.response.status_code}) | {appName[i]} | {phoneNumber[i]} | {err.response.json()}\n")
                        log_message(f'{time.strftime("%Y-%m-%d %H:%M:%S")} | {username} | phone number mismatch (status : {err.response.status_code}) | {appName[i]} | {phoneNumber[i]} | {err.response.json()}', get_file_paths()["log_file_path"])
                        log_csv(json.dumps({"AppID": appID[i], "AppName": appName[i], "PhoneNumber": phoneNumber[i], "WabaId": wabaId[i], "PhoneId": phoneId[i], "Status": moveToCAPIResponse.status_code, "Response": moveToCAPIResponse.json()['message']}))
                        write_to_csv([ appID[i], appName[i], phoneNumber[i], wabaId[i], phoneId[i], err.response.status_code, err.response.json()  ], get_file_paths()["mismatch_output_file"], open(get_file_paths()["log_file_path"], "a"),)
                        continue
                
                    print(f"error at move to capi api (status : {err.response.status_code}) | {appName[i]} | {phoneNumber[i]} | {err.response.json()}\n")
                    log_message(f'{time.strftime("%Y-%m-%d %H:%M:%S")} | {username} | error at move to capi api (status : {err.response.status_code}) | {appName[i]} | {phoneNumber[i]} | {err.response.json()}', get_file_paths()["log_file_path"])
                    write_to_csv([ appID[i], appName[i], phoneNumber[i], wabaId[i], phoneId[i], err.response.status_code, err.response.json() ], get_file_paths()["output_file"], open(get_file_paths()["log_file_path"], "a"),)
                    continue
    except IOError as e:
        print(f"error while opening csv at: ", e)
        open(get_file_paths()["log_file_path"], "a").write(f'{time.strftime("%Y-%m-%d %H:%M:%S")} | error while opening csv at ({get_file_paths()["data_csv_file_path"]}) |  {str(e)} \n')
        log_message(f'{time.strftime("%Y-%m-%d %H:%M:%S")} | {username} | error while opening csv at ({get_file_paths()["data_csv_file_path"]}) |  {str(e)}', get_file_paths()["log_file_path"])

def force_migration():
    try:
        csvData = read_from_csv(get_file_paths()["mismatch_output_file"], open(get_file_paths()["log_file_path"], "a"))
        if( len(csvData) == 0 ):
            return "No data found to be processed"
        (appID, appName, phoneNumber, wabaId, phoneId, status_code, response) = zip(*csvData)

        for i in range(0, len(phoneNumber)):
            if ( status_code[i] == 400 and "Given phone number does not match with app details record" or "phone number in meta does not match with phone number in SS" in response[i]):
                print(f"processing mismatched number {i} of {len(phoneNumber)} | | {appName[i]}| {phoneNumber[i]}\n")
                # moveToCAPIUrl = f"https://whatsapp-internal-support.gupshup.io/support/migrate/{appID[i]}/docker/embed"
                moveToCAPIUrl = f"https://whatsapp-internal-support.gupshup.io/support/migrate/{appID[i]}/docker/embed"                
                moveToCAPIPayload = f"phone={phoneNumber[i]}&clientName={appName[i]}&phoneId={phoneId[i]}&wabaId={wabaId[i]}&forceMigrate=true"
                moveToCAPIHeaders = {"Authorization": f"{LDAP}","Content-Type": "application/x-www-form-urlencoded",}
                time.sleep(1)
                moveToCAPIResponse = requests.post( moveToCAPIUrl, headers=moveToCAPIHeaders, data=moveToCAPIPayload,timeout=30 )
                moveToCAPIResponse.raise_for_status()
                write_to_csv([ appID[i], appName[i], phoneNumber[i], wabaId[i], phoneId[i], moveToCAPIResponse.status_code, moveToCAPIResponse.json()], get_file_paths()["output_file"], open(get_file_paths()["log_file_path"], "a"))
                print(f"cloud migration success for (status : {moveToCAPIResponse.status_code})| {appName[i]} | {phoneNumber[i]}\n")
                log_message(f'{time.strftime("%Y-%m-%d %H:%M:%S")} | {username} | success move to capi (status : {moveToCAPIResponse.status_code}) | {appName[i]} | {phoneNumber[i]} | {moveToCAPIResponse.json()}', get_file_paths()["log_file_path"])

    except ValueError as err:
        print(f'processing not required for | No data to process from the csv at {get_file_paths()["mismatch_output_file"]} | {err}')
        open(get_file_paths()["log_file_path"], "a").write(f'{time.strftime("%Y-%m-%d %H:%M:%S")} | processing not required for | No data to process from the csv at at {get_file_paths()["mismatch_output_file"]} | {err}\n')

    except requests.exceptions.Timeout as err:
            print("move to CAPI request timed out")
            log_message(f'{time.strftime("%Y-%m-%d %H:%M:%S")} | {username} | move to CAPI request timed out (status : {err.response.status_code}) | {appName[i]} | {phoneNumber[i]} | {err.response.json()}', get_file_paths()["log_file_path"])
            write_to_csv( [ appID[i], appName[i], phoneNumber[i], wabaId[i], phoneId[i], err.response.status_code, err.response.json() ], get_file_paths()["output_file"], open(get_file_paths()["log_file_path"], "a"))
    
    except requests.exceptions.HTTPError as err:
        print( f"error at move to capi api (status : {err.response.status_code}) | {appName[i]} | {phoneNumber[i]} | {err.response.json()}\n")
        log_message(f'{time.strftime("%Y-%m-%d %H:%M:%S")} | {username} | error at move to capi api (status : {err.response.status_code}) | {appName[i]} | {phoneNumber[i]} | {err.response.json()}', get_file_paths()["log_file_path"])
        write_to_csv( [ appID[i], appName[i], phoneNumber[i], wabaId[i], phoneId[i], err.response.status_code, err.response.json() ], get_file_paths()["output_file"], open(get_file_paths()["log_file_path"], "a"))

    except IOError as e:
        print(f"error while opening csv: ", e)
        log_message(f'{time.strftime("%Y-%m-%d %H:%M:%S")} | {username} | error while opening csv at ({get_file_paths()["data_csv_file_path"]}) |  {str(e)}', get_file_paths()["log_file_path"])

def main():
    process_migration_data()
    # force_migration()
    open(get_file_paths()["log_file_path"], "a").close()

if __name__ == "__main__":
    main()