**Bulk Move to CAPI Apps**

Pre-requisites:
Python 3.10+

To install dependencies run the following command
pip install -r requirements.txt

*Note 
Create an embedtocapi.csv file with title as "AppID, PhoneNumber, AppName, WabaId, PhoneId" case-sensitive for the program to read the data from the csv file.

Run **embedtocapi.py** file for the program to run and it will log all the exception and error on **log.txt** file and also store request/response data in **CAPIMigrationresult.xlsx** file
