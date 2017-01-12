# This script relies on the environment variable TCLLIBPATH being set correctly.
# It must point to at least one version of Spirent TestCenter.
package require SpirentTestCenter

set chassisip [lindex $argv 0]

stc::connect $chassisip

set version ""
foreach chassis [stc::get system1.physicalchassismanager -children-physicalchassis] {
    set version [stc::get $chassis -FirmwareVersion]
}

puts "$chassisip version=$version"

return $version