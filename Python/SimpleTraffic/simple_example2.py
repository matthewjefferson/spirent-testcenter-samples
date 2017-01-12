###############################################################################
#
#            Another Simple Spirent TestCenter Traffic Example for Python
#                         by Spirent Communications
#
#   Date: August 15, 2016
# Author: Matthew Jefferson - matt.jefferson@spirent.com
#
# Description: This is a simple traffic example that sends traffic from four
#              10GigE ports and returns the L1/L2 port rate stats.
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

# Point to the StcPython.py file in your Spirent TestCenter installation.
# You first need to either set the environment variable "STC_PRIVATE_INSTALL_DIR",
# or change the StcPython.py file ("STC_PRIVATE_INSTALL_DIR") to point to your
# installation.
# eg: os.environ['STC_PRIVATE_INSTALL_DIR'] = '/home/mjefferson/spirent/stc/stc4.59/'

print("Loading the Spirent TestCenter API...")
sys.path.append('/home/mjefferson/spirent/stc/stc4.69/API/Python')
from StcPython import StcPython
stc = StcPython()


###############################################################################
####
####    Global variables
####
###############################################################################

# Specify the labserver IP address if you want to use it. Specify an empty
# string to just connect to the hardware directly.
#labserverip = '192.168.130.135'
labserverip     = ''
locationlist    = ['10.140.96.81/7/1', '10.140.96.81/7/2', '10.140.96.81/7/3', '10.140.96.81/7/4']
learningmode    = "L2"
resultsfilename = "results.db"

###############################################################################
####
####    Main
####
###############################################################################

if labserverip:
    # If you are using a lab server, connect to it now.
    print("Connecting to Lab Server")
    stc.perform("CSTestSessionConnect", host=labserverip,
                                        TestSessionName="sample",
                                        CreateNewTestSession="true")

    # Terminate the Lab Server session when the last client disconnects.
    stc.perform("TerminateBll", TerminateType="ON_LAST_DISCONNECT")

# Instruct the API to not display all commands to STDOUT.
stc.config("AutomationOptions", logTo="stcapi.log", logLevel="INFO")

# Save the project handle for later. This is not strictly necessary.
project = stc.get("system1", "children-project")

# Create a port for each location specified.
for location in locationlist:
    # If you are connecting to a single-speed port, this is all you need to do.
    # If you are connecting to a multi-speed port, you may need to create the appropriate phy object (e.g., Ethernet10GigFiber).
    port = stc.create("port", under=project, location=location)

    # Configure the port rate to 100% line-rate.
    stc.config(port + ".generator.generatorconfig", fixedload=100, loadunit="PERCENT_LINE_RATE")

    # Create a raw streamblock. Headers include: EthernetII, Vlan, IPv4, IPv6, Mpls, Tcp, UDP, PPP, GRE, etc.
    streamblock = stc.create("StreamBlock", under=port, FrameConfig="EthernetII IPv4")
    # This get is required to update the API.
    stc.get(streamblock)
    stc.config(streamblock + ".ethernet:EthernetII", SrcMac="00:00:00:00:00:01")
    stc.config(streamblock + ".ipv4:IPv4", SourceAddr="1.1.1.2", DestAddr="2.1.1.2")
    

print("Subscribing to results...")
# Port results. These result objects are stored under the generator and analyzer objects.
rds = stc.subscribe(Parent=project, ConfigType="Generator", resulttype="GeneratorPortResults")
stc.create("ResultQuery", under=rds, ResultRootList=project, ConfigClassId="Analyzer", ResultClassId="AnalyzerPortResults")
#stc.subscribe(Parent=project, ConfigType="Analyzer",  resulttype="AnalyzerPortResults")

# Stream Results.
streamrds = stc.subscribe(Parent=project, ConfigType="StreamBlock", resulttype="TxStreamResults", RecordsPerPage=256)
stc.create("ResultQuery", under=streamrds, ResultRootList=project, ConfigClassId="streamblock", ResultClassId="rxstreamsummaryresults")


# OPTIONAL: Saving the configuration...
print("Saving configuration...")
stc.perform("SaveToTcc", config="system1", filename="traffic.tcc")

# Connect to the hardware.
print("Connecting to the hardware...")
stc.perform("AttachPorts", AutoConnect="true", PortList=stc.get("system1.project", "children-port"))
stc.apply


if learningmode == "L2":
    print("Starting L2 traffic learning...")    
    stc.perform("L2LearningStartCommand")
else:
    print("Starting L3 ARP...")
    stc.perform("ArpNdStartOnAllStreamBlocksCommand")

# If the GeneratorList argument is not specified, then all generators is assumed.
stc.perform("GeneratorStartCommand")

time.sleep(10)

# Grab some real-time stats.
for i in range(10):

    for port in stc.get(project, "children-port").split():
        # Display the port rates...
        txframerate = stc.get(port + ".Generator.GeneratorPortResults", "GeneratorFrameRate")
        txl1bitrate = stc.get(port + ".Generator.GeneratorPortResults", "L1BitRate")
        txl2bitrate = stc.get(port + ".Generator.GeneratorPortResults", "GeneratorBitRate")

        rxframerate = stc.get(port + ".Analyzer.AnalyzerPortResults", "SigFrameRate")
        rxl1bitrate = stc.get(port + ".Analyzer.AnalyzerPortResults", "L1BitRate")
        rxl2bitrate = stc.get(port + ".Analyzer.AnalyzerPortResults", "TotalBitRate")

        print(port + " TxFrameRate=" + txframerate + " TxL1BitRate=" + txl1bitrate + " TxL2BitRate=" + txl2bitrate)
        print(port + " RxFrameRate=" + rxframerate + " RxL1BitRate=" + rxl1bitrate + " RxL2BitRate=" + rxl2bitrate)

        # Display the stream rates...
        for streamblock in stc.get(port, "children-streamblock").split():
            txresulthandle = stc.get(streamblock, "children-TxStreamResults")            

            if txresulthandle != "":
                rxresulthandle = stc.get(txresulthandle, "associatedresult-Targets")

                txframerate = stc.get(txresulthandle, "FrameRate")
                txl1bitrate = stc.get(txresulthandle, "L1BitRate")
                txl2bitrate = stc.get(txresulthandle, "BitRate")

                rxframerate = stc.get(rxresulthandle, "FrameRate")
                rxl1bitrate = stc.get(rxresulthandle, "L1BitRate")
                rxl2bitrate = stc.get(rxresulthandle, "BitRate")                

                print(port + " " + streamblock + " TxFrameRate=" + txframerate + " TxL1BitRate=" + txl1bitrate + " TxL2BitRate=" + txl2bitrate)
                print(port + " " + streamblock + " RxFrameRate=" + rxframerate + " RxL1BitRate=" + rxl1bitrate + " RxL2BitRate=" + rxl2bitrate)

        print()

    time.sleep(1)

print("Stopping traffic...")
stc.perform("GeneratorStopCommand")

# Allow a little time for the counters to stabilize.
time.sleep(2)

# OPTIONAL: Save the results to a sqlite database.
resultsfilename = os.path.abspath(resultsfilename)
print("Saving results to " + resultsfilename)
stc.perform("SaveResult", CollectResult="TRUE",
                          SaveDetailedResults="TRUE",
                          DatabaseConnectionString=resultsfilename,
                          OverwriteIfExist="TRUE")

print("Done!")
exit()