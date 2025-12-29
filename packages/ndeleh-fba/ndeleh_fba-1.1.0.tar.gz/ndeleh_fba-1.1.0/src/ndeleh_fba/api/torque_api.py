from fastapi import APIRouter
from pydantic import BaseModel
from ndeleh_fba import (
    TorqueEvent,
    classify_torque_event,
    TorqueSeverity,
)

router = APIRouter(
    prefix="/api/torque",
    tags=["Torque Evaluation"],
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


@router.post("/evaluate")
def evaluate_torque(input_data: TorqueInput):
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

    result = classify_torque_event(event)

    return {
        "severity": result.severity.name,
        "score": result.score,
        "reason": result.reason,
    }
