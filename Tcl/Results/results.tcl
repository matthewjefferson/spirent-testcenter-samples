set apipath {c:/program files (x86)/spirent communications/spirent testcenter 4.61/spirent testcenter application}
lappend ::auto_path $apipath
package require SpirentTestCenter

###############################################################################
####
####    Procedures
####
###############################################################################
proc GetValidResultPaths { databasefilename } {
    # Return a list of valid ResultPaths for the specified database.
    # WARNING: Not all of the result paths returned with actually work with all
    #          database files.


    set resultpathlist ""

    # The QueryResult command returns a list of valid paths when you don't specify any path.
    catch {stc::perform QueryResult -DatabaseConnectionString $databasefilename -ResultPath "blaw"} errmsg
    
puts "DEBUG: $errmsg"    

    # Remove the extra "filler" from the error message, leaving only the valid result paths.
    regsub "RuntimeError in perform: no resultpath given: valid resultpaths are " $errmsg {} errmsg

    # Remove all of the commas.
    regsub -all "," $errmsg "" errmsg
    # Lastly, get rid of the " and"
    regsub " and" $errmsg "" resultpathlist

    return $resultpathlist
}

#==============================================================================
proc FormatColumns { text } {
    # Formats the specified text into rows and columns. Useful for
    # formatting output text.

    set alignment       "left"
    set columnpadding   1
    set showgrid        1
    set useheader       1
    set indent          0
    set inputdelimiters " "
    set outputdelimiter " "

    set output ""

    # Determine the column widths.
    set numberofcolumns 0
    set widths(0)       0   ;# Maintain a list of widths in this array.

    # On the first pass, determine the widest word for each column.
    foreach line [split $text \n] {
        set column 0
        foreach word [split $line $inputdelimiters] {
            set width [string length $word]
            if { ! [info exists widths($column)] } {
                set widths($column) $width
            } elseif { $width > $widths($column) } {
               set widths($column) $width
            }
            incr column
        }
        if { $column > $numberofcolumns } { set numberofcolumns $column }
    }

    set columnwidthlist ""
    for { set i 0 } { $i < $numberofcolumns } { incr i } {
        lappend columnwidthlist $widths($i)
    }

    # If the spacebetweencolumns value hasn't been specified, default to 3 spaces to
    # give the grid extra room.

    if { $showgrid } {
        set columnpadding 3

        # Add the column separator in the middle of the column space.
        set columnspace [string repeat " " [expr $columnpadding / 2]]
        append columnspace "|"
        set leftover [expr $columnpadding - [string length $columnspace]]
        append columnspace [string repeat " " $leftover]
    } else {
        set columnspace $outputdelimiter
        append columnspace [string repeat " " [expr $columnpadding - [string length $outputdelimiter]]]
    }

    set indenttext [string repeat " " $indent]

    # Strip off any trailing newlines (\n). This prevents an extra rows from being displayed.
    regsub -line {[\n]+\Z} $text {} text

    set row 0
    foreach line [split $text \n] {

        append output $indenttext

        set column 0
        foreach word [split $line $inputdelimiters] width $columnwidthlist {

            # Align the column according to the align parameter. Left-alignment is the default.
            switch [string tolower $alignment] {
                r -
                right   { append output [format %${width}s $word] $columnspace }
                c -
                center -
                centre {
                  # Determine the amount of space on the left side of the word.
                  set leftspace [expr ($width - [string length $word]) / 2]
                  set whitespace [string repeat " " $leftspace]
                  append output [format %-${width}s $whitespace$word] $columnspace
                }
                default { append output [format %-${width}s $word] $columnspace }
            }
            incr column
        }


        if { $useheader && $row == 0 } {
            append output \n [string repeat "-" [string length $output]]
        }

        append output \n
        incr row
    }

    return $output
}

###############################################################################
####
####    Main
####
###############################################################################

# I'm going to suppress error messages to STDOUT.
if { $::tcl_platform(platform) eq "unix" } {
    set logfilename /dev/null      ;# Use this if you want to disable logging.
} else {
    set logfilename NUL            ;# Use this if you want to disable logging.
}

stc::config automationoptions -logTo             $logfilename \
                              -logLevel          INFO         \
                              -suppresstclerrors false


set databasefilename "test.db"

# Initialize the results file.
set filename "results.txt"
set fh [open $filename w+]
close $fh

foreach query [GetValidResultPaths $databasefilename] {
    puts $query

    array unset result
    if { [catch {
        array set result [stc::perform QueryResult -DatabaseConnectionString $databasefilename \
                                                   -ResultPath               $query]} errmsg] } {
        puts $errmsg
    } else {

        # Format the results into something more readable and write it to a text file.
        set outputtext ""
        append outputtext $result(-Columns) \n
        foreach row $result(-Output) {
            append outputtext $row \n
        }

        set fh [open $filename a]
        puts $fh $query
        puts $fh [FormatColumns $outputtext]
        puts $fh ""
        puts $fh ""
        close $fh

    }
}
