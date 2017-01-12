###############################################################################
#
#                Spirent TestCenter Routing Wizards Example
#                         by Spirent Communications
#
#   Date: March 18, 2016
# Author: Matthew Jefferson - matt.jefferson@spirent.com
#
# Description: This example script demonstrates how to enable routing emulation 
#              and execute the OSPF, BGP and ISIS routing wizards.
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


import sys
import os.path

# Point to the StcPython.py file in your Spirent TestCenter installation.
# You first need to either set the environment variable "STC_PRIVATE_INSTALL_DIR",
# or change the StcPython.py file ("STC_PRIVATE_INSTALL_DIR") to point to your
# installation.
# eg: os.environ['STC_PRIVATE_INSTALL_DIR'] = '/home/mjefferson/spirent/stc/stc4.59/'

print "Loading the Spirent TestCenter API..."
sys.path.append('/home/mjefferson/spirent/stc/stc4.62/API/Python')
from StcPython import StcPython
stc = StcPython()

# Instruct the API to not display all log entries to STDOUT.
stc.config("AutomationOptions", logTo="stcapi.log", logLevel="INFO")

# The project object always exists (no need to create it).
project = stc.get("system1", "children-project")

# Create a single port that we want to enable routing emulation on.
port1 = stc.create("port", under=project, location="10.140.99.120/1/1")

# Create an emulated device associated with the port.
result = stc.perform("DeviceCreate", ParentList=project, DeviceType="Router", IfStack="Ipv4If EthIIIf", IfCount="1 1", Port=port1)
emulateddevice = result["ReturnList"]


###############################################################################
####
####    OSPF
####
###############################################################################
# Enable OSPF on the emulated device and create a 2x3 Router LSA topology.

# Enable OSPF.
stc.create("Ospfv2RouterConfig", under=emulateddevice)

# Now use the LSA generator to create a grid topology.
# We need to create a number of GenParam objects to feed to the "RouteGenApply" command,
# which will create the required router LSAs.
kwargs = {"SelectedRouterRelation-targets":emulateddevice}
genparams = stc.create("Ospfv2LsaGenParams", under=project, RouterIdStart="100.1.1.1", **kwargs)

# These are the types of topologies that can be created:
# RingTopologyGenParams
# TreeTopologyGenParams
# FullMeshTopologyGenParams
# GridTopologyGenParams
# HubSpokeTopologyGenParams
stc.create("GridTopologyGenParams", under=genparams, Rows=2, Columns=3)

# This command executes the wizard and generates the configuration.
stc.perform("RouteGenApply", genparams=genparams, deleteroutesonapply="no")


###############################################################################
####
####    BGP
####
###############################################################################

# Enable BGP on the emulated device and create 100 routes.

# Enable BGP.
stc.create("BGPRouterConfig", under=emulateddevice)

# Create the configuration objects for the BGP wizard. These objects are how
# we configure the parameters for the wizard.
kwargs = {"SelectedRouterRelation-targets":emulateddevice}
genparams = stc.create("BgpRouteGenParams", under=project, **kwargs)

# This will create the 100 routes.
stc.create("Ipv4RouteGenParams", under=genparams, Count=100, DisableRouteAggregation=True, IpAddrStart="101.1.1.1")
stc.create("BgpRouteGenRouteAttrParams", under=stc.get(genparams, "children-Ipv4RouteGenParams"))

# This command executes the wizard and generates the configuration.
stc.perform("RouteGenApply", genparams=genparams, deleteroutesonapply="no")


###############################################################################
####
####    ISIS
####
###############################################################################

# Enalbe ISIS on the emulated device and create a TREE LSP topology with 10 routers.

# Enable ISIS.
stc.create("IsisRouterConfig", under=emulateddevice)

kwargs = {"SelectedRouterRelation-targets":emulateddevice}
genparams = stc.create("IsisLspGenParams", under=project, **kwargs)

# These are the types of topologies that can be created:
# FullMeshTopologyGenParams
# GridTopologyGenParams
# HubSpokeTopologyGenParams
# RingTopologyGenParams
# TreeTopologyGenParams
stc.create("TreeTopologyGenParams", under=genparams, NumSimulatedRouters=10)

stc.create("Ipv4RouteGenParams", under=genparams, EnableIpAddrOverride=False)

stc.create("IsisLspGenRouteAttrParams", under=stc.get(genparams, "children-Ipv4RouteGenParams"), RouteType="INTERNAL")

stc.perform("RouteGenApply", genparams=genparams, deleteroutesonapply="no")


###############################################################################
####
####    Misc
####
###############################################################################

# (OPTIONAL) Save the current configuration to disk.
print "Saving the configuration..."
outputfilename = os.path.abspath("routingwizards.tcc")
stc.perform("SaveToTcc", config="system1", filename=outputfilename)

print "Done!"
exit()