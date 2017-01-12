###############################################################################
#
#                  Spirent TestCenter Load Library Example
#                         by Spirent Communications
#
#   Date: March 8, 2016
# Author: Matthew Jefferson - matt.jefferson@spirent.com
#
# Description: This script provides a procedure that loads the Spirent TestCenter
#              API version that matches the firmware for the specified chassis.
#              This is important in mixed-version firmware environments where 
#              a script may connect to chassis with different firmware versions.
# 
# NOTE: In order for this to work, the file "stc_get_version.tcl" must be located
#       in the same directory as this script.
#       Tcl must be able to find the pkgIndex.tcl files for each Spirent TestCenter
#       installation. You can either modify the environment variable "TCLLIBPATH", or
#       modify the Tcl global variable ::auto_path.
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

set ::thisfilepath [file normalize [file dirname [info script]]]


proc loadLib { {locationlist ""} } {
    # Load the Spirent TestCenter API.
    #
    # If the locationlist is specified, the specified chassis will be queried
    # for the firmware version, and then the matching Spirent TestCenter API
    # version will be loaded (if it's available).    
    # The locationlist can be either a chassis IP address, or a port location.

    # Extract the chassis address from the first element of the list.
    set chassisaddress ""
    foreach location $locationlist {
        # Remove any leading slash (/).
        regsub {^/+} $location {} location        
        set chassisaddress [lindex [split $location "/"] 0]
        break
    }

    set stcapiversion ""

    # First determine the version of Spirent TestCenter to load. We can find this information from a chassis.
    if { $chassisaddress ne "" } {        

        # The user has requested that we automatically discover the Spirent TestCenter API version to use.
        # Connect to the specified chassis and recover the version information.
        
        set filename [file join $::thisfilepath "stc_get_version.tcl"]

        # Be sure to set the TCLLIBPATH so that the discovery script can find at least
        # one version of Spirent TestCenter to use.
        set ::env(TCLLIBPATH) $::auto_path

        # The following would be the most efficient code to capture the information,
        # however, it appears that a known issue causes the process to hang when the
        # exec command and error output are not redirected.
        #set version [exec tclsh $filename $chassisaddress]

        # This is a work-around for the hang issue for the previous command.
        set output "stc_get_version_[pid].log"

        if { [file exists $filename] } {
            exec >& $output tclsh $filename $chassisaddress

            # Extract the version information from the output file.
            set fh [open $output r]
            set version ""
            regexp {version=(.+)} [read $fh] -> version
            close $fh
            catch {file delete -force $output}
            # End work-around.

            if { $version eq "" } {
                puts "WARNING: Unable to determine the firmware version for the chassis $chassisaddress."
            } else {

                set major [lindex [split $version .] 0]
                set minor [lindex [split $version .] 1]
                set build [lindex [split $version .] 2]

                set stcapiversion $major.$minor
            }

        } else {
            puts "WARNING: loadLib cannot find '$filename'. Loading the latest version of Spirent TestCenter."            
        }
    }

    if { $stcapiversion ne "" } {
        # This code is required to for Tcl to learn about all available packages.
        # Without this, the "package versions" command won't work.
        #eval [package unknown] Tcl [package provide Tcl]

        # Load the specific version of the package.
        set loadedversion [package require -exact SpirentTestCenter $stcapiversion]
    } else {
        # Load the latest version of the package.
        set loadedversion [package require SpirentTestCenter]
    }

    return $loadedversion
}

###############################################################################
####
####    Main
####
###############################################################################

# Tcl must be able to find the pkgIndex.tcl files for each Spirent TestCenter
# installation. You can either modify the environment variable "TCLLIBPATH", or
# modify the Tcl global variable ::auto_path.
lappend ::auto_path {~/spirent/stc}

puts [loadLib 10.140.99.120]