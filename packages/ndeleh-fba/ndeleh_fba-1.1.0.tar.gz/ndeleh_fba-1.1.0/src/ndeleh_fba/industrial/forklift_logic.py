from __future__ import annotations

from typing import Dict, List, Any

from ndeleh_fba.graph import Graph
from ndeleh_fba.fishbone_v2 import build_fishbone_v2


def analyze_forklift_event(
    speed_kmh: float,
    load_kg: float,
    rated_load_kg: float,
    tilt_warning: bool,
    proximity_alert: bool,
    brake_events: int,
    operator_id: str = "unknown",
) -> Dict[str, Any]:
    """
    Forklift safety + ops anomaly analysis using Ndeleh-FBA v2 reasoning.

    NOTE:
    - This is a rule + graph reasoning demo for industrial diagnostics/safety.
    - It is NOT a replacement for OEM safety systems, training, or site policies.
    """

    # ----------------------------
    # 1) Build a small cause-effect graph
    # ----------------------------
    g = Graph()

    # Seed: "forklift_event" connects to major risk categories
    g.add_edge("forklift_event", "operator_behavior", 0.9)
    g.add_edge("forklift_event", "load_condition", 0.9)
    g.add_edge("forklift_event", "environment", 0.8)
    g.add_edge("forklift_event", "equipment_state", 0.7)

    # Expand categories
    g.add_edge("operator_behavior", "speeding", 0.9)
    g.add_edge("operator_behavior", "hard_braking", 0.7)
    g.add_edge("load_condition", "overload", 1.0)
    g.add_edge("load_condition", "unstable_load", 0.8)
    g.add_edge("environment", "tight_aisles", 0.7)
    g.add_edge("environment", "pedestrian_zone", 0.9)
    g.add_edge("equipment_state", "brake_wear", 0.6)
    g.add_edge("equipment_state", "tilt_risk", 0.8)

    # ----------------------------
    # 2) Run N-FBA v2
    # ----------------------------
    fba = build_fishbone_v2(g, seed="forklift_event")
    spine = fba.get("spine_nodes", [])
    weights = fba.get("morphology", {})  # v2 returns morphology; treat as weights map
    microspines = fba.get("microspines", [])

    # ----------------------------
    # 3) Simple domain rules -> diagnostics list
    # ----------------------------
    diagnosis: List[str] = []

    overload_ratio = (load_kg / rated_load_kg) if rated_load_kg > 0 else 0.0
    if overload_ratio > 1.0:
        diagnosis.append("Overload detected (load exceeds rated capacity)")

    # You can tune these thresholds later
    if speed_kmh > 8.0:
        diagnosis.append("Possible speeding detected (site threshold exceeded)")

    if tilt_warning:
        diagnosis.append("Tilt warning event detected (tip-over risk)")

    if proximity_alert:
        diagnosis.append("Proximity alert event detected (collision/pedestrian risk)")

    if brake_events >= 3:
        diagnosis.append("High hard-brake count detected (operator behavior / environment risk)")

    # Basic root cause selection
    root_cause = diagnosis[0] if diagnosis else "No abnormal forklift condition detected"

    # Recommendation text
    if not diagnosis:
        recommendation = "No action required"
        confidence = 0.95
    else:
        recommendation = (
            "Review event timeline, operator behavior, load handling, and environment controls. "
            "If repeated, escalate to safety review and equipment inspection."
        )
        confidence = 0.85

    return {
        "status": "ok",
        "operator_id": operator_id,
        "inputs": {
            "speed_kmh": speed_kmh,
            "load_kg": load_kg,
            "rated_load_kg": rated_load_kg,
            "tilt_warning": tilt_warning,
            "proximity_alert": proximity_alert,
            "brake_events": brake_events,
        },
        "diagnosis": diagnosis,
        "root_cause": root_cause,
        "recommendation": recommendation,
        "confidence": confidence,
        # N-FBA v2 outputs (so users see *how* the reasoning is structured)
        "spine": spine,
        "weights": weights,
        "microspines": microspines,
    }
