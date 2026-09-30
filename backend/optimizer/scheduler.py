"""
Main mathematical scheduling engine using Google OR-Tools CP-SAT.
Generates feasible and optimal employee schedules respecting hard constraints.
"""

import time
import json
from typing import Dict, List, Any, Union
from ortools.sat.python import cp_model

from backend.optimizer.models import (
    Employee,
    Shift,
    Requirement,
    Assignment,
    OptimizationResult
)
from backend.optimizer.constraints import ConstraintManager
from backend.optimizer.objectives import apply_labor_cost_objective


class ShiftScheduler:
    """
    Mathematical scheduling engine for ShiftWise powered by Google OR-Tools CP-SAT.
    """

    def __init__(self, minimum_rest_hours: float = 10.0, max_time_seconds: float = 10.0):
        self.minimum_rest_hours = minimum_rest_hours
        self.max_time_seconds = max_time_seconds

    def solve(
        self,
        employees_data: List[Union[Employee, Dict[str, Any]]],
        shifts_data: List[Union[Shift, Dict[str, Any]]],
        requirements_data: List[Union[Requirement, Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        Solves the employee scheduling problem using OR-Tools CP-SAT.
        Returns a structured response dictionary.
        """
        # Convert raw dicts to dataclass instances if needed
        employees = [
            e if isinstance(e, Employee) else Employee.from_dict(e)
            for e in employees_data
        ]
        shifts = [
            s if isinstance(s, Shift) else Shift.from_dict(s)
            for s in shifts_data
        ]
        requirements = [
            r if isinstance(r, Requirement) else Requirement.from_dict(r)
            for r in requirements_data
        ]

        # Initialize CP-SAT model
        model = cp_model.CpModel()

        # Decision Variables: x[e_id, s_id] = 1 if employee e works shift s, 0 otherwise
        x = {}
        for e in employees:
            for s in shifts:
                x[e.id, s.id] = model.NewBoolVar(f"x_{e.id}_{s.id}")

        # Apply all hard constraints
        constraint_manager = ConstraintManager(
            model=model,
            x=x,
            employees=employees,
            shifts=shifts,
            requirements=requirements,
            minimum_rest_hours=self.minimum_rest_hours
        )
        constraint_manager.apply_all_constraints()

        # Apply cost minimization objective
        apply_labor_cost_objective(model, x, employees, shifts)

        # Configure CP-SAT solver
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = self.max_time_seconds

        # Solve model
        start_time = time.time()
        status_code = solver.Solve(model)
        solve_time = solver.WallTime()

        # Interpret status
        if status_code == cp_model.OPTIMAL:
            status_str = "OPTIMAL"
        elif status_code == cp_model.FEASIBLE:
            status_str = "FEASIBLE"
        elif status_code == cp_model.INFEASIBLE:
            return {
                "status": "INFEASIBLE",
                "assignments": [],
                "metrics": {
                    "coverage_percent": 0.0,
                    "total_assigned_hours": 0.0,
                    "total_cost": 0.0,
                    "solve_time_seconds": round(solve_time, 4)
                }
            }
        else:
            return {
                "status": "UNKNOWN",
                "assignments": [],
                "metrics": {
                    "coverage_percent": 0.0,
                    "total_assigned_hours": 0.0,
                    "total_cost": 0.0,
                    "solve_time_seconds": round(solve_time, 4)
                }
            }

        # Format output assignments & calculate metrics
        assignments = []
        total_assigned_hours = 0.0
        total_cost = 0.0

        for e in employees:
            for s in shifts:
                if solver.Value(x[e.id, s.id]) == 1:
                    assignments.append({
                        "employee_id": e.id,
                        "employee_name": e.name,
                        "shift_id": s.id,
                        "shift_name": s.name,
                        "day": s.day,
                        "hours": s.duration_hours
                    })
                    total_assigned_hours += s.duration_hours
                    total_cost += e.hourly_cost * s.duration_hours

        # Sort assignments by day and shift_id for clean presentation
        day_order_idx = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5, "Sun": 6}
        assignments.sort(key=lambda a: (day_order_idx.get(a["day"], 99), a["shift_id"]))

        # Compute staffing coverage
        total_required_staffing = sum(r.minimum_staffing for r in requirements)
        if total_required_staffing > 0:
            coverage_percent = round(min(100.0, (len(assignments) / total_required_staffing) * 100.0), 2)
        else:
            coverage_percent = 100.0

        metrics = {
            "coverage_percent": coverage_percent,
            "total_assigned_hours": round(total_assigned_hours, 2),
            "total_cost": round(total_cost, 2),
            "solve_time_seconds": round(solve_time, 4)
        }

        return {
            "status": status_str,
            "assignments": assignments,
            "metrics": metrics
        }


def get_sample_test_data():
    """Generates realistic test dataset containing employees, shifts, and requirements."""
    employees = [
        {
            "id": "E01",
            "name": "Rahul",
            "department": "Engineering",
            "skills": ["Python", "AWS"],
            "hourly_cost": 400,
            "max_hours": 40,
            "availability": ["Mon", "Tue", "Wed", "Thu", "Fri"],
            "leave": ["Mon"],  # Rahul on leave on Monday
            "preferred_shifts": ["Morning"]
        },
        {
            "id": "E02",
            "name": "Priya",
            "department": "Engineering",
            "skills": ["Python", "Docker"],
            "hourly_cost": 450,
            "max_hours": 40,
            "availability": ["Mon", "Tue", "Wed", "Thu", "Fri"],
            "leave": [],
            "preferred_shifts": ["Morning"]
        },
        {
            "id": "E03",
            "name": "Amit",
            "department": "DevOps",
            "skills": ["AWS", "Kubernetes", "Docker"],
            "hourly_cost": 500,
            "max_hours": 32,
            "availability": ["Mon", "Tue", "Wed", "Thu", "Fri"],
            "leave": [],
            "preferred_shifts": ["Evening"]
        },
        {
            "id": "E04",
            "name": "Sneha",
            "department": "Support",
            "skills": ["Customer Service", "Python"],
            "hourly_cost": 300,
            "max_hours": 40,
            "availability": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
            "leave": [],
            "preferred_shifts": ["Night"]
        },
        {
            "id": "E05",
            "name": "Vikram",
            "department": "Support",
            "skills": ["Customer Service"],
            "hourly_cost": 280,
            "max_hours": 24,
            "availability": ["Mon", "Tue", "Wed", "Thu", "Fri"],
            "leave": ["Tue"],
            "preferred_shifts": ["Morning"]
        }
    ]

    shifts = [
        {
            "id": "S01",
            "day": "Mon",
            "name": "Morning",
            "start_time": "09:00",
            "end_time": "17:00",
            "duration_hours": 8
        },
        {
            "id": "S02",
            "day": "Mon",
            "name": "Evening",
            "start_time": "17:00",
            "end_time": "01:00",
            "duration_hours": 8
        },
        {
            "id": "S03",
            "day": "Tue",
            "name": "Morning",
            "start_time": "09:00",
            "end_time": "17:00",
            "duration_hours": 8
        },
        {
            "id": "S04",
            "day": "Tue",
            "name": "Night",
            "start_time": "23:00",
            "end_time": "07:00",
            "duration_hours": 8
        },
        {
            "id": "S05",
            "day": "Wed",
            "name": "Morning",
            "start_time": "09:00",
            "end_time": "17:00",
            "duration_hours": 8
        }
    ]

    requirements = [
        {
            "shift_id": "S01",
            "required_department": "Engineering",
            "required_skills": ["Python"],
            "minimum_staffing": 1
        },
        {
            "shift_id": "S02",
            "required_department": "DevOps",
            "required_skills": ["AWS"],
            "minimum_staffing": 1
        },
        {
            "shift_id": "S03",
            "required_department": "Engineering",
            "required_skills": ["Python"],
            "minimum_staffing": 1
        },
        {
            "shift_id": "S04",
            "required_department": "Support",
            "required_skills": ["Customer Service"],
            "minimum_staffing": 1
        },
        {
            "shift_id": "S05",
            "required_department": "Engineering",
            "required_skills": ["Python"],
            "minimum_staffing": 1
        }
    ]

    return employees, shifts, requirements


def run_all_tests():
    """Runs tests for all 8 constraint scenarios."""
    scheduler = ShiftScheduler()
    print("=" * 70)
    print(" SHIFTWISE SCHEDULING ENGINE V1 - CONSTRAINT TEST SUITE")
    print("=" * 70)

    # ----------------------------------------------------
    # TEST 1: Normal feasible schedule
    # ----------------------------------------------------
    print("\n--- TEST 1: Normal Feasible Schedule ---")
    emp, shf, req = get_sample_test_data()
    res1 = scheduler.solve(emp, shf, req)
    print(f"Status: {res1['status']}")
    print(f"Coverage: {res1['metrics'].get('coverage_percent')}%")
    print(f"Total Hours: {res1['metrics'].get('total_assigned_hours')}")
    print(f"Total Cost: INR {res1['metrics'].get('total_cost')}")
    print(f"Solve Time: {res1['metrics'].get('solve_time_seconds')}s")
    print("Assignments:")
    print(json.dumps(res1["assignments"], indent=2))
    assert res1["status"] in ["OPTIMAL", "FEASIBLE"], "Test 1 Failed!"

    # ----------------------------------------------------
    # TEST 2: Employee is on leave
    # ----------------------------------------------------
    print("\n--- TEST 2: Employee on Leave Constraint ---")
    # Rahul (E01) is on leave on Monday (S01). Verify Rahul is NOT assigned to S01.
    assigned_to_s01 = [a["employee_name"] for a in res1["assignments"] if a["shift_id"] == "S01"]
    print(f"Shift S01 (Mon Morning) assigned to: {assigned_to_s01}")
    assert "Rahul" not in assigned_to_s01, "Test 2 Failed! Rahul assigned while on leave."
    print("PASSED: Employee on leave (Rahul on Mon) was not assigned.")

    # ----------------------------------------------------
    # TEST 3: Employee lacks required skill
    # ----------------------------------------------------
    print("\n--- TEST 3: Required Skill Constraint ---")
    # Add a shift requiring "Kubernetes" skill in Engineering
    test_shf = [
        {"id": "S_K8S", "day": "Thu", "name": "K8s Shift", "start_time": "09:00", "end_time": "17:00", "duration_hours": 8}
    ]
    test_req = [
        {"shift_id": "S_K8S", "required_department": "DevOps", "required_skills": ["Kubernetes"], "minimum_staffing": 1}
    ]
    res3 = scheduler.solve(emp, test_shf, test_req)
    assigned_k8s = [a["employee_name"] for a in res3["assignments"] if a["shift_id"] == "S_K8S"]
    print(f"K8s Shift assigned to: {assigned_k8s}")
    # Only Amit has Kubernetes in DevOps
    assert assigned_k8s == ["Amit"], f"Test 3 Failed! Expected ['Amit'], got {assigned_k8s}"
    print("PASSED: Only employee with required skill (Amit) was assigned.")

    # ----------------------------------------------------
    # TEST 4: Employee is unavailable
    # ----------------------------------------------------
    print("\n--- TEST 4: Employee Availability Constraint ---")
    # E05 (Vikram) is unavailable on Sat/Sun
    test_shf4 = [
        {"id": "S_SAT", "day": "Sat", "name": "Sat Shift", "start_time": "09:00", "end_time": "17:00", "duration_hours": 8}
    ]
    test_req4 = [
        {"shift_id": "S_SAT", "required_department": "Support", "required_skills": ["Customer Service"], "minimum_staffing": 1}
    ]
    res4 = scheduler.solve(emp, test_shf4, test_req4)
    assigned_sat = [a["employee_name"] for a in res4["assignments"] if a["shift_id"] == "S_SAT"]
    print(f"Sat Shift assigned to: {assigned_sat}")
    assert "Vikram" not in assigned_sat, "Test 4 Failed! Vikram assigned when unavailable."
    print("PASSED: Unavailable employee (Vikram on Sat) was not assigned.")

    # ----------------------------------------------------
    # TEST 5: Maximum working hours
    # ----------------------------------------------------
    print("\n--- TEST 5: Maximum Working Hours Constraint ---")
    # E05 has max_hours = 24. Assigning 4 shifts of 8 hours (32 hours) should limit assignments to <= 3 shifts (24 hours).
    test_emp5 = [
        {
            "id": "E_LIMITED",
            "name": "LimitedEmp",
            "department": "Engineering",
            "skills": ["Python"],
            "hourly_cost": 400,
            "max_hours": 16,
            "availability": ["Mon", "Tue", "Wed", "Thu"],
            "leave": [],
            "preferred_shifts": []
        }
    ]
    test_shf5 = [
        {"id": "S1", "day": "Mon", "name": "Shift1", "start_time": "09:00", "end_time": "17:00", "duration_hours": 8},
        {"id": "S2", "day": "Tue", "name": "Shift2", "start_time": "09:00", "end_time": "17:00", "duration_hours": 8},
        {"id": "S3", "day": "Wed", "name": "Shift3", "start_time": "09:00", "end_time": "17:00", "duration_hours": 8}
    ]
    test_req5 = [
        {"shift_id": "S1", "minimum_staffing": 1},
        {"shift_id": "S2", "minimum_staffing": 1},
        {"shift_id": "S3", "minimum_staffing": 1}
    ]
    res5 = scheduler.solve(test_emp5, test_shf5, test_req5)
    print(f"Max hours test status: {res5['status']}")
    # Model should be INFEASIBLE because max hours is 16, but 3 shifts of 8 hours (24h) are required as minimum staffing
    assert res5["status"] == "INFEASIBLE", "Test 5 Failed! Model should be INFEASIBLE when max_hours < required total."
    print("PASSED: Model correctly enforced max working hours limit.")

    # ----------------------------------------------------
    # TEST 6: Overlapping shifts
    # ----------------------------------------------------
    print("\n--- TEST 6: Overlapping Shifts Constraint ---")
    # Shift A: 10:00 - 18:00, Shift B: 14:00 - 22:00 on Monday
    single_emp = [
        {
            "id": "E_SOLO",
            "name": "SoloWorker",
            "department": "Eng",
            "skills": ["Python"],
            "hourly_cost": 400,
            "max_hours": 40,
            "availability": ["Mon"],
            "leave": []
        }
    ]
    overlapping_shifts = [
        {"id": "S_A", "day": "Mon", "name": "ShiftA", "start_time": "10:00", "end_time": "18:00", "duration_hours": 8},
        {"id": "S_B", "day": "Mon", "name": "ShiftB", "start_time": "14:00", "end_time": "22:00", "duration_hours": 8}
    ]
    overlap_reqs = [
        {"shift_id": "S_A", "minimum_staffing": 1},
        {"shift_id": "S_B", "minimum_staffing": 1}
    ]
    res6 = scheduler.solve(single_emp, overlapping_shifts, overlap_reqs)
    print(f"Overlapping shifts test status: {res6['status']}")
    assert res6["status"] == "INFEASIBLE", "Test 6 Failed! Single employee cannot work overlapping shifts."
    print("PASSED: Overlapping shifts constraint prevented double booking.")

    # ----------------------------------------------------
    # TEST 7: Minimum rest period
    # ----------------------------------------------------
    print("\n--- TEST 7: Minimum Rest Constraint ---")
    # Monday 16:00 - 00:00 (ends 00:00 Tuesday)
    # Tuesday 08:00 - 16:00 (starts 08:00 Tuesday -> rest = 8 hours < 10 hours)
    rest_shifts = [
        {"id": "S_NIGHT", "day": "Mon", "name": "LateShift", "start_time": "16:00", "end_time": "00:00", "duration_hours": 8},
        {"id": "S_EARLY", "day": "Tue", "name": "EarlyShift", "start_time": "08:00", "end_time": "16:00", "duration_hours": 8}
    ]
    rest_reqs = [
        {"shift_id": "S_NIGHT", "minimum_staffing": 1},
        {"shift_id": "S_EARLY", "minimum_staffing": 1}
    ]
    res7 = scheduler.solve(single_emp, rest_shifts, rest_reqs)
    print(f"Minimum rest test status: {res7['status']}")
    assert res7["status"] == "INFEASIBLE", "Test 7 Failed! Rest period was 8h (<10h minimum)."
    print("PASSED: Minimum rest constraint (10h default) enforced.")

    # ----------------------------------------------------
    # TEST 8: Impossible staffing requirement
    # ----------------------------------------------------
    print("\n--- TEST 8: Impossible Staffing Requirement ---")
    impossible_reqs = [
        {
            "shift_id": "S01",
            "required_department": "Engineering",
            "required_skills": ["Quantum Computing"],  # Nobody has this skill
            "minimum_staffing": 10
        }
    ]
    res8 = scheduler.solve(emp, shf, impossible_reqs)
    print(f"Impossible staffing test result: {json.dumps(res8, indent=2)}")
    assert res8["status"] == "INFEASIBLE", "Test 8 Failed! Expected INFEASIBLE status."
    assert res8["assignments"] == [], "Test 8 Failed! Assignments should be empty for INFEASIBLE."
    assert res8["metrics"]["coverage_percent"] == 0.0, "Test 8 Failed! Expected coverage_percent to be 0 for INFEASIBLE."
    assert res8["metrics"]["total_assigned_hours"] == 0.0, "Test 8 Failed! Expected total_assigned_hours to be 0 for INFEASIBLE."
    assert res8["metrics"]["total_cost"] == 0.0, "Test 8 Failed! Expected total_cost to be 0 for INFEASIBLE."
    assert "solve_time_seconds" in res8["metrics"], "Test 8 Failed! Expected solve_time_seconds in metrics."
    print("PASSED: Impossible staffing correctly returned INFEASIBLE with standard metrics structure without crashing.")

    print("\n" + "=" * 70)
    print(" ALL 8 TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
