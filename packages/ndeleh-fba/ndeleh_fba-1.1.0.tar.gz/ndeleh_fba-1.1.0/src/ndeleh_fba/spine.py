from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from .graph import Graph, NodeId


@dataclass
class SpineStep:
    """
    A single step along the N-FBA spine.

    Attributes
    ----------
    node_id:
        The node at this position on the spine.
    score:
        The activation / strength score at this step.
    from_node:
        The previous node on the spine (None for the seed).
    """
    node_id: NodeId
    score: float
    from_node: Optional[NodeId] = None


@dataclass
class SpineResult:
    """
    Result of running the dynamic spine builder.

    Attributes
    ----------
    steps:
        Ordered list of SpineStep objects from seed to final node.
    """
    steps: List[SpineStep]

    @property
    def nodes(self) -> List[NodeId]:
        """Return just the node ids along the spine in order."""
        return [step.node_id for step in self.steps]

    def __len__(self) -> int:
        return len(self.steps)


def build_spine(
    graph: Graph,
    seed: NodeId,
    *,
    max_length: int = 10,
    decay: float = 0.9,
    min_edge_weight: float = 0.0,
    avoid_cycles: bool = True,
) -> SpineResult:
    """
    Build the dynamic spine for the Ndeleh Fish Bone Algorithm (N-FBA).

    This function selects a path through the graph starting at `seed`,
    choosing at each step the neighbor with the highest propagated score:

        score(next) = score(current) * weight(current, next) * decay

    Parameters
    ----------
    graph:
        The associative graph.
    seed:
        Starting node id for the spine.
    max_length:
        Maximum number of nodes in the spine (including the seed).
    decay:
        Multiplicative decay applied at each hop (0 < decay <= 1).
        Lower values make the spine die out faster.
    min_edge_weight:
        Ignore edges with weight below this threshold.
    avoid_cycles:
        If True, the spine will not revisit a node already on the spine.

    Returns
    -------
    SpineResult
        An ordered list of steps representing the spine from the seed.
    """
    if seed not in graph.nodes:
        raise ValueError(f"Seed node {seed!r} not found in graph.")

    if not (0 < decay <= 1.0):
        raise ValueError("decay must be in (0, 1].")
    if max_length < 1:
        raise ValueError("max_length must be >= 1.")

    # Initial step: the seed is fully activated.
    steps: List[SpineStep] = [SpineStep(node_id=seed, score=1.0, from_node=None)]
    visited = {seed}
    current_node = seed
    current_score = 1.0

    # Grow the spine node-by-node.
    for _ in range(max_length - 1):
        neighbors = graph.neighbors(current_node)

        # Collect candidate neighbors and their propagated scores.
        candidates: List[Tuple[NodeId, float]] = []

        for nbr_id, weight in neighbors.items():
            if weight < min_edge_weight:
                continue
            if avoid_cycles and nbr_id in visited:
                continue

            # Propagate score with decay: this is the "dynamic" part.
            nbr_score = current_score * float(weight) * decay
            if nbr_score <= 0:
                continue

            candidates.append((nbr_id, nbr_score))

        if not candidates:
            # Spine cannot grow further.
            break

        # Choose the best candidate based on its predicted score.
        next_node, next_score = max(candidates, key=lambda x: x[1])

        # If the score is extremely small, stop to avoid meaningless steps.
        if next_score <= 1e-9:
            break

        steps.append(SpineStep(node_id=next_node, score=next_score, from_node=current_node))
        visited.add(next_node)
        current_node = next_node
        current_score = next_score

    return SpineResult(steps=steps)
