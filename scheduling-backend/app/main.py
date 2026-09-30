from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes_schedule import router as schedule_router

app = FastAPI(title="OptiShift Backend API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(schedule_router)

@app.get("/health")
def health_check():
    return {"status": "ok"}