# industrial_logic.py
from ndeleh_fba.graph import FishboneGraph
from ndeleh_fba.fishbone_v2 import build_fishbone_v2



def analyze_torque_event(
    torque_value: float,
    target_min: float,
    target_max: float,
    is_red_flag: bool,
    jam_detected: bool,
    cycle_time: float,
    retries: int,
    manual_check_used: bool
):
    """
    Industrial torque analysis + N-FBA reasoning.
    Returns a structured diagnosis for automotive production (GM use-case).
    """

    # -----------------------------------------
    # 1 — Build a simple cause-effect graph
    # -----------------------------------------
    g = FishboneGraph()
    g.add_edge("torque", "tool_wear", 0.9)
    g.add_edge("torque", "material_issue", 0.7)
    g.add_edge("torque", "machine", 1.0)
    g.add_edge("machine", "operator", 0.8)
    g.add_edge("operator", "environment", 0.5)

    # -----------------------------------------
    # 2 — Run the N-FBA model
    # -----------------------------------------
    result = build_fishbone_v2(g, seed="torque")

    # Extract values safely
    morphology = result.get("morphology", {})
    spine_nodes = result.get("spine_nodes", [])
    microspines = result.get("microspines", [])

    # -----------------------------------------
    # 3 — Industrial torque diagnostic rules
    # -----------------------------------------
    diagnosis = []

    if torque_value < target_min:
        diagnosis.append("Under-torque condition detected")

    if torque_value > target_max:
        diagnosis.append("Over-torque condition detected")

    if is_red_flag:
        diagnosis.append("Red-flag torque event")

    if jam_detected:
        diagnosis.append("Possible mechanical jam detected")

    if retries > 1:
        diagnosis.append("High retries — possible operator/tooling issue")

    if manual_check_used:
        diagnosis.append("Manual inspection required — automated variance detected")

    # -----------------------------------------
    # 4 — Build structured API response
    # -----------------------------------------
    root_cause = diagnosis[0] if diagnosis else "No abnormal torque condition detected"

    recommendation = (
        "Investigate torque anomaly immediately."
        if diagnosis
        else "No action required"
    )

    confidence = 0.85 if diagnosis else 0.99  # simple model for now
    return {
        "status": "ok",
        "torque_value": torque_value,
        "diagnosis": diagnosis,
        "root_cause": root_cause,
        "recommendation": recommendation,
        "confidence": confidence,
        "spine": spine_nodes,
        "weights": result.get("morphology", {})
    }

