import matplotlib.pyplot as plt
import networkx as nx


def visualize_microspine(result, title="N-FBA Micro-Spine Visualization"):
    """
    Visualizes the main spine and micro-spines from an N-FBA v2 output.
    """

    G = nx.DiGraph()

    # Add main spine edges
    spine = result["spine"]
    for i in range(len(spine) - 1):
        G.add_edge(spine[i], spine[i + 1], color="red", weight=3)

    # Add ribs and micro-spines
    for rib in result["ribs"]:
        source = rib["source"]
        target = rib["target"]
        w = rib["weight"]

        color = "orange" if w >= 0.7 else "gray"
        width = 2 if w >= 0.7 else 1

        G.add_edge(source, target, color=color, weight=width)

    # Plot
    pos = nx.spring_layout(G, seed=42)

    edges = G.edges()
    colors = [G[u][v]["color"] for u, v in edges]
    widths = [G[u][v]["weight"] for u, v in edges]

    plt.figure(figsize=(12, 8))
    nx.draw(G, pos, with_labels=True, node_size=1800,
            font_size=12, edge_color=colors, width=widths)

    plt.title(title, fontsize=16)
    plt.show()
