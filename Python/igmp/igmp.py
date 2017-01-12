###############################################################################
#
#                      Spirent TestCenter IGMP Example
#                         by Spirent Communications
#
#   Date: March 3, 2016
# Author: Matthew Jefferson - matt.jefferson@spirent.com
#
# Description: This is a simple IGMP example that sends multicast traffic.
#              The script creates two ports; one Tx (port1) and one Rx (port2).
#              There is an Emulated Device for each port, and the Rx device
#              has IGMP enabled.
#              One multicast group with two groups is created and linked to the
#              IGMP configuration on the Rx Emulated Device.
#              Finally, a single streamblock is created and bound to the 
#              Emulated Device on the Tx port, and the multicast group.
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
#import time
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

# Instruct the API to not display all commands to STDOUT.
stc.config("AutomationOptions", logTo="stcapi.log", logLevel="INFO")

# Create the configuration from scratch.
print "Creating the configuration from scratch..."
project = stc.get("system1", "children-project")

# Start by creating two ports. port1 is the Tx port, and port2 is the Rx.
port1   = stc.create("port", under=project, location="10.140.99.120/1/1")
port2   = stc.create("port", under=project, location="10.140.99.121/1/1")

# Create a single Emulated Device on each port.
# The "IfStack" is the space-separated list of interface objects used by the device.
# It is sorted top-down, meaning that the EthIIIf object will be the last element of the list.
#   eg: EthIIIf, VlanIf, IPv4If, IPv6If, GREIf, L2tpv2If, MplsIf, etc
# The "IfCount" is a space-separated list indicating how many interface object instances to create for each
# element of the IfStack. This list is ordered in the same way as the IfStack.
#   eg: IfStack="Ipv4If VlanIf EthIIIf", IfCount="2 2 1" will create two IPv4If, two VlanIf and one EthIIIf object.

result = stc.perform("DeviceCreate", ParentList=project, DeviceType="Host", IfStack="Ipv4If EthIIIf", IfCount="1 1", Port=port1)
ed1 = result["ReturnList"]

result = stc.perform("DeviceCreate", ParentList=project, DeviceType="Host", IfStack="Ipv4If EthIIIf", IfCount="1 1", Port=port1)
ed2 = result["ReturnList"]

# Enable IGMP to the second emulated device.
stc.perform("ProtocolCreate", ParentList=ed2, CreateClassId="IgmpHostConfig")
# We need to bind the IGMP protocol to a interface.
stc.config(ed2 + ".IgmpHostConfig", UsesIf=stc.get(ed2, "TopLevelIf"))

# Create an multicast group block with 2 groups.
igmpgroup = stc.create("Ipv4Group", under=project)
stc.config(igmpgroup + ".Ipv4NetworkBlock", StartIpList="225.1.1.1", NetworkCount=2)

# Add the multicast group to the Emulated Device on the receiving port (port2).
kwargs = {"SubscribedGroups-targets":igmpgroup}
stc.create("IgmpGroupMembership", under=stc.get(ed2, "children-IgmpHostConfig"), **kwargs)

# Create a StreamBlock from the Emulated Device on port 1 to the multicast group.
src = stc.get(ed1, "children-ipv4if")
dst = stc.get(igmpgroup, "children-Ipv4NetworkBlock")
streamblock1 = stc.create("StreamBlock", under=port1, srcbinding=src, dstbinding=dst)

# (OPTIONAL) Save the current configuration to disk.
print "Saving the configuration..."
outputfilename = os.path.abspath("output.tcc")
stc.perform("SaveToTcc", config="system1", filename=outputfilename)

# Connect to the hardware.
stc.perform("AttachPorts", AutoConnect="true", PortList=stc.get("system1.project", "children-port"))
stc.apply

# Start IGMP.
stc.perform("DevicesStartAll")

# If the GeneratorList argument is not specified, then all generators is assumed.
stc.perform("GeneratorStart")

print "Done!"
exit()