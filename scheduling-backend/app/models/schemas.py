from pydantic import BaseModel, Field
from typing import List, Optional

class Employee(BaseModel):
    id: str
    name: str
    roles: List[str]
    max_hours: float

class Shift(BaseModel):
    id: str
    start_time: str
    end_time: str
    required_roles: List[str]

class ConstraintsConfig(BaseModel):
    max_consecutive_shifts: int = 5
    min_rest_hours: int = 12

class ScheduleRequest(BaseModel):
    employees: List[Employee]
    shifts: List[Shift]
    constraints: ConstraintsConfig = Field(default_factory=ConstraintsConfig)

class Assignment(BaseModel):
    employee_id: str
    shift_id: str
    role: str

class ConflictDetail(BaseModel):
    type: str
    description: str

class ScheduleResponse(BaseModel):
    status: str
    assignments: List[Assignment]
    conflicts: List[ConflictDetail]
    summary: Optional[str] = None