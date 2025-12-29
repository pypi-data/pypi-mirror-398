import pytest
from ndeleh_fba.industrial.industrial_logic import analyze_torque_event


def test_normal_torque_case():
    """Should return no abnormal condition and high confidence."""
    result = analyze_torque_event(
        torque_value=25,
        target_min=22,
        target_max=30,
        is_red_flag=False,
        jam_detected=False,
        cycle_time=3.2,
        retries=0,
        manual_check_used=False
    )

    assert result["root_cause"] == "No abnormal torque condition detected"
    assert result["confidence"] > 0.9
    assert "recommendation" in result
    assert isinstance(result["spine"], list)
    assert isinstance(result["weights"], dict)


def test_under_torque_detection():
    """Should detect under-torque condition."""
    result = analyze_torque_event(
        torque_value=18,
        target_min=22,
        target_max=30,
        is_red_flag=False,
        jam_detected=False,
        cycle_time=3.2,
        retries=0,
        manual_check_used=False
    )

    assert "Under-torque condition detected" in result["root_cause"]


def test_over_torque_detection():
    """Should detect over-torque condition."""
    result = analyze_torque_event(
        torque_value=40,
        target_min=22,
        target_max=30,
        is_red_flag=False,
        jam_detected=False,
        cycle_time=3.2,
        retries=0,
        manual_check_used=False
    )

    assert "Over-torque condition detected" in result["root_cause"]


def test_red_flag_event():
    """Should detect a red-flag torque event."""
    result = analyze_torque_event(
        torque_value=25,
        target_min=22,
        target_max=30,
        is_red_flag=True,
        jam_detected=False,
        cycle_time=3.2,
        retries=0,
        manual_check_used=False
    )

    assert "Red-flag torque event" in result["root_cause"]


def test_jam_detection():
    """Should detect mechanical jam."""
    result = analyze_torque_event(
        torque_value=25,
        target_min=22,
        target_max=30,
        is_red_flag=False,
        jam_detected=True,
        cycle_time=3.2,
        retries=0,
        manual_check_used=False
    )

    assert "mechanical jam" in result["root_cause"]


def test_high_retry_detection():
    """Should detect excessive retries."""
    result = analyze_torque_event(
        torque_value=25,
        target_min=22,
        target_max=30,
        is_red_flag=False,
        jam_detected=False,
        cycle_time=3.2,
        retries=3,
        manual_check_used=False
    )

    assert "retries" in result["root_cause"]


def test_manual_check_detection():
    """Should require manual inspection."""
    result = analyze_torque_event(
        torque_value=25,
        target_min=22,
        target_max=30,
        is_red_flag=False,
        jam_detected=False,
        cycle_time=3.2,
        retries=0,
        manual_check_used=True
    )

    assert "manual" in result["root_cause"].lower()
