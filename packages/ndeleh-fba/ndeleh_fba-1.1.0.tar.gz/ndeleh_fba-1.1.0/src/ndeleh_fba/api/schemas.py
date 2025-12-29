from pydantic import BaseModel
from typing import List, Dict, Optional


# --------------------------------
# Edge Model
# --------------------------------
class Edge(BaseModel):
    source: str   # REQUIRED
    target: str   # REQUIRED
    weight: float = 1.0

# --------------------------------
# V2 Fishbone Request
# --------------------------------
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

    # REQUIRED ROOT SEED
    seed: str

# --------------------------------
# Legacy V1 Request
# --------------------------------
class FishboneRequest(BaseModel):
    edges: List[Edge]

# --------------------------------
# Response Model
# --------------------------------
class FishboneResponse(BaseModel):
    result: dict

# -----------------------
# INDUSTRIAL DIAGNOSTICS
# ---------------------

class TorqueReadingRequest(BaseModel):
    torque_value: float
    target_min: float
    target_max: float
    is_red_flag: bool
    jam_detected: bool
    cycle_time: float
    retries: int
    manual_check_used: bool = False


class TorqueDiagnosisResponse(BaseModel):
    root_cause: str
    confidence: float
    recommendation: str
    spine: List[str]
    weights: Dict[str, float]

