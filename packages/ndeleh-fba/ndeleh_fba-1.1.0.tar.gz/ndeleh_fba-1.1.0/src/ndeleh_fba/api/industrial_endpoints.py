from fastapi import APIRouter, Depends
from ndeleh_fba.api.auth import verify_api_key
from ndeleh_fba.api.schemas import TorqueReadingRequest, TorqueDiagnosisResponse
from ndeleh_fba.industrial.industrial_logic import analyze_torque_event
from ndeleh_fba.industrial.forklift_logic import analyze_forklift_event
router = APIRouter()

@router.post("/diagnose/torque", response_model=TorqueDiagnosisResponse)
def diagnose_torque(req: TorqueReadingRequest, key=Depends(verify_api_key)):

    # Run core torque diagnostic logic
    result = analyze_torque_event(
        torque_value=req.torque,
        target_min=req.angle,          # placeholder mapping (can refine later)
        target_max=req.angle + 100,    # placeholder
        is_red_flag=req.error_flag,
        jam_detected=req.vibration > 5.0,
        cycle_time=3.0,
        retries=0,
        manual_check_used=False
    )

    # Prepare clean response model
    return TorqueDiagnosisResponse(
        root_cause=" | ".join(result["diagnosis"]),
        confidence=result["confidence"],
        recommendation="Investigate torque anomaly",
        spine=["machine", "operator", "method"],
        weights={"torque": 1.0, "vibration": req.vibration}
    )

from fastapi import APIRouter, Depends
from pydantic import BaseModel

router = APIRouter()

class ForkliftEvent(BaseModel):
    speed_kmh: float
    load_kg: float
    rated_load_kg: float
    tilt_warning: bool = False
    proximity_alert: bool = False
    brake_events: int = 0
    operator_id: str = "unknown"

@router.post("/diagnose/forklift")
def diagnose_forklift(payload: ForkliftEvent):
    return analyze_forklift_event(**payload.model_dump())
