###############################################################################
#
#                 Spirent TestCenter Module Capabilities
#                         by Spirent Communications
#
#   Date: July 19, 2016
# Author: Matthew Jefferson - matt.jefferson@spirent.com
#
# Description: This is an example of how to determine the capabilities of a
#              module. This information is pulled from the RCM.db file, which
#              is included as part of the Spirent TestCenter installation.
#
###############################################################################
#
# Modification History
# Version  Modified
# 1.0.0    07/19/2016 by Matthew Jefferson
#           -Began work on package.
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
#  3. Neither the name SPIRENT, SPIRENT COMMUNICATIONS, SMARTBITS, SPIRENT
#     TESTCENTER, AVALANCHE NEXT, LANDSLIDE, nor the names of its contributors
#     may be used to endorse or promote products derived from this software
#     without specific prior written permission.
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
####    Public Procedures
####
###############################################################################

proc getCapabilities { {targetmodel ""} } {
    package require sqlite3

    if { [info exists ::env(STC_PRIVATE_INSTALL_DIR)] } {
        set dbfilename [file join $::env(STC_PRIVATE_INSTALL_DIR) "RcmDb/RCM.db"]
    } else {
        error "Unable to determine the Spirent TestCenter installation directory."
    }

    set db "::db"
    sqlite3 $db $dbfilename

    # Catch any exceptions so that we can properly close the database.
    set errorhasoccurred [catch {
        set query "SELECT * FROM capability WHERE key LIKE '${targetmodel}%'"
        set capabilities(modellist) ""
        $db eval $query result {
           
            set key [split $result(key) "/"]
            set model [lindex $key 0]
            set field [lrange $key 1 end]            
            set field [join $field "/"]

            set capabilities($model.$field) $result(value)

            if { [regexp {\.} $field] } { puts "FOUND: $field"}

            luniqueappend capabilities(modellist) $model
        }        

    } errmsg]

    catch {$db close}

    return [array get capabilities]        
}

###############################################################################
####
####    Private Procedures
####
###############################################################################
proc luniqueappend { listname args } {
    # Same as the TCL command "lappend", but only adds unique values on the list.
    upvar $listname varName

    if { ! [info exists varName] } {
        set varName ""
    }

    set length [llength $args]

    for { set i 0 } { $i < $length } { incr i } {
        set arg [lindex $args $i]
        if { [lsearch -exact $varName $arg] == -1 } {
            lappend varName $arg
        }
    }
    return
}

###############################################################################
####
####    Main
####
###############################################################################

lappend ::auto_path {/home/mjefferson/spirent/stc}
package require SpirentTestCenter


#array set capabilities [getCapabilities "CM-10G-S2"]
array set capabilities [getCapabilities]

stc::connect "10.140.96.51"

foreach chassis [stc::get "system1.physicalchassismanager" -children-physicalchassis] {
    foreach module [stc::get $chassis -children-physicaltestmodule] {
        set model [stc::get $module -Model]
        if { $model ne "" } {
            if { [lsearch -exact $capabilities(modellist) $model] != -1 } {
                set tx [lindex [split $capabilities($model.Default/GA/L2L3/generator/streams/count) ":"] 1]
                set rx $capabilities($model.Default/GA/L2L3/analyzer/anaStreams)
                puts "$model MaxTx=$tx MaxRx=$rx"
                
            } else {
                puts "WARNING: Unable to find a $model in the capabilities list."              
            }
        } else {
            # Probably just an empty slot.       
        }
    }

}