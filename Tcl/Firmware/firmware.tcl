###############################################################################
#
#                 Spirent TestCenter Firmware Upgrade Example
#                         by Spirent Communications
#
#   Date: March 11, 2016
# Author: Matthew Jefferson - matt.jefferson@spirent.com
#
# Description: This is an example script for upgrading the firmware on a
#              Spirent TestCenter chassis (including virtual).
#              The script accepts either a list of chassis IP addresses, or
#              the name of a file that contains a list of IP addresses as input.
#              the firmware files should be located in the same directory
#              as the script (in a subdirectory).
#
# Usage:
#   -chassisiplist: A list of Spirent TestCenter chassis IP addresses to upgrade/downgrade.
#   -filename:      A file containing a list of Spirent TestCenter chassis IP addresses to upgrade/downgrade.
#   -version:       (OPTIONAL) The firmware version to load. If not specified, then the latest available version is loaded.
#
# Examples:
#   tclsh firmware.tcl -chassisiplist "1.1.1.1 1.1.1.2"
#   tclsh firmware.tcl -filename "chassis.txt" -version 4.59  
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

proc getAvailableVersions { path versionarrayname } {
    upvar $versionarrayname versionarray
    
    # Determine which firmware versions are available in the current directory,
    # and in all subdirectories. Open the rawimage.map file to find the version
    # information.

    if { ! [info exists versionarray(list)] } {
        set versionarray(list) ""
    }

    set filename [file join $path "rawimage.map"]
    if { [file exists $filename] } {
        set fh [open $filename r]
        set filetext [read $fh]
        close $fh

        # The rawimage.map file has the following syntax:
        # DX-10G-S8 512 changeling_64-4.62.8276-fs
        set version ""
        regexp {([0-9]+\.[0-9]+\.[0-9]+)-fs} $filetext -> version

        if { $version ne "" && [lsearch -exact $versionarray(list) $version] == -1 } {
            lappend versionarray(list) $version
            set versionarray($version) [file normalize $path]
        }
    }

    # Now traverse all of the subdirectories.
    foreach subdirectory [glob -nocomplain -directory $path -type d *] {
        getAvailableVersions $subdirectory "versionarray"
    }

    return
}

#==============================================================================
proc loadFirmware { chassisiplist version } {

    # First, locate the firmware.
    getAvailableVersions $::firmwarepath "versionarray"

    if { $version eq "" } {
        # Just load the latest version.
        set versionarray(list) [lsort $versionarray(list)]
        set version [lindex $versionarray(list) end]

    } elseif { [lsearch $versionarray(list) "${version}*"] == -1 } {
        
        error "Unable to locate the firmware files for version '$version'."

    } else {
        # Determine the exact version that will be loaded.
        set index [lsearch $versionarray(list) "${version}*"]
        set version [lindex $versionarray(list) $index]
    }

    stc::perform SetRawArchivesDir -Dir $versionarray($version)

    # Connect to the hardware, and construct a list of equipment to upgrade.
    foreach chassisip $chassisiplist {
        catch {stc::connect $chassisip}
    }    

    set equipmentlist ""
    foreach chassis [stc::get "system1.physicalchassismanager" -children-physicalchassis] {
        set currentversion [stc::get $chassis -FirmwareVersion]
        # Remove the build number from the current version.
        regexp {[0-9]+\.[0-9]+} $currentversion currentversion       
        regexp {[0-9]+\.[0-9]+} $version        targetversion

        if { $currentversion != $targetversion } {
            lappend equipmentlist $chassis
        }

    }

    if { $equipmentlist ne "" } {
        puts "Loading version $version onto the following:"        
        foreach chassis $equipmentlist {
            puts "  [stc::get $chassis -Hostname]"
        }
        puts ""
        stc::perform InstallRawImage -EquipmentList $equipmentlist \
                                     -Version       $version

        puts "Update complete"
    }

    return
}


###############################################################################
####
####    Main
####
###############################################################################

package require cmdline

#lappend ::auto_path /home/mjefferson/spirent/stc/
package require SpirentTestCenter

set options {{chassisiplist.arg "" "A list of Spirent TestCenter chassis IP addresses to upgrade/downgrade."}
             {filename.arg      "" "A file containing a list of Spirent TestCenter chassis IP addresses to upgrade/downgrade."}
             {version.arg       "" "OPTIONAL: The firmware version to load. If not specified, then the latest available version is loaded."}}

# The command-line arguments will be stored in the "params" array.
array set params [::cmdline::getoptions argv $options]

# The user may specify both a list of chassis and/or a filename containing a list of chassis.
set chassisiplist $params(chassisiplist)

if { [file exists $params(filename)] } {
    set fh [open $params(filename) r]
    set filetext [read $fh]
    close $fh    

    foreach chassisip $filetext {
        if { [lsearch -exact $chassisiplist $chassisip] == -1 } {
            lappend chassisiplist $chassisip
        }
    }
}

# The firmware files must be in located in the same directory as the script.
set firmwarepath [file dirname [info script]]

loadFirmware $chassisiplist $params(version)