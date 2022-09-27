# these two are included in Python's "standard library"
import json
import sys
# this is an external requirement, to put inside 'requirements.txt'
# and install with 'pip3 install -r requirements.txt'
import requests
# disable SSL trust check. I *know* it's bad practice. I *know*.
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

############ LIBRARY FUNCTIONS
# vRA Login Token
# vRealize Automation login is composed of two phases:
# first you have to provide user&pass to get a refresh token
# afterwards, you'll use that to obtain a bearer token to be used in Authentication: token for subsequent API calls
def vraLogin(vraHost,vraUser,vraPassword):
    refreshtokenurl = f"https://{vraHost}/csp/gateway/am/api/login?access_token"
    iaasUrl = f"https://{vraHost}/iaas/api/login"
    # this is an object with two properties
    headers = {
        'accept': "application/json",
        'content-type': "application/json"
    }
    payload = f'{{"username":"{vraUser}","password":"{vraPassword}"}}'
    print(payload)
    # verify=false disable SSL verification (previously I've suppressed warnings)
    apioutput = requests.post(refreshtokenurl, data=payload, verify=False, headers=headers)
    # .json() is a function, used here to convert the request 'response' object type to something manageable
    print(apioutput.json())
    # get 'refreshtoken' property of the converted object
    refreshtoken = apioutput.json()['refresh_token']
    print(refreshtoken)
    iaasPayload = f'{{"refreshToken": "{refreshtoken}"}}'
    # oneline to obtain the property 'token' of the jsonified response
    iaasApiOutput = requests.post(iaasUrl, data=iaasPayload, headers=headers, verify=False).json()['token']
    vraToken = "Bearer " + iaasApiOutput
    return vraToken

# CLOUD ACCOUNTS
def getCloudAccounts(vraHost,vraToken):
    calledUrl = f"https://{vraHost}/iaas/api/cloud-accounts"
    # here I'm using the previously obtained token
    headers = {
        'accept': "application/json",
        'content-type': "application/json",
        'authorization': vraToken
    }
    ca = requests.get(calledUrl, headers=headers, verify=False)
    caJson = ca.json()
    # we need only the 'content' property of the jsonified response
    caContent = caJson['content']
    # we can return more than one value, in this case
    # ca.status_code is an attribute of the HTTP response, it contains... well, the HTTP status 
    # (200 OK, 400 you f*ked up your inputs, 401 who are you, 500 we've f*ked up somehow) 
    return ca.status_code,caContent

def getCloudAccountIdByName(vraHost,vraToken,caname):
    # obtaining two outputs calling the previous function
    scode,clacc = getCloudAccounts(vraHost,vraToken)
    # this one is interesting!
    # clacc is a List of Python objects, like that
    # [ {"name": "a", "id": "00001", "myprop": "whatever"}, {"name": "b", "id": "00002", "myprop": "no no no"}]
    # I *somehow* (external knowledge) know that there is *exactly one* member of this list whose 'name' property is equal to my 'caname' input's value
    # I need to get the corresponding 'id' property for this list member
    # So, first I create a 'derivative' list that only contains the member(s) of the original one whose 'name' property matches
    # then I take this unnamed list's first (and only) member
    # and I get its 'id' property
    caid = [x for x in clacc if x['name'] == caname][0]['id']
    # another, less cryptic way would be
    intermediatelist = [x for x in clacc if x['name'] == caname]
    firstlistmember = intermediatelist[0]
    caid = firstlistmember['id']
    return caid

def getCloudAccountsByProjectId(vraHost,vraToken,prjid):
    prjurl = f"/iaas/api/projects/{prjid}"
    # getCloudZones is another 'custom' function, very similar in structure to getCloudAccounts
    sc,cz = getCloudZones(vraHost,vraToken)
    headers = {
        'accept': "application/json",
        'content-type': "application/json",
        'authorization': vraToken
    }
    # here I need to return a list of CloudZones belonging to a Project with a specific project ID
    # I can't assume that there will be *only one* Cloud Zone per Project, so I can't use the previous approach
    # I create an empty list
    caurls = []
    # cycle over the input list
    for x in cz:
        # get the CloudZone's project reference
        for y in x['_links']['projects']['hrefs']:
            # if it's equal to my input project
            if y == prjurl:
                # add a member to the (previously empty) list, containing *only* the value of the subproperty that I need
                # this member won't be a 'composite' object anymore, only a string containing an URL
                caurls.append(x['_links']['cloud-account']['href'])
    # another empty list
    caobjects = []
    # cycle over the list of urls 
    for y in caurls:
        calledUrl = f"https://{vraHost}{y}"
        ca = requests.get(calledUrl, headers=headers, verify=False)
        caJson = ca.json()
        # this time I'm adding new members containining a whole 'CloudAccount' object, as obtained by the REST call
        caobjects.append(caJson)
    return caobjects
