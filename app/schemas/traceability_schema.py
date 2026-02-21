from pydantic import BaseModel
from typing import Optional


# ── Request Schemas ───────────────────────────────────────────────

class LoginRequest(BaseModel):
    """Request body for VALIDATEUSER_PC  (initial app login)."""
    user_id: str
    password: str


class TraceabilityUserRequest(BaseModel):
    """Request body for VALIDATEUSER  (get plant/line auto-fill)."""
    user_id: str
    password: str


class SupervisorLoginRequest(BaseModel):
    """Request body for VALIDATE_DEVICE_SUPERVISOR  (model-change supervisor auth)."""
    user_id: str
    password: str


# ── Response Schemas ──────────────────────────────────────────────

class LoginUserData(BaseModel):
    user_id: str
    user_name: str
    password: str
    email_id: Optional[str] = None
    group_id: Optional[int] = None
    group_name: Optional[str] = None
    is_supplier: Optional[str] = None
    supplier_code: Optional[str] = None
    denso_plant: Optional[str] = None
    supplier_plant_code: Optional[str] = None
    packing_station: Optional[str] = None
    plant_name: Optional[str] = None


class LoginResponse(BaseModel):
    success: bool
    message: str
    data: Optional[LoginUserData] = None


class TraceabilityUserData(BaseModel):
    supplier_code: Optional[str] = None
    supplier_plant_code: Optional[str] = None
    packing_station: Optional[str] = None
    user_id: str
    user_name: str
    plant_name: Optional[str] = None
    email_id: Optional[str] = None
    group_id: Optional[int] = None
    group_name: Optional[str] = None
    created_by: Optional[str] = None
    created_on: Optional[str] = None


class TraceabilityUserResponse(BaseModel):
    success: bool
    message: str
    data: Optional[TraceabilityUserData] = None


class SupervisorData(BaseModel):
    supplier_code: Optional[str] = None
    supplier_plant_code: Optional[str] = None
    packing_station: Optional[str] = None
    user_id: str
    user_name: str
    plant_name: Optional[str] = None
    email_id: Optional[str] = None
    group_id: Optional[int] = None
    group_name: Optional[str] = None
    created_by: Optional[str] = None
    created_on: Optional[str] = None


class SupervisorLoginResponse(BaseModel):
    success: bool
    message: str
    data: Optional[SupervisorData] = None


# ── Model List & Selection ────────────────────────────────────────

class GetModelListRequest(BaseModel):
    """
    Request to get available models (supplier part numbers) after
    supervisor login.  The dropdown in the 'Model Change' dialog.
    SP call: PRC_PrintKanban @Type = 'GET_SUPPLIERPART'
    """
    station_no: str
    plant_code: str
    printed_by: str          # logged-in user ID (UserID)


class ModelData(BaseModel):
    supplier_part: Optional[str] = None
    supplier_part_name: Optional[str] = None
    part_no: Optional[str] = None
    part_name: Optional[str] = None
    lot_size: Optional[int] = None
    supplier_part_lot_size: Optional[str] = None
    supplier_part_weight: Optional[float] = None
    bin_qty: Optional[int] = None
    shift: Optional[str] = None
    supplier_part_image: Optional[str] = None
    print_cycle_time: Optional[int] = None
    total_no_of_digits: Optional[int] = None
    no_of_steps: Optional[int] = None
    step_1_digits: Optional[int] = None
    step_2_digits: Optional[int] = None
    step_3_digits: Optional[int] = None
    step_4_digits: Optional[int] = None
    step_5_digits: Optional[int] = None
    step_6_digits: Optional[int] = None
    supplier_code: Optional[str] = None
    result: Optional[str] = None
    tolerance_weight: Optional[float] = None
    weighing_scale: Optional[str] = None
    image_name: Optional[str] = None
    bin_weight: Optional[float] = None
    bin_tolerance_weight: Optional[float] = None
    step_1_scan_type: Optional[str] = "Enter"
    step_2_scan_type: Optional[str] = "Enter"
    step_3_scan_type: Optional[str] = "Enter"
    step_4_scan_type: Optional[str] = "Enter"
    step_5_scan_type: Optional[str] = "Enter"
    step_6_scan_type: Optional[str] = "Enter"
    delimiter_type: Optional[str] = "Enter"
    character_length_from: Optional[int] = 0
    character_length_to: Optional[int] = 0
    lot_lock_type: Optional[str] = "Enable"


class SupplierPartItem(BaseModel):
    """One item in the Model Change dropdown."""
    supplier_part: str
    supplier_name: Optional[str] = None


class GetModelListResponse(BaseModel):
    success: bool
    message: str
    data: Optional[list[SupplierPartItem]] = None


class ConfirmModelSelectionRequest(BaseModel):
    """Request to confirm model selection and auto-fill fields."""
    supplier_part_no: str
    supplier_code: str
    plant_code: str
    station_no: str


class ConfirmModelSelectionResponse(BaseModel):
    success: bool
    message: str
    data: Optional[ModelData] = None


# ── Lock/Unlock Fields ────────────────────────────────────────────

class LockFieldsRequest(BaseModel):
    """Request to lock fields (make them read-only)."""
    supplier_code: str
    plant_code: str
    station_no: str


class LockFieldsResponse(BaseModel):
    success: bool
    message: str
    locked: bool
    data: Optional[dict] = None


class UnlockFieldsRequest(BaseModel):
    """Request to unlock fields (requires supervisor login)."""
    user_id: str
    password: str
    supplier_code: str
    plant_code: str
    station_no: str


class UnlockFieldsResponse(BaseModel):
    success: bool
    message: str
    unlocked: bool
    supervisor_verified: bool
    data: Optional[SupervisorData] = None
