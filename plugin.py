#
#   SNMPreader Plugin
#
#   Author: ycahome,    2017 
#           bramvreugd, 2020
#   https://www.domoticz.com/forum
#
#
#  version 1.0.0             : Initial
#          1.1.0             : Removed unneeded logging on debug mode
#                            : Ficed to work with python 3
#                            : Added interval attribute
#                            : Minor Ther fixes
#          1.2.0             : Now support Speed calculation and multiple OID's per instance 
#          1.3.0             : Bug fix for types other then speed data type
#                              Possibility to get value from table ipAddrTable with #n. 
#                              For example #1 is the first element of the table. Full OID of example: .1.3.6.1.2.1.4.20.1.1#1
#                              With this it is possible to retrieve the ip your modem/router got from your isp     
#
##
"""
<plugin key="SNMPreader2" name="SNMP Reader2" author="ycahome bramvreugd" version="1.3.0" wikilink="m" externallink="https://www.domoticz.com/forum/viewtopic.php?f=65">
    <description>
    * Use PRefix OID will be before all OID's<br/>
    * In the OIDlist use the form   OID1;Typename1|OID2;Typename2...<br/>
    * Typename can be a Domoticz typename of "Speed"<br/>
    * When using speed the speed is calculated by the difference un Octets per interval. Speed is in Mbps. 
    </description>
    <params>
        <param field="Address" label="Server IP" width="200px" required="true" default="192.168.1.1"/>
        <param field="Mode1" label="OID prefix" width="200px" required="true" default=".1.3.6.1.2.1.2.2.1."/>
        <param field="Mode2" label="Community" width="200px" required="true" default="public"/>
        <param field="Mode4" label="Check Interval(seconds)" width="75px" required="true" default="60"/>
        <param field="Mode5" label="OID list" width="200px" required="true" default="10.5;Speed|16.5;Speed|10.1;Speed|16.1;Speed|10.4;Speed|16.4;Speed"/>
        <param field="Mode6" label="Debug" width="75px">
            <options>
                <option label="True" value="Debug"/>
                <option label="False" value="Normal"  default="true" />
            </options>
        </param>
    </params>
</plugin>
"""
import Domoticz

import sys
sys.path.append('/usr/lib/python3/dist-packages/')
from pysnmp.entity.rfc3413.oneliner import cmdgen

import json
import urllib.request
import urllib.error
from pyasn1.error import PyAsn1Error

from math import radians, cos, sin, asin, sqrt
from datetime import datetime, timedelta


#############################################################################
#                      Domoticz call back functions                         #
#############################################################################

def onStart():
    global gdeviceSuffix
    global gdeviceTypeName
    global glastSNMPValue
    global interval
    
    gdeviceSuffix = "(SNMP)"
    interval = int(Parameters["Mode4"])

    createDevices()
    glastSNMPValue = list(range(1, len(Devices)+1))
    for i in range(0,len(Devices)):
       glastSNMPValue[i]=None

    if Parameters["Mode6"] == "Debug":
        DumpConfigToDebug()
    
    ServerIP = str(Parameters["Address"])
    snmpOID = str(Parameters["Mode1"])
    snmpCommunity = Parameters["Mode2"]
    #try:
    #   snmpDataValue = str(getSNMPvalue(ServerIP,snmpOID,snmpCommunity))
    #except:
    #  snmpDataValue= None
    onHeartbeat()

    Domoticz.Heartbeat(interval)
    Domoticz.Log("started with "+str(len(Devices))+ " devices")
        
    return True

def onHeartbeat():
    ServerIP = str(Parameters["Address"])
    snmpOIDPrefix = str(Parameters["Mode1"])
    snmpCommunity = Parameters["Mode2"]
    for item in Parameters["Mode5"].split('|'):
        unitNum=Parameters["Mode5"].split('|').index(item)
        Domoticz.Log("OID Item"+snmpOIDPrefix+item+" Unit:"+str(unitNum+1))
            
        params=item.split(';')
        GetSNMPDevice(unitNum,ServerIP,snmpCommunity,snmpOIDPrefix+params[0],params[1])

    return True

def GetSNMPDevice(Unit,ServerIP,snmpCommunity,snmpOID,TypeName):
    global glastSNMPValue
    # Get new information and update the devices
    OIDpart = snmpOID.split('#')
    if(len(OIDpart)==1):
        try:
            snmpDataValue = str(getSNMPvalue(ServerIP,snmpOID,snmpCommunity))
        except Exception as err:
            snmpDataValue = none
    else:
        #try:
        Domoticz.Log("OID Item"+OIDpart[0]+" index:"+OIDpart[1])
        snmpDataValue = str(getSNMPvalueIndex(ServerIP,OIDpart[0],snmpCommunity,int(OIDpart[1])))
        #except Exception as err:
        #    snmpDataValue = none
    
    if(TypeName=="Speed" and snmpDataValue!=None):
        if(glastSNMPValue[Unit]!=None):
            speed=int(snmpDataValue)-glastSNMPValue[Unit]
            if(speed<0):
                speed=speed+0x100000000
            speed=round(8*speed/interval/(1024*1024),2)
            UpdateDevice(Unit+1,0,str(speed)+" MB/s")
            Domoticz.Log("SNMP Value (" + ServerIP + "/" + snmpCommunity + "/"+ snmpOID + ") "+TypeName+" retrieved:"+snmpDataValue + " prev:" + str(glastSNMPValue[Unit]) + " speed"+ str(speed) + ")" )
            
        glastSNMPValue[Unit]=int(snmpDataValue)
    else:
        UpdateDevice(Unit+1,0,snmpDataValue)
        Domoticz.Log("SNMP Value (" + ServerIP + "/" + snmpCommunity + "/"+ snmpOID + ") "+TypeName+" retrieved:"+snmpDataValue)

    
#############################################################################
#                         Domoticz helper functions                         #
#############################################################################

def DumpConfigToDebug():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Log("'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Log("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Log("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Log("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Log("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Log("Device sValue:   '" + Devices[x].sValue + "'")


def UpdateDevice(Unit, nValue, sValue):
    # Make sure that the Domoticz device still exists before updating it.
    # It can be deleted or never created!

    if (Unit in Devices):
        Devices[Unit].Update(nValue, str(sValue))
        Domoticz.Debug("Update " + str(nValue) + ":'" + str(sValue) + "' (" + Devices[Unit].Name + ")")

#############################################################################
#                       Device specific functions                           #
#############################################################################

def createDevices():
    # Are there any devices?
    if len(Devices) == len(Parameters["Mode5"].split('|')):
        # Could be the user deleted some devices, so do nothing
        Domoticz.Debug("Devices already exist."+ str(len(Devices)))
    else:
        # Give the devices a unique unit number. This makes updating them more easy.
        # UpdateDevice() checks if the device exists before trying to update it.

        for item in Parameters["Mode5"].split('|'):
            unitNum=Parameters["Mode5"].split('|').index(item)+1
        
            if( unitNum not in Devices):
                params=item.split(';')
                if(params[1]!="Speed"):
                    Domoticz.Device(Name=gdeviceSuffix, Unit=unitNum, TypeName=params[1]).Create()
                else:
                    Domoticz.Device(Name=gdeviceSuffix, Unit=unitNum, TypeName="Custom", Options={"Custom": "1;Mbps"}).Create()
        Domoticz.Log("Devices created."+ str(len(Devices)))
    
def getSNMPvalue(ServerIP,snmpOID,snmpCommunity):
    cmdGen = cmdgen.CommandGenerator()

    #genData = cmdgen.CommunityData('public')
    genData = cmdgen.CommunityData(str(snmpCommunity))
    Domoticz.Debug("genData Loaded." + str(genData))

    TTData = cmdgen.UdpTransportTarget((str(ServerIP), 161), retries=2)
    Domoticz.Debug("TTData Loaded." + str(TTData))

    errorIndication, errorStatus, errorIndex, varBinds = cmdGen.getCmd(genData,TTData,snmpOID)
    Domoticz.Log("DATA Loaded." + str(varBinds))
    #Domoticz.Log("TTData Loaded." + str(TTData))

    # Check for errors and print out results
    if errorIndication:
        Domoticz.Error(str(errorIndication))
    else:
        if errorStatus:
            Domoticz.Error('%s at %s' % (errorStatus.prettyPrint(),errorIndex and varBinds[int(errorIndex)-1] or '?'))
        else:
            for name, val in varBinds:
                Domoticz.Debug('%s = %s' % (name.prettyPrint(), val.prettyPrint()))

                return val.prettyPrint()

# ipAddrTable are not numerical indexed. With this workarround you can access it numerical 
# normally you use .1.3.6.1.2.1.4.20.1.1.192.168.1.1
# but if you don't know your IP you don't have the OID.
# With this you can use .1.3.6.1.2.1.4.20.1.1 with an index. 
def getSNMPvalueIndex(ServerIP,snmpOID,snmpCommunity,index):
    cmdGen = cmdgen.CommandGenerator()

    genData = cmdgen.CommunityData(str(snmpCommunity))
    Domoticz.Log("genData Loaded." + str(genData))

    TTData = cmdgen.UdpTransportTarget((str(ServerIP), 161), retries=2)
    Domoticz.Log("TTData Loaded." + str(TTData))
    
    #try: 
    errorIndication, errorStatus, errorIndex, varBinds = cmdGen.nextCmd(genData,TTData,snmpOID)
    #except PyAsn1Error as err:
    #   Domoticz.Log("Error" + str(err))
    if(len(varBinds)<index):
       Domoticz.Log("Element index larger then elements in table.")
       return ""
    else:
       varBinds2=varBinds[int(index)-1]

    # Check for errors and print out results
    if errorIndication:
        Domoticz.Error(str(errorIndication))
    else:
        if errorStatus:
            Domoticz.Error('%s at %s' % (errorStatus.prettyPrint(),errorIndex and varBinds2[int(errorIndex)-1] or '?'))
        else:
            for name, val in varBinds2:
                Domoticz.Debug('%s = %s' % (name.prettyPrint(), val.prettyPrint()))

                return val.prettyPrint()


#
# Parse an int and return None if no int is given
#

def parseIntValue(s):
        try:
            return int(s)
        except:
            return None

#
# Parse a float and return None if no float is given
#

def parseFloatValue(s):
        try:
            return float(s)
        except:
            return None
