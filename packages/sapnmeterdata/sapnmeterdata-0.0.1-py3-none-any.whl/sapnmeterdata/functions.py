import requests
import json
from datetime import datetime, timedelta
import nemreader
from bs4 import BeautifulSoup

class LoginError(Exception):
    """Raised when login fails."""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
    pass
class AuthError(Exception):
    """Raised when failed to retrieved csrf and/or authorization."""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
    pass
class FetchError(Exception):
    """Raised when failed to retrieved meterdata."""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
    pass

class login():
    def __init__(self, email:str, password:str):
        CADSiteLogin_url = 'https://customer.portal.sapowernetworks.com.au/meterdata/CADSiteLogin'
        CADSiteLogin_response = requests.post(CADSiteLogin_url)

        if CADSiteLogin_response.status_code == 200:
            soup = BeautifulSoup(CADSiteLogin_response.text, 'html.parser')
            self.ViewState = soup.find('input', {'type': 'hidden', 'id': 'com.salesforce.visualforce.ViewState'}).get_attribute_list("value")[0]
            self.ViewStateMAC = soup.find('input', {'type': 'hidden', 'id': 'com.salesforce.visualforce.ViewStateMAC'}).get_attribute_list("value")[0]
        
        CADSiteLogin_url = 'https://customer.portal.sapowernetworks.com.au/meterdata/CADSiteLogin'
        CADSiteLogin_form_data = {
            "loginPage:SiteTemplate:siteLogin:loginComponent:loginForm": "loginPage:SiteTemplate:siteLogin:loginComponent:loginForm",
            "loginPage:SiteTemplate:siteLogin:loginComponent:loginForm:username": email,
            "loginPage:SiteTemplate:siteLogin:loginComponent:loginForm:password": password,
            "loginPage:SiteTemplate:siteLogin:loginComponent:loginForm:loginButton": "Login",
            "com.salesforce.visualforce.ViewState": self.ViewState,
            "com.salesforce.visualforce.ViewStateMAC": self.ViewStateMAC
        }
        CADSiteLogin_response = requests.post(CADSiteLogin_url, data=CADSiteLogin_form_data)

        if(CADSiteLogin_response.status_code == 200):
            print("successfully logged in")
        else:
            raise LoginError("failed to login")
        self.text = CADSiteLogin_response.text
        self.sid = CADSiteLogin_response.text[CADSiteLogin_response.text.find("sid="):CADSiteLogin_response.text.find("&",CADSiteLogin_response.text.find("sid="))]
        self.methods = {}
        link = CADSiteLogin_response.text[CADSiteLogin_response.text.find(".handleRedirect('")+17:CADSiteLogin_response.text.find("'); }",CADSiteLogin_response.text.find(".handleRedirect('")+17)]
        requests.get(link)
    def updatedownloadNMIDataKeys(self):
        cadenergydashboard_url = "https://customer.portal.sapowernetworks.com.au/meterdata/CADRequestMeterData"
        cadenergydashboard_headers = {
            "Cookie": self.sid
        }

        cadenergydashboard_response = requests.get(cadenergydashboard_url, headers=cadenergydashboard_headers)
        cadenergydashboard_response_data = cadenergydashboard_response.text

        cadenergydashboard_raw = cadenergydashboard_response_data[cadenergydashboard_response_data.find('{"name":"downloadNMIData"'):cadenergydashboard_response_data.find('"}',cadenergydashboard_response_data.find('{"name":"downloadNMIData"'))+2]
        downloadNMIData = json.loads(cadenergydashboard_raw)
        if 'csrf' in downloadNMIData and 'authorization' in downloadNMIData:
            print('successfully retrieved csrf & authorization')
        else:
            raise AuthError('failed to retrieved csrf and/or authorization')

        self.methods[downloadNMIData['name']] = {}
        self.methods[downloadNMIData['name']]['csrf'] = downloadNMIData['csrf']
        self.methods[downloadNMIData['name']]['authorization'] = downloadNMIData['authorization']
    def updategetNMIAssignmentsKeys(self):
        cadenergydashboard_url = "https://customer.portal.sapowernetworks.com.au/meterdata/apex/cadenergydashboardmeterdata/cadaccountpage"
        cadenergydashboard_cookies = {
            "sid": self.sid[4:]
        }

        cadenergydashboard_response = requests.get(cadenergydashboard_url, cookies=cadenergydashboard_cookies)
        cadenergydashboard_response_data = cadenergydashboard_response.text
        print(cadenergydashboard_response_data)
        cadenergydashboard_raw = cadenergydashboard_response_data[cadenergydashboard_response_data.find('{"name":"getNMIAssignments"'):cadenergydashboard_response_data.find('"}',cadenergydashboard_response_data.find('{"name":"getNMIAssignments"'))+2]
        getNMIAssignments = json.loads(cadenergydashboard_raw)
        if 'csrf' in getNMIAssignments and 'authorization' in getNMIAssignments:
            print('successfully retrieved csrf & authorization')
        else:
            raise AuthError('failed to retrieved csrf and/or authorization')

        self.methods['getNMIAssignments'] = {}
        self.methods['getNMIAssignments']['csrf'] = getNMIAssignments['csrf']
        self.methods['getNMIAssignments']['authorization'] = getNMIAssignments['authorization']
        
    def getNMIs(self):
        self.updategetNMIAssignmentsKeys()
        getNMIAssignments_data = {
            "action":"CADLandingPageController",
            "method":"getNMIAssignments",
            "type":"rpc",
            "tid":2,
            "ctx":{
                "csrf": self.methods['getNMIAssignments']['csrf'],
                "vid":"06628000004kHTl",
                "ns":"",
                "ver":35
            }
        }
        getNMIAssignments_headers = {
            "Cookie": self.sid,
            "referer":"https://customer.portal.sapowernetworks.com.au/meterdata/CADAccountPage"
        }
        getNMIAssignments_url = "https://customer.portal.sapowernetworks.com.au/meterdata/apexremote"

        getNMIAssignments_response = requests.post(getNMIAssignments_url, headers=getNMIAssignments_headers, json=getNMIAssignments_data)
        print(getNMIAssignments_response.text)

class meter():
    def __init__(self, NMI:int, login_details:login):
        self.nmi = NMI
        self.login_details = login_details
    def getdata(self, filepath:str, startdate:datetime = datetime.today() - timedelta(2), enddate:datetime = datetime.today()):
        self.login_details.updatedownloadNMIDataKeys()
        downloadNMIData_data = {
            "action": "CADRequestMeterDataController",
            "method": 'downloadNMIData',
            "data": [
                self.nmi,
                "SAPN",
                startdate.strftime("%a, %d %b %Y %H:%M:%S GMT"),
                enddate.strftime("%a, %d %b %Y %H:%M:%S GMT"),
                "Customer Access NEM12",
                "Detailed Report (CSV)",
                0
            ],
            "type": "rpc",
            "tid": 5,
            "ctx": {
                "csrf": self.login_details.methods['downloadNMIData']['csrf'],
                "vid": "06628000004kHU7",
                "ns": "",
                "ver": 35,
                "authorization": self.login_details.methods['downloadNMIData']['authorization']
            }
        }
        downloadNMIData_headers = {
            "referer": "https://customer.portal.sapowernetworks.com.au/meterdata/apex/cadenergydashboard"
        }
        downloadNMIData_url = "https://customer.portal.sapowernetworks.com.au/meterdata/apexremote"

        downloadNMIData_response = requests.post(downloadNMIData_url, headers=downloadNMIData_headers, json=downloadNMIData_data)
        downloadNMIData = json.loads(downloadNMIData_response.text)
        if 'message' in downloadNMIData[0]['result']:
            raise FetchError(downloadNMIData[0]['result']['message'])
        else:
            print('successfully retrieved meterdata')
        filename = downloadNMIData[0]['result']['filename']
        self.data = downloadNMIData[0]['result']['results']

        if filepath[-1] != "\\":
            filepath += "\\"
        
        with open(filepath + filename, "w") as text_file:
            text_file.write(self.data)
        self.dataframes = nemreader.output_as_data_frames(filepath + filename, split_days=True, set_interval=None, strict=False)
        return filepath + filename