from typing import List, Dict, Any
from .graph import Graph


def build_fishbone_v2(graph: Graph, seed: str) -> Dict[str, Any]:
    """
    N-FBA v2 — dynamic associative spine builder with micro-spine branching.
    Fully compatible with the simple Graph class.
    """

    # -------------------
    # 1. BUILD MAIN SPINE
    # -------------------
    current = seed
    spine = [current]
    visited = set([current])

    while True:
        neighbors_dict = graph.neighbors(current)  # returns {neighbor: weight}

        # Convert dict → list of tuples
        neighbors = [(n, w) for n, w in neighbors_dict.items() if n not in visited]

        if not neighbors:
            break

        # pick strongest neighbor
        neighbor, weight = max(neighbors, key=lambda x: x[1])

        spine.append(neighbor)
        visited.add(neighbor)
        current = neighbor

    # -------------------
    # 2. BUILD RIBS + MICRO-SPINES
    # -------------------

    ribs = []
    micro_spines = []

    for node in spine:
        for nbr, weight in graph.neighbors(node).items():

            # Skip nodes that are part of main spine
            if nbr in spine:
                continue

            ribs.append({"source": node, "target": nbr, "weight": weight})

            # strong ribs become micro-spines
            if weight >= 0.75:
                micro_spines.append(_grow_micro_spine(graph, nbr))

    # -------------------
    # RETURN RESULT
    # -------------------
    return {
        "spine": spine,
        "ribs": ribs,
        "micro_spines": micro_spines,
        "seed": seed,
    }


def _grow_micro_spine(graph: Graph, seed: str) -> List[str]:
    """
    Grows a micro-spine outward from a strong rib node.
    Fully compatible with Graph class.
    """

    current = seed
    micro = [current]
    visited = set([current])

    while True:
        neighbors_dict = graph.neighbors(current)
        neighbors = [(n, w) for n, w in neighbors_dict.items() if n not in visited]

        if not neighbors:
            break

        neighbor, weight = max(neighbors, key=lambda x: x[1])

        if weight < 0.70:  # threshold for micro-spine continuation
            break

        micro.append(neighbor)
        visited.add(neighbor)
        current = neighbor

    return micro

