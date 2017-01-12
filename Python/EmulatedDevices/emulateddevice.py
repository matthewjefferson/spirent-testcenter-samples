###############################################################################
#
#                  Spirent TestCenter Emulated Device Example
#                         by Spirent Communications
#
#   Date: March 7, 2016
# Author: Matthew Jefferson - matt.jefferson@spirent.com
#
# Description: This is a simple example of how to create Emulated Devices for
#              Spirent TestCenter, where one of the devices includes a VLAN.
#              It also includes the creation of a bound StreamBlock.
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
####    Main
####
###############################################################################

print "Loading libraries..."

import sys
import os.path

# Point to the StcPython.py file in your Spirent TestCenter installation.
# You first need to either set the environment variable "STC_PRIVATE_INSTALL_DIR",
# or change the StcPython.py file ("STC_PRIVATE_INSTALL_DIR") to point to your
# installation.
# eg: os.environ['STC_PRIVATE_INSTALL_DIR'] = '/home/mjefferson/spirent/stc/stc4.59/'

print "Loading the Spirent TestCenter API..."
sys.path.append('/home/mjefferson/spirent/stc/stc4.59/API/Python')
from StcPython import StcPython
stc = StcPython()

# Instruct the API to not display all log entries to STDOUT.
stc.config("AutomationOptions", logTo="stcapi.log", logLevel="INFO")

# Create the configuration from scratch.
print "Creating the configuration from scratch..."
project = stc.get("system1", "children-project")

# Start by creating two ports. port1 is the Tx port, and port2 is the Rx.
port1 = stc.create("port", under=project, location="10.140.99.120/1/1")
port2 = stc.create("port", under=project, location="10.140.99.121/1/1")

# Create a single Emulated Device on each port.
# The "IfStack" is the space-separated list of interface objects used by the device.
# It is sorted top-down, meaning that the EthIIIf object will be the last element of the list.
#   eg: EthIIIf, VlanIf, IPv4If, IPv6If, GREIf, L2tpv2If, MplsIf, etc
result = stc.perform("DeviceCreate", ParentList=project, DeviceType="Host", IfStack="Ipv4If VlanIf EthIIIf", IfCount="1 1 1", Port=port1)
ed1 = result["ReturnList"]

result = stc.perform("DeviceCreate", ParentList=project, DeviceType="Host", IfStack="Ipv4If EthIIIf", IfCount="1 1", Port=port2)
ed2 = result["ReturnList"]

# You can change the attributes of the objects after they have been created.
stc.config(ed1, EnablePingResponse=True)
stc.config(ed1 + ".VlanIf", VlanId=200)
stc.config(ed1 + ".Ipv4If", Address="1.1.1.2", Gateway="1.1.1.1")

# Create a bound StreamBlock that uses the first device as a source, and the second one as the destination.
src = stc.get(ed1, "children-IPv4If")
dst = stc.get(ed2, "children-IPv4If")
streamblock1 = stc.create("StreamBlock", under=port1, srcbinding=src, dstbinding=dst)


# (OPTIONAL) Save the current configuration to disk.
print "Saving the configuration..."
outputfilename = os.path.abspath("output.tcc")
stc.perform("SaveToTcc", config="system1", filename=outputfilename)

print "Done!"
exit()