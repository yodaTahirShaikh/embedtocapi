import requests
import json
import time
import os
import pandas as pd
from parseenv import parse_env_file
from generateLDAP import getLDAP
from readcsv import readFromCSV
from openpyxl import Workbook
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
LDAP = getLDAP(username, password, log_file)


# File path to input csv
csv_file_path = join(dirname(__file__), "embedtocapi.csv")


# File path to result csv
output_file = join(dirname(__file__), "CAPIMigrationresult.csv")
wb = Workbook()
ws = wb.active

# Add csv title
ws.append(["appID", "phoneNumber", "appName", "phoneId", "wabaId", "status_code", "desc"])




def moveToCAPI():

    try:

        pnSet = set()
        wabaSet = set()

        # Read data from csv file and store in csvData
        csvData = readFromCSV(csv_file_path, log_file)

        # Read data from csv file and store in csvData by unpacking
        appID, phoneNumber, appName, phoneId, wabaId = csvData

        for i in range(0, len(phoneNumber)):
            # To avoid rerun of migration api for the same number
            # Storing the process phone numbers in a set to have unique phone number and incrementing the index

            if phoneNumber[i] in pnSet:

                print(f'duplicate phone number or already processed ({phoneNumber[i]})')
                log_file.write(f'{time.strftime("%Y-%m-%d %H:%M:%S")} | duplicate phone number or already processed ({phoneNumber[i]})\n')
                i += 1
                continue
            else:
                # adding unique phone numbers and waba id to set to process further
                pnSet.add(phoneNumber[i])
                wabaSet.add(wabaId[i])

                # preping the url and payload for the Cloud Migration API
                moveToCAPIUrl = f'https://whatsapp-internal-support.gupshup.io/support/migrate/{appID[i]}/docker/embed'
                moveToCAPIPayload = f'phone={phoneNumber[i]}&clientName={appName[i]}&phoneId={phoneId[i]}&wabaId={wabaId[i]}'
                moveToCAPIHeaders = {'Authorization': f'{LDAP}','Content-Type': 'application/x-www-form-urlencoded'}

                try:

                    # API call with exception handling
                    moveToCAPIResponse = requests.request("POST", moveToCAPIUrl, headers=moveToCAPIPayload, data=moveToCAPIHeaders)


                    # if the status code from the api call is other than 200 
                    if moveToCAPIResponse.status_code != 200:


                        ws.append([appID[i],phoneNumber[i],appName[i],phoneId[i],wabaId[i],moveToCAPIResponse.status_code,moveToCAPIResponse.text,])
                        
                        
                        log_file.write(f'{time.strftime("%Y-%m-%d %H:%M:%S")} | error at move to capi api ({moveToCAPIResponse.status_code}) | {appName[i]} | {phoneNumber[i]} | {moveToCAPIResponse.text}\n')
                        continue
                    
                    # if the status code from the api call is 200 
                    else:
                        try:
                            setCloudSubscrption(wabaSet, systemToken)
                            ws.append([appID[i],phoneNumber[i],appName[i],phoneId[i],wabaId[i],moveToCAPIResponse.status_code,moveToCAPIResponse.text,])
                            log_file.write(f'{time.strftime("%Y-%m-%d %H:%M:%S")} | success move to capi ({moveToCAPIResponse.status_code}) | {appName[i]} | {phoneNumber[i]} | {moveToCAPIResponse.text}\n')
                        except:
                            print("error when adding subscription")

                except requests.exceptions.RequestException as e:
                    print(f'error while move to CAPI: ', e)
                    log_file.write(f'{time.strftime("%Y-%m-%d %H:%M:%S")} | error while opening csv at ({csv_file_path}) |  {str(e)} \n')

    except TypeError as e:
        print(f'error while loading data from ({csv_file_path}): ', e)
        log_file.write(f'{time.strftime("%Y-%m-%d %H:%M:%S")} | error while loading data from csv ({csv_file_path}) |  {str(e)} \n')

    except IOError as e:
        print(f'error while loading csv at ({csv_file_path}): ', e)
        log_file.write(f'{time.strftime("%Y-%m-%d %H:%M:%S")} | error while opening csv at ({csv_file_path}) |  {str(e)} \n')


moveToCAPI()


def setCloudSubscrption(wabaId, systemToken):
    payload = json.dumps({"override_callback_uri": "https://common-wa-event-fwdr.gupshup.io/globalPublisher/api/fb-cloud/events"})

    subscriptionHeaders = {'Authorization': f'Bearer {systemToken}','Content-Type': 'application/json'}

    for id in wabaId:
        subscriptionUrl = f'https://graph.facebook.com/v19.0/{id}/subscribed_apps'

        try:
            subscriptionResponse = requests.request("POST", subscriptionUrl, headers=subscriptionHeaders, data=payload)
            if(subscriptionResponse.status_code != 200):
                print(f'error while adding subscription to waba | ', wabaId)
                log_file.write(f'{time.strftime("%Y-%m-%d %H:%M:%S")} | error while adding subscription to waba | ({wabaId}) | {subscriptionResponse.status_code} | {subscriptionResponse.text}\n')
            else:
                print(f'subscription added to waba | ', wabaId)
                log_file.write(f'{time.strftime("%Y-%m-%d %H:%M:%S")} | subscription added to waba | ({wabaId}) | {subscriptionResponse.status_code} | {subscriptionResponse.text}\n')

        except requests.exceptions.RequestException as e:
            print(f'error while adding subscription to waba: ', e)
            log_file.write(f'{time.strftime("%Y-%m-%d %H:%M:%S")} | request exception while adding subscription to waba | ({wabaId}) | {subscriptionResponse.status_code} | {subscriptionResponse.text}\n')