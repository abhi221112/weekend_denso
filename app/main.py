"""
Traceability Tag Print – FastAPI application
=============================================
Only the APIs required for the tag-print workflow:
  1. POST /api/traceability/login                 → VALIDATEUSER_PC
  2. POST /api/traceability/traceability-user      → VALIDATEUSER
  3. POST /api/traceability/supervisor-login        → VALIDATE_DEVICE_SUPERVISOR
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.routes.traceability_route import router as traceability_router
from app.routes.register import router as register_router
from app.routes.print_route import router as print_router
from app.routes.rework_route import router as rework_router
from app.utils.logger import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="Traceability Tag  API",
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
app.include_router(print_router)
app.include_router(rework_router)


@app.on_event("startup")
def startup_event():
    logger.info("Traceability Tag Print API started")


@app.on_event("shutdown")
def shutdown_event():
    logger.info("Traceability Tag Print API shutting down")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info("Request: %s %s", request.method, request.url.path)
    response = await call_next(request)
    logger.info("Response: %s %s → %s", request.method, request.url.path, response.status_code)
    return response


@app.get("/", tags=["Health"])
def health_check():
    logger.info("Health check called")
    return {"status": "running", "app": "Traceability Tag Print API"}




