"""
Service layer – business logic for the Traceability Tag Print flow.
Maps raw SP result dicts → typed response schemas.
"""

from app.data_access import traceability_dal
from app.utils.jwt_handler import create_access_token, create_refresh_token
from app.schemas.traceability_schema import (
    LoginResponse,
    LoginUserData,
    TraceabilityUserResponse,
    TraceabilityUserData,
    SupervisorLoginResponse,
    SupervisorData,
    GetModelListResponse,
    SupplierPartItem,
    ModelData,
    ConfirmModelSelectionResponse,
    LockFieldsResponse,
    UnlockFieldsResponse,
)


# ─────────────────────────────────────────────────────────────────
# 1.  Login  (VALIDATEUSER_PC)
# ─────────────────────────────────────────────────────────────────
def login(user_id: str, password: str) -> LoginResponse:
    row = traceability_dal.validate_user_pc(user_id, password)

    if row is None or row.get("RESULT") != "Y":
        msg = (row or {}).get("MSG", "Invalid user ID or password")
        return LoginResponse(success=False, message=msg, data=None)

    data = LoginUserData(
        user_id=row.get("UserID", ""),
        user_name=row.get("USERNAME", ""),
        password=row.get("PASSWORD", ""),
        email_id=row.get("EmailId"),
        group_id=row.get("GroupID"),
        group_name=row.get("GroupName"),
        is_supplier=row.get("IsSupplier"),
        supplier_code=row.get("SupplierCode"),
        denso_plant=row.get("DensoPlant"),
        supplier_plant_code=row.get("SupplierPlantCode"),
        packing_station=row.get("PackingStation"),
        plant_name=row.get("PlantName"),
    )

    # Generate JWT tokens
    token_data = {
        "user_id": data.user_id,
        "supplier_code": data.supplier_code or "",
        "group_name": data.group_name or "",
    }
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token({"user_id": data.user_id})

    return LoginResponse(
        success=True,
        message="Login successful",
        data=data,
        access_token=access_token,
        refresh_token=refresh_token,
    )
# ─────────────────────────────────────────────────────────────────
def get_traceability_user(user_id: str, password: str) -> TraceabilityUserResponse:
    row = traceability_dal.validate_user(user_id, password)

    if row is None or not row.get("SupplierPlantCode"):
        return TraceabilityUserResponse(
            success=False,
            message="User not authorised for traceability tag or no plant mapped",
            data=None,
        )

    data = TraceabilityUserData(
        supplier_code=row.get("SupplierCode"),
        supplier_plant_code=row.get("SupplierPlantCode"),
        packing_station=row.get("PackingStation"),
        user_id=row.get("UserID", ""),
        user_name=row.get("USERNAME", ""),
        plant_name=row.get("PASSWORD"),          # SP returns PlantName in PASSWORD column
        email_id=row.get("EmailId"),
        group_id=row.get("GroupID"),
        group_name=row.get("GroupName"),
        created_by=row.get("CreatedBy"),
        created_on=row.get("CreatedOn"),
    )
    return TraceabilityUserResponse(
        success=True, message="User details fetched", data=data
    )


# ─────────────────────────────────────────────────────────────────
# 3.  Supervisor auth for Model Change  (VALIDATE_DEVICE_SUPERVISOR)
# ─────────────────────────────────────────────────────────────────
def validate_supervisor(user_id: str, password: str) -> SupervisorLoginResponse:
    row = traceability_dal.validate_device_supervisor(user_id, password)

    if row is None or not row.get("SupplierPlantCode"):
        return SupervisorLoginResponse(
            success=False,
            message="Supervisor authentication failed or insufficient rights",
            data=None,
        )

    data = SupervisorData(
        supplier_code=row.get("SupplierCode"),
        supplier_plant_code=row.get("SupplierPlantCode"),
        packing_station=row.get("PackingStation"),
        user_id=row.get("UserID", ""),
        user_name=row.get("USERNAME", ""),
        plant_name=row.get("PlantName"),
        email_id=row.get("EmailId"),
        group_id=row.get("GroupID"),
        group_name=row.get("GroupName"),
        created_by=row.get("CreatedBy"),
        created_on=row.get("CreatedOn"),
    )

    # Generate JWT tokens for supervisor
    token_data = {
        "user_id": data.user_id,
        "supplier_code": data.supplier_code or "",
        "group_name": data.group_name or "",
        "role": "supervisor",
    }
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token({"user_id": data.user_id})

    return SupervisorLoginResponse(
        success=True,
        message="Supervisor validated",
        data=data,
        access_token=access_token,
        refresh_token=refresh_token,
    )


# ─────────────────────────────────────────────────────────────────
# 4.  Get Model List (GET_SUPPLIERPART) – Model Change dropdown
# ─────────────────────────────────────────────────────────────────
def get_model_list(
    station_no: str,
    plant_code: str,
    printed_by: str,
) -> GetModelListResponse:
    """
    After supervisor login, return list of available supplier part
    numbers for the Model Change dropdown.

    SP call: PRC_PrintKanban @Type = 'GET_SUPPLIERPART'
    """
    rows = traceability_dal.get_supplier_parts(
        station_no, plant_code, printed_by
    )

    if rows is None or len(rows) == 0:
        return GetModelListResponse(
            success=False,
            message="No models found for this station/plant",
            data=None,
        )

    parts = []
    for row in rows:
        parts.append(SupplierPartItem(
            supplier_part=row.get("SupplierPart", ""),
            supplier_name=row.get("SupplierName", row.get("SupplierPart", "")),
        ))

    return GetModelListResponse(
        success=True,
        message=f"Found {len(parts)} model(s)",
        data=parts,
    )


# ─────────────────────────────────────────────────────────────────
# 5.  Confirm Model Selection (auto-fill fields)
# ─────────────────────────────────────────────────────────────────
def confirm_model_selection(
    supplier_part_no: str,
    supplier_code: str,
    plant_code: str,
    station_no: str,
) -> ConfirmModelSelectionResponse:
    """
    After supervisor selects a model and clicks "Confirm",
    return all field values to auto-fill the form.
    
    SP call: PRC_PrintKanban @Type = 'GET_PRINT_PARAMETER'
    """
    rows = traceability_dal.get_print_parameter(
        supplier_part_no, supplier_code, plant_code, station_no
    )

    if rows is None or len(rows) == 0:
        return ConfirmModelSelectionResponse(
            success=False,
            message="Model not found",
            data=None,
        )

    # Return first row (assumed supervisor selected this one)
    row = rows[0]

    # Check for error result
    if row.get("RESULT") and row.get("RESULT") != "Y":
        return ConfirmModelSelectionResponse(
            success=False,
            message=row.get("RESULT", "Error fetching model details"),
            data=None,
        )

    # Helper: safely convert DB Decimal/numeric to the expected Python type
    def _str(val):
        return str(val) if val is not None else None

    def _int(val):
        try:
            return int(val) if val is not None else None
        except (ValueError, TypeError):
            return None

    def _float(val):
        try:
            return float(val) if val is not None else None
        except (ValueError, TypeError):
            return None

    model = ModelData(
        supplier_part=row.get("SupplierPart"),
        supplier_part_name=row.get("SupplierPartName"),
        part_no=row.get("PartNo"),
        part_name=row.get("PartName"),
        lot_size=_int(row.get("LotSize")),
        supplier_part_lot_size=_str(row.get("SupplierPartLotSize")),
        supplier_part_weight=_float(row.get("SupplierPartWeight")),
        bin_qty=_int(row.get("BinQty")),
        shift=row.get("Shift"),
        supplier_part_image=row.get("SupplierPartImage"),
        print_cycle_time=_int(row.get("PrintCycleTime")),
        total_no_of_digits=_int(row.get("TotalNoOfDigits")),
        no_of_steps=_int(row.get("NoOfSteps")),
        step_1_digits=_int(row.get("Step_1_Digits")),
        step_2_digits=_int(row.get("Step_2_Digits")),
        step_3_digits=_int(row.get("Step_3_Digits")),
        step_4_digits=_int(row.get("Step_4_Digits")),
        step_5_digits=_int(row.get("Step_5_Digits")),
        step_6_digits=_int(row.get("Step_6_Digits")),
        supplier_code=row.get("SupplierCode"),
        result=row.get("RESULT"),
        tolerance_weight=_float(row.get("ToleranceWeight")),
        weighing_scale=row.get("WeighingScale"),
        image_name=row.get("ImageName"),
        bin_weight=_float(row.get("BinWeight")),
        bin_tolerance_weight=_float(row.get("BinToleranceWeight")),
        step_1_scan_type=row.get("Step_1_ScanType", "Enter"),
        step_2_scan_type=row.get("Step_2_ScanType", "Enter"),
        step_3_scan_type=row.get("Step_3_ScanType", "Enter"),
        step_4_scan_type=row.get("Step_4_ScanType", "Enter"),
        step_5_scan_type=row.get("Step_5_ScanType", "Enter"),
        step_6_scan_type=row.get("Step_6_ScanType", "Enter"),
        delimiter_type=row.get("DelimiterType", "Enter"),
        character_length_from=_int(row.get("CharacterLengthFrom")) or 0,
        character_length_to=_int(row.get("CharacterLengthTo")) or 0,
        lot_lock_type=row.get("LotLockType", "Enable"),
    )

    return ConfirmModelSelectionResponse(
        success=True,
        message="Model details loaded successfully",
        data=model,
    )


# ─────────────────────────────────────────────────────────────────
# 6.  Lock Fields (make them read-only)
# ─────────────────────────────────────────────────────────────────
def lock_fields(
    supplier_part_no: str,
    supplier_code: str,
    plant_code: str,
    station_no: str,
) -> LockFieldsResponse:
    """
    Lock the form fields to make them read-only.
    Called when user clicks the Lock button.
    Checks LotLockType from TM_Supplier_Lot_Structure:
      - 'Disable' → locking not allowed for this part
      - 'Enable' / 'STANDARD' → lock is allowed
    """
    success, lot_lock_type = traceability_dal.lock_fields(
        supplier_part_no, supplier_code, plant_code, station_no
    )

    if lot_lock_type is None:
        return LockFieldsResponse(
            success=False,
            message=f"Supplier part '{supplier_part_no}' not found in Lot Structure",
            locked=False,
            lot_lock_type=None,
            data=None,
        )

    if lot_lock_type == "Disable":
        return LockFieldsResponse(
            success=False,
            message=f"Locking is disabled for supplier part '{supplier_part_no}' (LotLockType=Disable)",
            locked=False,
            lot_lock_type=lot_lock_type,
            data={"supplier_part_no": supplier_part_no, "supplier_code": supplier_code,
                  "plant_code": plant_code, "station_no": station_no},
        )

    return LockFieldsResponse(
        success=success,
        message="Fields locked successfully" if success else "Failed to lock fields",
        locked=success,
        lot_lock_type=lot_lock_type,
        data={"supplier_part_no": supplier_part_no, "supplier_code": supplier_code,
              "plant_code": plant_code, "station_no": station_no},
    )


# ─────────────────────────────────────────────────────────────────
# 7.  Unlock Fields (requires supervisor auth)
# ─────────────────────────────────────────────────────────────────
def unlock_fields(
    user_id: str,
    password: str,
    supplier_part_no: str,
    supplier_code: str,
    plant_code: str,
    station_no: str,
) -> UnlockFieldsResponse:
    """
    Unlock the form fields to make them editable.
    Requires supervisor authentication first.
    Called when user clicks the Unlock button and completes supervisor login.
    """
    # First validate supervisor credentials
    supervisor_row = traceability_dal.validate_device_supervisor(user_id, password)

    if supervisor_row is None or not supervisor_row.get("SupplierPlantCode"):
        return UnlockFieldsResponse(
            success=False,
            message="Supervisor authentication failed",
            unlocked=False,
            supervisor_verified=False,
            data=None,
        )

    # Supervisor authenticated, now unlock fields
    unlock_success = traceability_dal.unlock_fields(
        supplier_part_no, supplier_code, plant_code, station_no
    )

    supervisor_data = SupervisorData(
        supplier_code=supervisor_row.get("SupplierCode"),
        supplier_plant_code=supervisor_row.get("SupplierPlantCode"),
        packing_station=supervisor_row.get("PackingStation"),
        user_id=supervisor_row.get("UserID", ""),
        user_name=supervisor_row.get("USERNAME", ""),
        plant_name=supervisor_row.get("PlantName"),
        email_id=supervisor_row.get("EmailId"),
        group_id=supervisor_row.get("GroupID"),
        group_name=supervisor_row.get("GroupName"),
        created_by=supervisor_row.get("CreatedBy"),
        created_on=supervisor_row.get("CreatedOn"),
    )

    return UnlockFieldsResponse(
        success=unlock_success,
        message="Fields unlocked successfully" if unlock_success else "Failed to unlock fields",
        unlocked=unlock_success,
        supervisor_verified=True,
        data=supervisor_data,
    )
