###############################################################################
#
#                      Real-time and DRV Results Example
#                         by Spirent Communications
#
#   Date: July 1, 2016
# Author: Matthew Jefferson - matt.jefferson@spirent.com
#
# Description: This is an example of how to use real-time results and Dynamic
#              Result Views (DRV).
#              Results subscription, real-time result paging and converting
#              result data into Python data structures is also covered.
#              It also shows how to connect to a Lab Server and utilize existing
#              result views.
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
from __future__ import print_function

###############################################################################
####
####    Required Modules
####
###############################################################################
import sys
import time
import os.path
# These are needed for processing the returned results.
import re
import ast 

###############################################################################
####
####    Global Variables
####
###############################################################################

# Set labserverip to "" if not connecting to an existing Lab Server session.
labserverip = "192.168.130.192"
username = "mjefferson"
sessionname = "demo"

###############################################################################
####
####    Public Functions
####
###############################################################################
def convertTclList(tcl, delimiters="\s", level=1, currentlevel=0):
    # The function converts a Tcl-based list string into a Python list.
    # It works with embedded lists, and you can set the "level" to control
    # whether nested braces are treated as lists or strings.
    # You can also change the list delimiter.

    # Start by iterating through each character in the string.
    # Identify tokens (words) and append them to the converted list.
    # If a brace or quote, single or double, is encountered, find the matching
    # end brace/quote and recurrsively call "convertTclList" to handle that substring.

    convertedlist     = []          # This is the resulting list that is returned.
    escaped           = False       # The flag is set when a backslash is detected. The following character is always treated as a string.
    token             = ""          # This is used to store each word.
    substringend      = ""          # The stores the character that indicates the end of the current substring.
    substring         = ""          
    sublevel          = 0           # The level of braces for the current character.

    # Currentlevel is an internal variable. The user should not set it, as it keeps track
    # of how many levels deep we are.
    currentlevel += 1

    # Define a regular expression to match the specified delimiters (whitespace by default).
    pattern = "[" + delimiters + "]+"

    # Iterate through each character in the string.
    for character in tcl:
        if character == "\\" and escaped == False:            
            # We have found an escaped character. Just treat it as a normal character.            
            escaped = True

        elif escaped == True:            
            # The previous character was a backslash. That means this is an escaped character, which
            # we simply add as a string.        
            escaped = False
            token += "\\" + character   

        elif (character == "\'" or character == "\"" or character == "{") and substringend == "" and token == "":
            # A new brace or quote has been found. Start constructing a substring that ends
            # when a matching brace/quote is found, and recursively pass the substring to this function.
            if character == "{":
                # We are dealing with an opening brace.
                sublevel += 1
                substringend = "}"
            else:
                # We are dealing with an opening quote.
                substringend = character

        elif character == "{" and substringend == "}":
            # We have found an embedded opening brace. 
            if sublevel > 0:
                # Do not capture the opening brace.
                substring += character
            sublevel += 1

        elif character == "}" and substringend == "}":
            # We have found a closing brace.
            sublevel -= 1
            if sublevel == 0:               
                # This is the closing brace that matching the opening brace for the current substring. 
                if currentlevel <= level:
                    # Convert the substring to a list.
                    sublist = convertTclList(substring, delimiters, level, currentlevel)
                else:
                    # Treat the substring as a...string.
                    sublist = substring    

                convertedlist.append(sublist)                

                substringend = ""
                substring    = ""
                token        = ""

            else:
                # This is the closing brace for an embedded list. Just continue adding to the substring.
                substring += character

        elif character == substringend and substringend != "":
            # We have found the closing quote for the current substring.
            if currentlevel <= level:
                # Convert the substring to a list.
                sublist = convertTclList(substring, delimiters, level, currentlevel)
            else:
                # Treat the substring as a...string.
                sublist = substring

            convertedlist.append(sublist)

            substringend = ""
            substring    = ""
            token        = ""

        elif substringend != "":
            # We are currently building a substring.
            substring += character                        

        elif re.search(pattern, character):
            # A delimiter has been detected.
            if token != "":
                value = ConvertStringToValue(token)                
                convertedlist.append(value)
                token = ""

        else:
            # Just another character for the current token.
            token += character

    if token != "":        
        # This is to add the last token to the list.
        value = ConvertStringToValue(token)
        convertedlist.append(value)

    return convertedlist

###############################################################################
####
####    Private Functions
####
###############################################################################
def ConvertStringToValue(string):
    # This function attempts to convert strings into different datatypes (int/float/etc).
    try:
        value = ast.literal_eval(string)
    except:
        value = string
    return value    

###############################################################################
####
####    Main
####
###############################################################################    

print("Loading the Spirent TestCenter API...")
sys.path.append('/home/mjefferson/spirent/stc/stc4.64/API/Python')
from StcPython import StcPython
stc = StcPython()

if labserverip != "":
    # Connect to an existing Lab Server session...
    print("Connecting to the Lab Server...")
    stc.perform("CSTestSessionConnect",
                     host=labserverip,
                     TestSessionName=sessionname,
                     OwnerId=username,
                     CreateNewTestSession="false")

    project = stc.get("system1", "children-project")
else:
    # Load from a configuration file, instead of connecting to an existing session.
    print("DEBUG ONLY!")
    stc.perform("LoadFromDatabaseCommand", DatabaseConnectionString="issue.tcc")
    project = stc.get("system1", "children-project")

    # Connect to the hardware.
    stc.perform("AttachPorts", AutoConnect="true", PortList=stc.get(project, "children-port"))
    stc.apply()


# First, find the Result Dataset objects for the various real-time result views.
portrds      = ""
streamrds    = ""
thresholdrds = ""

if labserverip != "":
    # Use this when connected to a Lab Server session...
    for rds in stc.get(project, "children-ResultDataSet").split():
        resultclass = stc.get(rds + ".ResultQuery", "ResultClassId")
        print(resultclass)
        if resultclass == "generatorportresults":
            portrds = rds
        if resultclass == "txstreamresults" or resultclass == "rxstreamsummaryresults":
            # The defaut for the GUI is 25...let's bump it up to 100.
            # The maximum is 256. To go higher, you must modify the stcbll.ini file.
            streamrds = rds
            #stc.config(streamrds, RecordsPerPage=50)
        if resultclass == "streamthresholdresults":
            thresholdrds = rds

    # Now find the Dynamic Result View objects.
    # I'm using the "GetObjects" command, however, you can also simply iterate through all DynamicResultView objects
    # to find the ones you are looking for.
    # for drv in stc.get(project, "children-DynamicResultView").split():
    #     print(stc.get(drv))

    result = stc.perform("GetObjects", ClassName="DynamicResultView", Condition="name = 'Dropped StreamsResults'")
    dropdrv = result['ObjectList']        

    result = stc.perform("GetObjects", ClassName="DynamicResultView", Condition="name = 'Dead Stream Results'")
    deaddrv = result['ObjectList']    

else:
    print("DEBUG ONLY!")
    for rds in stc.get(project, "children-ResultDataSet").split():
        stc.delete(rds)
    
    # The following code is used to subscribe to Dynamic Result Views.
    # Create the Dynamic Result Views for Dropped and Dead Streams.
    dropdrv = stc.create("DynamicResultView", under=project, ResultSourceClass="Project")
    properties = "StreamBlock.Name Port.Name StreamBlock.ActualRxPortName StreamBlock.FrameConfig.ipv4:IPv4.1.sourceAddr StreamBlock.FrameConfig.ipv4:IPv4.1.destAddr StreamBlock.FrameConfig.ethernet:EthernetII.1.srcMac StreamBlock.FrameConfig.ethernet:EthernetII.vlans.Vlan.1.id StreamBlock.TxFrameCount StreamBlock.RxSigFrameCount StreamBlock.TxFrameRate StreamBlock.RxSigFrameRate StreamBlock.DuplicateFrameCount StreamBlock.DroppedFrameCount StreamBlock.DroppedFrameDuration StreamBlock.MinLatency StreamBlock.MaxLatency StreamBlock.AvgLatency StreamBlock.IsExpected"
    conditions = "{StreamBlock.DroppedFrameCount > 0 AND StreamBlock.IsExpected = 1}" 
    stc.create("PresentationResultQuery", under=dropdrv, SelectProperties=properties, WhereConditions=conditions, FromObjects=project)
    stc.perform("SubscribeDynamicResultView", DynamicResultView=dropdrv)

    deaddrv = stc.create("DynamicResultView", under=project, ResultSourceClass="Project")
    properties = "StreamBlock.Name Port.Name StreamBlock.ActualRxPortName StreamBlock.FrameConfig.ipv4:IPv4.1.sourceAddr StreamBlock.FrameConfig.ipv4:IPv4.1.destAddr StreamBlock.FrameConfig.ethernet:EthernetII.1.srcMac StreamBlock.FrameConfig.ethernet:EthernetII.vlans.Vlan.1.id StreamBlock.TxFrameCount StreamBlock.RxSigFrameCount StreamBlock.TxFrameRate StreamBlock.RxSigFrameRate StreamBlock.DuplicateFrameCount StreamBlock.DroppedFrameCount StreamBlock.DroppedFrameDuration StreamBlock.MinLatency StreamBlock.MaxLatency StreamBlock.AvgLatency StreamBlock.IsExpected"
    conditions = "{StreamBlock.RxSigFrameCount = 0 OR StreamBlock.RxSigFrameRate = 0} {StreamBlock.IsExpected = 1}"
    stc.create("PresentationResultQuery", under=deaddrv, SelectProperties=properties, WhereConditions=conditions, FromObjects=project)
    stc.perform("SubscribeDynamicResultView", DynamicResultView=deaddrv)

    streamrds = stc.subscribe(Parent=project, ConfigType="StreamBlock", resulttype="TxStreamResults", RecordsPerPage=25)
    stc.create("ResultQuery", under=streamrds, ResultRootList=project, ConfigClassId="streamblock", ResultClassId="rxstreamsummaryresults")

    #The following code is used to subscribe to Real-time Results.
    #thresholdrds = stc.subscribe(parent=project, ResultParent=project, ConfigType="analyzer", ResultType="streamthresholdresults")

    # Port Results.
    portrds = stc.subscribe(parent=project, ConfigType="Generator", ResultType="GeneratorPortResults")    
    stc.create("ResultQuery", under=portrds, ResultRootList=project, ConfigClassId="Analyzer", ResultClassId="AnalyzerPortResults")    
    #rxportrds = stc.subscribe(parent=project, ConfigType="Analyzer",  ResultType="AnalyzerPortResults")  
    

print("PortRDS      = " + portrds)
print("StreamRDS    = " + streamrds)
print("ThresholdRDS = " + thresholdrds)
print("DropDRV      = " + dropdrv)
print("DeadDRV      = " + deaddrv)

# All changes must be applied before they can take effect.    
stc.apply()


#stc.perform("ResultsClearAllCommand")

stc.perform("GeneratorStartCommand")

time.sleep(6)

# Grab all results:
if portrds != "":
    print()
    print("Port Rates:")    
    for port in stc.get(project, "children-port").split():
        location = stc.get(port, "location")
        if stc.get(port + ".generator", "children-GeneratorPortResults") != "":
            tx = stc.get(port + ".generator.GeneratorPortResults", "GeneratorFrameRate")
            rx = stc.get(port + ".analyzer.AnalyzerPortResults",   "SigFrameRate")

            print("Port: " + location + "   TxRate=" + tx + "  RxRate=" + rx)
        else:
            print("WARNING: No port results!")

# Stop all traffic.
stc.perform("GeneratorStopCommand")

# Start/Stop traffic for individual StreamBlocks.
# Grab the stream results for all streams that are present on the current results page.
for name in ['sb 1', 'sb 2', 'sb 3', 'sb 4']:
    # Find the StreamBlock with the specified name.
    result = stc.perform("GetObjects", ClassName="StreamBlock", Condition="name = '" + name + "'")
    streamblock = result['ObjectList']

    print("StreamBlock=" + name + " Handle=" + streamblock)

    stc.perform("StreamBlockStartCommand", StreamBlockList=streamblock)

    time.sleep(5)

    stc.perform("StreamBlockStopCommand", StreamBlockList=streamblock)


if streamrds != "":
    # Grab ALL stream results on all pages.
    
    print()    

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
    
                # Find the matching Rx object.
                rxresult = stc.get(txresult, "associatedresult-Targets")

                streamid = stc.get(txresult, "StreamId")
                txcount   = stc.get(txresult, "FrameCount")
                rxcount   = stc.get(rxresult, "FrameCount")
                
                print("StreamId=" + streamid + "  TxCount=" + txcount + " RxCount=" + rxcount)

# droplist is list of dictionaries.
droplist = []
if dropdrv != "":
    stc.perform("UpdateDynamicResultView", DynamicResultView=dropdrv)
    for result in stc.get(dropdrv,"children-PresentationResultQuery").split():
        # Output the columns:
        columns = stc.get(result, 'SelectProperties').split()
        for view in stc.get(result, "children-resultviewdata").split():
            if stc.get(view, "IsDummy") != "true":
                tcldata = stc.get(view, "ResultData")
                data = convertTclList(tcldata, level=0)
                dropdict = dict(zip(columns, data))
                droplist.append(dropdict)

print()
print("DropList:")
for row in droplist:   
    streamblockname = row['StreamBlock.Name']
    dstip           = row['StreamBlock.FrameConfig.ipv4:IPv4.1.destAddr']
    txcount         = row['StreamBlock.TxFrameCount']
    dropcount       = row['StreamBlock.DroppedFrameCount']
    dropduration    = row['StreamBlock.DroppedFrameDuration']

    print("SB=" + streamblockname + " DstIP=" + dstip + " TxCount=" + str(txcount) + " DropCount=" + str(dropcount) + " DropDuration=" + str(dropduration))
             

# deadlist is a list of dictionaries.
deadlist = []
if deaddrv != "":
    stc.perform("UpdateDynamicResultView", DynamicResultView=deaddrv)
    for result in stc.get(deaddrv,"children-PresentationResultQuery").split():
        # Output the columns:
        columns = stc.get(result, 'SelectProperties').split()
        for view in stc.get(result, "children-resultviewdata").split():
            if stc.get(view, "IsDummy") != "true":
                tcldata = stc.get(view, "ResultData")
                data = convertTclList(tcldata, level=0)
                deaddict = dict(zip(columns, data))
                deadlist.append(deaddict)

print()                
print("DeadList:")
for row in deadlist:   
    streamblockname = row["StreamBlock.Name"]
    dstip           = row["StreamBlock.FrameConfig.ipv4:IPv4.1.destAddr"]
    txcount         = row["StreamBlock.TxFrameCount"]

    print("SB=" + streamblockname + " DstIP=" + dstip + " TxCount=" + str(txcount))


if thresholdrds != "":
    print()
    print("Threshold Results:")
    for result in stc.get(thresholdrds, "ResultHandleList").split():
        print(stc.get(result))



print("Done!")
exit()