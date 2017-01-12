###############################################################################
#
#            Simple Spirent TestCenter Traffic Example for Python
#                         by Spirent Communications
#
#   Date: December 5, 2012
# Author: Matthew Jefferson - matt.jefferson@spirent.com
#
# Description: This is a simple traffic example that sends traffic between two
#              Spirent TestCenter ports.
#
###############################################################################

###############################################################################
# Copyright (c) 2012 SPIRENT COMMUNICATIONS OF CALABASAS, INC.
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
####    Procedures
####
###############################################################################
def GetValidResultPaths(databasefilename):
    # Return a list of valid ResultPaths for the specified database.
    try:
        stc.perform("QueryResult", DatabaseConnectionString=databasefilename)
    except Exception, errmsgobject:
        # Convert the error message to a string.
        errmsg = str(errmsgobject)

    # Remove the extra "filler" from the error message, leaving only the valid result paths.
    errmsg = re.sub("in perform: no resultpath given: valid resultpaths are ", "", errmsg)
    # Remove all of the commas.
    errmsg = re.sub(",", "", errmsg)
    # Lastly, get rid of the " and"
    errmsg = re.sub(" and", "", errmsg)

    return str(errmsg).split(" ")

###############################################################################
####
####    Global variables
####
###############################################################################

# Specify the labserver IP address if you want to use it. Specify an empty
# string to just connect to the hardware directly.
#labserverip = '192.168.130.135'
labserverip = ''

# Specify the "TCC" configuration file to load, otherwise, the config will
# be created from scratch.
tcc_configuration = ''
#tcc_configuration = ''

# Learning Mode can be L2 or L3.
learning_mode = 'L2'

port_traffic1_location   = '//10.140.99.120/1/1'
port_traffic2_location   = '//10.140.99.121/1/1'

result_filename = "results.db"

###############################################################################
####
####    Main
####
###############################################################################

print "Loading libraries..."

import sys
import time
import re
import os.path
import pdb

# This is for training only...
pdb.set_trace()

# Point to the StcPython.py file in your Spirent TestCenter installation.
# You first need to either set the environment variable "STC_PRIVATE_INSTALL_DIR",
# or change the StcPython.py file ("STC_PRIVATE_INSTALL_DIR") to point to your
# installation.
# eg: os.environ['STC_PRIVATE_INSTALL_DIR'] = '/home/mjefferson/spirent/stc/stc4.59/'

print "Loading the Spirent TestCenter API..."
sys.path.append('/home/mjefferson/spirent/stc/stc4.59/API/Python')
from StcPython import StcPython
stc = StcPython()

# Instruct the API to not display all commands to STDOUT.
stc.config("AutomationOptions", logTo="stcapi.log", logLevel="INFO")

if labserverip:
    print 'Connecting to Lab Server'
    stc.perform("CSTestSessionConnect",
                 host=labserverip,
                 TestSessionName="Training",
                 OwnerId="matt",
                 CreateNewTestSession="true")

    # Terminate the Lab Server session when the last client disconnects.
    stc.perform("TerminateBll", TerminateType="ON_LAST_DISCONNECT")

if tcc_configuration:
    print "Loading TCC configuration ", tcc_configuration, ' loading it now'

    stc.perform("LoadFromDatabaseCommand", DatabaseConnectionString=tcc_configuration)

    # Re-enable logging.
    stc.config("AutomationOptions", logTo="stcapi.log", logLevel="INFO")

    project = stc.get("system1", "children-project")

    print "Project = ", project

    # This is an example of DDN notation.
    ports = stc.get("system1.project", "children-port").split(" ")


    #if stc.get("system1.project", "children-port") != "":
    #    stc.config("system1.project.port(3)", name="blaw")

    port_traffic1   = ports[0]
    port_traffic2   = ports[1]

    # Find the Emulated Devices with the names "Traffic1" and "Traffic2".
    result = stc.perform("GetObjects", ClassName="EmulatedDevice", Condition="name = 'Traffic1'")
    ed_traffic1 = result['ObjectList']

    result = stc.perform("GetObjects", ClassName="EmulatedDevice", Condition="name = 'Traffic2'")
    ed_traffic2 = result['ObjectList']
else:
    # Create the configuration from scratch.
    print "Creating the configuration from scratch..."
    project = stc.get("system1", "children-project")

    port_traffic1   = stc.create("port", under=project)
    port_traffic2   = stc.create("port", under=project)

    # Create the emulated devices and their interfaces...

    ed_traffic1   = stc.create("EmulatedDevice", under=project, AffiliatedPort=port_traffic1)
    eth2 = stc.create("EthIIIf", under=ed_traffic1)

    # NOTE: Dashes ("-") are not allowed in function argument names. We need to pass the arguments as
    #       a dictionary instead.

    kwargs = {"StackedOnEndpoint-targets":eth2, "Address":"1.1.1.2", "Gateway":"1.1.1.1"}
    ip2  = stc.create("Ipv4If",  under=ed_traffic1, **kwargs)
    del kwargs
    stc.config(ed_traffic1, TopLevelIf=ip2, primaryif=ip2)

    ed_traffic2   = stc.create("EmulatedDevice", under=project, AffiliatedPort=port_traffic2)
    eth3 = stc.create("EthIIIf", under=ed_traffic2)
    kwargs = {"StackedOnEndpoint-targets":eth3, "Address":"2.1.1.2", "Gateway":"2.1.1.1"}
    ip3  = stc.create("Ipv4If",  under=ed_traffic2, **kwargs)
    del kwargs
    stc.config(ed_traffic2, TopLevelIf=ip3, primaryif=ip3)

pdb.set_trace()

# Just display the port locations:
for port in stc.get("system1.project", "children-port").split(" "):
    print "Port Location ", stc.get(port, "location")

# Map the ports to the correct hardware.
stc.config(port_traffic1,   location=port_traffic1_location)
stc.config(port_traffic2,   location=port_traffic2_location)

# Set the load on both ports.
stc.config(port_traffic1 + ".generator.generatorconfig", fixedload=1000, loadunit="FRAMES_PER_SECOND")
stc.config(port_traffic2 + ".generator.generatorconfig", fixedload=1000, loadunit="FRAMES_PER_SECOND")

# Add a bound streamblock from port_traffic1 to port_traffic2. Notice how we are "binding" the 
# streamblock to the Emulated Device's IPv4 interface objects.
# If we were in an L2 environment, you would bind to the ethernet interface objects instead.
streamblock1 = stc.create("StreamBlock", under=port_traffic1, srcbinding=stc.get(ed_traffic1, "children-ipv4if"), dstbinding=stc.get(ed_traffic2, "children-ipv4if"))

pdb.set_trace()

print "Subscribing to results..."
# Results are also stored in objects. Where these objects are located varies for each result type.

# Port results. These result objects are stored under the generator and analyzer objects.
stc.subscribe(Parent=project, ConfigType="Generator", resulttype="GeneratorPortResults")
stc.subscribe(Parent=project, ConfigType="Analyzer",  resulttype="AnalyzerPortResults")

# Stream Results. These result objects are stored under the StreamBlock objects.
rds = stc.subscribe(Parent=project, ConfigType="StreamBlock", resulttype="TxStreamResults")
stc.create("ResultQuery", under=rds, ResultRootList=project, ConfigClassId="StreamBlock", ResultClassId="RxStreamSummaryResults") 


print "Saving configuration..."
stc.perform("SaveToTcc", config="system1", filename="traffic.tcc")

# Connect to the hardware.
stc.perform("AttachPorts", AutoConnect="true", PortList=stc.get("system1.project", "children-port"))
stc.apply

pdb.set_trace()

if learning_mode == "L2":
    print "Starting L2 traffic learning..."
    stc.perform("L2LearningStartCommand", HandleList=port_traffic1 + " " + port_traffic2)
else:
    print "Starting L3 ARP..."
    stc.perform("ArpNdStartOnAllStreamBlocksCommand", PortList=port_traffic1 + " " + port_traffic2)

# If the GeneratorList argument is not specified, then all generators is assumed.
stc.perform("GeneratorStartCommand")

# Grab some real-time stats.
for i in range(15):
    # DDN notation.
    txrate = stc.get(port_traffic1 + ".Generator.GeneratorPortResults", "GeneratorFrameRate")
    rxrate = stc.get(port_traffic2 + ".Analyzer.AnalyzerPortResults",   "SigFrameRate")

    print "TxRate=", txrate, " RxRate=", rxrate

    time.sleep(1)

pdb.set_trace()

print "Stopping traffic..."
stc.perform("GeneratorStopCommand", GeneratorList=port_traffic1)

# Allow a little time for the counters to stabilize.
time.sleep(2)

# Now display the stream counters.
txresulthandle = stc.get(streamblock1, "children-TxStreamResults")
rxresulthandle = stc.get(streamblock1, "children-RxStreamSummaryResults")
txframes = stc.get(txresulthandle, "FrameCount")
rxframes = stc.get(rxresulthandle, "FrameCount")

print "Stream Results: TxCount=", txframes, " RxCount=", rxframes

# Save the results to a sqlite database.
result_filename = os.path.abspath(result_filename)

print "Saving results to ", result_filename
stc.perform("SaveResult", CollectResult="TRUE",
                          SaveDetailedResults="TRUE",
                          DatabaseConnectionString=result_filename,
                          OverwriteIfExist="TRUE")


pdb.set_trace()

# Display all available result views.
for resultpath in GetValidResultPaths(result_filename):    
    try:
        result = stc.perform("QueryResult", DatabaseConnectionString=result_filename, ResultPath=resultpath)
        print "ResultPath=", resultpath
        print result['Columns']
        print result['Output']
        print "\n"
    except:
        pass

print "Done!"
exit()