from typing import List, Dict

def auto_build_edges_from_torque(req) -> List[Dict]:
    edges = []

    # Rule 1: Low torque → “under-torque”
    if req.torque_value < req.target_min:
        edges.append({"src": "torque_value", "dst": "under_torque", "weight": 0.9})

    # Rule 2: Over torque → “over-torque”
    if req.torque_value > req.target_max:
        edges.append({"src": "torque_value", "dst": "over_torque", "weight": 0.9})

    # Rule 3: Jam detection strongly connected
    if req.jam_detected:
        edges.append({"src": "jam_detected", "dst": "cycle_time", "weight": 1.0})

    # Rule 4: Red flag increases weight
    if req.is_red_flag:
        edges.append({"src": "is_red_flag", "dst": "manual_check_used", "weight": 0.8})

    # Rule 5: Too many retries indicate tool degradation
    if req.retries > 1:
        edges.append({"src": "retries", "dst": "tool_warning", "weight": 1.0})

    return edges
