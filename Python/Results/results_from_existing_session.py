###############################################################################
#
#              Pulling Results from an Existing Lab Server Session
#                         by Spirent Communications
#
#   Date: September 29, 2016
# Author: Matthew Jefferson - matt.jefferson@spirent.com
#
# Description: This example demonstrates how to connect to an existing Lab
#              Server session and extract the stats.
#
###############################################################################

###############################################################################
# Copyright (c) 2016 SPIRENT COMMUNICATIONS OF CALABASAS, INC.
# All Rights Reserved
#
#                SPIRENT COMMUNICATIONS OF CALABASAS, INC.
#                            LICENSE AGREEMENT
#
#  By accessing or executing this software, you agree to be bound by the terms
#  of this agreement.
#
# Redistribution and use of this software in source and binary forms, with or
# without modification, are permitted provided that the following conditions
# are met:
#  1. Redistribution of source code must retain the above copyright notice,
#     this list of conditions and the following disclaimer.
#  2. Redistribution's in binary form must reproduce the above copyright notice.
#     This list of conditions and the following disclaimer in the documentation
#     and/or other materials provided with the distribution.
#  3. Neither the name SPIRENT, SPIRENT COMMUNICATIONS, SMARTBITS, nor the names
#     of its contributors may be used to endorse or promote products derived
#     from this software without specific prior written permission.
#
# This software is provided by the copyright holders and contributors [as is]
# and any express or implied warranties, including, but not limited to, the
# implied warranties of merchantability and fitness for a particular purpose
# are disclaimed. In no event shall the Spirent Communications of Calabasas,
# Inc. Or its contributors be liable for any direct, indirect, incidental,
# special, exemplary, or consequential damages (including, but not limited to,
# procurement of substitute goods or services; loss of use, data, or profits;
# or business interruption) however caused and on any theory of liability,
# whether in contract, strict liability, or tort (including negligence or
# otherwise) arising in any way out of the use of this software, even if
# advised of the possibility of such damage.
#
###############################################################################

# For Python 2.x compatibility (use Python3 syntax in Python2.7).
from __future__ import print_function

# This is the only module that is required by the Spirent TestCenter API.
import sys

import time
import os.path
import re

# Point to the StcPython.py file in your Spirent TestCenter installation.
# You first need to either set the environment variable "STC_PRIVATE_INSTALL_DIR",
# or change the StcPython.py file ("STC_PRIVATE_INSTALL_DIR") to point to your
# installation.
# eg: os.environ['STC_PRIVATE_INSTALL_DIR'] = '/home/mjefferson/spirent/stc/stc4.59/'

print("Loading the Spirent TestCenter API...")
#sys.path.append('/home/mjefferson/spirent/stc/stc4.66/API/Python')
sys.path.append('c:/program files (x86)/Spirent Communications/Spirent TestCenter 4.66/Spirent TestCenter Application/API/Python')
from StcPython import StcPython
stc = StcPython()


###############################################################################
####
####    Global variables
####
###############################################################################

labserverip = '192.168.130.207'
sessionname = 'test'
username    = 'mjefferson'


###############################################################################
####
####    Procedures
####
###############################################################################
def getRDS(resultclass):
    # Find the ResultDataSet object for the specified ResultClass.
    # Delete any existing RDS objects that are not in use.    
    targetrds = ""
    project = stc.get("system1", "children-project")

    for rds in stc.get(project, "children-ResultDataSet").split():
        for rq in stc.get(rds, "children-ResultQuery").split():

            resultclassid = stc.get(rq, "ResultClassId")

            if resultclassid.lower() == resultclass.lower():
                # We found the right resultclass. Make sure it's in use.
                if stc.get(rds, "ResultHandleList") == "":
                    # This RDS is not in use. Delete it.
                    stc.delete(rds)
                    break
                else:
                    # This is what we are looking for.
                    targetrds = rds
                    break
        if targetrds != "":
            break

    return targetrds

###############################################################################
####
####    Main
####
###############################################################################

print("Connecting to Lab Server")
stc.perform("CSTestSessionConnect", host=labserverip,
                                    TestSessionName=sessionname,
                                    OwnerId=username,
                                    CreateNewTestSession="false")

project = stc.get("system1", "children-project")


# Subscribe to port results.
portrds = getRDS("GeneratorPortResults")

if portrds == "":
    print("Subscribing to port results...")
    # Port results. These result objects are stored under the generator and analyzer objects.
    rds = stc.subscribe(Parent=project, ConfigType="Generator", resulttype="GeneratorPortResults")
    stc.create("ResultQuery", under=rds, ResultRootList=project, ConfigClassId="Analyzer", ResultClassId="AnalyzerPortResults")

# Subscribe to stream results.
streamrds = getRDS("TxStreamResults")

if streamrds == "":
    print("Subscribing to stream results...")
    streamrds = stc.subscribe(Parent=project, ConfigType="StreamBlock", resulttype="TxStreamResults", RecordsPerPage=256)
    stc.create("ResultQuery", under=streamrds, ResultRootList=project, ConfigClassId="streamblock", ResultClassId="rxstreamsummaryresults")


# Grab some real-time stats.
for i in range(10):

    for port in stc.get(project, "children-port").split():
        # Display the port rates...
        print("Port Results")
        txframerate = stc.get(port + ".Generator.GeneratorPortResults", "GeneratorFrameRate")
        txl1bitrate = stc.get(port + ".Generator.GeneratorPortResults", "L1BitRate")
        txl2bitrate = stc.get(port + ".Generator.GeneratorPortResults", "GeneratorBitRate")

        rxframerate = stc.get(port + ".Analyzer.AnalyzerPortResults", "SigFrameRate")
        rxl1bitrate = stc.get(port + ".Analyzer.AnalyzerPortResults", "L1BitRate")
        rxl2bitrate = stc.get(port + ".Analyzer.AnalyzerPortResults", "TotalBitRate")

        print(port + " TxFrameRate=" + txframerate + " TxL1BitRate=" + txl1bitrate + " TxL2BitRate=" + txl2bitrate)
        print(port + " RxFrameRate=" + rxframerate + " RxL1BitRate=" + rxl1bitrate + " RxL2BitRate=" + rxl2bitrate)

        # Display the stream rates...
        print("")
        print("Stream Results")
        totalpages = int(stc.get(streamrds, "TotalPageCount"))    
        for page in range(1, totalpages+1):    
            print("Page " + str(page) + " of " + str(totalpages))
            stc.config(streamrds, PageNumber=page)
            stc.apply()
            # You must wait a certain amount of time for the result objects to be populated.
            time.sleep(4)

            # Now grab the results.    
            for txresult in stc.get(streamrds, "ResultHandleList").split():
                regex = re.compile("txstreamresults.")
                if re.match(regex, txresult):
                    rxresult = stc.get(txresult, "associatedresult-Targets")

                    streamblock = stc.get(txresult, "parent")

                    txframerate = stc.get(txresult, "FrameRate")
                    txl1bitrate = stc.get(txresult, "L1BitRate")
                    txl2bitrate = stc.get(txresult, "BitRate")

                    rxframerate = stc.get(rxresult, "FrameRate")
                    rxl1bitrate = stc.get(rxresult, "L1BitRate")
                    rxl2bitrate = stc.get(rxresult, "BitRate")                

                    print(port + " " + streamblock + " TxFrameRate=" + txframerate + " TxL1BitRate=" + txl1bitrate + " TxL2BitRate=" + txl2bitrate)
                    print(port + " " + streamblock + " RxFrameRate=" + rxframerate + " RxL1BitRate=" + rxl1bitrate + " RxL2BitRate=" + rxl2bitrate)

        print()

    time.sleep(1)

print("Done!")
exit()