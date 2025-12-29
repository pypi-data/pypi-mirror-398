from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .graph import Graph, NodeId
from .spine import build_spine, SpineResult
from .ribs import build_ribs, RibNode


@dataclass
class FishBoneResult:
    """
    The full output of the Ndeleh Fish Bone Algorithm (N-FBA).

    Contains:
    - spine: the main dynamic path
    - ribs: branching secondary associations for each spine node
    - morphology: a string describing the overall fish shape
    """
    spine: SpineResult
    ribs: Dict[NodeId, Dict[NodeId, RibNode]]
    morphology: str

    @property
    def spine_nodes(self) -> List[NodeId]:
        return self.spine.nodes


def _detect_morphology(spine: SpineResult, ribs: Dict[NodeId, Dict[NodeId, RibNode]]) -> str:
    """
    Determine the 'shape' of the fish skeleton.
    Gives N-FBA adaptive intelligence.

    Types:
        - linear
        - rib-heavy
        - curved
        - clustered
        - sparse
    """
    spine_len = len(spine)
    rib_counts = [len(r) for r in ribs.values()]
    avg_ribs = sum(rib_counts) / len(rib_counts) if rib_counts else 0

    # Simple heuristics — can be upgraded later
    if spine_len >= 8 and avg_ribs < 1:
        return "linear"

    if avg_ribs >= 3:
        return "rib-heavy"

    # If ribs attach in clusters
    if max(rib_counts) >= 4:
        return "clustered"

    if avg_ribs == 0:
        return "sparse"

    return "curved"


def build_fishbone(
    graph: Graph,
    seed: NodeId,
    *,
    spine_length: int = 10,
    spine_decay: float = 0.9,
    rib_decay: float = 0.6,
    min_rib_score: float = 0.05,
    max_rib_depth: int = 3,
) -> FishBoneResult:
    """
    Build the FULL Ndeleh Fish Bone skeleton.

    Steps:
    1. Build the dynamic spine.
    2. Build ribs & micro-ribs from each spine node.
    3. Analyze the structure to determine morphology.
    """

    # Step 1: dynamic spine
    spine = build_spine(
        graph,
        seed,
        max_length=spine_length,
        decay=spine_decay,
    )

    # Step 2: ribs + micro-ribs
    ribs = build_ribs(
        graph,
        spine,
        decay=spine_decay,
        rib_decay=rib_decay,
        min_score=min_rib_score,
        max_depth=max_rib_depth,
    )

    # Step 3: detect morphology
    morphology = _detect_morphology(spine, ribs)

    return FishBoneResult(
        spine=spine,
        ribs=ribs,
        morphology=morphology
    )

