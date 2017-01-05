"""this one is where the command is parsed and further routines are called"""


import common
import myprint
import cisco
import dellquanta
import re
import definitions
#from islands import *

"""check number of devices passed as argument. if number is different from what it shoud be, return error"""
def check_device_list(device_list, number):
    if len(device_list) != number:
        myprint.error("Wrong number of devices, should be " + str(number))
    else:
        return True

"""get vendor name, with long output (show version)"""
def get_device_vendors(device_list, option):
    if option == "short":
        vendors = common.get_device_vendors(device_list)
        myprint.vendors(vendors, "short")
    else:
        vendors = common.get_device_vendors(device_list)
        myprint.vendors(vendors, "all")        


"""***********************************************************************************************************"""
"""    VLAN ROUTINES                                                                                          """
"""***********************************************************************************************************"""

"""all the vlan options parsed here"""
def get_vlans_info(device_list, task, parameter1, parameter2):
    #all this option accept only one device
    #check_device_list(device_list, 1)
    #device = device_list[0]
    for i in range (0,len(device_list)):
        device = device_list[i]
        vendor_name = common.get_device_vendor(device)

        if vendor_name == "Cisco":
            vendor = cisco
        elif vendor_name == "Dell":
            vendor = dellquanta
        elif vendor_name == "Quanta":
            vendor = dellquanta
        else:
            myprint.error("Only Cisco, Dell and Quanta deviced supported")

        if task == "all":
            vlan_list = get_vlans_on_device(device, vendor)
            myprint.vlan_list_joined(vlan_list, str("\nConfigured vlans on: " + device + "\n"))
        elif task == "allinfo":
            (interfaces_dict, vlan_list, native_tagged)  = get_all_vlans_on_all_ports(device, vendor_name)
            myprint.all_ports_all_vlan(device, interfaces_dict, vlan_list, native_tagged) 
        elif task == "allinfo-dict": #za apis klic, ki vrne dict
            (interfaces_dict, native_tagged)  = get_all_vlans_on_all_ports(device, vendor_name)
            return interfaces_dict, native_tagged
        elif task == "check":
            (interfaces_dict, vlan_list) = check_vlans(device, vendor_name)
            myprint.check_vlans(device, interfaces_dict, vlan_list)
        elif task == "vlan_island":
            (vlan_list, vlan_island_list) = check_island_vlans(device, vendor_name, parameter1+"_vlan")
            myprint.check_island_vlans(device, vlan_list, vlan_island_list, parameter1)
        elif task == "ports_with_this_vlan":
            vlan_id = parameter1
            interfaces_dict = get_ports_with_this_vlan(device, vendor, vlan_id)
            myprint.ports_with_vlan(device, vlan_id, interfaces_dict)
        elif task == "vlans_on_this_port":
            port = parameter1
            vlan_list_on_port = get_vlans_on_this_port(device, vendor, port)
            myprint.vlan_list_joined(vlan_list_on_port, str("\nFollowing vlans are configured on " + device + " port " + str(port) + "\n"))
        elif task == "is_vlan_on_this_port":
            port = parameter1
            vlan_id = parameter2
            status = is_vlan_on_this_port(device, vendor, port, vlan_id)
            myprint.myprint("\nOn " + str(device) + " port " + str(port) + " vlan " + str(vlan_id) + (" CONFIGURED\n" if status else " NOT CONFIGURED\n"))
        else:
            myprint.error("Wrong parameter options")
    exit(0)


"""what are vlans on specific device"""
def get_vlans_on_device(device, vendor):
    vlan_list = vendor.configured_vlans_on_device(device)
    return vlan_list


"""search all the ports on device and find out where this vlan in configured in either access or trunk port"""
#def get_ports_with_this_vlan(device_list,vlanid):
def get_ports_with_this_vlan(device, vendor, vlan_id):
    #here we allow only one device as search object
    #vlan should be in range
    if (vlan_id<1 or vlan_id>4094):
        myprint.error("Wrong vlan id, should be between 1-4094, exiting")
        exit(0)

    #torej npr. sljptl1 vlan 14, zelim izpis na katerih portih je vse ta vlan (access in trunk)
    vlan_list = vendor.configured_vlans_on_device(device)
    if vlan_id not in vlan_list:
        myprint.warning("\nWARNING: Vlan "+ str(vlan_id) + " not configured on " + device + "\n")

    interfaces_dict = common.get_interfaces_id(device)
    interfaces_dict = common.get_interfaces_status(device,interfaces_dict)
    interfaces_dict = vendor.get_interfaces_lacp(device, interfaces_dict)
    interfaces_dict = vendor.get_interfaces_trunk(device, interfaces_dict, vendor)
    interfaces_dict = common.get_interfaces_desc(device, interfaces_dict)
    interfaces_dict = vendor.vlan_on_all_ports(device,interfaces_dict, vlan_id) 
    return interfaces_dict

def is_vlan_on_this_port(device, vendor, port, vlan):
    vlan_list = vendor.configured_vlans_on_device(device)
    if vlan not in vlan_list:
        myprint.warning("\nWARNING: Vlan "+ str(vlan) + " not configured on " + device + "\n")

    interfaces_dict = common.get_interfaces_id(device)
    common.check_if_interface_exists(interfaces_dict,port)
    interfaces_dict = common.get_interfaces_status(device,interfaces_dict)
    interfaces_dict = vendor.get_interfaces_lacp(device, interfaces_dict)
    interfaces_dict = vendor.get_interfaces_trunk(device, interfaces_dict, vendor)
    port_id = common.find_port_id(interfaces_dict,port)

    if interfaces_dict[port_id][1] == "Down":
        myprint.warning("\nPort is down, vlan information maybe not reliable.")

    status = vendor.is_vlan_on_port(device, port_id, vlan)
    return status

def get_vlans_on_this_port(device, vendor, port):
    #here we need to now port type, in case of port channel return nothing...
    interfaces_dict = common.get_interfaces_id(device)
    common.check_if_interface_exists(interfaces_dict,port)
    interfaces_dict = common.get_interfaces_status(device,interfaces_dict)
    interfaces_dict = vendor.get_interfaces_lacp(device, interfaces_dict)
    interfaces_dict = vendor.get_interfaces_trunk(device, interfaces_dict, vendor)
    port_id = common.find_port_id(interfaces_dict,port)

    if interfaces_dict[port_id][1] == "Down":
        myprint.warning("\nPort is down, vlan information maybe not reliable.")

    vlan_list = vendor.configured_vlans_on_device(device)
    vlan_list_on_port = vendor.vlans_on_port(device, port_id, vlan_list)
    return vlan_list_on_port

def get_all_vlans_on_all_ports(device, vendor):
    if vendor == "Cisco":
        specific = cisco
    else:
        specific = dellquanta

    vlan_list = specific.configured_vlans_on_device(device)
    interfaces_dict = common.get_interfaces_id(device)
    interfaces_dict = common.get_interfaces_desc(device,interfaces_dict)
    interfaces_dict = common.get_interfaces_status(device,interfaces_dict)
    interfaces_dict = specific.get_interfaces_lacp(device, interfaces_dict)
    interfaces_dict = specific.get_interfaces_trunk(device, interfaces_dict, vendor)
    interfaces_dict = specific.get_interfaces_native_vlan(device, interfaces_dict, vendor)
    for key, value in interfaces_dict.items():
        if str(key) == "int_id":
            interfaces_dict['int_id'].append('Member')
        else:
            vlan_list_on_port = []
            vlan_list_on_port = specific.vlans_on_port(device, key, vlan_list)
            interfaces_dict[key].append(vlan_list_on_port)
    interfaces_dict = common.get_interfaces_desc(device, interfaces_dict)
    native_tagged = specific.get_native_tagged(device)
    return interfaces_dict, vlan_list, native_tagged
                
def check_vlans(device, vendor):
    if vendor != "Cisco":
        myprint.error("\nThis only works for cisco\n")
    vendor = cisco
    vlan_list = vendor.configured_vlans_on_device(device)
    interfaces_dict = common.get_interfaces_id(device)
    interfaces_dict = common.get_interfaces_status(device,interfaces_dict)
    interfaces_dict = vendor.get_interfaces_trunk(device, interfaces_dict, vendor)
    for key, value in interfaces_dict.items():
        if str(key) == "int_id":
            interfaces_dict['int_id'].append('Member')
        else:
            vlan_list_on_port = []
            vlan_list_on_port = vendor.vlans_on_port(device, key, vlan_list)
            interfaces_dict[key].append(vlan_list_on_port)
    #print interfaces_dict
    return interfaces_dict, vlan_list

def check_island_vlans(device, vendor, island_name):
    from islands import * 
    if vendor == "Cisco":
        specific = cisco
    else:
        specific = dellquanta
    #if island_name in globals():
    if island_name in locals():
        island_vlans = eval(island_name)
        island_vlans = island_vlans.split(',')
        #print island_vlans
    else:
        myprint.error("Vlans for this island not specified correctly") 


    vlan_list = specific.configured_vlans_on_device(device)
    #print vlan_list

    return vlan_list, island_vlans



"""***********************************************************************************************************"""
"""    PORT ROUTINES                                                                                          """
"""***********************************************************************************************************"""

def get_ports_on_devices(device_list):
    check_device_list(device_list, 1)
    name = device_list[0]
    vendor_name = common.get_device_vendor(name)
    interfaces_dict = common.get_interfaces_id(name)
    interfaces_dict = common.get_interfaces_desc(name,interfaces_dict)
    #myprint.dict_sorted_with_message(interfaces_dict, str("Ports on " + name))
    myprint.dict_sorted_interface(interfaces_dict, name)


def get_ports_info_on_device(device_list):
    check_device_list(device_list, 1)
    name = device_list[0]
    vendor_name = common.get_device_vendor(name)
    if vendor_name == "Cisco":
        specific = cisco
    else:
        specific = dellquanta

    interfaces_dict = common.get_interfaces_id(name)
    interfaces_dict = common.get_interfaces_admin_status(name,interfaces_dict)
    interfaces_dict = common.get_interfaces_status(name,interfaces_dict)
    interfaces_dict = common.get_interfaces_speed(name, interfaces_dict)
    interfaces_dict = specific.get_interfaces_lacp(name, interfaces_dict)
    interfaces_dict = specific.get_interfaces_trunk(name, interfaces_dict, vendor_name) #first is link up/down info, second is lacp info
    interfaces_dict = common.get_interfaces_desc(name,interfaces_dict)
    myprint.dict_sorted_interface(interfaces_dict, name)


def get_single_port_info(device_list, port):
    check_device_list(device_list, 1)
    name = device_list[0]
    vendor_name = common.get_device_vendor(name)
    if vendor_name == "Cisco":
        specific = cisco
    else:
        specific = dellquanta

    interfaces_dict = common.get_interfaces_id(name)
    common.check_if_interface_exists(interfaces_dict,port)
    interfaces_dict = common.get_interfaces_admin_status(name,interfaces_dict)
    interfaces_dict = common.get_interfaces_status(name,interfaces_dict)
    interfaces_dict = common.get_interfaces_speed(name, interfaces_dict)
    interfaces_dict = cisco.get_interfaces_lacp(name, interfaces_dict)
    interfaces_dict = cisco.get_interfaces_trunk(name, interfaces_dict, vendor_name) #first is link up/down info, second is lacp info
    interfaces_dict = common.get_interfaces_desc(name,interfaces_dict)
    myprint.dict_interface(interfaces_dict, name, port)


"""***********************************************************************************************************"""
"""    CHECK ROUTINES                                                                                         """
"""***********************************************************************************************************"""

def get_link_info(device_list, task, vlan_id):
    #all this option accept two devices
    check_device_list(device_list, 2)
    device1 = device_list[0]
    device2 = device_list[1]
    vendor_name1 = common.get_device_vendor(device1)
    vendor_name2 = common.get_device_vendor(device2)

    if vendor_name1 == "Cisco":
        vendor1 = cisco
    elif vendor_name1 == "Dell":
        vendor1 = dellquanta
    elif vendor_name1 == "Quanta":
        vendor1 = dellquanta
    else:
        myprint.error("Only Cisco, Dell and Quanta deviced supported")
    if vendor_name2 == "Cisco":
        vendor2 = cisco
    elif vendor_name2 == "Dell":
        vendor2 = dellquanta
    elif vendor_name2 == "Quanta":
        vendor2 = dellquanta
    else:
        myprint.error("Only Cisco, Dell and Quanta deviced supported")


    if task == None:
        (port1, port2) = get_common_link(device1, device2)
        if port1 != None and port2 != None:
            myprint.myprint("\nBased on descripton this is common link: %s %s %s %s \n" % (device1, port1, device2, port2))
        else:
            myprint.error("\nNo common link between %s and %s \n" % (device1, device2))

    elif task == "vlan" and vlan_id == "all":
        (port1, port2) = get_common_link(device1, device2)
        if port1 != None and port2 != None:
            myprint.myprint("\nBased on descripton this is common link: %s %s %s %s \n" % (device1, port1, device2, port2))
        else:
            myprint.error("\nNo common link between %s and %s \n" % (device1, device2))

        (list1, list2) = check_common_link_vlans(device1, vendor1, port1, device2, vendor2, port2)
        
        print device1, port1, "vlans: ", (', '.join(str(x) for x in list1))
        print device2, port2, "vlans: ", (', '.join(str(x) for x in list2))

        #on dell and quanta we can not remove vlan 1, so let's ignore it in compare
        if list1 == list2:
            print "\nConfigured vlans are the same"
        elif list1[0] == 1:
            if list1[1:] == list2:
                print "\nConfigured vlans are the same, ignoring vlan 1 on " + device1 + "\n"
        elif list2[0] == 1:
            if list1 == list2[1:]:
                print "\nConfigured vlans are the same, ignoring vlan 1 on " + device2 + "\n"
        else:
            print "\nConfigured vlans are NOT the same\n"

    elif task == "island":
        island_id = vlan_id
        (island_dev, island_v) = get_island_info(island_id, "values")

        island_dev_list = island_dev.split(",")
        island_vlan_list = island_v.split(",")
        #print island_dev
        if device1 not in island_dev_list:
            myprint.error("\nDevice %s not part of island %s \n" % (device1, island_id))
        if device2 not in island_dev_list:
            myprint.error("\nDevice %s not part of island %s \n" % (device2, island_id))


        (port1, port2) = get_common_link(device1, device2)
        if port1 != None and port2 != None:
            myprint.myprint("Based on descripton this is common link: %s %s %s %s \n" % (device1, port1, device2, port2))
        else:
            myprint.error("\nNo common link between %s and %s \n" % (device1, device2))

        (list1, list2) = check_common_link_vlans(device1, vendor1, port1, device2, vendor2, port2)
        
        print "Vlans in island", island_id, island_v
        print device1, port1, "vlans: ", (', '.join(str(x) for x in list1))
        print device2, port2, "vlans: ", (', '.join(str(x) for x in list2))

        #print island_vlan_list
        #print list1
        print
        for i in island_vlan_list:
            if int(i) not in list1:
                print "Vlan", i, "missing on", device1, port1
        for i in island_vlan_list:
            if int(i) not in list2:
                print "Vlan", i, "missing on", device2, port2
        for i in list1:
            if str(i) not in island_vlan_list:
                print "... but vlan", i, "configured on", device1, port1, "and not part of island", island_id
        for i in list2:
            if int(i) not in list2:
                print "... but vlan", i, "configured on", device2, port2, "and not part of island", island_id
        print

    elif task == "vlan":
        (port1, port2) = get_common_link(device1, device2)
        if port1 != None and port2 != None:
            myprint.myprint("\nBased on descripton this is common link: %s %s %s %s \n" % (device1, port1, device2, port2))
        else:
            myprint.error("\nNo common link between %s and %s \n" % (device1, device2))
        (list1, list2) = check_common_link_vlans(device1, vendor1, port1, device2, vendor2, port2)
        myprint.myprint("On " + str(device1) + " port " + str(port1) + " vlan " + str(vlan_id) + (" CONFIGURED" if vlan_id in list1 else " NOT CONFIGURED"))
        myprint.myprint("On " + str(device2) + " port " + str(port2) + " vlan " + str(vlan_id) + (" CONFIGURED\n" if vlan_id in list2 else " NOT CONFIGURED\n"))
    else:
        myprint.error("Wrong parameter options")

def get_common_link(device1, device2):
    port1 = None
    port2 = None
    interfaces_dict1 = common.get_interfaces_id(device1)
    interfaces_dict1 = common.get_interfaces_status(device1,interfaces_dict1)
    interfaces_dict1 = common.get_interfaces_desc(device1, interfaces_dict1)
    interfaces_dict2 = common.get_interfaces_id(device2)
    interfaces_dict2 = common.get_interfaces_status(device2,interfaces_dict2)
    interfaces_dict2 = common.get_interfaces_desc(device2, interfaces_dict2)
    for key, value in interfaces_dict1.items():
        string = '\\b%s\\b' % device2
        if len(re.findall(string, value[2])) > 0:
            port1 = value[0]
    for key, value in interfaces_dict2.items():
        string = '\\b%s\\b' % device1
        if len(re.findall(string, value[2])) > 0:
            port2 = value[0]
    return port1, port2

def check_common_link_vlans(device1, vendor1, port1, device2, vendor2, port2):
    list1 = get_vlans_on_this_port(device1, vendor1, port1)
    list2 = get_vlans_on_this_port(device2, vendor2, port2)
    return list1, list2

    
def get_multiple_link_info(device_list, vlan_id):
    items_number = len(device_list)
    if (items_number % 2) != 0:
        myprint.error("Number of devices must be odd")

    for i in range(0, items_number, 2):
        device1 = device_list[i]
        device2 = device_list[i+1]
        vendor_name1 = common.get_device_vendor(device1)
        vendor_name2 = common.get_device_vendor(device2)
        if vendor_name1 == "Cisco":
            vendor1 = cisco
        elif vendor_name1 == "Dell":
            vendor1 = dellquanta
        elif vendor_name1 == "Quanta":
            vendor1 = dellquanta
        else:
            myprint.error("Only Cisco, Dell and Quanta deviced supported")
        if vendor_name2 == "Cisco":
            vendor2 = cisco
        elif vendor_name2 == "Dell":
            vendor2 = dellquanta
        elif vendor_name2 == "Quanta":
            vendor2 = dellquanta
        else:
            myprint.error("Only Cisco, Dell and Quanta deviced supported")

        (port1, port2) = get_common_link(device1, device2)
        if port1 != None and port2 != None:
            myprint.myprint("\nBased on descripton this is common link: %s %s %s %s \n" % (device1, port1, device2, port2))
        else:
            myprint.error("\nNo common link between %s and %s \n" % (device1, device2))

        (list1, list2) = check_common_link_vlans(device1, vendor1, port1, device2, vendor2, port2)
        myprint.myprint("On " + str(device1) + " port " + str(port1) + " vlan " + str(vlan_id) + (" CONFIGURED" if vlan_id in list1 else " NOT CONFIGURED"))
        myprint.myprint("On " + str(device2) + " port " + str(port2) + " vlan " + str(vlan_id) + (" CONFIGURED\n" if vlan_id in list2 else " NOT CONFIGURED\n"))


def get_ring_check(device_list, vlan_id):
    items_number = len(device_list)
    if (items_number < 3):
        myprint.error("Minimum devices is 3...")

    for i in range(0, items_number-1):
        device1 = device_list[i]
        device2 = device_list[i+1]
        vendor_name1 = common.get_device_vendor(device1)
        vendor_name2 = common.get_device_vendor(device2)
        if vendor_name1 == "Cisco":
            vendor1 = cisco
        elif vendor_name1 == "Dell":
            vendor1 = dellquanta
        elif vendor_name1 == "Quanta":
            vendor1 = dellquanta
        else:
            myprint.error("Only Cisco, Dell and Quanta deviced supported")
        if vendor_name2 == "Cisco":
            vendor2 = cisco
        elif vendor_name2 == "Dell":
            vendor2 = dellquanta
        elif vendor_name2 == "Quanta":
            vendor2 = dellquanta
        else:
            myprint.error("Only Cisco, Dell and Quanta deviced supported")

        (port1, port2) = get_common_link(device1, device2)
        if port1 != None and port2 != None:
            myprint.myprint("\nBased on descripton this is common link: %s %s %s %s \n" % (device1, port1, device2, port2))
        else:
            myprint.error("\nError! No common link between %s and %s \nAre doing it wireless? :)\n" % (device1, device2))
    exit(0)

def get_ring_vlan_check(device_list, vlan_id):
    ring_status = 1
    items_number = len(device_list)
    if (items_number < 3):
        myprint.error("Minimum devices is 3...")

    for i in range(0, items_number-1):
        segment_status = 1
        device1 = device_list[i]
        device2 = device_list[i+1]
        vendor_name1 = common.get_device_vendor(device1)
        vendor_name2 = common.get_device_vendor(device2)
        if vendor_name1 == "Cisco":
            vendor1 = cisco
        elif vendor_name1 == "Dell":
            vendor1 = dellquanta
        elif vendor_name1 == "Quanta":
            vendor1 = dellquanta
        else:
            myprint.error("Only Cisco, Dell and Quanta deviced supported")
        if vendor_name2 == "Cisco":
            vendor2 = cisco
        elif vendor_name2 == "Dell":
            vendor2 = dellquanta
        elif vendor_name2 == "Quanta":
            vendor2 = dellquanta
        else:
            myprint.error("Only Cisco, Dell and Quanta deviced supported")

        myprint.myprint("\n------------------------------------------------")
        myprint.myprint("Checking segment between %s and %s" % (device1, device2))
        vlan_list = vendor1.configured_vlans_on_device(device1)
        if vlan_id in vlan_list:
            myprint.myprint("Vlan "+ str(vlan_id) + " configured on " + device1)
        else:
            myprint.warning("!!! WARNING: Vlan "+ str(vlan_id) + " NOT configured on " + device1 + "!!!")
            segment_status = 0
            ring_status = 0
        vlan_list = vendor2.configured_vlans_on_device(device2)
        if vlan_id in vlan_list:
            myprint.myprint("Vlan "+ str(vlan_id) + " configured on " + device2)
        else:
            myprint.warning("!!! WARNING: Vlan "+ str(vlan_id) + " NOT configured on " + device2 + "!!!")
            segment_status = 0
            ring_status = 0

        (port1, port2) = get_common_link(device1, device2)
        if port1 != None and port2 != None:
            myprint.myprint("Based on descripton this is common link: %s %s %s %s" % (device1, port1, device2, port2))
        else:
            myprint.error("\nError! No common link between %s and %s \n" % (device1, device2))

        (list1, list2) = check_common_link_vlans(device1, vendor1, port1, device2, vendor2, port2)
        if vlan_id in list1:
            myprint.myprint("On " + str(device1) + " port " + str(port1) + " vlan " + str(vlan_id) + " CONFIGURED")
        else:
            myprint.myprint("On " + str(device1) + " port " + str(port1) + " vlan " + str(vlan_id) + " NOT CONFIGURED")
            segment_status = 0
            ring_status = 0
        if vlan_id in list2:
            myprint.myprint("On " + str(device2) + " port " + str(port2) + " vlan " + str(vlan_id) + " CONFIGURED")
        else:
            myprint.myprint("On " + str(device2) + " port " + str(port2) + " vlan " + str(vlan_id) + " NOT CONFIGURED")
            segment_status = 0
            ring_status = 0

        if segment_status == 1:
            myprint.myprint("Segment OK")
        else:
            myprint.myprint("Segment NOK")
    if ring_status == 1:
        myprint.myprint("\nTotal path OK\n")
    else:
        myprint.myprint("\nTotal path NOK\n")
    exit(0)


def get_island_info(island_name, parameter1):
    from islands import *
    print
    #if island_name in globals():
    if island_name in locals():
        island_devices = eval(island_name)
        if parameter1 != "values":
            myprint.myprint("Devices in island " + island_name + ": " + island_devices)
    else:
        myprint.error("Wrong island name") 

    island_vlan_name = island_name + "_vlan" 
    #if island_vlan_name in globals():
    if island_vlan_name in locals():
        island_vlans = eval(island_vlan_name)
        if parameter1 != "values":
            myprint.myprint("Vlans in island " + island_name + ": " + island_vlans)
    else:
        myprint.error("Missing island vlans") 

    if parameter1 == "values":
        #return island_devices.split(","), island_vlans.split(",")
        return island_devices, island_vlans
    else:
        print
        exit(0)

def get_island_search(device_list):
    print
    from islands import *
    for key,value in locals().items():
        if str(key)  == "device_list":
            pass
        elif device_list[0] in value:
            print device_list[0], "is member of island", key

    print
    exit(0)
