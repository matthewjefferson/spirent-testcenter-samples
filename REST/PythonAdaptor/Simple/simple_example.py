###############################################################################
#
#       Simple Spirent TestCenter Traffic Example for Python using REST
#                         by Spirent Communications
#
#   Date: April 19, 2016
# Author: Matthew Jefferson - matt.jefferson@spirent.com
#
# Description: This is a simple Python traffic example that sends traffic 
#              between two Spirent TestCenter ports.
#              The REST API in the back-end.
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

###############################################################################
####
####    Global variables
####
###############################################################################

# The Lab Server is required when using the REST API.
labserverip = '192.168.130.207'

# Learning Mode can be L2 or L3.
learning_mode = 'L2'

port_traffic1_location   = '//10.140.96.81/7/1'
port_traffic2_location   = '//10.140.96.81/7/2'

result_filename = "results.db"

###############################################################################
####
####    Main
####
###############################################################################

print("Loading libraries...")

import sys
import time
import re
import os.path
import os

print("Loading the Spirent TestCenter API...")
#from stcrestclient import stchttp
#stc = stchttp.StcHttp(labserverip)
#sid = stc.new_session('mjefferson', 'PythonTest', kill_existing=True)

os.environ['STC_SESSION_TERMINATE_ON_DISCONNECT'] = "1"


from stcrestclient.stcpythonrest import StcPythonRest as StcPython
stc = StcPython()

#stc._new_session(server=labserverip, session_name="PythonRest", user_name="mjefferson", kill_existing=True)

stc.perform("CsTestSessionConnect", host=labserverip, createnewtestsession=True, testsessionname="blaw", ownerid="mjefferson")



# Create the configuration from scratch.
print("Creating the configuration from scratch...")
project = stc.get("system1", "children-project")

port_traffic1   = stc.create("port", under=project)
port_traffic2   = stc.create("port", under=project)

# Create the emulated devices and their interfaces...
result = stc.perform("DeviceCreate", ParentList=project, DeviceType="Host", IfStack="Ipv4If EthIIIf", IfCount="1 1", Port=port_traffic1)
ed_traffic1 = result["ReturnList"]
stc.config(ed_traffic1 + ".ipv4if", Address="1.1.1.2", Gateway="1.1.1.1")

result = stc.perform("DeviceCreate", ParentList=project, DeviceType="Host", IfStack="Ipv4If EthIIIf", IfCount="1 1", Port=port_traffic2)
ed_traffic2 = result["ReturnList"]    
stc.config(ed_traffic2 + ".ipv4if", Address="2.1.1.2", Gateway="2.1.1.1")

# Map the ports to the correct hardware locations.
stc.config(port_traffic1, location=port_traffic1_location)
stc.config(port_traffic2, location=port_traffic2_location)

# Set the load on both ports.
stc.config(port_traffic1 + ".generator.generatorconfig", fixedload=100, loadunit="FRAMES_PER_SECOND")
stc.config(port_traffic2 + ".generator.generatorconfig", fixedload=100, loadunit="FRAMES_PER_SECOND")

# Add a bound streamblock from port_traffic1 to port_traffic2. Notice how we are "binding" the 
# streamblock to the Emulated Device's IPv4 interface objects.
# If we were in an L2 environment, you would bind to the ethernet interface objects instead.
streamblock1 = stc.create("StreamBlock", under=port_traffic1, srcbinding=stc.get(ed_traffic1, "children-ipv4if"), dstbinding=stc.get(ed_traffic2, "children-ipv4if"))

print("Subscribing to results...")
# Results are also stored in objects. Where these objects are located varies for each result type.

# Port results. These result objects are stored under the generator and analyzer objects.
stc.subscribe(Parent=project, ConfigType="Generator", resulttype="GeneratorPortResults")
stc.subscribe(Parent=project, ConfigType="Analyzer",  resulttype="AnalyzerPortResults")

# Stream Results. These result objects are stored under the StreamBlock objects.
rds = stc.subscribe(Parent=project, ConfigType="StreamBlock", resulttype="TxStreamResults")
stc.create("ResultQuery", under=rds, ResultRootList=project, ConfigClassId="StreamBlock", ResultClassId="RxStreamSummaryResults") 
#stc.subscribe(Parent=project, ConfigType="StreamBlock", resulttype="RxStreamSummaryResults")

print("Saving configuration...")
stc.perform("SaveToTcc", config="system1", filename="traffic.tcc")

# Connect to the hardware.
stc.perform("AttachPorts", AutoConnect="true", PortList=stc.get("system1.project", "children-port"))
stc.apply

if learning_mode == "L2":
    print("Starting L2 traffic learning...")
    stc.perform("L2LearningStartCommand", HandleList=port_traffic1 + " " + port_traffic2)
else:
    print("Starting L3 ARP...")
    stc.perform("ArpNdStartOnAllStreamBlocksCommand", PortList=port_traffic1 + " " + port_traffic2)

# If the GeneratorList argument is not specified, then all generators is assumed.
stc.perform("GeneratorStartCommand")

# Grab some real-time stats.
for i in range(15):
    # DDN notation.
    txrate = stc.get(port_traffic1 + ".Generator.GeneratorPortResults", "GeneratorFrameRate")
    rxrate = stc.get(port_traffic2 + ".Analyzer.AnalyzerPortResults",   "SigFrameRate")

    print("TxRate=", txrate, " RxRate=", rxrate)

    time.sleep(1)

print("Stopping traffic...")
stc.perform("GeneratorStopCommand", GeneratorList=port_traffic1)

# Allow a little time for the counters to stabilize.
time.sleep(2)

# Now display the stream counters.
txresulthandle = stc.get(streamblock1, "children-TxStreamResults")
rxresulthandle = stc.get(streamblock1, "children-RxStreamSummaryResults")
txframes = stc.get(txresulthandle, "FrameCount")
rxframes = stc.get(rxresulthandle, "FrameCount")

print("Stream Results: TxCount=", txframes, " RxCount=", rxframes)

# Save the results to a sqlite database.
#result_filename = os.path.abspath(result_filename)
result_filename = "myresults.db"

print("Saving results to ", result_filename)
stc.perform("SaveResult", CollectResult="TRUE",
                          SaveDetailedResults="TRUE",
                          DatabaseConnectionString=result_filename,
                          OverwriteIfExist="TRUE")


stc.perform("cssynchronizefiles")

import pdb
pdb.set_trace()

print("Done!")


exit()