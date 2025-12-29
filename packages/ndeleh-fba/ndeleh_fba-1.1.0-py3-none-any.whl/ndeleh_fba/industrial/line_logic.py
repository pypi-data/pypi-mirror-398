"""
Line continuity logic for Ndeleh-FBA v1.1.0

Purpose:
- Prevent full line stoppage when a single station underperforms
- Preserve throughput while isolating local issues
"""

from typing import Dict


def analyze_line_continuity(
    station_id: str,
    performance_score: float,
    is_critical: bool,
    dependency_clear: bool,
) -> Dict:
    """
    Analyze whether a production line should continue running.
    """

    diagnosis = []

    # Default assumptions
    line_status = "CONTINUE"
    action = "continue"

    # Performance analysis
    if performance_score < 0.5:
        diagnosis.append("Severe underperformance detected")
    elif performance_score < 0.75:
        diagnosis.append("Moderate underperformance detected")

    # Decision logic
    if is_critical and performance_score <= 0.5:
        line_status = "STOP"
        action = "halt_line"
        diagnosis.append("Critical station failure — line stopped")

    elif not is_critical and performance_score < 0.75:
        if dependency_clear:
            line_status = "CONTINUE"
            action = "isolate_station"
            diagnosis.append("Station isolated — line continues")
        else:
            line_status = "CONTINUE"
            action = "slow_line"
            diagnosis.append("Dependencies unclear — line slowed")

    # Confidence heuristic
    confidence = round(0.9 - max(0, 0.7 - performance_score), 2)
    confidence = max(0.5, min(confidence, 0.99))

    return {
        "station_id": station_id,
        "line_status": line_status,
        "action": action,
        "diagnosis": diagnosis,
        "confidence": confidence,
    }

