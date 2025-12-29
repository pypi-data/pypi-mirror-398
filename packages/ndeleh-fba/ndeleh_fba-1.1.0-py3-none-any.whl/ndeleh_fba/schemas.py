from typing import List, Optional
from pydantic import BaseModel

# -----------------------------
# Edge Model
# -----------------------------
class Edge(BaseModel):
    src: str
    dst: str
    weight: float = 1.0


# -----------------------------
# V2 Fishbone Request
# -----------------------------
class FishboneV2Request(BaseModel):
    # Optional custom graph edges
    edges: Optional[List[Edge]] = None

    # Torque-related plant metrics
    torque_value: float
    target_min: float
    target_max: float
    is_red_flag: bool
    jam_detected: bool
    cycle_time: float
    retries: int
    manual_check_used: bool


# -----------------------------
# Legacy Fishbone Request (simple)
# -----------------------------
class FishboneRequest(BaseModel):
    edges: List[Edge]


# -----------------------------
# Fishbone Response
# -----------------------------
class FishboneResponse(BaseModel):
    result: dict

