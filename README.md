# SNMPReader
With this plugin you can bring several SNMP OID per ip address each time on your Domoticz server.

Debian Requirements:
 - Install "python3-pysnmp4" with "sudo apt-get install python3-pysnmp4"

Domoticz Installation instructions:
 - Create Plugin Folder "SNMPreader2" under "domoticz/plugins" folder
 - Save this script as "plugin.py" on "SNMPreader2" folder
 - Restart domoticz service.
 - Add a new entry of this Hardware on your domoticz installation (Setup/Hardware/select and add "SNMPreader2")

 - use OID prefix the part of the OID that is the same for all values you have to read
   Example: .1.3.6.1.2.1.2.2.1.
 - Use OID list for the list of OID's you want to read
   Each OID is follow by the type in Domoticz of the OID's
   The type Speed is used to calculate the speed from a octet counter
   
   Example: 10.5;Speed|16.5;Speed|10.1;Speed|16.1;Speed|10.4;Speed|16.4;Speed
   
   This example will read OID's and calculate the speed from it
   
       .1.3.6.1.2.1.2.2.1.10.5     inOctets on WAN2   
       .1.3.6.1.2.1.2.2.1.16.5     outOctets on WAN2       
       .1.3.6.1.2.1.2.2.1.10.1     inOctets on LAN 
       .1.3.6.1.2.1.2.2.1.16.1     outOctets on LAN 
       .1.3.6.1.2.1.2.2.1.10.4     inOctets on WAN1        
       .1.3.6.1.2.1.2.2.1.16.4     outOctets on WAN1
       
    With .1.3.6.1.2.1.4.20.1.1#1 you can get the first element of the ipAddrTable (WAN) table. of course you can use #2 for the second in case of dual WAN modems  
    Normally you shouled use .1.3.6.1.2.1.4.20.1.1.192.168.1.1
    But if you don't know your IP you don't have the OID.
    
Hope you like it!!
