import sys
sys.path.append('/home/mjefferson/spirent/stc/stc4.61/API/Python/')
from StcPython import StcPython
stc = StcPython()

port_traffic1 = stc.create("port", under="project1")
port_traffic2 = stc.create("port", under="project1")

# NOTE: The FrameConfig PDUs are case-sensitive. 
#       Examples are: EthernetII, Vlan, IPv4, IPv6, Mpls, Tcp, UDP, PPP, Gre, etc. There are many more.
# Default: "EthernetII IPv4"}
streamblock1 = stc.create("StreamBlock", under=port_traffic1, FrameConfig="EthernetII IPv4")
stc.get(streamblock1)
stc.config(streamblock1 + ".ethernet:EthernetII", srcMac="00:11:94:00:00:02",
                                                  dstMac="00:12:94:00:00:02")
stc.config(streamblock1 + ".ipv4:IPv4", sourceAddr="192.168.11.2",
                                        destAddr="192.168.12.2",
                                        gateway="192.168.11.1",
                                        prefixlength="24",
                                        destprefixlength="24")
                
                
streamblock2 = stc.create("StreamBlock", under=port_traffic2, FrameConfig="EthernetII IPv4")
stc.get(streamblock2)
stc.config(streamblock2 + ".ethernet:EthernetII", srcMac="00:12:94:00:00:02",
                                                  dstMac="00:11:94:00:00:02")

stc.config(streamblock2 + ".ipv4:IPv4", sourceAddr="192.168.12.2",
                                        destAddr="192.168.11.2",
                                        gateway="192.168.12.1",
                                        prefixlength="24",
                                        destprefixlength="24")

