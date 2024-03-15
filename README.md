**Bulk Move to CAPI Apps**

Pre-requisites:
Python 3.10+

To install dependencies run the following command: 
**pip install -r requirements.txt**

**Note**
1. Place your LDAP username and password in a **.env** file in the same folder as of the python files and name your vairable as  "**USERNAME**, **PASSWORD**" Please note this is case-sensitive for the program.
2. Create an **Embed_To_CAPI.csv** file in the same folder as of the python files with title as "**AppID**, **PhoneNumber**, **AppName**, **WabaId**, **PhoneId**" case-sensitive for the program to read the data from the csv file.

**To Run the python code**

Run **main.py** file for the program to run and it will log all the exception and error on **log.txt** file and also store request/response data in **CAPI_Migration_result.csv** file
