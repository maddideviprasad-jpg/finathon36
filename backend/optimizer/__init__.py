"""
Optimization package for ShiftWise scheduling engine.
"""

from backend.optimizer.models import (
    Employee,
    Shift,
    Requirement,
    Assignment,
    Metrics,
    OptimizationResult
)


def __getattr__(name: str):
    if name == "ShiftScheduler":
        from backend.optimizer.scheduler import ShiftScheduler
        return ShiftScheduler
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__all__ = [
    "Employee",
    "Shift",
    "Requirement",
    "Assignment",
    "Metrics",
    "OptimizationResult",
    "ShiftScheduler"
]
