import time
import requests


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