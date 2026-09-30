"""
Hard constraints implementation for the ShiftWise CP-SAT scheduling engine.
Enforces availability, leave, required skills, department matching, minimum staffing,
max working hours, non-overlapping shifts, and minimum rest periods.
"""

from typing import Dict, List, Tuple, Any
from ortools.sat.python import cp_model
from backend.optimizer.models import Employee, Shift, Requirement

DAY_ORDER = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5, "Sun": 6}


def parse_time_to_minutes(time_str: str) -> int:
    """Converts a HH:MM string to total minutes from midnight."""
    parts = time_str.strip().split(":")
    hours = int(parts[0])
    minutes = int(parts[1]) if len(parts) > 1 else 0
    return hours * 60 + minutes


def get_day_index(day_str: str, day_map: Dict[str, int]) -> int:
    """Returns the integer index for a day string."""
    if day_str in DAY_ORDER:
        return DAY_ORDER[day_str]
    return day_map.get(day_str, 0)


def get_shift_interval(shift: Shift, day_map: Dict[str, int]) -> Tuple[int, int]:
    """Calculates absolute start and end minutes for a shift from week start."""
    d_idx = get_day_index(shift.day, day_map)
    start_min = parse_time_to_minutes(shift.start_time)
    start_abs = d_idx * 24 * 60 + start_min
    duration_min = int(round(shift.duration_hours * 60))
    end_abs = start_abs + duration_min
    return start_abs, end_abs


def is_employee_qualified_for_shift(
    employee: Employee,
    shift: Shift,
    requirements: List[Requirement]
) -> bool:
    """
    Checks if an employee has all required skills and department matching
    for any applicable requirements of a shift.
    """
    shift_reqs = [r for r in requirements if r.shift_id == shift.id]
    
    # If no explicit requirements exist, any employee can work the shift
    if not shift_reqs:
        return True

    # Employee must satisfy at least one requirement entry for the shift
    for req in shift_reqs:
        # Department check
        if req.required_department and employee.department != req.required_department:
            continue
        # Skills check - employee must possess ALL required skills
        if not set(req.required_skills).issubset(set(employee.skills)):
            continue
        return True

    return False


class ConstraintManager:
    """Applies all hard constraints to the CP-SAT model."""

    def __init__(
        self,
        model: cp_model.CpModel,
        x: Dict[Tuple[str, str], Any],
        employees: List[Employee],
        shifts: List[Shift],
        requirements: List[Requirement],
        minimum_rest_hours: float = 10.0
    ):
        self.model = model
        self.x = x
        self.employees = employees
        self.shifts = shifts
        self.requirements = requirements
        self.minimum_rest_hours = minimum_rest_hours

        # Build dynamic day map if custom days are present
        all_days = [s.day for s in shifts]
        self.day_map = {}
        idx = 0
        for d in all_days:
            if d not in DAY_ORDER and d not in self.day_map:
                self.day_map[d] = idx
                idx += 1

    def apply_all_constraints(self) -> None:
        """Applies all 8 hard constraints to the CP-SAT model."""
        self.add_availability_constraints()
        self.add_leave_constraints()
        self.add_required_skills_and_department_constraints()
        self.add_minimum_staffing_constraints()
        self.add_max_hours_constraints()
        self.add_no_overlapping_shifts_constraints()
        self.add_minimum_rest_constraints()

    def add_availability_constraints(self) -> None:
        """Constraint 1: Employee must be available on the shift's day."""
        for e in self.employees:
            for s in self.shifts:
                if s.day not in e.availability:
                    self.model.Add(self.x[e.id, s.id] == 0)

    def add_leave_constraints(self) -> None:
        """Constraint 2: Employee on leave cannot work on that day (overrides availability)."""
        for e in self.employees:
            for s in self.shifts:
                if s.day in e.leave:
                    self.model.Add(self.x[e.id, s.id] == 0)

    def add_required_skills_and_department_constraints(self) -> None:
        """Constraints 3 & 4: Employee must meet required skills and department for the shift."""
        for e in self.employees:
            for s in self.shifts:
                if not is_employee_qualified_for_shift(e, s, self.requirements):
                    self.model.Add(self.x[e.id, s.id] == 0)

    def add_minimum_staffing_constraints(self) -> None:
        """
        Constraint 5: Minimum staffing requirements per shift/requirement.
        If required qualified staff cannot be provided, the model becomes INFEASIBLE.
        """
        for s in self.shifts:
            shift_reqs = [r for r in self.requirements if r.shift_id == s.id]
            
            if not shift_reqs:
                # Default minimum staffing of 1 if no explicit requirement
                eligible_employees = [
                    e for e in self.employees 
                    if s.day in e.availability and s.day not in e.leave
                ]
                self.model.Add(
                    sum(self.x[e.id, s.id] for e in eligible_employees) >= 1
                )
            else:
                for req in shift_reqs:
                    eligible_employees = []
                    for e in self.employees:
                        # Check availability & leave
                        if s.day not in e.availability or s.day in e.leave:
                            continue
                        # Check department
                        if req.required_department and e.department != req.required_department:
                            continue
                        # Check skills
                        if not set(req.required_skills).issubset(set(e.skills)):
                            continue
                        eligible_employees.append(e)

                    # Hard constraint for minimum staffing
                    self.model.Add(
                        sum(self.x[e.id, s.id] for e in eligible_employees) >= req.minimum_staffing
                    )

    def add_max_hours_constraints(self) -> None:
        """Constraint 6: Employee total assigned hours cannot exceed max_hours (No overtime in V1)."""
        for e in self.employees:
            # Scaled to integer minutes to avoid floating-point inaccuracies
            max_minutes = int(round(e.max_hours * 60))
            employee_shift_minutes = []
            for s in self.shifts:
                duration_minutes = int(round(s.duration_hours * 60))
                employee_shift_minutes.append(self.x[e.id, s.id] * duration_minutes)
            
            self.model.Add(sum(employee_shift_minutes) <= max_minutes)

    def add_no_overlapping_shifts_constraints(self) -> None:
        """Constraint 7: Employee cannot work two shifts that overlap in time."""
        shift_intervals = {s.id: get_shift_interval(s, self.day_map) for s in self.shifts}
        
        n_shifts = len(self.shifts)
        for i in range(n_shifts):
            s1 = self.shifts[i]
            start1, end1 = shift_intervals[s1.id]

            for j in range(i + 1, n_shifts):
                s2 = self.shifts[j]
                start2, end2 = shift_intervals[s2.id]

                # Check if intervals [start1, end1) and [start2, end2) overlap
                if max(start1, start2) < min(end1, end2):
                    for e in self.employees:
                        self.model.Add(self.x[e.id, s1.id] + self.x[e.id, s2.id] <= 1)

    def add_minimum_rest_constraints(self) -> None:
        """Constraint 8: Minimum rest period between consecutive shifts for an employee."""
        min_rest_minutes = int(round(self.minimum_rest_hours * 60))
        shift_intervals = {s.id: get_shift_interval(s, self.day_map) for s in self.shifts}

        n_shifts = len(self.shifts)
        for i in range(n_shifts):
            s1 = self.shifts[i]
            start1, end1 = shift_intervals[s1.id]

            for j in range(n_shifts):
                if i == j:
                    continue
                s2 = self.shifts[j]
                start2, end2 = shift_intervals[s2.id]

                # If s1 ends before s2 starts
                if end1 <= start2:
                    rest_duration = start2 - end1
                    if rest_duration < min_rest_minutes:
                        for e in self.employees:
                            self.model.Add(self.x[e.id, s1.id] + self.x[e.id, s2.id] <= 1)
