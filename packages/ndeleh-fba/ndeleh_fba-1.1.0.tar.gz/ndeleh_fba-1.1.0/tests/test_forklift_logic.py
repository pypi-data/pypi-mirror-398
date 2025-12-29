from ndeleh_fba.industrial.forklift_logic import analyze_forklift_event

def test_forklift_normal_case():
    result = analyze_forklift_event(
        speed_kmh=5.0,
        load_kg=500,
        rated_load_kg=1000,
        tilt_warning=False,
        proximity_alert=False,
        brake_events=0,
        operator_id="op1",
    )
    assert result["status"] == "ok"
    assert result["root_cause"] == "No abnormal forklift condition detected"
    assert isinstance(result["spine"], list)
    assert isinstance(result["weights"], dict)

def test_forklift_overload():
    result = analyze_forklift_event(
        speed_kmh=5.0,
        load_kg=1200,
        rated_load_kg=1000,
        tilt_warning=False,
        proximity_alert=False,
        brake_events=0,
        operator_id="op2",
    )
    assert "Overload" in result["root_cause"]

def test_forklift_tilt_warning():
    result = analyze_forklift_event(
        speed_kmh=5.0,
        load_kg=500,
        rated_load_kg=1000,
        tilt_warning=True,
        proximity_alert=False,
        brake_events=0,
        operator_id="op3",
    )
    assert "Tilt warning" in result["root_cause"]
