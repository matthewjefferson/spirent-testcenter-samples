from __future__ import print_function

import sys
import time
import os.path
import re


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



print("Loading the Spirent TestCenter API...")
#sys.path.append('/home/mjefferson/spirent/stc/stc4.66/API/Python')
sys.path.append('C:/Program Files (x86)/Spirent Communications/Spirent TestCenter 4.66/Spirent TestCenter Application/API/Python')
                 
from StcPython import StcPython
stc = StcPython()

labserverip = "192.168.130.207"
sessionname = "test"
username = "mjefferson"

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