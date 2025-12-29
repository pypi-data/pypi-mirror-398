"""
ndeleh_fba

Implementation of the Ndeleh Fish Bone Algorithm (N-FBA).
Core concepts:
- Dynamic spine: strongest associative path through the graph.
- Ribs & micro-ribs: branching associative structures around the spine.

Algorithm created by Ndeleh, 2025.
"""

from .graph import Graph
from .spine import SpineResult, SpineStep, build_spine
from .industrial import (
    TorqueSeverity,
    TorqueClassification,
    TorqueEvent,
    classify_torque_event,
)
from .spine_v2 import (
    MorphologyClass,
    SpineNodeV2,
    FishboneV2,
    build_fishbone_v2,
)


__all__ = [
    "Graph",
    "SpineResult",
    "SpineStep",
    "build_spine",
]

from .industrial import (
    TorqueSeverity,
    TorqueClassification,
    TorqueEvent,
    classify_torque_event,
)
