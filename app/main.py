"""
Traceability Tag Print – FastAPI application
=============================================
Only the APIs required for the tag-print workflow:
  1. POST /api/traceability/login                 → VALIDATEUSER_PC
  2. POST /api/traceability/traceability-user      → VALIDATEUSER
  3. POST /api/traceability/supervisor-login        → VALIDATE_DEVICE_SUPERVISOR
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.traceability_route import router as traceability_router
from app.routes.register import router as register_router

app = FastAPI(
    title="Traceability Tag Print API",
    description="APIs for the Traceability Tag Print flow (Denso D-Trace)",
    version="1.0.0",
)

# Allow CORS for frontend / desktop app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(traceability_router)
app.include_router(register_router)


@app.get("/", tags=["Health"])
def health_check():
    return {"status": "running", "app": "Traceability Tag Print API"}
