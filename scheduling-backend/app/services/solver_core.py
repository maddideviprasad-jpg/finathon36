import time
from app.models.schemas import ScheduleRequest, ScheduleResponse, Assignment, ConflictDetail
from app.services.explainer import explainer_instance

def run_optimization_pipeline(request: ScheduleRequest, task_id: str) -> ScheduleResponse:
    # Simulate computation time
    time.sleep(2)
    
    # Mock some output
    assignments = []
    if request.employees and request.shifts:
        assignments.append(
            Assignment(
                employee_id=request.employees[0].id,
                shift_id=request.shifts[0].id,
                role=request.employees[0].roles[0] if request.employees[0].roles else "staff"
            )
        )
    
    # Mock some conflicts
    conflicts = []
    if len(request.employees) < len(request.shifts):
        conflicts.append(
            ConflictDetail(
                type="Understaffed",
                description="Not enough employees to cover all shifts."
            )
        )
    
    summary = explainer_instance.summarize_conflicts(conflicts)
    
    return ScheduleResponse(
        status="success",
        assignments=assignments,
        conflicts=conflicts,
        summary=summary
    )