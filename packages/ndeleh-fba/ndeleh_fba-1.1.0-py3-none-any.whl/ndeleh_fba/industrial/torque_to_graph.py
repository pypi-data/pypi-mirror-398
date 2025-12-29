from ndeleh_fba import Graph
from .torque import TorqueEvent, classify_torque_event


def torque_event_to_graph(event: TorqueEvent) -> Graph:
    """
    Convert a torque event into a Graph suitable for N-FBA v2 reasoning.

    The idea:
        - The seed node is "TorqueEvent"
        - Other nodes represent features like:
            "LowTorque", "JamDetected", "RedFlag", "Retries", etc.
        - The weight of each edge represents how strongly that feature
          contributes to the event.
    """

    g = Graph()

    # Main seed node
    seed = "TorqueEvent"

    # Every feature is connected to the seed with weight proportional to severity
    def add_feature(name: str, weight: float):
        if weight > 0:
            g.add_edge(seed, name, weight=weight)

    # Torque too low
    if event.torque_value < event.target_min:
        diff = event.target_min - event.torque_value
        add_feature(f"LowTorque({diff:.1f})", 1.0 + diff / 10)

    # Torque too high
    if event.torque_value > event.target_max:
        diff = event.torque_value - event.target_max
        add_feature(f"HighTorque({diff:.1f})", 1.0 + diff / 10)

    # Red flag
    if event.is_red_flag:
        add_feature("RedFlag", 1.5)

    # Jam
    if event.jam_detected is True:
        add_feature("JamDetected", 1.8)
    elif event.jam_detected is False:
        add_feature("NoJam", 0.5)

    # Retries
    if event.retries > 0:
        add_feature(f"Retries({event.retries})", 0.5 + event.retries * 0.3)

    # Manual check
    if event.manual_check_used:
        add_feature("ManualCheck", 0.8)

    # Cycle time
    if event.cycle_time is not None:
        if event.cycle_time > 3.0:
            add_feature(f"LongCycle({event.cycle_time})", 1.2)
        elif event.cycle_time < 0.4:
            add_feature(f"ShortCycle({event.cycle_time})", 0.7)

    return g
