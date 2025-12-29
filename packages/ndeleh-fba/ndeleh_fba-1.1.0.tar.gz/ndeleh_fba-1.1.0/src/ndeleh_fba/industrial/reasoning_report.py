from __future__ import annotations

from typing import Dict

from ndeleh_fba import (
    TorqueClassification,
    TorqueSeverity,
    FishboneV2,
    SpineNodeV2,
)


def _count_micro_spines(fishbone: FishboneV2) -> int:
    """Count how many ribs behave like 'micro-spines' (depth > parent.depth + 1)."""
    count = 0
    depth_by_id = {n.node_id: n.depth for n in fishbone.spine}

    for spine_node in fishbone.spine:
        ribs = fishbone.ribs_by_node.get(spine_node.node_id, [])
        parent_depth = depth_by_id[spine_node.node_id]
        for r in ribs:
            if r.depth > parent_depth + 1:
                count += 1
    return count


def generate_torque_reports(
    classification: TorqueClassification,
    fishbone: FishboneV2,
) -> Dict[str, str]:
    """
    Generate human + technical reasoning for GM automotive usage.
    """

    severity = classification.severity
    score = classification.score
    reason_text = classification.reason

    spine_nodes = [n.node_id for n in fishbone.spine]
    morphology = fishbone.morphology.name
    meta = fishbone.metadata

    total_ribs = meta.get("total_ribs", sum(len(v) for v in fishbone.ribs_by_node.values()))
    spine_len = meta.get("spine_length", len(spine_nodes))
    max_depth = meta.get("max_spine_depth", 0)
    micro_count = _count_micro_spines(fishbone)
    industrial_mode = meta.get("industrial_mode", True)

    # -----------------------------
    # HUMAN READABLE SUMMARY
    # -----------------------------
    human_parts = []

    # Severity summary
    human_parts.append(
        f"The event was classified as {severity.name} with a risk score of {score:.1f}. "
        f"This indicates { 'a safe and stable torque' if severity==TorqueSeverity.SAFE else 'a condition that requires attention before continuing production' }."
    )

    human_parts.append(
        f"The algorithm identified key contributing factors including: {reason_text}. "
        "These factors together shaped the outcome of this torque cycle."
    )

    human_parts.append(
        f"The system traced the event through a reasoning path of {spine_len} steps "
        f"({ ' → '.join(spine_nodes) })."
    )

    if total_ribs > 0:
        human_parts.append(
            f"Additional influencing conditions were detected ({total_ribs} side associations), "
            "representing supportive or conflicting signals during the torque attempt."
        )

    if micro_count > 0:
        human_parts.append(
            f"Notably, {micro_count} strong branching patterns were observed. "
            "These represent repeated or escalating behaviors such as jam interactions, retries, or unstable torque responses."
        )

    human_parts.append(
        f"Overall, this cycle exhibits a {morphology.lower()} behavior pattern."
    )

    human = " ".join(human_parts)

    # -----------------------------
    # TECHNICAL ENGINEERING EXPLANATION
    # -----------------------------
    tech = []

    tech.append(
        f"N-FBA v2 produced morphology={morphology}, spine_length={spine_len}, "
        f"total_ribs={total_ribs}, max_depth={max_depth}, micro_spines={micro_count}, "
        f"industrial_mode={industrial_mode}."
    )

    tech.append(
        "The main associative pathway was: " + " → ".join(spine_nodes) + "."
    )

    tech.append(
        "Side associations with weights above the threshold generated micro-spine structures, "
        "indicating non-linear interactions in sensor readings or torque progression."
    )

    tech.append(
        f"The classifier determined severity={severity.name} with score={score:.1f}, "
        "derived from tolerance deviation, jam flags, cycle anomalies, and retry patterns."
    )

    tech.append(
        "This combined view provides both scalar classification and structural context, "
        "making it suitable for diagnosing torque-tool failures, sensor conflicts, and "
        "pattern-based non-conformances in GM assembly operations."
    )

    return {
        "human": human,
        "technical": " ".join(tech),
    }

