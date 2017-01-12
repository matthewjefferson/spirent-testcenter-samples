###############################################################################
#
#              Spirent TestCenter Basic Real-time Traffic Results
#                         by Spirent Communications
#
#   Date: September 26, 2016
# Author: Matthew Jefferson - matt.jefferson@spirent.com
#
# Description: This basic script demonstrates how to use the subscribe command 
#              for real-time results. This code works for stand-alone tests, as
#              well as connecting to an existing Lab Server session.
#              This script should be considered the best-practice way of
#              subscribing to real-time result views.
#
#              The following result views are demonstrated here:
#                -Port
#                -StreamBlock
#                -Stream
#                -DRV
#                -Filtered Stream
#
# Notes: 
#   -I am purposely setting the RecordsPerPage setting to a small value, so that
#    the paging mechanism is used.
#   -Any result views created by the API do NOT show up in the GUI. 
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
####    Procedures
####
###############################################################################
proc getRDS { resultclass } {
    # Find the ResultDataSet object for the specified ResultClass.
    # Delete any existing RDS objects that are not in use.    
    set targetrds ""
    set project [stc::get "system1" -children-project]

    foreach rds [stc::get $project -children-ResultDataSet] {
        foreach rq [stc::get $rds -children-ResultQuery] {

            set resultclassid [stc::get $rq -ResultClassId]

            if { [string match -nocase $resultclassid $resultclass] } {
                # We found the right resultclass. Make sure it's in use.

                if { [stc::get $rds -ResultHandleList] eq "" } {
                    # This RDS is not in use. Delete it.
                    stc::delete $rds
                    break
                } else {
                    # This is what we are looking for.
                    set targetrds $rds
                    break
                }
            }
        }
        if { $targetrds ne "" } {
            break
        }
    }

    return $targetrds
}

###############################################################################
####
####    Main
####
###############################################################################
lappend ::auto_path ~/spirent/stc
package require SpirentTestCenter


set uselabserver 0

if { $uselabserver } {

    # Connect to an existing Lab Server session...
    puts "Connecting to the Lab Server..."
    stc::perform "CSTestSessionConnect" -host                 "192.168.130.207" \
                                        -TestSessionName      "test"            \
                                        -OwnerId              "mjefferson"      \
                                        -CreateNewTestSession "false"
} else {

    # Load a configuration TCC file.
    # We are doing this so that we can simply focus on the results configuration.
    puts "Loading configuration..."
    stc::perform LoadFromDatabaseCommand -DatabaseConnectionString "realtime.tcc"
}

set project [stc::get "system1" -children-project]


# The first step is the subscribe to the desired result views.
# Subscribing can actually be done at any time prior to pulling the stats.

# Port results
set portrds [getRDS "GeneratorPortResults"]

if { $portrds eq "" } {    
    puts "Subscribing to port results..."
    array unset result
    array set result [stc::perform "ResultsSubscribe" -Parent $project -ConfigType "Generator" -resulttype "GeneratorPortResults" -RecordsPerPage 256]
    set portrds $result(-ReturnedDataSet)

    # There isn't must of an advantage to putting both the Tx and Rx port result queries under the same RDS.
    stc::create "ResultQuery" -under $portrds -ResultRootList $project -ConfigClassId "Analyzer" -ResultClassId "AnalyzerPortResults"
}

# StreamBlock results
set streamblockrds [getRDS "TxStreamBlockResults"]

if { $streamblockrds eq "" } {
    puts "Subscribing to streamblock results..."
    # I purposely set the page size to be small. I would normally recommend a setting of 256.
    array unset result
    array set result [stc::perform "ResultsSubscribe" -Parent $project -ConfigType "StreamBlock" -resulttype "TxStreamBlockResults" -RecordsPerPage 5]
    set streamblockrds $result(-ReturnedDataSet) 

    # There is a very important reason for adding the Rx streamblock result query to the same RDS at the Tx results; the Tx and Rx result objects
    # will be linked to each other.
    stc::create "ResultQuery" -under $streamblockrds -ResultRootList $project -ConfigClassId "StreamBlock" -ResultClassId "RxStreamBlockResults"
}

# Stream results
set streamrds [getRDS "TxStreamResults"]

if { $streamrds eq "" } {
    puts "Subscribing to stream results..."
    # I purposely set the page size to be small. I would recommend a setting of 256.
    array unset result
    array set result [stc::perform "ResultsSubscribe" -Parent $project -ConfigType "StreamBlock" -resulttype "TxStreamResults" -RecordsPerPage 200]
    set streamrds $result(-ReturnedDataSet) 

    # There is a very important reason for adding the Rx streamblock result query to the same RDS at the Tx results; the Tx and Rx result objects
    # will be linked to each other, and it will be trivial to correlate the Tx and Rx. This is NOT the case if you use two, separate subscribe commands.
    stc::create "ResultQuery" -under $streamrds -ResultRootList $project -ConfigClassId "StreamBlock" -ResultClassId "RxStreamSummaryResults"
}

set thresholdrds [getRDS "streamthresholdresults"]

# Filtered results
if { $thresholdrds eq "" } {
    puts "Subscribing to stream threshold results..."    

    set filter1 [stc::create "CounterResultFilter" -under $project -Name "Errors > 0"]
    set fp1 [stc::create "CounterFilterProperty" -under $filter1 -FilterDisplayName "Rx IPv4 Checksum Error Count" -PropertyOperand "Ipv4ChecksumErrorCount"   -BooleanOperator "OR"]
    set fp2 [stc::create "CounterFilterProperty" -under $fp1 -FilterDisplayName "Rx TCP/UDP Checksum Error Count"  -PropertyOperand "TcpUdpChecksumErrorCount" -BooleanOperator "OR"]
    set fp3 [stc::create "CounterFilterProperty" -under $fp2 -FilterDisplayName "Rx FCS Error Count (Frames)"      -PropertyOperand "FcsErrorFrameCount"       -BooleanOperator "OR"]
    stc::create          "CounterFilterProperty" -under $fp3 -FilterDisplayName "PRBS Error Count (bits)"          -PropertyOperand "PrbsBitErrorCount"        -BooleanOperator "OR"    

    set filter2 [stc::create "CounterResultFilter" -under $project -Name "Dropped Count (Frames) > 0"]
    stc::create "CounterFilterProperty" -under $filter2 -FilterDisplayName "Dropped Count (Frames)" -PropertyOperand "DroppedFrameCount"

    set filter3 [stc::create "CounterResultFilter" -under $project -Name "Avg Latency (us) > 250"]
    stc::create "CounterFilterProperty" -under $filter3 -FilterDisplayName "Avg Latency (us)" -PropertyOperand "AvgLatency" -ValueOperand "250"

    set filter4 [stc::create "CounterResultFilter" -under $project -Name "Avg Jitter (us) > 5"]
    stc::create "CounterFilterProperty" -under $filter4 -FilterDisplayName "Avg Jitter (us)" -PropertyOperand "AvgJitter" -ValueOperand "5"

    set filter5 [stc::create "CounterResultFilter" -under $project -Name "Avg Interarrival Time (us) > 250"]
    stc::create "CounterFilterProperty" -under $filter5 -FilterDisplayName "Avg Interarrival Time (us)" -PropertyOperand "AvgInterarrivalTime" -ValueOperand "250"

    set filter6 [stc::create "CounterResultFilter" -under $project -Name "FCS Errors > 0"]
    stc::create "CounterFilterProperty" -under $filter6 -FilterDisplayName "Rx FCS Error Count (Frames)" -PropertyOperand "FcsErrorFrameCount"

    set filter7 [stc::create "CounterResultFilter" -under $project -Name "IPv4 Checksum Errors > 0"]
    stc::create "CounterFilterProperty" -under $filter7 -FilterDisplayName "Rx IPv4 Checksum Error Count" -PropertyOperand "Ipv4ChecksumErrorCount"

    set filter8 [stc::create "CounterResultFilter" -under $project -Name "TCP/UDP Checksum Errors > 0"]
    stc::create "CounterFilterProperty" -under $filter8 -FilterDisplayName "Rx TCP/UDP Checksum Error Count" -PropertyOperand "TcpUdpChecksumErrorCount"

    set filter9 [stc::create "CounterResultFilter" -under $project -Name "Duplicate > 0"]
    stc::create "CounterFilterProperty" -under $filter9 -FilterDisplayName "Duplicate Count (Frames)" -PropertyOperand "DuplicateFrameCount"

    set filter10 [stc::create "CounterResultFilter" -under $project -Name "Out of Sequence > 0"]
    stc::create "CounterFilterProperty" -under $filter10 -FilterDisplayName "Out of Sequence Count (Frames)" -PropertyOperand "OutSeqFrameCount"
    
    set filter11 [stc::create "CounterResultFilter" -under $project -Name "Reordered > 0"]
    stc::create "CounterFilterProperty" -under $filter11 -FilterDisplayName "Reordered Count (Frames)" -PropertyOperand "ReorderedFrameCount"

    set filter12 [stc::create "CounterResultFilter" -under $project -Name "Late > 0"]
    stc::create "CounterFilterProperty" -under $filter12 -FilterDisplayName "Late Count (Frames)" -PropertyOperand "LateFrameCount"

    set filter13 [stc::create "CounterResultFilter" -under $project -Name "PRBS Bit Errors > 0"]
    stc::create "CounterFilterProperty" -under $filter13 -FilterDisplayName "PRBS Error Count (bits)" -PropertyOperand "PrbsBitErrorCount"

    set filter14 [stc::create "CounterResultFilter" -under $project -Name "PRBS Frame Errors > 0"]
    stc::create "CounterFilterProperty" -under $filter14 -FilterDisplayName "PRBS Error Count (Frames)" -PropertyOperand "PrbsErrorFrameCount"   
        
    set filterlist ""        
    lappend filterlist $filter1 $filter2 $filter3 $filter4 $filter5 $filter6 $filter7 $filter8 $filter9 $filter10 $filter11 $filter12 $filter13 $filter14

    set thresholdrds [stc::subscribe -parent $project -configType "analyzer" -resultType "streamthresholdresults" -filterList $filterlist]
}

# DRV Results
# Look for any existing drop DRV results.
array unset result
array set result [stc::perform "GetObjects" -ClassName "DynamicResultView" -Condition "name = 'Dropped StreamsResults'"]

# Make sure any existing drop DRV objects are actually in use.
foreach dropdrv $result(-ObjectList) {
    if { $dropdrv ne "" && [string match -nocase [stc::get $dropdrv -ResultState] "SUBSCRIBED"] } {
        # The existing DRV is not active. Delete it and start from scratch.
        stc::delete $dropdrv
        set dropdrv ""
    } else {
        # We have found an active drop DRV object, so we will use it.
        break
    }
}

if { $dropdrv eq "" } {
    # We didn't find any active drop DRV results, so we will create a new one.
    set dropdrv [stc::create "DynamicResultView" -under $project -ResultSourceClass "Project"]

    set properties "StreamBlock.Name Port.Name StreamBlock.ActualRxPortName StreamBlock.FrameConfig.ipv4:IPv4.1.sourceAddr StreamBlock.FrameConfig.ipv4:IPv4.1.destAddr StreamBlock.FrameConfig.ethernet:EthernetII.1.srcMac StreamBlock.FrameConfig.ethernet:EthernetII.vlans.Vlan.1.id StreamBlock.TxFrameCount StreamBlock.RxSigFrameCount StreamBlock.TxFrameRate StreamBlock.RxSigFrameRate StreamBlock.DuplicateFrameCount StreamBlock.DroppedFrameCount StreamBlock.DroppedFrameDuration StreamBlock.MinLatency StreamBlock.MaxLatency StreamBlock.AvgLatency StreamBlock.IsExpected"
    set conditions "{StreamBlock.DroppedFrameCount > 0 AND StreamBlock.IsExpected = 1}" 

    # Use these conditions if connected back-to-back. This allows the DRV results to display something.
    #set conditions "{StreamBlock.DroppedFrameCount = 0 AND StreamBlock.IsExpected = 1}" 

    stc::create "PresentationResultQuery" -under $dropdrv -SelectProperties $properties -WhereConditions $conditions -FromObjects $project
    stc::perform "SubscribeDynamicResultView" -DynamicResultView $dropdrv
}

# Connect to the hardware. This works even if we are already connected.
stc::perform "AttachPorts" -AutoConnect True -PortList [stc::get $project -children-port]
stc::apply

puts "Starting traffic..."
stc::perform "GeneratorStart"
after 5000


# Now gab the stats.
for { set i 0 } { $i < 3 } { incr i } {
    puts "Port Results"
    # Port results normally fit on a single page, so paging shouldn't be necessary.
    foreach port [stc::get "system1.project" -children-port] {                     
        set txcount [stc::get $port.generator.generatorportresults -GeneratorFrameCount]
        set rxcount [stc::get $port.analyzer.analyzerportresults -SigFrameCount]
        set rxrate  [stc::get $port.analyzer.analyzerportresults -SigFrameRate]
        puts "$port Tx=$txcount Rx=$rxcount Rate=$rxrate"            
    }

    puts ""
    puts "StreamBlock Results"
    # You must manually "refresh" StreamBlock result objects.
    stc::perform "RefreshResultView" -ResultDataSet $streamblockrds
    
    for { set page 1 } { $page <= [stc::get $streamblockrds -TotalPageCount] } { incr page } {
        puts "Page=$page"
        stc::config $streamblockrds -PageNumber $page
        stc::apply
        # The delay is required, otherwise, the results will not be properly populated.
        after 1000

        foreach element [stc::get $streamblockrds -ResultHandleList] {            
            if { [regexp -nocase "txstreamblockresults" $element] } {  
                set txresult $element          
                
                set parent [stc::get $txresult -parent]
                set rxresult [stc::get $txresult -associatedresult-Targets]
                puts "$parent Tx=[stc::get $txresult -FrameCount] Rx=[stc::get $rxresult -FrameCount] Rate=[stc::get $rxresult -FrameRate]"
            }
        }
    }

    puts ""
    puts "Stream Results"    
    for { set page 1 } { $page <= [stc::get $streamrds -TotalPageCount] } { incr page } {
        puts "Page=$page"
        stc::config $streamrds -PageNumber $page
        stc::apply
        # The delay is required, otherwise, the results will not be properly populated.
        after 4000

        foreach element [stc::get $streamrds -ResultHandleList] {            
            if { [regexp -nocase "txstreamresults" $element] } {  
                set txresult $element          
                
                set parent [stc::get $txresult -parent]
                set rxresult [stc::get $txresult -associatedresult-Targets]
                puts "$parent Tx=[stc::get $txresult -FrameCount] Rx=[stc::get $rxresult -FrameCount] Rate=[stc::get $rxresult -FrameRate]"
            }
        }
    }

    puts ""
    puts "Stream Threshold Results"
    # NOTE: I'm not using the paging mechanism here, but it is entirely possible that you might have to.
    foreach element [stc::get $thresholdrds -ResultHandleList] {
        array unset result
        array set result [stc::get $element]
        parray result
        puts ""
    }

    puts ""
    puts "Drop DRV Results"
    # DRV results also need to be manually updated.
    stc::perform "UpdateDynamicResultView" -DynamicResultView $dropdrv
    foreach element [stc::get $dropdrv -children-PresentationResultQuery] {
        # Output the columns:
        set columns [stc::get $element -SelectProperties]
        foreach view [stc::get $element -children-resultviewdata] {
            if { ! [stc::get $view  -IsDummy] } {
                set valuelist [stc::get $view -ResultData]                
                foreach header $columns value $valuelist {
                    set data($header) $value
                }

                set name         $data(StreamBlock.Name)
                set dstip        $data(StreamBlock.FrameConfig.ipv4:IPv4.1.destAddr)
                set txcount      $data(StreamBlock.TxFrameCount)
                set dropcount    $data(StreamBlock.DroppedFrameCount)
                set dropduration $data(StreamBlock.DroppedFrameDuration)

                puts "$name DstIP=$dstip Tx=$txcount Drop=$dropcount Duration=$dropduration"
            }
        }
    }
 
    after 1000
}