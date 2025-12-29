from ndeleh_fba.industrial.line_logic import analyze_line_continuity


def test_non_critical_station_continues():
    result = analyze_line_continuity(
        station_id="S4",
        performance_score=0.55,
        is_critical=False,
        dependency_clear=True
    )
    assert result["line_status"] == "CONTINUE"


def test_critical_station_stops():
    result = analyze_line_continuity(
        station_id="S1",
        performance_score=0.5,
        is_critical=True,
        dependency_clear=True
    )
    assert result["line_status"] == "STOP"
