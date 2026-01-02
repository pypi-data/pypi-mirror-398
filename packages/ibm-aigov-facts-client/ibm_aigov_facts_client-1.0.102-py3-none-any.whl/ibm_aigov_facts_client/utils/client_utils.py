import requests,json
from requests.models import Response
import urllib3
from ibm_cloud_sdk_core.authenticators import BearerTokenAuthenticator

from http import HTTPStatus

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def get_iamtoken(url, username, password,bedrock_url = None):
    if bedrock_url is None:
        fqdn = urllib3.util.parse_url(url).netloc
        domain = '.'.join(fqdn.split('.')[1:])
        bedrock_url = 'https://cp-console.{}'.format(domain)
        print("Generated bedrock url {}".format(bedrock_url))
    else:
        print("Found bedrock url {}".format(bedrock_url))    
    bedrock_url = bedrock_url + "/idprovider/v1/auth/identitytoken"     
    data = {
        'grant_type': 'password',
        'username': username,
        'password': password,
        'scope': 'openid'
    }
    
    response = None
    try:
        response = requests.post(bedrock_url, data, verify=False)
    except Exception as e:
        response = Response()
        response.code = "unavailable"
        response.error_type = "Service Unavailable for retrieving access token"
        response.status_code = 503
        response._content = { "Reason" : "Unable to generate access token using bedrock url {}".format(bedrock_url) }
        
    return response

def get_accesstoken(url, username, iamtoken):
    url = '{}/v1/preauth/validateAuth'.format(url)
    headers = {
        'Content-type': 'application/json',
        'username': username,
        'iam-token': iamtoken
    }
    return requests.get(url, headers=headers, verify=False)

def get_access_token(url, username, password, apikey = None, bedrock_url = None):
    #For CPD 3.5.x system and for CP4D 4.0.X system where iam-integration is not enabled
    if bedrock_url == None:
        return get_bearer_token(url, username, password,apikey=apikey)
    
    response = get_iamtoken(url,username,password, bedrock_url=bedrock_url)
    #service is not available when iamintegration=false so fall back to old way of generating code
    if response.status_code==HTTPStatus.SERVICE_UNAVAILABLE:
        print("Service Unavailable..falling back to old way")
        return get_bearer_token(url, username, password=password, apikey=apikey)
    else:
        return get_accesstoken(url,username, response.json()['access_token']).json()['accessToken']

def get_bearer_token(url, username, password=None,apikey = None,bedrock_url = None):  
    if bedrock_url is None:
        headers = {'Content-type': 'application/json'} 
        token_url = '{}/icp4d-api/v1/authorize'.format(url)
        response = requests.post(
                headers=headers,
                url=token_url,verify=False,
                data=json.dumps({
                    "username": username,
                    "password": password,
                    "api_key": apikey
                }))
        if response.status_code==HTTPStatus.UNAUTHORIZED:
            print("Authorization failed. Checking for CP4D 4.x system") 
            #Assume it's 4.0 system with iam-integration turned on and try to authenticate           
            token_response = get_iamtoken(url,username,password)
            if token_response.status_code==HTTPStatus.SERVICE_UNAVAILABLE or token_response.status_code==HTTPStatus.BAD_REQUEST or token_response.status_code==HTTPStatus.UNAUTHORIZED:
                msg = "Please check the CPD credentials.\n"
                msg = msg + "Note: \n"
                msg = msg + "If you are using CP4D 4.0.x cluster with iam-integration turned ON then please set the `bedrock_url` parameter in CloudPakforDataConfig when providing to Facts Client \n"
                msg = msg + "CloudPakforDataConfig = (service_url=<hosturl> \n"
                msg = msg + "            username=<username> \n"
                msg = msg + "            password=<password> \n"
                msg = msg + "            bedrock_url=<cluster bedrock url>\n"
                msg = msg + "          \n)"

                raise Exception(response.text + msg)
            else:
               token = get_accesstoken(url,username, token_response.json()['access_token']).json()['accessToken']
               print("Authentication successful")
               return token     
    
        return response.json()['token']
        
             
def retry_session(retries, session=None, backoff_factor=0.5):
    from requests.adapters import HTTPAdapter
    from requests.packages.urllib3.util.retry import Retry
    session = session or requests.Session()
    retry = Retry(connect=retries
    , backoff_factor=backoff_factor,allowed_methods=frozenset(['GET', 'POST']))
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

        