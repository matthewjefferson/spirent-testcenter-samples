#!/usr/local/bin/python3
from __future__ import print_function

import sys
import time
import os.path
import re

os.environ['STC_SESSION_TERMINATE_ON_DISCONNECT'] = "0"
# We don't need these environment variables since we are using the new_session method.
# os.environ['STC_SERVER_ADDRESS'] = "192.168.130.192"
# os.environ['STC_SESSION_NAME'] = "demo"
sys.path.append('/Users/mjefferson/Projects/REST/Python/py-stcrestclient-1.5.0/stcrestclient')

# This is the Python adapter for the Spirent TestCenter REST API.
from stcrestclient.stcpythonrest import StcPythonRest as StcPython

# This will give us access to some commands for manipulating Lab Server sessions.
#from stcrestclient.stchttp import StcHttp as StcTool


def sbrds():
    # Find the ResultDataSet object for the StreamBlockResults.
    # Delete any existing RDS objects that are not in use.
    # Subscribe to the StreamBlockResults if they are not present.
    sbrds = ""
    project = stc.get("system1", "children-project")

    for rds in stc.get(project, "children-ResultDataSet").split():
        resultclass = stc.get(rds + ".ResultQuery", "ResultClassId")

        if resultclass == "txstreamblockresults" or resultclass == "rxstreamblockresults":
            if stc.get(rds, "ResultHandleList") == "":
                # This RDS is not in use. Delete it.
                stc.delete(rds)
            else:
                sbrds = rds
                break

    if sbrds == "":
        sbrds = stc.subscribe(Parent=project, ConfigType="StreamBlock", resulttype="TxStreamBlockResults", RecordsPerPage=7)        
        stc.create("ResultQuery", under=sbrds, ResultRootList=project, ConfigClassId="StreamBlock", ResultClassId="RxStreamBlockResults")

    return sbrds



#print("Loading the Spirent TestCenter API...")
#sys.path.append('/home/mjefferson/spirent/stc/stc4.66/API/Python')
#sys.path.append('C:/Program Files (x86)/Spirent Communications/Spirent TestCenter 4.66/Spirent TestCenter Application/API/Python')
                 
#from StcPython import StcPython
#stc = StcPython()

print("Loading the REST Python front-end...")

labserverip = "192.168.130.207"
sessionname = "test"
username = "mjefferson"

stc = StcPython()
stc.new_session(server=labserverip, session_name=sessionname, user_name=username, existing_session="join")


# Connect to an existing Lab Server session...
print("Connecting to the Lab Server...")
stc.perform("CSTestSessionConnect",
                 host=labserverip,
                 TestSessionName=sessionname,
                 OwnerId=username,
                 CreateNewTestSession="false")

project = stc.get("system1", "children-project")

# # Load from a configuration file, instead of connecting to an existing session.
# print("DEBUG ONLY!")
# stc.perform("LoadFromDatabaseCommand", DatabaseConnectionString="streamblock.tcc")
# project = stc.get("system1", "children-project")

# # Connect to the hardware.
# stc.perform("AttachPorts", AutoConnect="true", PortList=stc.get(project, "children-port"))
# stc.apply()

stc.perform("GeneratorStart")
time.sleep(5)

rds = sbrds()

for count in range(3):
    stc.perform("RefreshResultView", ResultDataSet=rds)

    pages = int(stc.get(rds, "TotalPageCount"))
    
    for page in range(1,pages + 1):
        print("Page=", page)
        stc.config(rds, PageNumber=page)
        stc.apply()
        time.sleep(1)

        # stc.perform("RefreshResultView", ResultDataSet=txrds)
        # stc.perform("RefreshResultView", ResultDataSet=rxrds)

        for result in stc.get(rds, "ResultHandleList").split():
            regex = re.compile("txstreamblockresults.")
            if re.match(regex, result):
                parent = stc.get(result, "parent")                
                rxresult = stc.get(result, "associatedresult-Targets")
                print(parent, " Tx=", stc.get(result, "FrameCount"), " Rx=", stc.get(rxresult, "FrameCount"), " Rate=", stc.get(rxresult, "FrameRate"))                
  
    time.sleep(1)