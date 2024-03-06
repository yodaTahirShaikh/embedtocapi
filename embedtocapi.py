import requests
import json
import time
import os
import pandas as pd
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


# File path to result csv
output_file = "CAPIMigrationresult.xlsx"


def moveToCAPI():
    try:
        pnSet = set()
        wabaSet = set()

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
                
                i += 1

                continue
            else:

                # adding unique phone numbers and waba id to set to process further
                pnSet.add(phoneNumber[i])

                print(f'processing {phoneNumber[i]}\n')
                
                # preping the url and payload for the Cloud Migration API
                moveToCAPIUrl = f"https://whatsapp-internal-support.gupshup.io/support/migrate/{appID[i]}/docker/embed"
                moveToCAPIPayload = f"phone={phoneNumber[i]}&clientName={appName[i]}&phoneId={phoneId[i]}&wabaId={wabaId[i]}"
                moveToCAPIHeaders = {
                    "Authorization": f"{LDAP}",
                    "Content-Type": "application/x-www-form-urlencoded",
                }

                try:

                    # API call with exception handling
                    moveToCAPIResponse = requests.post(moveToCAPIUrl,headers=moveToCAPIPayload, data=moveToCAPIHeaders)
                    moveToCAPIResponse.raise_for_status()
                    time.sleep(3)
                    # if the status code from the api call is other than 200
                    if moveToCAPIResponse.status_code != 200:

                        print(f'error at move to capi api (status : {moveToCAPIResponse.status_code}) | {appName[i]} | {phoneNumber[i]} | {moveToCAPIResponse}\n')
                        
                        write_to_csv([appID[i],phoneNumber[i],appName[i],phoneId[i],wabaId[i], moveToCAPIResponse.status_code, moveToCAPIResponse], output_file, log_file )

                        log_file.write(f'{time.strftime("%Y-%m-%d %H:%M:%S")} | error at move to capi api (status : {moveToCAPIResponse.status_code}) | {appName[i]} | {phoneNumber[i]} | {moveToCAPIResponse}\n')
                        
                        i += 1

                        continue

                    # if the status code from the api call is 200
                    else:
                        try:
                            if wabaId[i] in pnSet:

                                print(f"duplicate phone number or already processed ({wabaId[i]})\n")

                                log_file.write(f'\n{time.strftime("%Y-%m-%d %H:%M:%S")} | duplicate phone number or already processed ({wabaId[i]})\n')

                                continue
                            else:
                                wabaSet.add(wabaId[i])

                                setCloudSubscrption(wabaId[i], systemToken)
                        
                                write_to_csv([appID[i],phoneNumber[i],appName[i],phoneId[i],wabaId[i], moveToCAPIResponse.status_code, moveToCAPIResponse], output_file, log_file )

                                print(f'cloud migration success for {phoneNumber[i]}\n')

                                log_file.write(f'{time.strftime("%Y-%m-%d %H:%M:%S")} | success move to capi (status : {moveToCAPIResponse.status_code}) | {appName[i]} | {phoneNumber[i]} | {moveToCAPIResponse}\n')
                        
                        except:
                            print("error when adding subscription \n")

                except requests.exceptions.HTTPError as err:
                
                    error_msg = f"error at support login | {err.response.status_code} | {username}  | {err.response.json()['message']}"

                    print(f"{error_msg}\n")

                    log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} | error at support login (status : {err.response.status_code}) | {username} | {err.response.json()['message']}\n")

    except requests.exceptions.RequestException as e:
        
        print(f"error while move to CAPI: ", e)
        
        log_file.write(f'{time.strftime("%Y-%m-%d %H:%M:%S")} | error while opening csv at ({csv_file_path}) |  {str(e)} \n')



def setCloudSubscrption(wabaId, systemToken):
    
    payload = json.dumps({"override_callback_uri": "https://common-wa-event-fwdr.gupshup.io/globalPublisher/api/fb-cloud/events"})

    subscriptionHeaders = {'Authorization': f'Bearer {systemToken}','Content-Type': 'application/json'}

    subscriptionUrl = f'https://graph.facebook.com/v19.0/{wabaId}/subscribed_apps'
    try:
        subscriptionResponse = requests.post(subscriptionUrl, headers=subscriptionHeaders, data=payload)
        subscriptionResponse.raise_for_status()
        
        if subscriptionResponse.status_code != 200:

            print(f'error while adding subscription to waba | {wabaId} \n')
            
            log_file.write(f'{time.strftime("%Y-%m-%d %H:%M:%S")} | error while adding subscription to waba | ({wabaId}) | {subscriptionResponse["status_code"]} | {subscriptionResponse}\n')
        
        else:
            
            print(f'subscription added to waba | {wabaId}\n')
            
            log_file.write(f'{time.strftime("%Y-%m-%d %H:%M:%S")} | subscription added to waba | ({wabaId}) | {subscriptionResponse["status_code"]} | {subscriptionResponse}\n')

    except requests.exceptions.RequestException as e:

        print(f'RequestException while adding subscription to waba: {e}\n')
        
        log_file.write(f'{time.strftime("%Y-%m-%d %H:%M:%S")} | request exception while adding subscription to waba | ({wabaId}) | {subscriptionResponse["status_code"]} | {subscriptionResponse}\n')


moveToCAPI()


log_file.close()