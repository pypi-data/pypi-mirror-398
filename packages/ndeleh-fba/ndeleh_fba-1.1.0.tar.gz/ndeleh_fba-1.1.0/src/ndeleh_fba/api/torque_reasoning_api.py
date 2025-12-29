from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any

from ndeleh_fba import (
    TorqueEvent,
    classify_torque_event,
    build_fishbone_v2,
    FishboneV2,
)
from ndeleh_fba.industrial.torque_to_graph import torque_event_to_graph
from ndeleh_fba.industrial.reasoning_report import generate_torque_reports



router = APIRouter(
    prefix="/api/torque/reason",
    tags=["Torque Reasoning (N-FBA v2)"],
)


class TorqueInput(BaseModel):
    torque_value: float
    target_min: float
    target_max: float
    is_red_flag: bool = False
    jam_detected: bool | None = None
    cycle_time: float | None = None
    retries: int = 0
    manual_check_used: bool = False


@router.post("/")
def reason_about_torque(input_data: TorqueInput) -> Dict[str, Any]:
    # Build torque event
    event = TorqueEvent(
        torque_value=input_data.torque_value,
        target_min=input_data.target_min,
        target_max=input_data.target_max,
        is_red_flag=input_data.is_red_flag,
        jam_detected=input_data.jam_detected,
        cycle_time=input_data.cycle_time,
        retries=input_data.retries,
        manual_check_used=input_data.manual_check_used,
    )

    # Classify event
    classification = classify_torque_event(event)

    # Convert to graph
    g = torque_event_to_graph(event)

    # Build fishbone v2 reasoning structure (this is the FishboneV2 dataclass)
    result: FishboneV2 = build_fishbone_v2(
        graph=g,
        seed="TorqueEvent",
        industrial_mode=True,
    )

    # Generate human + technical reports
    reports = generate_torque_reports(classification, result)

    return {
        "classification": {
            "severity": classification.severity.name,
            "score": classification.score,
            "reason": classification.reason,
        },
        "fishbone": {
            "morphology": result.morphology.name,
            "spine": [n.node_id for n in result.spine],
            "ribs": {k: [r.node_id for r in v] for k, v in result.ribs_by_node.items()},
            "metadata": result.metadata,
        },
        "reports": reports,
    }

