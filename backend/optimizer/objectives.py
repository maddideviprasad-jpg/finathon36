"""
Objective functions for the ShiftWise scheduling engine.
For Version 1, provides labor cost minimization.
"""

from typing import Dict, List, Tuple, Any
from ortools.sat.python import cp_model
from backend.optimizer.models import Employee, Shift


def apply_labor_cost_objective(
    model: cp_model.CpModel,
    x: Dict[Tuple[str, str], Any],
    employees: List[Employee],
    shifts: List[Shift]
) -> None:
    """
    Minimizes total labor cost across all assigned shifts.
    Cost for (e, s) = employee.hourly_cost * shift.duration_hours.
    """
    cost_terms = []
    for e in employees:
        for s in shifts:
            cost = int(round(e.hourly_cost * s.duration_hours))
            cost_terms.append(x[e.id, s.id] * cost)

    model.Minimize(sum(cost_terms))
