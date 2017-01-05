import sys
import re
#sys.path.append("/home/nms/devel-mihaj/")
sys.path.append("./")
from snmp_helper import snmp_get_oids,snmp_get_oid,snmp_extract,snmp_extract_multi
import cisco
import dellquanta
import myprint
import socket
import definitions 

SNMP_PORT = 161

vendor_desc_oid = '1.3.6.1.2.1.1.1.0' #oid to find out which vendor is behing a certain switch name 
ifDescr_oid = '.1.3.6.1.2.1.2.2.1.2'  #imena vmesnikov
ifAlias_oid = '1.3.6.1.2.1.31.1.1.1.18'  #description na vmesnikih
ifName_oid = '1.3.6.1.2.1.31.1.1.1.1'
ifHighSpeed_oid = '1.3.6.1.2.1.31.1.1.1.15' #interface status (Up/Down)
ifStatus_oid = '1.3.6.1.2.1.2.2.1.8' #interface status (Up/Down)
ifAdminStatus_oid = '1.3.6.1.2.1.2.2.1.7' #admin interface status (Up/Down)

last_oid_number_re = re.compile('\d+$')


"""with certain snmp calls the result we get back includes only certain interfaces, for example is_trunk_interfaces()
excludes Portchannel interfaces... Becasue we want that all entries have the same length of entries, we add empty string
for other entries, so that the dictionary is alligned for all interfaces"""
def allign_dict(dictionary):
    length = 0
    for value in dictionary.itervalues():
        if len(value) > length:
            length = len(value)
        #print length
    for key, value in dictionary.items():
        #print key, value
        if len(value) < length:
            dictionary[key].append("   ") 
    return dictionary

"""given the interfaces dictionary, find out the corresponding int id"""
def find_port_id(int_dict, port):
    for key, value in int_dict.items():
        if port.lower()==value[0]:
            return key

"""return vendor_name for a device name requested"""
""" example: get_device_vendor(sljtpl211a) > return Quanta """
def get_device_vendor(device):
    COMMUNITY_STRING = definitions.COMMUNITY_STRING
    snmp_data = snmp_get_oid((device, COMMUNITY_STRING, SNMP_PORT), vendor_desc_oid, display_errors=True)
    vendor_id = str(snmp_data[0][1])
    vendor_id = vendor_id.lower()
    if "cisco" in vendor_id:
        vendor_name = "Cisco"
    elif "ly" in vendor_id:
        vendor_name = "Quanta"
    elif "powerconnect" in vendor_id:
        vendor_name = "Dell"
    else:
            myprint.error("Only Cisco, Dell, Quanta supported. No Juniper??? Can't believe....")
            exit(0)
    return vendor_name  

"""return vendor names for device names requested (multiple), return values are dict"""
""" example: get_device_vendors(sljtpl1, sljtpl211a) -> return {sljtpl1:Cisco, sljtpl211a:Quanta}"""
def get_device_vendors(devices):
    COMMUNITY_STRING = definitions.COMMUNITY_STRING
    devices_dict = {}
    for value in devices:   #print value
        snmp_data = snmp_get_oid((value, COMMUNITY_STRING, SNMP_PORT), vendor_desc_oid, display_errors=True)
        vendor_id = str(snmp_data[0][1])
        vendor_id = vendor_id.lower()
        #print vendor_name
        if "cisco" in vendor_id:
            devices_dict.update({value:("Cisco",vendor_id)})
        elif "ly" in vendor_id:
            devices_dict.update({value:("Quanta",vendor_id)})
        elif "powerconnect" in vendor_id:
            devices_dict.update({value:("Dell",vendor_id)})
        else:
            myprint.error("unknown device in devices list")
            exit(0)
    devices_dict = allign_dict(devices_dict)
    return devices_dict 

"""for interfaces, we want to get back oid nr that describes them, for example te1/1 <---> .49 """
""" return value {int_id:(interface name)} """
def get_interfaces_id(host):
    COMMUNITY_STRING = definitions.COMMUNITY_STRING
    interfaces_d = {}
    interfaces_d.update({'int_id':['Interface']})
    #snmp_data = snmp_get_oids((host, COMMUNITY_STRING, SNMP_PORT), ifDescr_oid, display_errors=True)    
    snmp_data = snmp_get_oids((host, COMMUNITY_STRING, SNMP_PORT), ifName_oid, display_errors=True)    
    for varBindTableRow in snmp_data:
        for name, val in varBindTableRow:
            #print name, val, name2, val2
            val = (str(val)).lower()
            int_id = int(last_oid_number_re.findall(str(name))[0])
            """ZAENKRAT NAS NE ZANIMAJO VLAN VMESNIKI ITD"""
            if "vl" in val:
                continue
            elif "vlan" in val:
                continue
            elif "tu" in val:
                continue
            elif "nu" in val:
                continue
            elif "lo" in val:
                continue
            elif "controlled" in val:
                continue
            elif "null" in val:
                continue
            elif "cpu" in val:
                continue
            elif "cpp" in val:
                continue
            elif "span" in val:
                continue
            elif "nde" in val:
                continue
            else:
                interfaces_d.update({int_id:[val]})
    interfaces_d = allign_dict(interfaces_d)
    return interfaces_d

""" get interface description"""
def get_interfaces_desc(host, interfaces_d):
    COMMUNITY_STRING = definitions.COMMUNITY_STRING
    interfaces_d['int_id'].append('Description')
    snmp_data = snmp_get_oids((host, COMMUNITY_STRING, SNMP_PORT), ifAlias_oid, display_errors=True)    
    for varBindTableRow in snmp_data:
        for name, val in varBindTableRow:
          for name2, val2 in interfaces_d.items():
            #print name, val, name2, val2
            val = (str(val)).lower()
            val2 = (str(val2)).lower()
            int_id = int(last_oid_number_re.findall(str(name))[0])
            if int_id == name2:
                interfaces_d[int_id].append(val)
    interfaces_d = allign_dict(interfaces_d)
    return interfaces_d

""" get interface admin status """
def get_interfaces_admin_status(host, interfaces_d):
    COMMUNITY_STRING = definitions.COMMUNITY_STRING
    interfaces_d['int_id'].append('Admin')
    #print interfaces_d['int_id']
    snmp_data = snmp_get_oids((host, COMMUNITY_STRING, SNMP_PORT), ifAdminStatus_oid, display_errors=True)    
    for varBindTableRow in snmp_data:
        for name, val in varBindTableRow:
          for name2, val2 in interfaces_d.items():
            #print name, val, name2, val2
            val = (str(val)).lower()
            val2 = (str(val2)).lower()
            int_id = int(last_oid_number_re.findall(str(name))[0])
            if int_id == name2:
                if int(val) == 1:
                    interfaces_d[int_id].append(" Up  ")
                else:
                    interfaces_d[int_id].append(" Down")
    #interfaces_d = allign_dict(interfaces_d)
    return interfaces_d

""" get interface speed"""
def get_interfaces_speed(host, interfaces_d):
    COMMUNITY_STRING = definitions.COMMUNITY_STRING
    interfaces_d['int_id'].append('Speed')
    snmp_data = snmp_get_oids((host, COMMUNITY_STRING, SNMP_PORT), ifHighSpeed_oid, display_errors=True)    
    for varBindTableRow in snmp_data:
        for name, val in varBindTableRow:
          for name2, val2 in interfaces_d.items():
            #print name, val, name2, val2
            val = (str(val)).lower()
            val2 = (str(val2)).lower()
            int_id = int(last_oid_number_re.findall(str(name))[0])
            if int_id == name2:
                interfaces_d[int_id].append(val)
    interfaces_d = allign_dict(interfaces_d)
    return interfaces_d

""" get interface actual status """
def get_interfaces_status(host, interfaces_d):
    COMMUNITY_STRING = definitions.COMMUNITY_STRING
    interfaces_d['int_id'].append('Status')
    snmp_data = snmp_get_oids((host, COMMUNITY_STRING, SNMP_PORT), ifStatus_oid, display_errors=True)    
    for varBindTableRow in snmp_data:
        for name, val in varBindTableRow:
          for name2, val2 in interfaces_d.items():
            #print name, val, name2, val2
            val = (str(val)).lower()
            val2 = (str(val2)).lower()
            int_id = int(last_oid_number_re.findall(str(name))[0])
            if int_id == name2:
                if int(val) == 1:
                    interfaces_d[int_id].append("Up")
                else:
                    interfaces_d[int_id].append("Down")
    interfaces_d = allign_dict(interfaces_d)
    return interfaces_d

""" check if interface (port) is available on this device """
def check_if_interface_exists(interfaces_dict,port):
    interface = interfaces_dict['int_id'].index('Interface')
    for value in interfaces_dict.itervalues():
        if str(value[interface]) == str(port):
            return
    myprint.error("\nThis interface does not exists.\n")


def hostname_resolves(hostname):
    for name in hostname:
        try:
            socket.gethostbyname(name)
            continue 
        except socket.error:
            myprint.error("\nThis host does not exists: " + name + "\n")






