###############################################################################
#
#               Packet Capture Example for Spirent TestCenter
#                         by Spirent Communications
#
#   Date: April 14, 2016
# Author: Matthew Jefferson - matt.jefferson@spirent.com
#
# Description: This is a simple example of packet capture.
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
####    Globals
####
###############################################################################
# Set port_locations to an empty list if you want to keep the existing locations
# from the configuration file.
# Otherwise, create a list of port locations to use.
port_locations = ["10.140.96.51/1/7", "10.140.96.51/1/8"]

###############################################################################
####
####    Functions
####
###############################################################################
def captureStart():
    
    for port in stc.get("system1.project", "children-port").split():
        stc.perform("CaptureStart", captureProxyId=stc.get(port, "children-capture"))

    return

#==============================================================================
def captureStop(filenameprefix="capture", timestamp=True):
    # Stop the capture engine and save the captured files to disk as a PCAP file.
    portlist = stc.get("system1.project", "children-port")

    for port in portlist.split():
        if timestamp:
            # Add a timestamp to the capture filename.
            now = datetime.datetime.now()
            timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")    
            filename = filenameprefix + port + "_" + timestamp + ".pcap"
        else:
            filename = filenameprefix + port + ".pcap"
        
        filename = os.path.abspath(filename)

        stc.perform("CaptureStop",     captureProxyId=stc.get(port, "children-capture"))
        stc.perform("CaptureDataSave", captureProxyId=stc.get(port, "children-capture"), filename=filename)

        packetscaptured = stc.get(port + ".capture", "PktCount")

        print port + " captured " + str(packetscaptured) + " frames."

    return

###############################################################################
####
####    Main
####
###############################################################################

print "Loading libraries..."

import sys
import time
import datetime
import os.path

# Point to the StcPython.py file in your Spirent TestCenter installation.
# You first need to either set the environment variable "STC_PRIVATE_INSTALL_DIR",
# or change the StcPython.py file ("STC_PRIVATE_INSTALL_DIR") to point to your
# installation.
# eg: os.environ['STC_PRIVATE_INSTALL_DIR'] = '/home/mjefferson/spirent/stc/stc4.59/'

print "Loading the Spirent TestCenter API..."
sys.path.append('/home/mjefferson/spirent/stc/stc4.61/API/Python')
from StcPython import StcPython
stc = StcPython()

# Instruct the API to not display all commands to STDOUT.
stc.config("AutomationOptions", logTo="stcapi.log", logLevel="INFO")

stc.perform("LoadFromDatabaseCommand", DatabaseConnectionString="capturetest.tcc")

# Remap port locations if necessary.
for port, location in zip(stc.get("system1.project", "children-port").split(), port_locations):
    print "Remapping " + port + " to " + location
    stc.config(port, location=location)

# Connect to the hardware.
stc.perform("AttachPorts", AutoConnect="true", PortList=stc.get("system1.project", "children-port"))
stc.apply()

captureStart()

# If the GeneratorList argument is not specified, then all generators is assumed.
print "Starting traffic"
stc.perform("GeneratorStartCommand")

time.sleep(5)

print "Stopping traffic..."
stc.perform("GeneratorStopCommand")

captureStop()

print "Done!"
exit()