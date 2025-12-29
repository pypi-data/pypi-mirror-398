from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List, Optional, Any, Iterable, Tuple


class MorphologyClass(Enum):
    """
    High-level shape classification for a fishbone structure.

    - LINEAR:   Mostly a straight spine with few ribs.
    - BRANCHING:Spine with many side ribs.
    - DEEP:     Spine plus long chains (micro-spines) off ribs.
    - HYBRID:   Combination of branching + some deep micro-spines.
    """

    LINEAR = auto()
    BRANCHING = auto()
    DEEP = auto()
    HYBRID = auto()


@dataclass
class SpineNodeV2:
    """
    Node inside a fishbone spine or rib structure.
    """

    node_id: str
    depth: int
    weight: float
    parent_id: Optional[str] = None
    is_spine: bool = True  # False => rib / micro-spine node


@dataclass
class FishboneV2:
    """
    Result of building an N-FBA v2 fishbone structure.

    Attributes
    ----------
    seed:
        Starting node (e.g., main concept, tool, or event).
    spine:
        Ordered list of spine nodes from root outward.
    ribs_by_node:
        Mapping from spine node_id -> list of rib / micro-spine nodes.
    morphology:
        High-level shape classification (linear, branching, deep, hybrid).
    metadata:
        Extra stats that can be used in logs, proposals, or dashboards.
    """

    seed: str
    spine: List[SpineNodeV2]
    ribs_by_node: Dict[str, List[SpineNodeV2]]
    morphology: MorphologyClass
    metadata: Dict[str, Any]


def _get_neighbors_with_weights(
    graph: Any,
    node_id: str,
) -> List[Tuple[str, float]]:
    """
    Safely extract neighbors and weights from the graph.

    This is written defensively to work with a variety of Graph
    implementations. It makes minimal assumptions:

      - graph.neighbors(node_id) -> iterable of neighbor ids
      - optional: graph.get_edge_data(u, v) -> dict with 'weight'

    If no weight exists, defaults to 1.0.
    """

    neighbors: Iterable[str]

    if hasattr(graph, "neighbors"):
        neighbors = graph.neighbors(node_id)
    elif hasattr(graph, "get_neighbors"):
        neighbors = graph.get_neighbors(node_id)
    else:
        raise AttributeError(
            "Graph object must implement .neighbors(node_id) or .get_neighbors(node_id)."
        )

    result: List[Tuple[str, float]] = []

    for nbr in neighbors:
        w = 1.0
        if hasattr(graph, "get_edge_data"):
            try:
                data = graph.get_edge_data(node_id, nbr) or {}
                w = float(data.get("weight", 1.0))
            except Exception:
                # Fallback to unweighted if anything goes wrong
                w = 1.0
        result.append((nbr, w))

    return result


def build_fishbone_v2(
    graph: Any,
    seed: str,
    max_spine_length: int = 7,
    max_ribs_per_spine_node: int = 4,
    max_depth_micro_spine: int = 3,
    industrial_mode: bool = True,
) -> FishboneV2:
    """
    Build an upgraded N-FBA v2 fishbone structure.

    This function is *backwards-compatible* in spirit with the original
    fishbone builder, but adds:

      - dynamic spine growth based on highest-weight associations
      - ribs attached per spine node
      - optional micro-spine growth from strong ribs
      - morphology classification (linear / branching / deep / hybrid)

    Parameters
    ----------
    graph:
        Your Graph object. It must expose either:
          - graph.neighbors(node_id)
          - or graph.get_neighbors(node_id)
        and optionally:
          - graph.get_edge_data(u, v) -> {'weight': ...}
    seed:
        Starting node id.
    max_spine_length:
        Maximum number of nodes allowed on the main spine.
    max_ribs_per_spine_node:
        Maximum number of ribs to attach to each spine node.
    max_depth_micro_spine:
        How deep micro-spines (secondary spines) can grow off ribs.
    industrial_mode:
        If True, uses more conservative branching limits, which is
        recommended for deterministic, safety-critical environments.

    Returns
    -------
    FishboneV2
    """

    if industrial_mode:
        # Keep structure shallow and predictable for plant usage.
        max_spine_length = min(max_spine_length, 7)
        max_ribs_per_spine_node = min(max_ribs_per_spine_node, 3)
        max_depth_micro_spine = min(max_depth_micro_spine, 2)

    visited: set[str] = set()
    spine: List[SpineNodeV2] = []
    ribs_by_node: Dict[str, List[SpineNodeV2]] = {}

    current_id = seed
    depth = 0
    visited.add(current_id)

    # --- Build main spine greedily by strongest-weight neighbors ---
    while len(spine) < max_spine_length:
        # Compute weight of "staying here" as 0; moving based on neighbors.
        neighbors = _get_neighbors_with_weights(graph, current_id)
        # Filter out visited to avoid cycles.
        candidates = [(nid, w) for nid, w in neighbors if nid not in visited]

        spine.append(
            SpineNodeV2(
                node_id=current_id,
                depth=depth,
                weight=1.0,  # actual weight can be refined if needed
                parent_id=None if depth == 0 else spine[-1].node_id,
                is_spine=True,
            )
        )

        if not candidates:
            break

        # Choose the best neighbor as next spine node.
        # Sort by weight descending.
        candidates.sort(key=lambda x: x[1], reverse=True)
        best_next_id, best_weight = candidates[0]

        visited.add(best_next_id)
        current_id = best_next_id
        depth += 1

    # --- Attach ribs and potential micro-spines to each spine node ---
    for spine_node in spine:
        node_id = spine_node.node_id
        neighbors = _get_neighbors_with_weights(graph, node_id)
        # Exclude spine nodes themselves from rib candidates.
        rib_candidates = [(nid, w) for nid, w in neighbors if nid not in {s.node_id for s in spine}]

        # Sort ribs by weight (strongest associations first).
        rib_candidates.sort(key=lambda x: x[1], reverse=True)
        rib_candidates = rib_candidates[:max_ribs_per_spine_node]

        ribs: List[SpineNodeV2] = []
        ribs_by_node[node_id] = ribs

        for rib_id, rib_w in rib_candidates:
            if rib_id in visited:
                continue
            visited.add(rib_id)

            rib_node = SpineNodeV2(
                node_id=rib_id,
                depth=spine_node.depth + 1,
                weight=rib_w,
                parent_id=node_id,
                is_spine=False,
            )
            ribs.append(rib_node)

            # --- Optional micro-spine growth off this rib ---
            # We treat a strong rib as the start of a secondary "micro-spine"
            # emanating from the main spine.
            if max_depth_micro_spine > 1 and rib_w >= 1.0:
                _grow_micro_spine(
                    graph=graph,
                    start_node=rib_node,
                    visited=visited,
                    ribs=ribs,
                    max_depth=max_depth_micro_spine,
                )

    morphology = _classify_morphology(spine=spine, ribs_by_node=ribs_by_node)

    metadata: Dict[str, Any] = {
        "spine_length": len(spine),
        "total_ribs": sum(len(v) for v in ribs_by_node.values()),
        "max_spine_depth": max((n.depth for n in spine), default=0),
        "industrial_mode": industrial_mode,
    }

    return FishboneV2(
        seed=seed,
        spine=spine,
        ribs_by_node=ribs_by_node,
        morphology=morphology,
        metadata=metadata,
    )


def _grow_micro_spine(
    graph: Any,
    start_node: SpineNodeV2,
    visited: set[str],
    ribs: List[SpineNodeV2],
    max_depth: int,
) -> None:
    """
    Grow a short "micro-spine" starting from a rib node.

    This reflects your idea that, under strong association, a rib can
    begin to behave like a new mini-spine branching away from the main spine.
    """

    current = start_node
    for _ in range(max_depth - 1):
        neighbors = _get_neighbors_with_weights(graph, current.node_id)
        # Only consider neighbors not yet visited.
        candidates = [(nid, w) for nid, w in neighbors if nid not in visited]

        if not candidates:
            break

        candidates.sort(key=lambda x: x[1], reverse=True)
        next_id, w = candidates[0]

        visited.add(next_id)
        micro_node = SpineNodeV2(
            node_id=next_id,
            depth=current.depth + 1,
            weight=w,
            parent_id=current.node_id,
            is_spine=False,  # still classified as rib / micro-spine
        )
        ribs.append(micro_node)
        current = micro_node


def _classify_morphology(
    spine: List[SpineNodeV2],
    ribs_by_node: Dict[str, List[SpineNodeV2]],
) -> MorphologyClass:
    """
    Simple morphology classifier based on spine length and rib patterns.
    """

    spine_len = len(spine)
    total_ribs = sum(len(v) for v in ribs_by_node.values())
    max_ribs_on_node = max((len(v) for v in ribs_by_node.values()), default=0)
    max_depth = 0
    for ribs in ribs_by_node.values():
        for r in ribs:
            if r.depth > max_depth:
                max_depth = r.depth

    if total_ribs == 0 or max_ribs_on_node <= 1:
        return MorphologyClass.LINEAR

    # deeper structures (micro-spines)
    if max_depth >= 3 and total_ribs >= spine_len:
        return MorphologyClass.DEEP

    if total_ribs > spine_len * 2:
        return MorphologyClass.BRANCHING

    return MorphologyClass.HYBRID
