"""
Industrial / plant-focused extensions for N-FBA.

This module contains helper logic for reasoning about tools, sensors,
and production events (e.g., torque tool behavior in an automotive plant).
"""
from .line_logic import analyze_line_continuity
from .torque import (
    TorqueSeverity,
    TorqueClassification,
    TorqueEvent,
    classify_torque_event,
)
