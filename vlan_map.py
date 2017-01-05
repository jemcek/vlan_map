#!/usr/bin/python

import re
import sys
import time
import argparse
sys.path.append("/home/nms/devel-mihaj/")
#sys.path.append("./")
from snmp_helper import snmp_get_oids,snmp_get_oid,snmp_extract,snmp_extract_multi
import common
import cisco
import dellquanta
import myprint
import command
import definitions
from islands import *


"""
main program part
"""

"""parse the arguments"""
parser = argparse.ArgumentParser()
parser.add_argument("-a", "--access", help="access customer equipment",action="store_true")
parser.add_argument("-d", "--debug", help="print debug messages",action="store_true")
parser.add_argument("devices")
parser.add_argument("task", help="vendor, vlan, port, trunk, vlan-port")
parser.add_argument("parameter1", nargs="?", help="options")
parser.add_argument("parameter2", nargs="?", help="options")
parser.add_argument("-o")
#parser.add_argument("-p", action="store", dest = "port")
if len(sys.argv)==1:
    txt = open('command_tree.txt', 'r')
    print txt.read()
    sys.exit(1)

args = parser.parse_args()
devices = args.devices
task = args.task
parameter1 = args.parameter1
parameter2 = args.parameter2

if args.access:
    definitions.set_community('...')
else:
    definitions.set_community('...')

print "\n##################################################################################################################"
#check if for devices name an island was given, if yes assign all the devices to devices_list
if devices in locals():
    island_name = devices
    devices = eval(devices)
    print "Devices to check:", devices
    device_list = devices.split(',')
    island_is = 1
else:
    print "Devices to check:", devices
    if parameter2 == None: 
        island_name = ""
    else:
        island_name = parameter2
    device_list = devices.split(',')
    island_is = 0
    
#print device_list 
#check if devices exists
common.hostname_resolves(device_list)

print "##################################################################################################################"

"""main part depending on tasks"""
#who is vendor
if task == "vendor":
    #get vendor name, multiple devices accepted
    if parameter1 == None:
        command.get_device_vendors(device_list, "short")
    #get vendor names with some details, multiple devices accepted
    elif parameter1 == "all" or parameter1 == "detail":  
        command.get_device_vendors(device_list, "all")
    #
    else:
        myprint.error("Error parameter: " + parameter1)
    exit(0)            

#what vlans are configured on device    
elif task == "vlan":
    #get list of vlans configured on a device, multiple devicec accepted
    if parameter1 == None:
        command.get_vlans_info(device_list, "all", None, None)
    #ok, now the user parameter1 can be either vlan id or port id. 
    #if this is vlan id, then try to convert parameter to int, and if an int is returned we accept this as vlan id since ports are never only integers 
    #otherwise assume that this parameter was passed as interface id eq. Te1/1, 0/1, g23 etc...
    elif parameter1 == "all":
        command.get_vlans_info(device_list, "allinfo", None, None)
    elif parameter1 == "check":
        command.get_vlans_info(device_list, "check", None, None)
    elif parameter1 == "island":
        command.get_vlans_info(device_list, "vlan_island", island_name, None)

    else:
        #in case of vlan as parameter, get all the ports with this vlan configured (trunk and access)
        try:
            vlan_id = int(parameter1)
            if (vlan_id > 0) and (vlan_id < 4094):
                if parameter2 == None:
                    #command.get_ports_with_this_vlan(device_list,vlan_id), accepts multiple devices...
                    command.get_vlans_info(device_list, "ports_with_this_vlan", vlan_id, None)
                else:
                    #command.is_vlan_on_this_port(device_list, parameter2, vlan_id)
                    command.get_vlans_info(device_list, "is_vlan_on_this_port", parameter2, vlan_id)
            else:
                myprint.error("Wrong vlan id")
        #in case port as parameter, print vlans on this port
        except ValueError:
            if parameter2 == None:
                #command.get_vlans_on_this_port(device_list, parameter1, 0)
                command.get_vlans_info(device_list, "vlans_on_this_port", parameter1, 0)
            else:
                try:
                    vlan_id = int(parameter2)
                    if (vlan_id > 0) and (vlan_id < 4094):
                        command.get_vlans_info(device_list, "is_vlan_on_this_port", parameter1, vlan_id)
                    else: 
                        myprint.error("Wrong vlan id")
                except ValueError:
                    myprint.error("Wrong parameter")
    exit(0)            
            
#what ports are on device
elif task == "port":
    #print all the ports with description, multiple devices accepted
    if parameter1 == None: 
        command.get_ports_on_devices(device_list)
    #print all the ports with more details (admin status, status, speed, lacp info, trunk/access mode)
    elif parameter1 == "all" or parameter1 == "detail":
        command.get_ports_info_on_device(device_list)
    #get a single port detail information
    elif parameter1 == "vlan":
        myprint.error("Wrong parameters")
    else:
        command.get_single_port_info(device_list, parameter1)
    exit(0)            


elif task == "link":
    if parameter1 == None: 
        #command.get_common_link(device_list)
        command.get_link_info(device_list, None, None)
    #print all the ports with more details (admin status, status, speed, lacp info, trunk/access mode)
    elif parameter1 == "vlan":
        if parameter2 == None:
            #command.check_common_link_vlans(device_list)
            command.get_link_info(device_list, "vlan", "all")
        else:
            try:
                vlan_id = int(parameter2)
                if (vlan_id > 0) and (vlan_id < 4094):
                    command.get_link_info(device_list, "vlan", vlan_id)
                else: 
                    myprint.error("Wrong vlan id")
            except ValueError:
                myprint.error("Wrong parameter: %s" % parameter2)
    elif parameter1 == "island":
        #if parameter2 == None:
        command.get_link_info(device_list, "island", parameter2)
        #else:
        #    try:
        #        vlan_id = int(parameter2)
        #        print "se ne dela dobro"
        #        exit(0)
        #        if (vlan_id > 0) and (vlan_id < 4094):
        #            command.get_multiple_link_info(device_list, vlan_id)
        #        else: 
        #            myprint.error("Wrong vlan id")
        #    except ValueError:
        #        myprint.error("Wrong parameter: %s" % parameter2)
    else:
        myprint.error("Wrong parameter: %s" % parameter1)
    exit(0)            

elif task == "island":
    #
    if parameter1 == None:
        if island_is == 1:
            command.get_island_info(island_name, None)
        else:
            command.get_island_search(device_list)
    elif parameter1 == "vlan":
        command.get_vlans_info(device_list, "vlan_island", island_name, None)
    else:
        myprint.error("Wrong or missing parameters")
        exit(0)            
    #ok, now the user parameter1 can be either vlan id or port id. 
    #if this is vlan id, then try to convert parameter to int, and if an int is returned we accept this as vlan id since ports are never only integers 
    #otherwise assume that this parameter was passed as interface id eq. Te1/1, 0/1, g23 etc...
    #else:
    #    myprint.error("Wrong parameter: %s" % parameter1)
    #exit(0)            

elif task == "path":
    if parameter1 == None:
        command.get_ring_check(device_list, None)
    elif parameter1 == "vlan":
        try:
            vlan_id = int(parameter2)
            if (vlan_id > 0) and (vlan_id < 4094):
                command.get_ring_vlan_check(device_list, vlan_id)
            else: 
                myprint.error("Wrong vlan id")
        except ValueError:
            myprint.error("Wrong parameter: %s" % parameter2)
    else:
        myprint.error("Wrong or missing parameters")
        exit(0)            
    #ok, now the user parameter1 can be either vlan id or port id. 
    #if this is vlan id, then try to convert parameter to int, and if an int is returned we accept this as vlan id since ports are never only integers 
    #otherwise assume that this parameter was passed as interface id eq. Te1/1, 0/1, g23 etc...
    #else:
    #    myprint.error("Wrong parameter: %s" % parameter1)
    #exit(0)            

#not yet below this line, not yet below this line"
#not yet below this line, not yet below this line"
elif task == "vlan-port":
        vlan_list = configured_vlans_on_device(key, value)
        interfaces_dict = get_interfaces_id(key, value)
        data.append([key, value, vlan_list, interfaces_dict])
        for rows in data:
            #print rows[0], rows[1], port, vlan
            result = is_vlan_in_trunk(rows[0], rows[1], port,vlan)
            if result == True:
                print "\nvlan", vlan, "on device", devices[0], "on port", port, "set\n" 
            else:
                print "\nvlan", vlan, "on device", devices[0], "on port", port, "not set\n" 

else:
    myprint.error("\nWrong or missing command?\n")
    exit(0)



"""we do this anyway: for every device, do query on vlans configured, and port query with interface names)"""
# ok, find out what devices we have
#devices_dict = get_device_vendor(devices)
#print devices_dict
# what are vlans configerd on them, what interfaces are there with ID for snmp query
#for key, value in devices_dict.items():
#    print key, value
#    vlan_list = configured_vlans_on_device(key, value)
#    interfaces_dict = get_interfaces_id(key, value)
#    data.append([key, value, vlan_list, interfaces_dict])

#print data

exit (0)

""" recimo da zelimo preveriti otok domene na roke, podamo stikala in linke med njimi 
stikala sljtpl206a, sljtpl206b, sarnes17a, sarnes17b, lljtpl0, lljtpl1, fw zaenkrat ne stejemo zraven
preveriti zelimo ali so vlani pravilno skonfigurirani

izpis bi bil:
vlan xy manjka na stikalu switchX na linku switchX - switchY 
"""

#tole listo bi se dalo zgraditi tudi avtomatsko
links_to_check = [['lljtpl1','te1/1','sljtpl206a','0/4']]#,
        #          ['sljtpl206a','0/5','sljtpl206b','0/1'],
        #          ['sljtpl206a','0/3','sarnes17a','0/3'],
        #          ['sljtpl206b','0/3','sarnes17b','0/3'],
        #          ['sarnes17a','0/5','sarnes17b','0/1'],
        #          ['sarnes17a','0/4','larnes0','Te1/8']]



command.get_vlans_info(device_list, "allinfo", None, None)

