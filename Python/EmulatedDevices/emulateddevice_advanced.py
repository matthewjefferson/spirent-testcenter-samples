###############################################################################
#
#             Spirent TestCenter Advanced Emulated Device Example
#                         by Spirent Communications
#
#   Date: March 7, 2016
# Author: Matthew Jefferson - matt.jefferson@spirent.com
#
# Description: This is a more advanced example of how to create Emulated Devices.
#              There are (at least) three methods for creating devices: manually,
#              using the DeviceCreate command, and using the Emulated Device
#              Creation wizard.
#              This example also includes how to modify an existing interface
#              stack, as well as device-behind-device.
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

###############################################################################
####
####    Method 1 : DeviceCreateCommand
####
###############################################################################

# This is generally the easiest method. Simply execute a single command to
# generate the device. There are many options available for the command that
# allow you to customize what gets created.

# Create three Emulated Devices (CreateCount=3), with each device having 8 unique
# IPv4 addresses and 2 vlans (IfStack="4 2 1").
result = stc.perform("DeviceCreate", ParentList=project, CreateCount=3, DeviceType="Host", IfStack="Ipv4If VlanIf EthIIIf", IfCount="4 2 1", Port=port1)
edlist = result["ReturnList"].split()


# Change the attributes of the first device:
stc.config(edlist[0], EnablePingResponse=True)
stc.config(edlist[0] + ".VlanIf", VlanId=200)
stc.config(edlist[0] + ".Ipv4If", Address="1.1.1.2", Gateway="1.1.1.1")


###############################################################################
####
####    Method 2 : Manually
####
###############################################################################

# Manual creation means that you need to create the EmulatedDevice object, and all
# other necessay objects, manually. You also need to "link" (using "relations) 
# the various objects together. 
ed = stc.create("EmulatedDevice", under=project, AffiliatedPort=port1, EnablePingResponse=True, Name="Manual")

ethif = stc.create("EthIIIf", under=ed, SourceMac="00:00:00:00:00:01")
vlanif = stc.create("VlanIf", under=ed, StackedOn=ethif)
ipv4if = stc.create("Ipv4If", under=ed, StackedOn=vlanif, Address="2.1.1.2")

stc.config(ed, TopLevelIf=ipv4if, PrimaryIf=ipv4if)

###############################################################################
####
####    Method 3 : Device Wizard
####
###############################################################################

# This method is the same as what the GUI uses when you select "Add" under Devices.
# This is useful when creating a large number of devices with a predictable 
# addressing scheme.

# This example creates 3 IPv4 devices with dual-stack vlans.

# The first step is to create the GenParams objects for device, and each of the
# interface objects. This step is equivalent to populating the values of the 
# device wizard in the GUI.

edp = stc.create("EmulatedDeviceGenParams", under=project,
                                            Port=port1,
                                            Count=1,
                                            DeviceName="Wizard",
                                            Role="Router",                                            
                                            BlockMode="ONE_DEVICE_PER_BLOCK")

stc.create("DeviceGenEthIIIfParams", under=edp,
                                     SrcMac="00:00:02:03:04:05",
                                     SrcMacStep="00:00:00:00:00:02")

stc.create("DeviceGenVlanIfParams", under=edp,
                                    Count=3,
                                    VlanID=200,
                                    IdStep=1,
                                    RepeatMode="NO_REPEAT")

stc.create("DeviceGenVlanIfParams", under=edp,
                                    Count=1,
                                    VlanID=300,
                                    IdStep=1,
                                    RepeatMode="NO_REPEAT")

stc.create("DeviceGenIpv4IfParams", under=edp,
                                    Addr="3.1.1.2",
                                    AddrStep="0.0.2.0",
                                    Gateway="3.1.1.1")                                    

# Finally, execute the command that will create the emulated devices.
result = stc.perform("DeviceGenConfigExpand", DeleteExisting="No", GenParams=edp)
devicelist = result["ReturnList"].split()

###############################################################################
####
####    Device-Behind-Device
####
###############################################################################

# We can use the "LinkCreate" command to create a link between two devices
# for a device-behind-device scenario.

# The source device is behind the other device.
srcdev = devicelist[0]
srcif  = stc.get(srcdev, "children-ipv4if")

# The destination is the device in front of the source device.
dstdev = edlist[0]
dstif  = stc.get(dstdev, "children-ipv4if")

# There are many link types.
stc.perform("LinkCreate", LinkType="L3 Forwarding Link", SrcDev=srcdev, SrcIf=srcif, DstDev=dstdev, DstIf=dstif)

###############################################################################
####
####    Misc
####
###############################################################################

# You can add/modify the interface stack for existing devices with the IfStackXXX commands.
#   IfStackAddCommand       - Use if the device does not have any interface objects.
#   IfStackAttachCommand    - Use to add additional interface objects.
#   IfStackGetCommand       
#   IfStackRemoveCommand    
#   IfStackReplaceCommand   - Replace existing interface objects.

# Add IPv6 (dual-stack) to the device we manually created.

# This will be the global address.
stc.perform("IfStackAttachCommand", DeviceList=ed, AttachToIf=vlanif, IfStack="Ipv6If", IfCount="1")

# This will be the link-local interface.
stc.perform("IfStackAttachCommand", DeviceList=ed, AttachToIf=vlanif, IfStack="Ipv6If", IfCount="1", IsPrimaryIf=True)

ipv6iflist = stc.get(ed, "children-ipv6if").split()
ipv6ifg  = ipv6iflist[0]
ipv6ifll = ipv6iflist[1]

stc.config(ipv6ifll, Address="fe80::1")





# (OPTIONAL) Save the current configuration to disk.
print "Saving the configuration..."
outputfilename = os.path.abspath("output.tcc")
stc.perform("SaveToTcc", config="system1", filename=outputfilename)

print "Done!"
exit()