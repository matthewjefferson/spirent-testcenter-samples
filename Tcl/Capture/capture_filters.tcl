###############################################################################
#
#                     Spirent TestCenter Capture Filters
#                         by Spirent Communications
#
#   Date: January 12, 2017
# Author: Matthew Jefferson - matt.jefferson@spirent.com
#
# Description: This is a basic Spirent TestCenter capture filter script.
#              In this example, two streamblocks will be sending traffic to the
#              receiving port, however, only frames from one streamblock will be
#              captured.
#
###############################################################################

###############################################################################
# Copyright (c) 2017 SPIRENT COMMUNICATIONS OF CALABASAS, INC.
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

proc createCaptureFilter { port headers } {
    set filter [stc::create CaptureAnalyzerFilter -under       [stc::get $port.Capture -children-CaptureFilter] \
                                                   -FrameConfig ""]

    # Create the specified header PDUs for the filter.
    foreach headertype $headers {
        stc::create $headertype -under $filter
    }

    return $filter
}

###############################################################################
####
####    Main
####
###############################################################################

lappend ::auto_path {c:/program files (x86)/spirent communications/spirent testcenter 4.71/spirent testcenter application}
package require SpirentTestCenter

set project [stc::get "system1" -children-project]


set txport [stc::create port -under $project -location "10.140.96.51/4/1"]
set rxport [stc::create port -under $project -location "10.140.96.51/4/5"]

# Create the stream that will be matched.
set streamblock_matched [stc::create "StreamBlock" -under $txport -FrameConfig "EthernetII IPv4 Custom"]

# We need to call this get command in order for the API to learn about the child objects of the streamblock.
# If we don't do it, the API will throw an error.
stc::get $streamblock_matched

stc::config $streamblock_matched.ipv4:IPv4 -sourceAddr "1.1.1.1" -destAddr "2.2.2.2" -ttl 10
stc::config $streamblock_matched.custom:Custom -pattern "DEADBEEF0001"

# Create a second stream that will not be matched.
set streamblock_notmatched [stc::create "StreamBlock" -under $txport -FrameConfig "EthernetII IPv4 Custom"]

# Configure the capture filter to look for specific frames. In this case, we are
# looking for frames with the "DEADBEEF0001" payload pattern, IPv4 TTL of 10, 
# source IP 1.1.1.1 and destination IP of 2.2.2.2.

# Custom Payload Pattern:
set filter [createCaptureFilter $rxport "ethernet:EthernetII ipv4:IPv4 custom:Custom"]

# NOTE: The "ValueToBeMatched" and "FilterDescription" attributes are not necessary, and are only used in the GUI for display purposes.
stc::config $filter -IsSelected           "TRUE" \
                    -IsNotSelected        "FALSE" \
                    -RelationToNextFilter "AND"   \
                    -FilterDescription    "Custom Payload" \
                    -ValueToBeMatched     {DEADBEEF0001}

stc::config $filter.custom:Custom -pattern {DEADBEEF0001}

# IPv4 TTL:
set filter [createCaptureFilter $rxport "ethernet:EthernetII ipv4:IPv4"]

stc::config $filter -IsSelected           "TRUE" \
                    -IsNotSelected        "FALSE" \
                    -RelationToNextFilter "AND"   \
                    -FilterDescription    "IPv4 TTL" \
                    -ValueToBeMatched     10

stc::config $filter.ipv4:IPv4 -TTL 10

# IPv4 Source IP:
set filter [createCaptureFilter $rxport "ethernet:EthernetII ipv4:IPv4"]

stc::config $filter -IsSelected           "TRUE" \
                    -IsNotSelected        "FALSE" \
                    -RelationToNextFilter "AND"   \
                    -FilterDescription    "IPv4 SIP" \
                    -ValueToBeMatched     {1.1.1.1}

stc::config $filter.ipv4:IPv4 -sourceAddr 1.1.1.1

# IPv4 Destination IP:
set filter [createCaptureFilter $rxport "ethernet:EthernetII ipv4:IPv4"]

stc::config $filter -IsSelected           "TRUE" \
                    -IsNotSelected        "FALSE" \
                    -RelationToNextFilter "AND"   \
                    -FilterDescription    "IPv4 DIP" \
                    -ValueToBeMatched     {2.2.2.2}

stc::config $filter.ipv4:IPv4 -destAddr 2.2.2.2

# Configure some general capture attributes:
stc::config $rxport.Capture -SrcMode    "RX_MODE"      \
                           -BufferMode "STOP_ON_FULL"

# Use this option to start capturing frames upon matching the specified pattern.
stc::config $rxport.Capture.CaptureFilterStartEvent -StartEvents "TRUE"

# Set the generator to only send 10 frames.
stc::config $txport.generator.generatorconfig -DurationMode "Bursts" -Duration 10

# OPTIONAL: Save this configuration to a file. This can be loaded into the GUI
stc::perform SaveToTcc -config system1 -filename [file normalize "capture_filters.tcc"]


puts "Connecting..."
stc::perform AttachPorts -AutoConnect true -PortList [stc::get system1.project -children-port]

# Subscript to Tx and Rx port results:
puts "Subscribing to port results..."
array set result [stc::perform "ResultsSubscribe" -Parent         $project \
                                                  -ConfigType     "Generator" \
                                                  -resulttype     "GeneratorPortResults" \
                                                  -RecordsPerPage 256]
set portrds $result(-ReturnedDataSet)

stc::create "ResultQuery" -under          $portrds \
                          -ResultRootList $project \
                          -ConfigClassId  "Analyzer" \
                          -ResultClassId  "AnalyzerPortResults"

stc::apply

stc::perform CaptureStart

puts "Starting the traffic..."
stc::perform GeneratorStart

after 5000

stc::perform CaptureStop

puts "Display the captured frames..."
set capturecount [stc::get $rxport.capture -PktCount]
for { set index 0 } { $index < $capturecount } { incr index } {
    array unset result
    array set result [stc::perform "CaptureGetFrameCommand" -CaptureProxyId $rxport -FrameIndex $index]
    puts "Packet Data=$result(-PacketData)"    
}
puts ""

puts "Saving capture..."
stc::perform CaptureDataSave -captureProxyId [stc::get $rxport -children-capture] \
                             -filename       [file join [pwd] "capture_filter.pcap"]

# Display some of the Rx port counters:
set anaresults [stc::get $rxport.Analyzer -children-AnalyzerPortResults]

puts "SignatureFrameCount = [stc::get $anaresults -SigFrameCount]"
puts "Trigger1Count       = [stc::get $anaresults -Trigger1Count]"
puts "Trigger2Count       = [stc::get $anaresults -Trigger2Count]"
puts "Trigger3Count       = [stc::get $anaresults -Trigger3Count]"
puts "Trigger4Count       = [stc::get $anaresults -Trigger4Count]"
puts "Trigger5Count       = [stc::get $anaresults -Trigger5Count]"
puts "Trigger6Count       = [stc::get $anaresults -Trigger6Count]"
puts "Trigger7Count       = [stc::get $anaresults -Trigger7Count]"
puts "Trigger8Count       = [stc::get $anaresults -Trigger8Count]"
puts "ComboTriggerCount   = [stc::get $anaresults -ComboTriggerCount]"

puts "Done!"

