import pandas as pd
import networkx as nx


def build_intelligence_graph(relationship_df):

    G = nx.Graph()

    for _, row in relationship_df.iterrows():

        G.add_edge(
            row["device_a"],
            row["device_b"],
            weight=row["relationship_strength"]
        )

    return G


def centrality_analysis(G):

    degree = nx.degree_centrality(G)

    results = []

    for device, score in degree.items():

        results.append({

            "device_id": device,

            "centrality_score":
            round(score * 100, 2)

        })

    return (
        pd.DataFrame(results)
        .sort_values(
            "centrality_score",
            ascending=False
        )
    )


def identify_key_suspects(G):

    between = nx.betweenness_centrality(G)

    results = []

    for device, score in between.items():

        results.append({

            "device_id": device,

            "broker_score":
            round(score * 100, 2)

        })

    return (
        pd.DataFrame(results)
        .sort_values(
            "broker_score",
            ascending=False
        )
    )