###############################################################################
#
#                            EoT Results Example
#                         by Spirent Communications
#
#   Date: March 8, 2016
# Author: Your Name - your.name@spirent.com
#
# Description: This is an example of how to access the various views stored in 
#              a Spirent TestCenter results database.
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

def getValidResultPaths(databasefilename):
    # Return a list of valid ResultPaths for the specified database file.

    # When we call QueryResult without a valid "ResultPath", and exception will
    # be thrown with a list of all valid paths.
    # Remove the error message text and simple return the list of valid paths.
    try:
        stc.perform("QueryResult", DatabaseConnectionString=databasefilename)
    except Exception, errmsgobject:
        # Convert the error message to a string.
        errmsg = str(errmsgobject)

    # Remove the extra "filler" from the error message, leaving only the valid result paths.
    errmsg = re.sub("in perform: no resultpath given: valid resultpaths are ", "", errmsg)
    # Remove all of the commas.
    errmsg = re.sub(",", "", errmsg)
    # Lastly, get rid of the " and"
    errmsg = re.sub(" and", "", errmsg)

    return str(errmsg).split(" ")

###############################################################################
####
####    Main
####
###############################################################################

print "Loading libraries..."

import sys
import os.path
import re
import pyparsing

# Point to the StcPython.py file in your Spirent TestCenter installation.
# You first need to either set the environment variable "STC_PRIVATE_INSTALL_DIR",
# or change the StcPython.py file ("STC_PRIVATE_INSTALL_DIR") to point to your
# installation.
# eg: os.environ['STC_PRIVATE_INSTALL_DIR'] = '/home/mjefferson/spirent/stc/stc4.59/'

print "Loading the Spirent TestCenter API..."
sys.path.append('/home/mjefferson/spirent/stc/stc4.62/API/Python')
from StcPython import StcPython
stc = StcPython()

# Prevent the API from output log messages to STDOUT.
stc.config("AutomationOptions", logTo="stcapi.log", logLevel="INFO")

# Each results database file contains a number of result "views", which are
# statistics in a tabular format (rows and columns). Each database contains a number
# of different ResultPaths (views). You can use the "getValidResultPaths" function to
# determine what the valid ResultPaths are for any database.
# Once you have a valid ResultPath, you can pass it into the "QueryResult" command to
# extract the result data from the database.

resultsdbfilename = "test.db"
for resultpath in getValidResultPaths(resultsdbfilename):
    try:
        result = stc.perform("QueryResult", DatabaseConnectionString=resultsdbfilename, ResultPath=resultpath)        

        expr = pyparsing.nestedExpr(opener='{', closer='}')

        # Add a set of outer brackets so that Python interprets the data as a list.
        data = "{" + result['Output'] + "}"
        outputlist = expr.parseString()

        for row in outputlist:
            for key,value in zip(result["Columns"].split(), row):
                print key + "=" + value
    except:
        pass

print "Done!"
exit()