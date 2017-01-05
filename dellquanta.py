import sys
import re
import common
import definitions

#sys.path.append("/home/nms/devel-mihaj/")
sys.path.append("./")
from snmp_helper import snmp_get_oids,snmp_get_oid,snmp_extract,snmp_extract_multi

SNMP_PORT = 161

port_type_other_oid = '1.2.840.10006.300.43.1.2.1.1.4'
is_trunk_other_oid = '1.3.6.1.2.1.17.7.1.4.5.1.2' # pove ali so dovoljeni tag ali untagged, ocitno dela samo za Quanto
trunk_vlan_other_oid = '1.3.6.1.2.1.17.7.1.4.2.1.4.0' # no idea where the last 0 commes from, it also works with 1,2,3...
vlans_on_other_oid ="1.3.6.1.2.1.17.7.1.4.3.1.1"


last_oid_number_re = re.compile('\d+$')


def vlans_on_port(device_name,port,vlans_configured):
    COMMUNITY_STRING = definitions.COMMUNITY_STRING
    vlan_list = [] 
    #print vlans_configured
    for vlan in vlans_configured:
        oid_new = trunk_vlan_other_oid+'.'+str(vlan)
        snmp_data = snmp_get_oid((device_name, COMMUNITY_STRING, SNMP_PORT), oid_new, display_errors=True)
        result = snmp_data[0][1].prettyPrint()
        result = result[2:] #remove 0x at the beggining
        #if int(result,16) & 2**(4*len(result)-int(key)):
        if int(result,16) & 2**(4*len(result)-port):    
            #print "vlan", vlan, "on port", port
            vlan_list.append(vlan)
    if len(vlan_list) == 4094:
            return ["all"]            
    else:
            return vlan_list        
            
def is_vlan_on_port(device_name,port,vlan):
    #print vlans_configured
    COMMUNITY_STRING = definitions.COMMUNITY_STRING
    oid_new = trunk_vlan_other_oid+'.'+str(vlan)
    snmp_data = snmp_get_oid((device_name, COMMUNITY_STRING, SNMP_PORT), oid_new, display_errors=True)
    result = snmp_data[0][1].prettyPrint()
    result = result[2:] #remove 0x at the beggining
        #if int(result,16) & 2**(4*len(result)-int(key)):
    if int(result,16) & 2**(4*len(result)-port):    
        return 1
    else:
        return 0

def vlan_on_all_ports(device_name, interfaces_d, vlan):
    COMMUNITY_STRING = definitions.COMMUNITY_STRING
    interfaces_d['int_id'].append('Member')
    oid_new = trunk_vlan_other_oid+'.'+str(vlan)
    snmp_data = snmp_get_oid((device_name, COMMUNITY_STRING, SNMP_PORT), oid_new, display_errors=True)
    result = snmp_data[0][1].prettyPrint()
    result = result[2:] #remove 0x at the beggining
    #print result
    #print interfaces_d
    for key, value in interfaces_d.items():
        try:
            int_id = int(key)
            #print int_id
            if int(result,16) & 2**(4*len(result)-int(key)):
            #    print "member"
                interfaces_d[key].append(True)
            else:
            #    print "not member"
                interfaces_d[key].append(False)
        except ValueError:
            continue

    interfaces_d = common.allign_dict(interfaces_d)
    return interfaces_d

def is_vlan_in_trunk(device_name,vendor,port,vlan):
    COMMUNITY_STRING = definitions.COMMUNITY_STRING
    oid_new = trunk_vlan_other_oid+'.'+str(vlan)
    snmp_data = snmp_get_oid((device_name, COMMUNITY_STRING, SNMP_PORT), oid_new, display_errors=True)
    result = snmp_data[0][1].prettyPrint()
    result = result[2:] #remove 0x at the beggining
    #print result
    for n in range(1,4*len(result)):
        if int(result,16) & 2**(4*len(result)-n):
            print "ports included", n
    if int(result,16) & 2**(4*len(result)-port_id):
        return True
    else:
        return False

def get_interfaces_trunk(device_name,interfaces_d, vendor):
    COMMUNITY_STRING = definitions.COMMUNITY_STRING
    interfaces_d['int_id'].append('Type')
    status = interfaces_d['int_id'].index('Status')
    lacp = interfaces_d['int_id'].index('Lacp')
    snmp_data = snmp_get_oids((device_name, COMMUNITY_STRING, SNMP_PORT), is_trunk_other_oid, display_errors=True)    
    for varBindTableRow in snmp_data:
        for name, val in varBindTableRow:
            for name2, val2 in interfaces_d.items():
                int_id = int(last_oid_number_re.findall(str(name))[0])
                if int_id == name2:
                    #print name, val, name2, val2, vendor
                    if interfaces_d[int_id][status] == "Up" and vendor == "Quanta":
                        #int(val) == 1 pomeni access
                        if int(val) == 1:
                            #we print this only for non LACP ports, for LACP information is not reliable
                            if interfaces_d[int_id][lacp] == "Yes":
                                interfaces_d[int_id].append("    ")
                            else:
                                interfaces_d[int_id].append("Access")
                        else:
                            if interfaces_d[int_id][lacp] == "Yes":
                                interfaces_d[int_id].append("      ")
                            else:
                                interfaces_d[int_id].append("Trunk ")
                    else:
                        interfaces_d[int_id].append("     ")

    common.allign_dict(interfaces_d)
    return interfaces_d

def get_interfaces_lacp(device_name,interfaces_d):
    COMMUNITY_STRING = definitions.COMMUNITY_STRING
    interfaces_d['int_id'].append('Lacp')
    status = interfaces_d['int_id'].index('Status')
    snmp_data = snmp_get_oids((device_name, COMMUNITY_STRING, SNMP_PORT), port_type_other_oid, display_errors=True)    
    for varBindTableRow in snmp_data:
        for name, val in varBindTableRow:
            for name2, val2 in interfaces_d.items():
                int_id = int(last_oid_number_re.findall(str(name))[0])
                if int_id == name2:
                    #print name, val, name2, val2
                    if (int(val)>0) and (int(val) != int(name2)):
                        interfaces_d[int_id].append("Yes")
                    else:
                        interfaces_d[int_id].append("   ")

    interfaces_d = common.allign_dict(interfaces_d)
    return interfaces_d

def configured_vlans_on_device(device):
    COMMUNITY_STRING = definitions.COMMUNITY_STRING
    vlans = []
    snmp_data = snmp_get_oids((device, COMMUNITY_STRING, SNMP_PORT), vlans_on_other_oid, display_errors=True)
    for varBindTableRow in snmp_data:   
        for name, val in varBindTableRow:
            #print name, val
            vlans.append(int(last_oid_number_re.findall(str(name))[0]))

    return vlans

#tole je dodano zaenkrat samo da napolni dictionary, brez vrednosti
def get_interfaces_native_vlan(device_name,interfaces_d,vendor):
    COMMUNITY_STRING = definitions.COMMUNITY_STRING
    interfaces_d['int_id'].append('Native')
    interfaces_d = common.allign_dict(interfaces_d)        
    return interfaces_d

def get_native_tagged(device):
    return 1

