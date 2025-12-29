from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

from .graph import Graph, NodeId
from .spine import SpineResult


@dataclass
class RibNode:
    """
    Represents a rib or micro-rib in the N-FBA structure.

    Attributes
    ----------
    node_id:
        The node ID of this rib.
    score:
        Activation score inherited from the spine or parent rib.
    parent:
        The spine node or rib node that generated this rib.
    children:
        Dict of further ribs (micro-ribs).
    """
    node_id: NodeId
    score: float
    parent: Optional[NodeId]
    children: Dict[NodeId, "RibNode"]


def _expand_ribs_recursive(
    graph: Graph,
    parent_node: NodeId,
    parent_score: float,
    visited: set,
    *,
    decay: float,
    rib_decay: float,
    min_score: float,
    max_depth: int,
    depth: int = 1,
) -> Dict[NodeId, RibNode]:
    """
    Recursive builder for ribs → micro-ribs → nano-ribs.

    Stops automatically when:
    - activation falls under threshold
    - depth > max_depth
    """
    if depth > max_depth:
        return {}

    ribs: Dict[NodeId, RibNode] = {}

    for nbr, weight in graph.neighbors(parent_node).items():
        if nbr in visited:
            continue

        score = parent_score * weight * (rib_decay ** depth)
        if score < min_score:
            continue

        visited.add(nbr)

        new_rib = RibNode(
            node_id=nbr,
            score=score,
            parent=parent_node,
            children={}
        )

        # recursing deeper (micro-ribs)
        new_rib.children = _expand_ribs_recursive(
            graph,
            parent_node=nbr,
            parent_score=score,
            visited=visited,
            decay=decay,
            rib_decay=rib_decay,
            min_score=min_score,
            max_depth=max_depth,
            depth=depth + 1,
        )

        ribs[nbr] = new_rib

    return ribs


def build_ribs(
    graph: Graph,
    spine: SpineResult,
    *,
    decay: float = 0.9,
    rib_decay: float = 0.6,
    min_score: float = 0.05,
    max_depth: int = 3,
) -> Dict[NodeId, Dict[NodeId, RibNode]]:
    """
    Build ribs + micro-ribs branching from each spine node.

    Returns a dict:
        {
          spine_node: {
              rib_node: RibNode(...),
              rib2: RibNode(...)
          }
        }
    """
    ribs_by_spine: Dict[NodeId, Dict[NodeId, RibNode]] = {}
    visited = set(spine.nodes)  # spine is sacred, don’t revisit it

    for step in spine.steps:
        node = step.node_id
        score = step.score

        ribs_by_spine[node] = _expand_ribs_recursive(
            graph,
            parent_node=node,
            parent_score=score,
            visited=visited,
            decay=decay,
            rib_decay=rib_decay,
            min_score=min_score,
            max_depth=max_depth,
        )

    return ribs_by_spine

