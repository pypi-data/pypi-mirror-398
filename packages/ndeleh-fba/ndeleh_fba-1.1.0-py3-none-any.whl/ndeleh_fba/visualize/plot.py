import matplotlib.pyplot as plt
import networkx as nx

from ndeleh_fba.fishbone import FishBoneResult
from ndeleh_fba.graph import Graph


def plot_fishbone(graph: Graph, result: FishBoneResult, *, title="N-FBA Fishbone"):
    """
    Visualize the Ndeleh Fish Bone structure using networkx and matplotlib.

    - Spine = thick edges
    - Ribs = medium edges
    - Micro-ribs = thin edges
    """

    G = nx.Graph()

    # Add all nodes
    for node in graph.nodes:
        G.add_node(node)

    # Add normal edges
    for src, neighbors in graph.edges.items():
        for dst, w in neighbors.items():
            G.add_edge(src, dst, weight=w)

    # Highlight spine (thick)
    spine_edges = [
        (result.spine.steps[i].node_id, result.spine.steps[i+1].node_id)
        for i in range(len(result.spine.steps) - 1)
    ]

    # Collect all ribs and micro-ribs
    rib_edges = []
    micro_edges = []

    for spine_node, rib_dict in result.ribs.items():
        for rib_node, rib_obj in rib_dict.items():
            # Rib edge
            rib_edges.append((spine_node, rib_node))

            # Micro-ribs
            for child_id, child in rib_obj.children.items():
                micro_edges.append((rib_node, child_id))

    # Layout (spring layout looks best)
    pos = nx.spring_layout(G, seed=42, k=0.6)

    plt.figure(figsize=(10, 8))
    plt.title(title, fontsize=16)

    # Draw base graph (very light)
    nx.draw_networkx_edges(G, pos, edge_color="#cccccc", width=1, alpha=0.3)

    # Draw micro-ribs (thin)
    if micro_edges:
        nx.draw_networkx_edges(
            G,
            pos,
            edgelist=micro_edges,
            width=1,
            edge_color="#00aaff",
            alpha=0.7,
        )

    # Draw ribs (medium)
    if rib_edges:
        nx.draw_networkx_edges(
            G,
            pos,
            edgelist=rib_edges,
            width=2,
            edge_color="#0066ff",
            alpha=0.9,
        )

    # Draw spine (thick)
    nx.draw_networkx_edges(
        G,
        pos,
        edgelist=spine_edges,
        width=4,
        edge_color="#ff3300",
        alpha=1.0,
    )

    # Draw nodes and labels
    nx.draw_networkx_nodes(
        G,
        pos,
        node_size=700,
        node_color="#ffffff",
        edgecolors="#000000",
        linewidths=1.5,
    )

    nx.draw_networkx_labels(G, pos, font_size=10)

    plt.axis("off")
    plt.tight_layout()
    plt.show()
