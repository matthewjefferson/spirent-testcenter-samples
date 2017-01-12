###############################################################################
#
#                   Spirent TestCenter Basic Traffic Example
#                         by Spirent Communications
#
#   Date: March 18, 2016
# Author: Matthew Jefferson - matt.jefferson@spirent.com
#
# Description: This is a basic Spirent TestCenter example script for loading
#              an existing TCC configuration file and then sending traffic.
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


lappend ::auto_path ~/spirent/stc
package require -exact SpirentTestCenter 4.59


# Load a configuration TCC file.
stc::perform LoadFromDatabaseCommand -DatabaseConnectionString "basic.tcc"

set project [stc::get system1 -children-project]

# Configurate the rate and duration for traffic.
foreach port [stc::get "system1.project" -children-port] {

    # If you want to change the ports that are mapped to this configuration, you simply
    # need to change the "location" attribute for each port.
    # stc::config $port -location $newlocation

    stc::config $port.generator.generatorconfig -SchedulingMode "PORT_BASED"        \
                                                -FixedLoad      100                 \
                                                -LoadUnit       "FRAMES_PER_SECOND" \
                                                -Duration       10                  \
                                                -DurationMode   "SECONDS"
}

# Connect, Reserve and map the ports to the hardware. 
# NOTE: The "RevokeOwner" argument will override any existing port reservations.
stc::perform AttachPorts -AutoConnect true -PortList [stc::get "system1.project" -children-port] -RevokeOwner true
stc::apply

# We need to subscribe to the desired results.

# First, delete all existing results subscriptions. We need to recreate the ones that we want to use.
foreach dataset [stc::get "system1.project" -children-ResultDataSet] {
    stc::delete $dataset
}

# Now subscribe to the desired results.
set rds [stc::subscribe -Parent $project -ConfigType "StreamBlock" -resulttype "TxStreamResults"]
stc::create "ResultQuery" -under $rds -ResultRootList $project -ConfigClassId "StreamBlock" -ResultClassId "RxStreamSummaryResults"
#stc::subscribe -Parent $project -ConfigType "StreamBlock" -resulttype "RxStreamSummaryResults"

puts "Starting traffic on all ports..."
stc::perform GeneratorStart

# Display the real-time results.
# The "GetObjects" command is used to find all objects of the specified type (ClasssName).
array set result [stc::perform GetObjects -ClassName "StreamBlock"]
set streamblocklist $result(-ObjectList)

# Wait for the generators to stop sending traffic.
while { [stc::get "system1.project.port(1).generator" -state] ne "STOPPED" } {
    # The result objects are children of the streamblocks.
    foreach streamblock $streamblocklist {
        set port            [stc::get $streamblock -parent]
        set portname        [stc::get $port -name]
        set streamblockname [stc::get $streamblock -name]

        set txrate [stc::get $streamblock.TxStreamResults        -FrameRate]
        set rxrate [stc::get $streamblock.RxStreamSummaryResults -FrameRate]
        
        puts "$portname $streamblockname TxRate=$txrate RxRate=$rxrate"
    }
    after 1000
}

stc::perform GeneratorStop

puts "Done!"
