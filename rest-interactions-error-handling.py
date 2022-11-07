import json
import sys
import requests
from requests.auth import HTTPBasicAuth
from requests.exceptions import HTTPError
from requests.exceptions import RequestException
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def lcmLogin(lcmhost,username,password):
  """ Returns API token (a string)
      The token is passed back in response header
      along with other informations that have to be discarded
      Set-Cookie: JSESSIONID=DCB0CE82925D3AE8F878B30AEED75E52; Path=/; HttpOnly; Secure; HttpOnly; SameSite=Lax
      We need only the JSESSIONID part
      UPDATE: 2022-11-04 this mechanism doesn't work anymore
  """
  authUrl=f"https://{lcmhost}/lcm/authzn/api/login"
  try:
      response = requests.post(authUrl, verify=False, auth=HTTPBasicAuth(username,password))
      response.raise_for_status()
  except HTTPError as e:
      print(e, file=sys.stderr)
      print("ERROR: check credentials!")
  except RequestException as e:
      print(e, file=sys.stderr)
  return response.headers['Set-Cookie'].split('; ')[0]

def getAllDatacenters(lcmhost,username,password):
  """ returns all Datacenters (a list of objects)
      or an empty list
  """
  dcUrl = f"https://{lcmhost}/lcm/lcops/api/v2/datacenters"
  headers = {
      'accept': "application/json",
      'content-type': "application/json"
  }
  try:
      response = requests.get(dcUrl, verify=False, headers=headers, auth=HTTPBasicAuth(username,password))
      response.raise_for_status()
  except HTTPError as e:
      print(e, file=sys.stderr)
      print("ERROR:",response.json())
      return []
  except RequestException as e:
      print(e, file=sys.stderr)
      return []
  return response.json()

def getDatacenterIdByName(lcmhost,username,password,dcname):
  """ returns datacenter ID (a string) 
      or null (None in Python) when a DC named dcname isn't found
      I could have replaced the last line with 'pass'
      (have the same effect)
      but this way I'm explicitly returning something
  """
  alldcs=getAllDatacenters(lcmhost,username,password)
  if len(alldcs) != 0:
      desireddc=[x for x in alldcs if x['dataCenterName'] == dcname]
      if len(desireddc) == 1:
          return desireddc[0]['dataCenterVmid']
  return None

def getAllVcentersByDatacenterId(lcmhost,username,password,dcid):
  """ returns all vCenters under a specific Datacenter (a list)
      or an empty list 
  """
  vcUrl=f"https://{lcmhost}/lcm/lcops/api/v2/datacenters/{dcid}/vcenters"
  headers = {
      'accept': "application/json",
      'content-type': "application/json"
  }
  try:
      response = requests.get(vcUrl, verify=False, headers=headers, auth=HTTPBasicAuth(username,password))
      response.raise_for_status()
  except HTTPError as e:
      print(e, file=sys.stderr)
      print("ERROR:",response.json())
      return []
  except RequestException as e:
      print(e, file=sys.stderr)
      return []
  return response.json()

def getVcenterByNameAndDatacenterId(lcmhost,username,password,dcid,vcname):
  """ returns an object containing only vRSLCM-related attributes
      or None, in case of error
  """
  vcUrl=f"https://{lcmhost}/lcm/lcops/api/v2/datacenters/{dcid}/vcenters/{vcname}"
  headers = {
      'accept': "application/json",
      'content-type': "application/json"
  }
  try:
      response = requests.get(vcUrl, verify=False, headers=headers, auth=HTTPBasicAuth(username,password))
      response.raise_for_status()
  except HTTPError as e:
      print(e, file=sys.stderr)
      print("ERROR:",response.json())
      return None,None
  except RequestException as e:
      print(e, file=sys.stderr)
      return None,None 
  subset={}
  responseJson=response.json()
  # {
  #   "vCenterHost": "vcenter-1.example.com",
  #   "vCenterName": "vCenter-1",
  #   "vcPassword": "locker:password:<vmid>:<alias>",
  #   "vcUsedAs": "MANAGEMENT",
  #   "vcUsername": "administrator@vsphere.local"
  # }
  subset['vCenterHost']=responseJson['vCenterHost']
  subset['vCenterName']=responseJson['vCenterName']
  subset['vcPassword']=responseJson['vcPassword']
  subset['vcUsedAs']=responseJson['vcUsedAs']
  subset['vcUsername']=responseJson['vcUsername']
  return subset

def setVcenterProperties(lcmhost,username,password,dcid,vcname,dto):
  """ returns the request ID (a string)
      or None in case of some failure
  """
  vcUrl=f"https://{lcmhost}/lcm/lcops/api/v2/datacenters/{dcid}/vcenters/{vcname}"
  headers = {
      'accept': "application/json",
      'content-type': "application/json"
  }
  # from dict to JSON
  data=json.dumps(dto)
  try:
      response = requests.put(vcUrl, verify=False, headers=headers, auth=HTTPBasicAuth(username,password),data=data)
      response.raise_for_status()
  except HTTPError as e:
      print(e, file=sys.stderr)
      print("ERROR:",response.json())
      return None
  except RequestException as e:
      print(e, file=sys.stderr)
      return None
  return response.json()['requestId']
