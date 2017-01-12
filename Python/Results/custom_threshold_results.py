
from __future__ import print_function

import sys
import time
import os.path

print("Loading the Spirent TestCenter API...")
sys.path.append('/home/mjefferson/spirent/stc/stc4.66/API/Python')
from StcPython import StcPython
stc = StcPython()

stc.perform("LoadFromDatabaseCommand", DatabaseConnectionString="base.tcc")

project = stc.get("system1", "children-project")

# Delete all existing result subscriptions.
for rds in stc.get(project, "children-ResultDataSet").split():
    stc.delete(rds)


# Create the filters for the threshold results.

# Number of streams that dropped.
crf1 = stc.create("CounterResultFilter", under=project, Name="# Streams That Dropped")
cfp1 = stc.create("CounterFilterProperty", under=crf1, FilterDisplayName="Dropped Count (Frames)", PropertyOperand="DroppedFrameCount")
stc.create("CounterFilterProperty", under=cfp1, FilterDisplayName="Is Expected", PropertyOperand="IsExpected", ValueOperand=1, ComparisonOperator="EQUAL")

# Number of streams that duplicated.
crf2 = stc.create("CounterResultFilter", under=project, Name="# Streams That Duplicated")
cfp2 = stc.create("CounterFilterProperty", under=crf2, FilterDisplayName="Duplicate Count (Frames)", PropertyOperand="DuplicateFrameCount")
stc.create("CounterFilterProperty", under=cfp2, FilterDisplayName="Is Expected", PropertyOperand="IsExpected", ValueOperand=1, ComparisonOperator="EQUAL")

# Don't know.
crf3 = stc.create("CounterResultFilter", under=project)
stc.create("CounterFilterProperty", under=crf3)

# Number of streams currently dropping.
crf4 = stc.create("CounterResultFilter", under=project, Name="# Streams Currently Dropping")
cfp3 = stc.create("CounterFilterProperty", under=crf4, FilterDisplayName="Dropped Rate (fps)", PropertyOperand="DroppedFrameRate")
stc.create("CounterFilterProperty", under=cfp3, FilterDisplayName="Is Expected", PropertyOperand="IsExpected", ValueOperand=1, ComparisonOperator="EQUAL")

# Number of streams currently duplicating.
crf5 = stc.create("CounterResultFilter", under=project, Name="# Streams Currently Duplicating")
cfp4 = stc.create("CounterFilterProperty", under=crf5, FilterDisplayName="Duplicate Rate (fps)", PropertyOperand="DuplicateFrameRate")
stc.create("CounterFilterProperty", under=cfp4, FilterDisplayName="Is Expected", PropertyOperand="IsExpected", ValueOperand=1, ComparisonOperator="EQUAL")

# Number of streams currently alive.
crf6 = stc.create("CounterResultFilter", under=project, Name="# Streams Currently Alive")
cfp5 = stc.create("CounterFilterProperty", under=crf6, FilterDisplayName="Rx Sig Rate (fps)", PropertyOperand="SigFrameRate")
stc.create("CounterFilterProperty", under=cfp5, FilterDisplayName="Is Expected", PropertyOperand="IsExpected", ValueOperand=1, ComparisonOperator="EQUAL")

# Number of streams currently dead.
crf7 = stc.create("CounterResultFilter", under=project, Name="# Streams Currently Dead")
cfp6 = stc.create("CounterFilterProperty", under=crf7, FilterDisplayName="Rx Sig Rate (fps)", PropertyOperand="SigFrameRate", ComparisonOperator="EQUAL")
stc.create("CounterFilterProperty", under=cfp6, FilterDisplayName="Is Expected", PropertyOperand="IsExpected", ValueOperand=1, ComparisonOperator="EQUAL")

# Number of streams currently flooding.
crf8 = stc.create("CounterResultFilter", under=project, Name="# Streams Currently Flooding")
cfp7 = stc.create("CounterFilterProperty", under=crf8, FilterDisplayName="Rx Sig Rate (fps)", PropertyOperand="SigFrameRate")
stc.create("CounterFilterProperty", under=cfp7, FilterDisplayName="Is Expected", PropertyOperand="IsExpected", ComparisonOperator="EQUAL")

# Number of streams that flooded.
crf9 = stc.create("CounterResultFilter", under=project, Name="# Streams That Flooded")
cfp8 = stc.create("CounterFilterProperty", under=crf9, FilterDisplayName="Rx Sig Count (Frames)", PropertyOperand="SigFrameCount")
stc.create("CounterFilterProperty", under=cfp8, FilterDisplayName="Is Expected", PropertyOperand="IsExpected", ComparisonOperator="EQUAL")

# Number of streams totally dead.
crf10 = stc.create("CounterResultFilter", under=project, Name="# Streams Totally Dead")
cfp9 = stc.create("CounterFilterProperty", under=crf10, FilterDisplayName="Rx Sig Count (Frames)", PropertyOperand="SigFrameCount", ComparisonOperator="EQUAL")
stc.create("CounterFilterProperty", under=cfp9, FilterDisplayName="Is Expected", PropertyOperand="IsExpected", ValueOperand=1, ComparisonOperator="EQUAL")

# Number of streams alive at some time.
crf11 = stc.create("CounterResultFilter", under=project, Name="# Streams Alive at Sometime")
cfp10 = stc.create("CounterFilterProperty", under=crf11, FilterDisplayName="Rx Sig Count (Frames)", PropertyOperand="SigFrameCount")
stc.create("CounterFilterProperty", under=cfp10, FilterDisplayName="Is Expected", PropertyOperand="IsExpected", ValueOperand=1, ComparisonOperator="EQUAL")

# Add all of the filters to a list.
filterlist = [crf1, crf4, crf2, crf5, crf6, crf7, crf8, crf9, crf10, crf11]

stc.subscribe(parent=project, 
              configType="analyzer", 
              resultType="streamthresholdresults", 
              filterList=" ".join(filterlist),
              viewAttributeList="customfiltercount1 customfiltercount2 customfiltercount3 customfiltercount4 customfiltercount5 customfiltercount6 customfiltercount7 customfiltercount8 customfiltercount9 customfiltercount10 customfiltercount11")            


stc.perform("AttachPorts", AutoConnect=True, PortList=stc.get(project, "children-port"))
stc.apply()

print("Starting traffic on all ports...")
stc.perform("GeneratorStart")

time.sleep(5)

print("Pulling the stats...")
for rds in stc.get(project, "children-ResultDataSet").split():    
    for result in stc.get(rds, "ResultHandleList").split():        
        print(stc.get(result))
        print()        


