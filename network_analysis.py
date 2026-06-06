import networkx as nx

def build_device_network(colocation_df):

    G = nx.Graph()

    for _, row in colocation_df.iterrows():

        devices = row["device_id"]

        for i in range(len(devices)):
            for j in range(i + 1, len(devices)):

                G.add_edge(
                    devices[i],
                    devices[j]
                )

    return G