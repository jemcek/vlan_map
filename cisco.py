import sys
import re
import common

#sys.path.append("/home/nms/devel-mihaj/")
sys.path.append("./")
from snmp_helper import snmp_get_oids,snmp_get_oid,snmp_extract,snmp_extract_multi
import definitions

SNMP_PORT = 161

#cisco specific
vlans_on_cisco_oid = '1.3.6.1.4.1.9.9.46.1.3.1.1.2' #kateri vlani so kreirani na stikalu
is_trunk_cisco_oid = '1.3.6.1.4.1.9.9.46.1.6.1.1.14' #pove ali je port trunk ali access? (1 - trunk, 2 - access)
access_vlan_cisco_oid = '1.3.6.1.4.1.9.9.68.1.2.2.1.2' #ce je port access, kateremu vlanu pripada
trunk_vlans_cisco_oid =['1.3.6.1.4.1.9.9.46.1.6.1.1.4', #kateri vlani so v trunk portu za vlane od 0-1024
                        '1.3.6.1.4.1.9.9.46.1.6.1.1.17', # za vlane od 1024 - 2048
                        '1.3.6.1.4.1.9.9.46.1.6.1.1.18', #za vlane od 2048 - 3072
                        '1.3.6.1.4.1.9.9.46.1.6.1.1.19'] #za vlane od 3072 - 4096
native_vlan_cisco_oid = '1.3.6.1.4.1.9.9.46.1.6.1.1.5' #native
native_vlan_tagged_cisco_oid = '1.3.6.1.4.1.9.9.46.1.6.3.0' #native tagged
port_type_cisco_oid = '1.2.840.10006.300.43.1.2.1.1.4' 
port_channel_cisco_oid = '1.2.840.10006.300.43.1.2.1.1.13' 


last_oid_number_re = re.compile('\d+$')

#after some probes I discoverd, that this oid 1.2.840.10006.300.43.1.2.1.1.13 returns 0 if port is not a member of portchannel
#and returns other number, if port is member of portchannel. Besides this oid 1.2.840.10006.300.43.1.2.1.1.4 returns 1 if port 
#a port channel type and 0 if not
def get_interfaces_lacp(device_name,interfaces_d):
    COMMUNITY_STRING = definitions.COMMUNITY_STRING
    interfaces_d['int_id'].append('Lacp')
    #find position of interface status, we need this in our decision
    status = interfaces_d['int_id'].index('Status')
    snmp_data = snmp_get_oids((device_name, COMMUNITY_STRING, SNMP_PORT), port_type_cisco_oid, display_errors=True)    
    for varBindTableRow in snmp_data:
        for name, val in varBindTableRow:
            for name2, val2 in interfaces_d.items():
                int_id = int(last_oid_number_re.findall(str(name))[0])
                if int_id == name2:
                    #print name, val, name2, val2
                    if interfaces_d[int_id][status] == "Up":
                        if int(val) > 0:
                            interfaces_d[int_id].append("Yes")
                        else:
                            interfaces_d[int_id].append("   ")
                    else:
                        interfaces_d[int_id].append("   ")

    interfaces_d = common.allign_dict(interfaces_d)        
    return interfaces_d

#this one relies on the interface status, because otherwise the information is not relevant
#the status parameter indicates position inside the list of specific interface where the int status is stored
def get_interfaces_trunk2(device_name,interfaces_d,vendor):
    COMMUNITY_STRING = definitions.COMMUNITY_STRING
    interfaces_d['int_id'].append('Type')
    status = interfaces_d['int_id'].index('Status')
    lacp = interfaces_d['int_id'].index('Lacp')
    snmp_data = snmp_get_oids((device_name, COMMUNITY_STRING, SNMP_PORT), is_trunk_cisco_oid, display_errors=True)    
    for varBindTableRow in snmp_data:
        for name, val in varBindTableRow:
            for name2, val2 in interfaces_d.items():
                int_id = int(last_oid_number_re.findall(str(name))[0])
                if int_id == name2:
                    if interfaces_d[int_id][status] == "Up":
                        if interfaces_d[int_id][lacp] == "Yes":
                            interfaces_d[int_id].append(" ?? ")
                        else:
                            if int(val) == 1:
                                interfaces_d[int_id].append("Trunk")
                            else:
                                interfaces_d[int_id].append("Access")
                    else:
                        interfaces_d[int_id].append("    ")

    interfaces_d = common.allign_dict(interfaces_d)        
    return interfaces_d

def get_interfaces_trunk(device_name,interfaces_d,vendor):
    COMMUNITY_STRING = definitions.COMMUNITY_STRING
    interfaces_d['int_id'].append('Type')
    for key, value in interfaces_d.items():
        if key == 'int_id': continue
        snmp_data = snmp_get_oid((device_name, COMMUNITY_STRING, SNMP_PORT), access_vlan_cisco_oid+"."+str(key), display_errors=True)
        result = snmp_data[0][1].prettyPrint()
        if result == "No Such Instance currently exists at this OID":
            interfaces_d[key].append("Trunk")
        else:
            interfaces_d[key].append("Access")
    interfaces_d = common.allign_dict(interfaces_d)        
    return interfaces_d

def get_interfaces_native_vlan(device_name,interfaces_d,vendor):
    COMMUNITY_STRING = definitions.COMMUNITY_STRING
    interfaces_d['int_id'].append('Native')
    status = interfaces_d['int_id'].index('Status')
    trunk = interfaces_d['int_id'].index('Type')
    snmp_data = snmp_get_oids((device_name, COMMUNITY_STRING, SNMP_PORT), native_vlan_cisco_oid, display_errors=True)    
    for varBindTableRow in snmp_data:
        for name, val in varBindTableRow:
            for name2, val2 in interfaces_d.items():
                int_id = int(last_oid_number_re.findall(str(name))[0])
                if int_id == name2:
                    #if interfaces_d[int_id][status] == "Up":
                        if interfaces_d[int_id][trunk] == "Trunk":
                            interfaces_d[int_id].append(int(val))
                        else:
                            interfaces_d[int_id].append("    ")

    interfaces_d = common.allign_dict(interfaces_d)        
    return interfaces_d

def get_native_tagged(device):
    COMMUNITY_STRING = definitions.COMMUNITY_STRING
    snmp_data = snmp_get_oid((device, COMMUNITY_STRING, SNMP_PORT), native_vlan_tagged_cisco_oid, display_errors=True)
    native_tagged = snmp_data[0][1]
    return native_tagged


"""search for vlan on all ports and append for each interface info if this vlan in configured on port or not"""
def vlan_on_all_ports(device_name, interfaces_d, vlan):
    COMMUNITY_STRING = definitions.COMMUNITY_STRING
    interfaces_d['int_id'].append('Member')
    status = interfaces_d['int_id'].index('Status')
    lacp = interfaces_d['int_id'].index('Lacp')
    trunk = interfaces_d['int_id'].index('Type')
    for key, value in interfaces_d.items():
            if value[trunk] == "Trunk":
                if 0 <= int(vlan) < 1024:
                    oid_new = trunk_vlans_cisco_oid[0]+'.'+str(key)
                    factor = 1
                elif 1024 <= int(vlan) < 2048:
                    oid_new = trunk_vlans_cisco_oid[1]+'.'+str(key)
                    factor = 2
                elif 2048 <= int(vlan) < 3072:
                    oid_new = trunk_vlans_cisco_oid[2]+'.'+str(key)
                    factor = 3
                elif 3072 <= int(vlan) < 4096:
                    oid_new = trunk_vlans_cisco_oid[3]+'.'+str(key)
                    factor = 4
                else:
                    myprint.error("strange...")
                snmp_data = snmp_get_oid((device_name, COMMUNITY_STRING, SNMP_PORT), oid_new, display_errors=True)
                result = snmp_data[0][1].prettyPrint()
                if result == "No Such Instance currently exists at this OID": continue
                result = result[2:]
                result = result.ljust(256,"0") #for 2k, 3k and 4k the result in not full table so we fill it

                a = (factor*1024) - (int(vlan)+1)
                if int(result,16) & 2**a:
                    interfaces_d[key].append(True)
                else:
                    interfaces_d[key].append(False)

            elif value[trunk] == "Access":
                if value[lacp]  != "Yes":
                    snmp_data = snmp_get_oid((device_name, COMMUNITY_STRING, SNMP_PORT), access_vlan_cisco_oid+"."+str(key), display_errors=True)
                    result = snmp_data[0][1].prettyPrint()
                    if int(result) == vlan:
                        interfaces_d[key].append(True)
                    else:
                        interfaces_d[key].append(False)

    interfaces_d = common.allign_dict(interfaces_d)
    return interfaces_d

"""is particular vlan configured on particular port"""
def is_vlan_on_port(device_name, port_id, vlan):
    COMMUNITY_STRING = definitions.COMMUNITY_STRING
    snmp_data = snmp_get_oid((device_name, COMMUNITY_STRING, SNMP_PORT), access_vlan_cisco_oid+"."+str(port_id), display_errors=True)
    result = snmp_data[0][1].prettyPrint()
    if result == "No Such Instance currently exists at this OID":
        if 0 <= int(vlan) < 1024:
            oid_new = trunk_vlans_cisco_oid[0]+'.'+str(port_id)
            factor = 1
        elif 1024 <= int(vlan) < 2048:
            oid_new = trunk_vlans_cisco_oid[1]+'.'+str(port_id)
            factor = 2
        elif 2048 <= int(vlan) < 3072:
            oid_new = trunk_vlans_cisco_oid[2]+'.'+str(port_id)
            factor = 3
        elif 3072 <= int(vlan) < 4096:
            oid_new = trunk_vlans_cisco_oid[3]+'.'+str(port_id)
            factor = 4
        else:
            myprint.error("strange...")

        snmp_data = snmp_get_oid((device_name, COMMUNITY_STRING, SNMP_PORT), oid_new, display_errors=True)
        result = snmp_data[0][1].prettyPrint()
        result = result[2:]
        result = result.ljust(256,"0") #for 2k, 3k and 4k the result in not full table so we fill it

        a = (factor*1024) - (int(vlan)+1)
        if int(result,16) & 2**a:
            return 1
        else:
            return 0

    else: #access port
        snmp_data = snmp_get_oid((device_name, COMMUNITY_STRING, SNMP_PORT), access_vlan_cisco_oid+"."+str(port_id), display_errors=True)
        result = snmp_data[0][1].prettyPrint()
        if int(result) == int(vlan):
            return 1
        else:
            return 0

"""which vlans are configured on specicic port"""
# popravi kako dobis trunk informacijo
# ce je skonfiguriran kot lacp, potem vlan info ni nujno pravi...
#
def vlans_on_port(device_name,port_id,vlans_configured):
    COMMUNITY_STRING = definitions.COMMUNITY_STRING
    vlan_list = []
    #trunk or access?
    snmp_data = snmp_get_oid((device_name, COMMUNITY_STRING, SNMP_PORT), access_vlan_cisco_oid+"."+str(port_id), display_errors=True)
    result = snmp_data[0][1].prettyPrint()
    if result == "No Such Instance currently exists at this OID":
        for i in range(1,5):
            snmp_data = snmp_get_oid((device_name, COMMUNITY_STRING, SNMP_PORT), trunk_vlans_cisco_oid[i-1]+"."+str(port_id), display_errors=True)
            result = snmp_data[0][1].prettyPrint()
            if result == "No Such Instance currently exists at this OID": continue
            result = result[2:]
            result = result.ljust(256,"0") 
            for n in range (1024,-1,-1):
                if int(result,16) & 2**n:
                    vlan_list.append((i*1024)-(n+1))
        if len(vlan_list) == 4094:
            return ["all"]            
        else:
            return vlan_list
    else: #this is access port
        snmp_data = snmp_get_oid((device_name, COMMUNITY_STRING, SNMP_PORT), access_vlan_cisco_oid+"."+str(port_id), display_errors=True)
        result = snmp_data[0][1].prettyPrint()
        vlan_list.append(int(result))
        return vlan_list


#return lins of vlans configured on the device
def configured_vlans_on_device(device):
    COMMUNITY_STRING = definitions.COMMUNITY_STRING
    vlans = []
    snmp_data = snmp_get_oids((device, COMMUNITY_STRING, SNMP_PORT), vlans_on_cisco_oid, display_errors=True)
    for varBindTableRow in snmp_data:   
        for name, val in varBindTableRow:
            vlans.append(int(last_oid_number_re.findall(str(name))[0]))
    return vlans

#check if vlan in member of given trunk
def is_vlan_in_trunk(device_name,port,vlan):
        COMMUNITY_STRING = definitions.COMMUNITY_STRING
        port_id = find_port_id(device_name,port)
        if 0 <= int(vlan) < 1024:
            oid_new = trunk_vlans_cisco_oid1k+'.'+str(port_id)
            factor = 1
        elif 1024 <= int(vlan) < 2048:
            oid_new = trunk_vlans_cisco_oid2k+'.'+str(port_id)
            factor = 2
        elif 2048 <= int(vlan) < 3072:
            oid_new = trunk_vlans_cisco_oid3k+'.'+str(port_id)
            factor = 3
        elif 3072 <= int(vlan) < 4096:
            oid_new = trunk_vlans_cisco_oid4k+'.'+str(porti_id)
            factor = 4
        snmp_data = snmp_get_oid((device_name, COMMUNITY_STRING, SNMP_PORT), oid_new, display_errors=True)
        result = snmp_data[0][1].prettyPrint()
        if len(result) == 0:
            print "return value empty, exiting..."
            return False
        else:
            result = result[2:]
            result = result.ljust(256,"0") #for 2k, 3k and 4k the result in not full table so we fill it

        
        a = (factor*1024) - (int(vlan)+1)
        if int(result,16) & 2**a:
            return True
        else:
            return False

