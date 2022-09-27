import sys
import requests
import pickle
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
import smc.elements
import smc.core.engine
import smc.core.engines
import smc.policy
import smc.api.web
from smc.api.exceptions import SMCConnectionError
from smc.api.exceptions import SMCOperationFailure
from smc.base.util import unicode_to_bytes

from smc import session
from smc.elements.network import IPList

from cryptography.fernet import Fernet

# the 'requirements.txt' file for this project is:
#requests
#fp-ngfw-smc-python
#cryptography
# the first is for making HTTP requests
# the second library allows to interact with Forcepoint's SMC REST API
# the third is for encryption/decryption
# 'pickle' is for file I/O

# encryption key
encryptKey = b'WHATEVERBLAHBLAH='
# SMC address
smchost = 'https://smc.whatever.com:8082'
targetIpList = 'TEST_SOC_IP_LIST'

# Fernet encryption/decryption key
def getApiKey(encryptKey):    
    fernetObject = Fernet(encryptKey)
    # Read crypted API key from file
    with open('cryptedapikey.bin', 'rb') as keyFile:
        cryptedApiKey = pickle.load(keyFile)
        keyFile.close()
    # Decrypt using Fernet key
    apiKey = bytes.decode(fernetObject.decrypt(cryptedApiKey), 'utf-8')
    return apiKey

def loginSMC(smchost=smchost):
    apiKey = getApiKey(encryptKey)
    # try to connect
    try:
        session.login(url=smchost, api_key=apiKey, verify=False)
    # if the connection doesn't establish, write the reason on standard error instead of crashing the whole program
    # I've explicitly imported SMCConnectionError and SMCOperationFailure from smc.api.exceptions
    # to be able to use directly 'except SMCConnectionError' here
    # I'm *not* catching (intercepting) any other Exception type
    except SMCConnectionError as e:
        errmsg = "No connection with SMC {smchost} : {e}"
        print(errmsg,file=sys.stderr)
        sys.exit()

# a function with a single parameter with a default value
# if you don't specify the parameter when calling, it's assumed the default
def listIPLIST(targetIpList=targetIpList):
    # login to SMC
    loginSMC()
    myList = IPList(targetIpList)
    currentIpList = myList.iplist
    print("Current IP list for",targetIpList)
    for x in range(len(currentIpList)):
        print(currentIpList[x])
    session.logout()

# one mandatory parameter (they have to appear first in the parameter list)
# and two optional (with default values)
def addToIPLIST(inputCIDR,targetIpList=targetIpList,verbose=True):
    print("Start add to list:",inputCIDR)
    # login to SMC
    loginSMC()
    myList = IPList(targetIpList)
    currentIpList = myList.iplist
    # verbose is a boolean
    if verbose:
        print("Current IP list for",targetIpList)
        print(currentIpList)
    # check if at least one member of 'currentIpList' is equal to 'inputCIDR'
    if not inputCIDR in currentIpList:
        currentIpList.append(inputCIDR)
        newList = {"ip": currentIpList}
        # another exception management
        try:
            myList.upload(json=newList,as_type='json')
        except SMCOperationFailure as e:
            errmsg = "SMC {smchost} : {e}"
            print(errmsg,file=sys.stderr)
            session.logout()
            sys.exit()
        currentIpList = myList.iplist
        if verbose:
            print(currentIpList)
        print("Add to list completed:",inputCIDR)
    else:
        print("Already present in list:",inputCIDR)
    session.logout()        
