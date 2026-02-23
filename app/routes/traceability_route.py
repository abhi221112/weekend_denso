"""
Routes for the Traceability Tag Print workflow.

Flow (matches the desktop app screenshots):
  1. POST /login                    → VALIDATEUSER_PC   (app login)
  2. POST /traceability-user        → VALIDATEUSER      (auto-fill Plant, Line, Shift)
  3. POST /supervisor-login         → VALIDATE_DEVICE_SUPERVISOR (Model Change → Supervisor Auth)
  4. POST /model-list               → GET_SUPPLIERPART  (Model Change dropdown list)
  5. POST /confirm-model            → GET_PRINT_PARAMETER (select model → auto-fill all fields)
  6. POST /lock-fields              → Lock form fields
  7. POST /unlock-fields            → Unlock form fields (supervisor auth required)

  Lot No. 1 & Lot No. 2 fields are entered manually by the user.
"""

from fastapi import APIRouter, HTTPException

from app.schemas.traceability_schema import (
    LoginRequest,
    LoginResponse,
    TraceabilityUserRequest,
    TraceabilityUserResponse,
    SupervisorLoginRequest,
    SupervisorLoginResponse,
    GetModelListRequest,
    GetModelListResponse,
    ConfirmModelSelectionRequest,
    ConfirmModelSelectionResponse,
    LockFieldsRequest,
    LockFieldsResponse,
    UnlockFieldsRequest,
    UnlockFieldsResponse,
)
from app.services import traceability_service

router = APIRouter(
    prefix="/api/traceability",
    tags=["Traceability Tag Print"],
)


# ── 1. Login  ──────────────────────────────────────────────────────
@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest):
    """
    **Step 1 – App Login**

    Authenticates an EOL User / EOL Supervisor.

    SP call: `@Type = 'VALIDATEUSER_PC'`

    Returns user profile with plant, group, supplier info.
    """
    result = traceability_service.login(body.user_id, body.password)
    if not result.success:
        raise HTTPException(status_code=401, detail=result.message)
    return result


# ── 2. Traceability Tag auto-fill  ─────────────────────────────────
@router.post("/traceability-user", response_model=TraceabilityUserResponse)
def get_traceability_user(body: TraceabilityUserRequest):
    """
    **Step 2 – Open Traceability Tag Tab**

    Returns the logged-in user's Plant, Line (PackingStation),
    SupplierCode etc. so the UI can auto-fill those fields.

    SP call: `@Type = 'VALIDATEUSER'`
    """
    result = traceability_service.get_traceability_user(body.user_id, body.password)
    if not result.success:
        raise HTTPException(status_code=403, detail=result.message)
    return result


# ── 3. Supervisor login (Model Change)  ────────────────────────────
@router.post("/supervisor-login", response_model=SupervisorLoginResponse)
def supervisor_login(body: SupervisorLoginRequest):
    """
    **Step 3 – Model Change → Supervisor Auth**

    Only a user with supervisor rights (ScreenId 3002/2003) can
    authenticate here.  After success the client fetches the model
    list and lets the supervisor pick one.

    SP call: `@Type = 'VALIDATE_DEVICE_SUPERVISOR'`
    """
    result = traceability_service.validate_supervisor(body.user_id, body.password)
    if not result.success:
        raise HTTPException(status_code=403, detail=result.message)
    return result


# ── 4. Get Model List (after supervisor login)  ────────────────
@router.post("/model-list", response_model=GetModelListResponse)
def get_model_list(body: GetModelListRequest):
    """
    **Step 4 – Get Available Models (Supplier Part Numbers)**

    After supervisor authenticates via `/supervisor-login`, the UI
    shows a **Model Change** dropdown.  This endpoint returns the
    list of supplier part numbers available for that station/plant.

    The user (logged-in `printed_by`) determines which supplier
    parts they have access to.

    SP call: `PRC_PrintKanban @Type = 'GET_SUPPLIERPART'`

    **Request:**
    ```json
    {
        "station_no": "Station-1",
        "plant_code": "PLANT01",
        "printed_by": "Mukesh"
    }
    ```
    """
    result = traceability_service.get_model_list(
        body.station_no,
        body.plant_code,
        body.printed_by,
    )
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return result


# ── 5. Confirm Model Selection (auto-fill all fields)  ────────────
@router.post("/confirm-model", response_model=ConfirmModelSelectionResponse)
def confirm_model_selection(body: ConfirmModelSelectionRequest):
    """
    **Step 5 – Select Model → Auto-Fill All Fields**

    When the user selects a Supplier Part No. from the Model Change
    dropdown, this endpoint returns ALL part details to auto-fill:

    - **Customer Part No.** (e.g. HA229876-0471)
    - **Part Name** (e.g. PLATE REAR)
    - **Supplier Part No.**
    - **Batch Size** (e.g. 72)
    - **Weight (g)** with tolerance range
    - **Shift** (e.g. B)
    - **Last Tag Serial, No. of Tag Stock In, Total Qty. Stock In**

    **Lot No. 1 and Lot No. 2 are entered manually by the user.**

    SP call: `PRC_PrintKanban @Type = 'GET_PRINT_PARAMETER'`

    **Request:**
    ```json
    {
        "supplier_part_no": "HA229876-0471",
        "supplier_code": "SUP001",
        "plant_code": "PLANT01",
        "station_no": "Station-1"
    }
    ```
    """
    result = traceability_service.confirm_model_selection(
        body.supplier_part_no,
        body.supplier_code,
        body.plant_code,
        body.station_no,
    )
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return result


# ── 6. Lock Fields (make them read-only)  ──────────────────────
@router.post("/lock-fields", response_model=LockFieldsResponse)
def lock_fields_endpoint(body: LockFieldsRequest):
    """
    **Step 6 – Lock Fields**

    When user clicks the **Lock** button, all form fields become
    read-only (greyed out). The UI shows a "visibility lock" icon.

    Requires **supplier_part_no** to look up `LotLockType` from
    `TM_Supplier_Lot_Structure`:
    - `Enable` / `STANDARD` → lock is allowed
    - `Disable` → lock is **not** allowed for this part
    """
    result = traceability_service.lock_fields(
        body.supplier_part_no,
        body.supplier_code,
        body.plant_code,
        body.station_no,
    )
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return result


# ── 7. Unlock Fields (with supervisor auth)  ──────────────────
@router.post("/unlock-fields", response_model=UnlockFieldsResponse)
def unlock_fields_endpoint(body: UnlockFieldsRequest):
    """
    **Step 7 – Unlock Fields (Supervisor Auth Required)**

    When user clicks the **Unlock** button on a locked form:
    1. A supervisor login dialog appears
    2. Only users with supervisor rights can authenticate
    3. After successful auth, fields become editable
    """
    result = traceability_service.unlock_fields(
        body.user_id,
        body.password,
        body.supplier_part_no,
        body.supplier_code,
        body.plant_code,
        body.station_no,
    )
    if not result.success:
        raise HTTPException(status_code=403, detail=result.message)
    return result

