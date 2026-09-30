"""
Data models for the ShiftWise mathematical scheduling engine.
Defines Employee, Shift, Requirement, Assignment, Metrics, and OptimizationResult.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any


@dataclass
class Employee:
    """Represents an employee in the scheduling system."""
    id: str
    name: str
    department: str
    skills: List[str] = field(default_factory=list)
    hourly_cost: float = 0.0
    max_hours: float = 40.0
    availability: List[str] = field(default_factory=list)
    leave: List[str] = field(default_factory=list)
    preferred_shifts: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Employee":
        return cls(
            id=str(data["id"]),
            name=str(data["name"]),
            department=str(data["department"]),
            skills=list(data.get("skills", [])),
            hourly_cost=float(data.get("hourly_cost", 0.0)),
            max_hours=float(data.get("max_hours", 40.0)),
            availability=list(data.get("availability", [])),
            leave=list(data.get("leave", [])),
            preferred_shifts=list(data.get("preferred_shifts", []))
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Shift:
    """Represents a work shift in the scheduling system."""
    id: str
    day: str
    name: str
    start_time: str
    end_time: str
    duration_hours: float

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Shift":
        return cls(
            id=str(data["id"]),
            day=str(data["day"]),
            name=str(data["name"]),
            start_time=str(data["start_time"]),
            end_time=str(data["end_time"]),
            duration_hours=float(data.get("duration_hours", 8.0))
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Requirement:
    """Represents staffing requirements for a shift."""
    shift_id: str
    required_department: Optional[str] = None
    required_skills: List[str] = field(default_factory=list)
    minimum_staffing: int = 1

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Requirement":
        return cls(
            shift_id=str(data["shift_id"]),
            required_department=data.get("required_department"),
            required_skills=list(data.get("required_skills", [])),
            minimum_staffing=int(data.get("minimum_staffing", 1))
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Assignment:
    """Represents an employee shift assignment result."""
    employee_id: str
    employee_name: str
    shift_id: str
    shift_name: str
    day: str
    hours: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Metrics:
    """Key performance metrics of the generated schedule."""
    coverage_percent: float
    total_assigned_hours: float
    total_cost: float
    solve_time_seconds: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "coverage_percent": round(self.coverage_percent, 2),
            "total_assigned_hours": round(self.total_assigned_hours, 2),
            "total_cost": round(self.total_cost, 2),
            "solve_time_seconds": round(self.solve_time_seconds, 4)
        }


@dataclass
class OptimizationResult:
    """Structured response from the scheduling engine."""
    status: str  # OPTIMAL, FEASIBLE, INFEASIBLE, UNKNOWN
    assignments: List[Assignment] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "assignments": [a.to_dict() for a in self.assignments],
            "metrics": self.metrics
        }
