###############################################################################
#
#                               Tcl 2 Python
#                         by Spirent Communications
#
#   Date: April 1, 2016
# Author: Matthew Jefferson - matt.jefferson@spirent.com
#
# Description: This module provides a fuction to convert Tcl lists to Python lists.
#
###############################################################################
#
# Modification History
# Version  Modified
# 1.0.0    04/01/2016 by Matthew Jefferson
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
####    Required Modules
####
###############################################################################
import re
import ast 

###############################################################################
####
####    Public Functions
####
###############################################################################
def convertTclList(tcl, delimiters="\s", level=1, currentlevel=0):
    # The function converts a Tcl-based list string into a Python list.
    # It works with embedded lists, and you can set the "level" to control
    # whether nested braces are treated as lists or strings.
    # You can also change the list delimiter.

    # Start by iterating through each character in the string.
    # Identify tokens (words) and append them to the converted list.
    # If a brace or quote, single or double, is encountered, find the matching
    # end brace/quote and recurrsively call "convertTclList" to handle that substring.

    convertedlist     = []          # This is the resulting list that is returned.
    escaped           = False       # The flag is set when a backslash is detected. The following character is always treated as a string.
    token             = ""          # This is used to store each word.
    substringend      = ""          # The stores the character that indicates the end of the current substring.
    substring         = ""          
    sublevel          = 0           # The level of braces for the current character.

    # Currentlevel is an internal variable. The user should not set it, as it keeps track
    # of how many levels deep we are.
    currentlevel += 1

    # Define a regular expression to match the specified delimiters (whitespace by default).
    pattern = "[" + delimiters + "]+"

    # Iterate through each character in the string.
    for character in tcl:
        if character == "\\" and escaped == False:            
            # We have found an escaped character. Just treat it as a normal character.            
            escaped = True

        elif escaped == True:            
            # The previous character was a backslash. That means this is an escaped character, which
            # we simply add as a string.        
            escaped = False
            token += "\\" + character   

        elif (character == "\'" or character == "\"" or character == "{") and substringend == "" and token == "":
            # A new brace or quote has been found. Start constructing a substring that ends
            # when a matching brace/quote is found, and recursively pass the substring to this function.
            if character == "{":
                # We are dealing with an opening brace.
                sublevel += 1
                substringend = "}"
            else:
                # We are dealing with an opening quote.
                substringend = character

        elif character == "{" and substringend == "}":
            # We have found an embedded opening brace. 
            if sublevel > 0:
                # Do not capture the opening brace.
                substring += character
            sublevel += 1

        elif character == "}" and substringend == "}":
            # We have found a closing brace.
            sublevel -= 1
            if sublevel == 0:               
                # This is the closing brace that matching the opening brace for the current substring. 
                if currentlevel <= level:
                    # Convert the substring to a list.
                    sublist = convertTclList(substring, delimiters, level, currentlevel)
                else:
                    # Treat the substring as a...string.
                    sublist = substring    

                convertedlist.append(sublist)                

                substringend = ""
                substring    = ""
                token        = ""

            else:
                # This is the closing brace for an embedded list. Just continue adding to the substring.
                substring += character

        elif character == substringend and substringend != "":
            # We have found the closing quote for the current substring.
            if currentlevel <= level:
                # Convert the substring to a list.
                sublist = convertTclList(substring, delimiters, level, currentlevel)
            else:
                # Treat the substring as a...string.
                sublist = substring

            convertedlist.append(sublist)

            substringend = ""
            substring    = ""
            token        = ""

        elif substringend != "":
            # We are currently building a substring.
            substring += character                        

        elif re.search(pattern, character):
            # A delimiter has been detected.
            if token != "":
                value = ConvertStringToValue(token)                
                convertedlist.append(value)
                token = ""

        else:
            # Just another character for the current token.
            token += character

    if token != "":        
        # This is to add the last token to the list.
        value = ConvertStringToValue(token)
        convertedlist.append(value)

    return convertedlist

###############################################################################
####
####    Private Functions
####
###############################################################################
def ConvertStringToValue(string):
    # This function attempts to convert strings into different datatypes (int/float/etc).
    try:
        value = ast.literal_eval(string)
    except:
        value = string
    return value        

###############################################################################
####
####    Examples and Testing
####
###############################################################################

# columns = 'PortName AdjacencyState SubscriberState Adjacenciesestablished Adjacenciesdown Subscribersup Subscribersdown RxTCPresetbypeer TxSYN RxSYN TxSYNACK RxSYNACK TxACK RxACK TxRSTACK RxRSTACK TxKeep-alive RxKeep-alive Keep-alivetimeouts TxPortUp TxPortDown RxManagement'
# tcl = "{{Port //1/7 (offline)} NONE NONE 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 3 2 1} {{Port //1/8 (offline)} NONE NONE 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 3 4 5}"
tcl = "{StreamBlock 1} {Port //1/1} {Port //1/2} 192.85.1.2 192.0.0.2 5504 3934 193 199 0 438836 99.1115025859927 2194180000.0 7850000.0 0.11 0.14 0.12 1 200.0 3934 510.32 65537 65537"

print tcl.split()

exit()

# tcl = "{{\"Port //1/7\" (offline)} 'NONE NONE' '{0 0 0 {0 0 0} 0 0 0} 0 0' 0 0 0 0 0 3 2 1} 666 {{Port //1/8 (offline)} NONE NONE 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 3 4 5 ''} ''"

# #tcl = """{StreamBlock 1} {Port //1/1} {Port //1/2} 192.85.1.2 192.0.0.2 5504 3934 193 199 0 438836 99.1115025859927 2194180000.0 7850000.0 0.11 0.14 0.12 1 200.0 3934 510.32 65537 65537"""

# #print tcl
# result = convertTclList(tcl, level=2)

# print "RESULT!"
# print result


portlist = stc.get("project1", "children-port")
"port1 port2 port3"

for port in portlist.spit(): 