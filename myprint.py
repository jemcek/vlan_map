"""
different print routines:
errors, dictionaries, lists, custom etc...
what ever you want to put out, do it here preferable to print statement
"""

#error message
def error(message):
    print message
    exit(0)

#warning message
def warning(message):
    print message

#normal print
def myprint(message):
    print message

#normal dict print
def print_dict(dictionary):
    for key, value in dictionary.items():
        print key, value

#print dict sorted
def dict_sorted_with_message(dictionary, message):
    print message  
    for key in sorted(dictionary):
        print '\t'.join(dictionary[key]) 

#this one is to print the port all information
def dict_sorted_interface(dictionary, host):
    print "\nPorts on:", host, "\n"
    #first print the "Info" line
    print '\t'.join(dictionary['int_id'])
    #all the rest, skip Info line
    for key in sorted(dictionary):
        if key != 'int_id':
            s = '\t'.join(dictionary[key]) 
            if len(dictionary[key][0]) < 8:
                s = s.replace('\t', '\t\t', 1)
            print s

#this one is to print one interface 
def dict_interface(dictionary, host, port):
    #first print the "Info" line
    print 
    print '\t'.join(dictionary['int_id'])
    #all the rest, skip Info line
    for key in sorted(dictionary):
        if dictionary[key][0] == port:
            s = '\t'.join(dictionary[key]) 
            if len(dictionary[key][0]) < 8:
                s = s.replace('\t', '\t\t', 1)
            print s
    print 

#print vlan list
def vlan_list_joined(list, message):
    print message, (', '.join(str(x) for x in list)), "\n"

#print vendors, if requested with details
def vendors(device_list, option):
    print
    for key, value in device_list.items():
        if option == "short":
            print "Device", key, "is", value[0]
        elif option == "all":  
            print "Device", key, "is", value[0], "\n", value[1], "\n"
    print


def check_vlans(name, dictionary, vlan_list):
    print "\nOn", name, "Vlans configured on interfaces, but vlans not configured on switch:\n"
    member = dictionary['int_id'].index('Member')
    status = dictionary['int_id'].index('Status')
    trunk = dictionary['int_id'].index('Type')
    interface = dictionary['int_id'].index('Interface')

    #first check if there is a vlan configured on any interface but not configured globally on switch
    for key in sorted(dictionary):
        if key == "int_id": continue
        vlans = dictionary[key][member]
        #print vlans
        for i in vlans:
            if i == "all":
                continue
            elif i in vlan_list:
                continue
            else:
                #print i, vlan_list
                print "Vlan", "\t", i, "\tInterface", dictionary[key][interface].title()
            #break
    print
    #now check if there are vlans configured globally but not used on any of the interfaces
    print "On", name, "Vlans configured on switch, but not used on interfaces:\n"

    for global_vlan in vlan_list:
        #print global_vlan
        vlan_exist = 0
        for key in dictionary:
            if key == "int_id": continue
            vlans = dictionary[key][member]
            #print vlans
            if global_vlan in vlans:
                vlan_exist = 1
        if vlan_exist == 0:
            print "Vlan", global_vlan, "configured but not used"
    print
    #exit(0)

def check_island_vlans(name, vlan_list, island_vlan_list, island_name):
    #print island_vlan_list
    #print vlan_list
    #print "\nVlans in island", island_name, ": ", (', '.join(str(x) for x in island_vlan_list))
    print "\n", name
    #print "Vlans on:", name, ": ", (', '.join(str(x) for x in vlan_list))
    missing = []
    configured = []
    other = []
    for i in island_vlan_list:
        if int(i) in vlan_list:
            configured.append(i)
        else:
            missing.append(i)
    for i in vlan_list:
        if str(i) not in island_vlan_list:
            other.append(i)
    print "Missing vlans:", (', '.join(str(x) for x in missing))
    print "Configured vlans: ", (', '.join(str(x) for x in configured))
    print "Other vlans: ", (', '.join(str(x) for x in other))


def all_ports_all_vlan(name, dictionary, vlan_list, native_tagged):
    print "\nOn", name, "native vlan is", ("TAGGED" if native_tagged == 1 else " NOT TAGGED\n"  )
    member = dictionary['int_id'].index('Member')
    status = dictionary['int_id'].index('Status')
    native = dictionary['int_id'].index('Native')
    trunk = dictionary['int_id'].index('Type')
    interface = dictionary['int_id'].index('Interface')
    desc = dictionary['int_id'].index('Description')
    print "Int",  "\t", "Description", "\t\t", "Status", "\t", "Type", "\t", "Native", "\t", "Vlans"
    print "----------------------------------------------------------------------------"
    for key in sorted(dictionary):
        if key == "int_id": continue
        vlans = dictionary[key][member]
        vlans = (', '.join(str(x) for x in vlans))
        print dictionary[key][interface].title(), "\t", dictionary[key][desc].ljust(20)[0:20], "\t", dictionary[key][status], "\t", dictionary[key][trunk], "\t", dictionary[key][native], "\t", vlans 
    print
    #exit(0)

#print all the ports that include specified vlan
def ports_with_vlan(name, vlanid, dictionary):
    print "\nOn", name, "vlan", vlanid, "is a member of:"
    member = dictionary['int_id'].index('Member')
    status = dictionary['int_id'].index('Status')
    trunk = dictionary['int_id'].index('Type')
    interface = dictionary['int_id'].index('Interface')
    desc = dictionary['int_id'].index('Description')
    print
    print "Interface", "\t", "Status", "\t\t", "Type", "\t\t", "Description"
    print "----------------------------------------------------------------------------"
    for key in sorted(dictionary):
        #print key, dictionary[key][member]
        if dictionary[key][member] == True: 
           print dictionary[key][interface].title(), "\t\t", dictionary[key][status], "\t\t", dictionary[key][trunk], "\t\t", dictionary[key][desc]
    print
    #exit(0)
