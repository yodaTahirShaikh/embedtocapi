import requests
import time
from parseenv import parse_env_file
from generateLDAP import get_ldap_token
from readcsv import read_from_csv, write_to_csv
from os.path import join, dirname



# File path to log file
log_file_path = join(dirname(__file__), "log.txt")
log_file = open(log_file_path, "a")



# File path to env variable
env_file_path = join(dirname(__file__), ".env")
env_vars = parse_env_file(env_file_path)



# Extract variable from env file
username = env_vars.get("USERNAME")
password = env_vars.get("PASSWORD")
systemToken = env_vars.get("SYSTEMTOKEN")




# Generate LDAP Token
LDAP = get_ldap_token(username, password, log_file)



# File path to input csv
csv_file_path = join(dirname(__file__), "embedtocapi.csv")



# File path to result file
output_file = "CAPIMigrationresult.xlsx"


def moveToCAPI():
    try:

        # To avoid rerun of migration api for the same number
        # Storing the process phone numbers in a set
        pnSet = set()

        # Read data from csv file and store in csvData
        csvData = read_from_csv(csv_file_path, log_file)

        # Read data from csv file and store in csvData by unpacking
        appID, phoneNumber, appName, phoneId, wabaId = csvData

        for i in range(0, len(phoneNumber)):


            # To avoid rerun of migration api for the same number
            # Storing the process phone numbers in a set to have unique phone number and incrementing the index

            if phoneNumber[i] in pnSet:

                print(f"duplicate phone number or already processed ({phoneNumber[i]})\n")
                
                log_file.write(f'{time.strftime("%Y-%m-%d %H:%M:%S")} | duplicate phone number or already processed ({phoneNumber[i]})\n')
                
                # incrementing the index to avoid rerun
                i += 1

                continue
            else:

                # adding unique phone numbers and waba id to set to process further
                pnSet.add(phoneNumber[i])

                print(f'processing {phoneNumber[i]}\n')
                
                # preping the url and payload for the Cloud Migration API
                moveToCAPIUrl = f"https://whatsapp-internal-support.gupshup.io/support/migrate/{appID[i]}/docker/embed"
                moveToCAPIPayload = f"phone={phoneNumber[i]}&clientName={appName[i]}&phoneId={phoneId[i]}&wabaId={wabaId[i]}&forceMigrate=true"
                moveToCAPIHeaders = {
                    "Authorization": f"{LDAP}",
                    "Content-Type": "application/x-www-form-urlencoded",
                }

                try:
                    
                    # Migrate to CAPI api call with exception handling
                    # handle connection timeout within 30 seconds and response time to 70 seconds before raising exception
                    moveToCAPIResponse = requests.post(moveToCAPIUrl,headers=moveToCAPIPayload, data=moveToCAPIHeaders, timeout=(30, 70))

                    # raise exception if status code is not 200
                    moveToCAPIResponse.raise_for_status()

                    time.sleep(2)


                    # if the status code from the api call is other than 200
                    if moveToCAPIResponse.status_code != 200:

                        print(f'error at move to capi api (status : {moveToCAPIResponse.status_code}) | {appName[i]} | {phoneNumber[i]} | {moveToCAPIResponse}\n')
                        
                        write_to_csv([appID[i],phoneNumber[i],appName[i],phoneId[i],wabaId[i], moveToCAPIResponse.status_code, moveToCAPIResponse], output_file, log_file )

                        log_file.write(f'{time.strftime("%Y-%m-%d %H:%M:%S")} | error at move to capi api (status : {moveToCAPIResponse.status_code}) | {appName[i]} | {phoneNumber[i]} | {moveToCAPIResponse}\n')
                        
                        i += 1

                        continue

                    # if the status code from the api call is 200
                    else:
                                    
                        write_to_csv([appID[i],phoneNumber[i],appName[i],phoneId[i],wabaId[i], moveToCAPIResponse.status_code, moveToCAPIResponse], output_file, log_file )

                        print(f'cloud migration success for {phoneNumber[i]}\n')

                        log_file.write(f'{time.strftime("%Y-%m-%d %H:%M:%S")} | success move to capi (status : {moveToCAPIResponse.status_code}) | {appName[i]} | {phoneNumber[i]} | {moveToCAPIResponse}\n')


                except requests.exceptions.Timeout:
                        print("move to CAPI request timed out")

                except requests.exceptions.HTTPError as err:
                
                    error_msg = f"error at support login | {err.response.status_code} | {username}  | {err.response.json()['message']}"

                    print(f"{error_msg}\n")

                    log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} | error while  (status : {err.response.status_code}) | {username} | {err.response.json()['message']}\n")

    except requests.exceptions.RequestException as e:
        
        print(f"error while move to CAPI: ", e)
        
        log_file.write(f'{time.strftime("%Y-%m-%d %H:%M:%S")} | error while opening csv at ({csv_file_path}) |  {str(e)} \n')



moveToCAPI()

log_file.close()