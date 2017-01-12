#import sys
from collections import defaultdict


rowlist = [['StreamBlock 1', 'Port //1/1', 'Port //1/2', '192.85.1.2', '192.0.0.2', 5452, 3929, 194, 199, 0, 444403, 99.123640516403, 2222015000.0, 7615000.0, 0.13, 0.15, 0.1355612115042, 1, 200.0, 3929, 532.62, 65537, 65537],
['StreamBlock 1', 'Port //1/1', 'Port //1/2', '192.85.1.2', '192.0.0.1', 5450, 3930, 194, 199, 0, 444402, 99.1234174674125, 2222010000.0, 7600000.0, 0.13, 0.14, 0.135491094147583, 1, 200.0, 3930, 532.48, 65536, 65536],
['StreamBlock 1', 'Port //1/1', 'Port //1/2', '192.85.1.2', '192.0.0.3', 5443, 3930, 194, 202, 0, 444402, 99.1234174674125, 2222010000.0, 7565000.0, 0.13, 0.14, 0.135580152671756, 1, 200.0, 3930, 532.83, 65538, 65538],
['StreamBlock 1', 'Port //1/1', 'Port //1/2', '192.85.1.2', '192.0.0.4', 5447, 3929, 194, 199, 0, 444402, 99.1236385616877, 2222010000.0, 7590000.0, 0.13, 0.14, 0.135451768897938, 1, 200.0, 3929, 532.19, 65539, 65539],
['StreamBlock 1', 'Port //1/1', 'Port //1/2', '192.85.1.2', '192.0.0.5', 5447, 3929, 194, 199, 0, 444402, 99.1236385616877, 2222010000.0, 7590000.0, 0.13, 0.14, 0.135612115041995, 1, 200.0, 3929, 532.82, 65540, 65540]]

results = {'columnlist': ['StreamBlock.Name', 'Port.Name', 'StreamBlock.ActualRxPortName', 'StreamBlock.FrameConfig.ipv4:IPv4.1.sourceAddr', 'StreamBlock.FrameConfig.ipv4:IPv4.1.destAddr', 'StreamBlock.TxFrameCount', 'StreamBlock.RxSigFrameCount', 'StreamBlock.TxFrameRate', 'StreamBlock.RxSigFrameRate', 'StreamBlock.DuplicateFrameCount', 'StreamBlock.DroppedFrameCount', 'StreamBlock.DroppedFramePercent', 'StreamBlock.DroppedFrameDuration', 'StreamBlock.FrameLossDuration', 'StreamBlock.MinLatency', 'StreamBlock.MaxLatency', 'StreamBlock.AvgLatency', 'StreamBlock.IsExpected'], 'rowlist': []}

#print results['columnlist']


resultdata = defaultdict(dict)

for i, row in enumerate(rowlist):
    for column, value in zip(results['columnlist'], row):
        resultdata[i][column] = value

#print resultdata

for row in resultdata:
    print resultdata[row]['StreamBlock.FrameConfig.ipv4:IPv4.1.sourceAddr']


print resultdata

exit()



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

def ConvertStringToValue(string):
    # This function attempts to convert strings into different datatypes (int/float/etc).
    try:
        value = ast.literal_eval(string)
    except:
        value = string
    return value        


import re
import ast 
#import ast 

columns = 'PortName AdjacencyState SubscriberState Adjacenciesestablished Adjacenciesdown Subscribersup Subscribersdown RxTCPresetbypeer TxSYN RxSYN TxSYNACK RxSYNACK TxACK RxACK TxRSTACK RxRSTACK TxKeep-alive RxKeep-alive Keep-alivetimeouts TxPortUp TxPortDown RxManagement'
tcl = "{{Port //1/7 (offline)} NONE NONE 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 3 2 1} {{Port //1/8 (offline)} NONE NONE 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 3 4 5}"
tcl = "{StreamBlock 1} {Port //1/1} {Port //1/2} 192.85.1.2 192.0.0.2 5504 3934 193 199 0 438836 99.1115025859927 2194180000.0 7850000.0 0.11 0.14 0.12 1 200.0 3934 510.32 65537 65537"

tcl = "{{\"Port //1/7\" (offline)} 'NONE NONE' '{0 0 0 {0 0 0} 0 0 0} 0 0' 0 0 0 0 0 3 2 1} 666 {{Port //1/8 (offline)} NONE NONE 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 3 4 5 ''} ''"

#tcl = """{StreamBlock 1} {Port //1/1} {Port //1/2} 192.85.1.2 192.0.0.2 5504 3934 193 199 0 438836 99.1115025859927 2194180000.0 7850000.0 0.11 0.14 0.12 1 200.0 3934 510.32 65537 65537"""

#print tcl
result = convertTclList(tcl, level=2)

print "RESULT!"
print result


exit()

#from pyparsing import *




# tcllist =Forward() 
# element = Group( '{' + tcllist + '}' )
# tcllist << ZeroOrMore( element )

# print tcllist.parseString(tcl).asList()

expr = nestedExpr(opener='{', closer='}')

#outputlist = expr.parseString(output).asList()
result = expr.parseString(tcl)



exit()

tcllist = Forward()
element = quotedString | Combine(Optional("$") + Word(alphas,alphanums+"_")) | Combine(Optional(oneOf(list("+-")))+ Word(nums) + "." + Optional(Word(nums)) ) | Word(nums+"+-",nums) | oneOf( list(r"(),.+=`~!@#$%^&*-|\?/><;:") ) | Group( '{' + tcllist + '}' )
tcllist << ZeroOrMore( element )

import pprint
pprint.pprint( tcllist.parseString(tcl).asList() )


print output.split(" ")


exit()

# def listit(t):
#     return list(map(listit, t)) if isinstance(t, (list, tuple)) else t

# #print listit(mystring)    

# print ast.literal_eval(mystring)


# def parseit(mystring):


#from pyparsing import nestedExpr

#from pyparsing import nestedExpr
import pyparsing
#from pyparsing import originalTextFor
txt = "{ { a } { b } { { { c } } } }"

r = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!'
expr = pyparsing.nestedExpr(opener='{', closer='}')

#outputlist = expr.parseString(output).asList()
outputlist = expr.parseString(output)

#expr.setParseAction(keepOriginalText)

# expr = originalTextFor(nestedExpr("{","}"))
# print expr.parseString(output)

print outputlist

for row in outputlist[0]:
    print row
    #for value, key in zip(row, columns.split()):
    #    print str(key) + "=" + str(value)


# from pyparsing import nestedExpr, originalTextFor

# nestedBraces1 = nestedExpr('{', '}')
# for nb in nestedBraces1.searchString(output):
#     print nb

# nestedBraces2 = originalTextFor(nestedExpr('{', '}'))
# for nb in nestedBraces2.searchString(output):
#     print nb


exit()

for row in outputlist[0]:
    for value, key in zip(row, columns.split()):
        print str(key) + "=" + str(value)        