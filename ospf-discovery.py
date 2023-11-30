import matplotlib.pyplot as plt
import networkx as nx
from easysnmp import Session
from pprint import pprint

# Asking the user for input
ip = input("\nEnter the 'root' device IP address: ")

# List to store OSPF devices
ospf = []

# Discovering OSPF neighbors for the root device
def ospf_func(ip):
    # Creating empty containers for adding discovered devices
    nbridlist = []
    nbriplist = []
    ospf_device = {}

    # Opening the SNMPv3 session to the device
    session = Session(
        hostname=ip,
        version=3,
        security_level="auth_with_privacy",
        security_username="mihai",
        auth_protocol="SHA",
        auth_password="shapass1234",
        privacy_protocol="AES",
        privacy_password="aespass1234"
    )

    # Getting device OSPF ID
    snmp_walk = session.walk('.1.3.6.1.2.1.14.1.1')
    ospf_host_id = snmp_walk[0].value

    # Performing SNMP WALK to get OSPF neighbor IDs
    snmp_walk = session.walk('.1.3.6.1.2.1.14.10.1.3')
    nbridlist = [neighbor_id.value for neighbor_id in snmp_walk]

    # Performing SNMP WALK to get OSPF neighbor IPs
    snmp_walk = session.walk('.1.3.6.1.2.1.14.10.1.1')
    nbriplist = [neighbor_ip.value for neighbor_ip in snmp_walk]

    # Building the dictionary with the device's OSPF info
    ospf_device["HostID"] = ospf_host_id
    ospf_device["NbrRtrID"] = nbridlist
    ospf_device["NbrRtrIP"] = nbriplist

    # List of OSPF devices
    if ospf_device not in ospf:
        ospf.append(ospf_device)

    return ospf

# Calling the function above
ospf = ospf_func(ip)

# Querying neighbors to find other OSPF routers (if any)
def neighbor_query():
    # All queried OSPF routers (by ID)
    all_rtr_ids = [ospf[router]["HostID"] for router in range(len(ospf))]

    # All discovered neighbor OSPF router IDs
    all_nbr_ids = [nbr_id for router in range(len(ospf)) for nbr_id in ospf[router]["NbrRtrID"]]

    # All unqueried OSPF routers (by ID)
    all_unqueried = [nbr_id for nbr_id in all_nbr_ids if nbr_id not in all_rtr_ids]

    # Running the ospf_func() function for each unqueried neighbor (by IP)
    for q in all_unqueried:
        for r in range(len(ospf)):
            for index, s in enumerate(ospf[r]["NbrRtrID"]):
                if q == s:
                    new_ip_to_query = ospf[r]["NbrRtrIP"][index]
                    ospf_func(new_ip_to_query)

    # Remove duplicates and return the unique OSPF devices
    all_devices = list(set(ospf))

    return all_rtr_ids, all_nbr_ids, all_devices

# Calling the neighbor_query() function
while True:
    neighbor_query()
    if len(list(set(neighbor_query()[0]))) == len(list(set(neighbor_query()[1]))):
        break

final_devices_list = neighbor_query()[2]

# Creating a dictionary of neighborships
neighborship_dict = {}

for each_dictionary in final_devices_list:
    for index, each_neighbor in enumerate(each_dictionary["NbrRtrID"]):
        each_tuple = (each_dictionary["HostID"], each_neighbor)
        neighborship_dict[each_tuple] = each_dictionary["NbrRtrIP"][index]

# Generating the OSPF graph
print("\nGenerating OSPF network topology...\n")

# Drawing the topology using the dictionary of neighborships
G = nx.Graph()

G.add_edges_from(neighborship_dict.keys())

pos = nx.spring_layout(G, k=0.1, iterations=70)

nx.draw_networkx_labels(G, pos, font_size=9, font_family="sans-serif", font_weight="bold")

nx.draw_networkx_edges(G, pos, width=4, alpha=0.4, edge_color='black')

nx.draw_networkx_edge_labels(G, pos, neighborship_dict, label_pos=0.3, font_size=6)

nx.draw(G, pos, node_size=700, with_labels=False)

plt.show()

# End of program