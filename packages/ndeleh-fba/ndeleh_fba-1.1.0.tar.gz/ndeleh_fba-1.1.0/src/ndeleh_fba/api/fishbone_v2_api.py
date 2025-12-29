from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any

from ndeleh_fba import (
    Graph,
    build_fishbone_v2,
    MorphologyClass,
)


router = APIRouter(
    prefix="/api/fishbone/v2",
    tags=["Fishbone v2"],
)


class Edge(BaseModel):
    source: str
    target: str
    weight: float = 1.0


class FishboneRequest(BaseModel):
    seed: str
    edges: list[Edge]
    max_spine_length: int = 7
    max_ribs_per_spine_node: int = 3
    max_depth_micro_spine: int = 2
    industrial_mode: bool = True


@router.post("/build")
def build_v2(request: FishboneRequest) -> Dict[str, Any]:
    g = Graph()

    # Add edges
    for e in request.edges:
        g.add_edge(e.source, e.target, weight=e.weight)

    result = build_fishbone_v2(
        graph=g,
        seed=request.seed,
        max_spine_length=request.max_spine_length,
        max_ribs_per_spine_node=request.max_ribs_per_spine_node,
        max_depth_micro_spine=request.max_depth_micro_spine,
        industrial_mode=request.industrial_mode,
    )

    # Format output
    spine_nodes = [
        {
            "node": n.node_id,
            "depth": n.depth,
            "weight": n.weight,
            "parent": n.parent_id,
        }
        for n in result.spine
    ]

    ribs_dict = {}
    for sid, ribs in result.ribs_by_node.items():
        ribs_dict[sid] = [
            {
                "node": r.node_id,
                "depth": r.depth,
                "weight": r.weight,
                "parent": r.parent_id,
            }
            for r in ribs
        ]

    return {
        "seed": result.seed,
        "morphology": result.morphology.name,
        "spine": spine_nodes,
        "ribs": ribs_dict,
        "metadata": result.metadata,
    }
