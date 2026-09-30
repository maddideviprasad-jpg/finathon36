import uuid
from fastapi import APIRouter, BackgroundTasks, HTTPException
from app.models.schemas import ScheduleRequest, ScheduleResponse
from app.services.solver_core import run_optimization_pipeline

router = APIRouter(prefix="/api/v1/schedules", tags=["Schedules"])

# In-memory store for task results (Replace with Redis in production if needed)
tasks_db: dict[str, dict] = {}

def execute_solver_task(task_id: str, request_data: ScheduleRequest):
    try:
        result = run_optimization_pipeline(request_data, task_id)
        tasks_db[task_id] = {"status": "SUCCESS", "data": result}
    except Exception as e:
        tasks_db[task_id] = {"status": "FAILED", "error": str(e)}

@router.post("/generate", status_code=202)
def generate_schedule(request_data: ScheduleRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    tasks_db[task_id] = {"status": "PENDING", "data": None}
    
    # Run solver asynchronously in the background
    background_tasks.add_task(execute_solver_task, task_id, request_data)
    
    return {
        "task_id": task_id,
        "status": "PENDING",
        "message": "Optimization process started."
    }

@router.get("/{task_id}")
def get_schedule_status(task_id: str):
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task ID not found")
    
    task_info = tasks_db[task_id]
    if task_info["status"] == "PENDING":
        return {"task_id": task_id, "status": "PENDING"}
    elif task_info["status"] == "FAILED":
        return {"task_id": task_id, "status": "FAILED", "error": task_info["error"]}
    
    return task_info["data"]