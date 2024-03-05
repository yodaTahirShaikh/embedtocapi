import time
import requests

def getLDAP(username, password, log_file):
    getLDAPurl = "https://whatsapp-internal-support.gupshup.io/support/auth/login"
    getLDAPpayload = f'username={username}&password={password}'
    getLDAPheaders = {"Content-Type": "application/x-www-form-urlencoded"}
    try:
        getLDAPresponse = requests.request("POST", getLDAPurl, headers=getLDAPheaders, data=getLDAPpayload)

        if getLDAPresponse.status_code != 200:
            print(f'error at support login | {getLDAPresponse.status_code} | {username}')
            log_file.write(f'{time.strftime("%Y-%m-%d %H:%M:%S")} | error at support login ({getLDAPresponse.status_code}) | {username} | {getLDAPresponse.json()['message']}\n')

        else:
            getLDAPToken = getLDAPresponse.json()["message"]["token"]
            print(f'login success for {username}')
            log_file.write(f'{time.strftime("%Y-%m-%d %H:%M:%S")} | login Success for {username}\n')

#-------------------------------------------------------------------------------------------#
            
            return getLDAPToken
        
    except requests.exceptions.RequestException as e:
        print(f'error at support login: ', e)
        log_file.write(f'{time.strftime("%Y-%m-%d %H:%M:%S")} | request exception at support login {str(e)}\n')