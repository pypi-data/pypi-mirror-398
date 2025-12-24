"""
Type stubs for srmp module
Provides type hints and documentation for IDE autocomplete
"""

from .planner_interface import (
    PlannerInterface,
    Pose,
    GoalType,
    GoalConstraint,
    Trajectory
)

__all__ = [
    'PlannerInterface',
    'Pose',
    'GoalType',
    'GoalConstraint',
    'Trajectory'
]
