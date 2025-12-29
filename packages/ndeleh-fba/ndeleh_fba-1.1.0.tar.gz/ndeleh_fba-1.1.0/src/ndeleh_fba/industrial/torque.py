from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional


class TorqueSeverity(Enum):
    """
    Severity level for a torque event.

    - SAFE:      No action needed, within expected noise.
    - WARNING:   Operator should check or re-torque, but no hard stop needed.
    - CRITICAL:  Potential safety/quality issue, safe stop / escalation recommended.
    """

    SAFE = auto()
    WARNING = auto()
    CRITICAL = auto()


@dataclass
class TorqueClassification:
    """
    Result of classifying a torque event.

    Attributes
    ----------
    severity:
        Severity level of the event.
    score:
        0–100 risk-style score. Higher = more concerning.
    reason:
        Human-readable explanation – suitable for logs, dashboards,
        and proposal examples.
    """

    severity: TorqueSeverity
    score: float
    reason: str


@dataclass
class TorqueEvent:
    """
    A single torque event for one bolt / fastener.

    This is intentionally simple and rule-based so that:
      - It is easy for engineers to review.
      - It is deterministic (no hidden learning).
      - It is safe for initial industrial evaluation.
    """

    # Measured torque value reported by the tool (e.g., in Nm).
    torque_value: float

    # Expected acceptable range for this fastener in this station.
    target_min: float
    target_max: float

    # True if the tool's built-in logic turned the meter "red" / NOK.
    # (Meaning the tool itself thinks something went wrong.)
    is_red_flag: bool = False

    # True if a jam or stall was detected (e.g., screw not going in, cross-thread).
    # If unknown, leave as None.
    jam_detected: Optional[bool] = None

    # Total cycle duration in seconds (optional).
    # Abnormally long or short cycles can signal issues.
    cycle_time: Optional[float] = None

    # Number of retries the operator or system attempted on this fastener.
    retries: int = 0

    # Whether the operator had to switch to a hand-check / manual torque meter.
    manual_check_used: bool = False


def classify_torque_event(event: TorqueEvent) -> TorqueClassification:
    """
    Classify a torque event using simple, transparent rules.

    This version is intentionally *fixed-rule* so that GM engineers
    can review and reason about it. No hidden learning is enabled here.

    The logic is roughly:
      - Start with a base score.
      - Add risk for:
          * red flag from the tool
          * being outside the target range
          * jams / stalls
          * excessive retries
          * suspicious cycle times
          * needing manual confirmation

      - Map the final score into SAFE / WARNING / CRITICAL.
    """

    score = 0.0
    reasons = []

    # 1. Basic range check vs target window
    if event.torque_value < event.target_min:
        score += 25
        reasons.append(
            f"Torque below target range ({event.torque_value:.1f} < {event.target_min:.1f})."
        )
    elif event.torque_value > event.target_max:
        score += 25
        reasons.append(
            f"Torque above target range ({event.torque_value:.1f} > {event.target_max:.1f})."
        )
    else:
        reasons.append(
            f"Torque within target range ({event.target_min:.1f}–{event.target_max:.1f})."
        )

    # 2. Tool red/NOK indicator
    if event.is_red_flag:
        score += 35
        reasons.append("Tool reported NOK / red condition.")

    # 3. Jamming / stall
    if event.jam_detected is True:
        score += 30
        reasons.append("Jam / stall detected (possible cross-thread or misalignment).")
    elif event.jam_detected is False:
        reasons.append("No jam / stall detected.")
    # If None, we simply don't add anything.

    # 4. Retries
    if event.retries >= 3:
        score += 25
        reasons.append(f"{event.retries} retries – repeated difficulty seating fastener.")
    elif event.retries == 2:
        score += 15
        reasons.append("2 retries – some difficulty seating fastener.")
    elif event.retries == 1:
        score += 5
        reasons.append("1 retry – minor difficulty.")
    else:
        reasons.append("No retries – normal cycle.")

    # 5. Manual check usage
    if event.manual_check_used:
        score += 15
        reasons.append("Manual torque check used – operator lacked confidence in tool reading.")

    # 6. Cycle time – rough heuristic if available
    if event.cycle_time is not None:
        # These thresholds are just example defaults; in a real plant
        # they would be tuned per station.
        if event.cycle_time > 3.0:
            score += 10
            reasons.append(
                f"Cycle time long ({event.cycle_time:.2f}s) – may signal struggle or jam."
            )
        elif event.cycle_time < 0.4:
            score += 5
            reasons.append(
                f"Cycle time very short ({event.cycle_time:.2f}s) – may signal mis-trigger."
            )
        else:
            reasons.append(
                f"Cycle time in normal band ({event.cycle_time:.2f}s)."
            )

    # Normalize score into [0, 100] soft cap
    if score < 0:
        score = 0.0
    if score > 100:
        score = 100.0

    # Map score to severity
    if score >= 60:
        severity = TorqueSeverity.CRITICAL
        reasons.append("Overall assessment: CRITICAL – safe stop / escalation recommended.")
    elif score >= 30:
        severity = TorqueSeverity.WARNING
        reasons.append("Overall assessment: WARNING – operator / technician check recommended.")
    else:
        severity = TorqueSeverity.SAFE
        reasons.append("Overall assessment: SAFE – no immediate action required.")

    reason_text = " ".join(reasons)

    return TorqueClassification(
        severity=severity,
        score=score,
        reason=reason_text,
    )
