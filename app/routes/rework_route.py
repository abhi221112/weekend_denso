"""
Routes for Rework Traceability Tag.

Endpoints:
  POST /api/rework/validate-tag          → VALIDATE_TAG
  POST /api/rework/print-details         → GET_PRINT_DETAILS
  POST /api/rework/last-print-details    → GET_LAST_PRINT_DETAILS
  POST /api/rework/print                 → KANBAN_PRINT (rework)
  POST /api/rework/reprint-parameter     → GET_REPRINT_PARAMETER
"""

from fastapi import APIRouter, HTTPException, Depends

from app.schemas.rework_schema import (
    ReworkValidateTagRequest,
    ReworkValidateTagResponse,
    ReworkGetPrintDetailsRequest,
    ReworkGetPrintDetailsResponse,
    ReworkGetLastPrintRequest,
    ReworkGetLastPrintResponse,
    ReworkPrintRequest,
    ReworkPrintResponse,
    ReworkReprintParamRequest,
    ReworkReprintParamResponse,
)
from app.services import rework_service
from app.utils.jwt_handler import get_current_user

router = APIRouter(
    prefix="/api/rework",
    tags=["Rework Traceability Tag"],
)


# ── 1. Validate Tag (scan barcode)  ───────────────────────────────
@router.post("/validate-tag", response_model=ReworkValidateTagResponse)
def validate_tag(body: ReworkValidateTagRequest, user: dict = Depends(get_current_user)):
    """
    **Validate / scan a barcode for rework.**

    SP call: `PRC_Print_Rework_Kanban @TYPE = 'VALIDATE_TAG'`

    Checks if the barcode exists in `TT_Kanban_Print` and returns
    all tag details (part info, lot numbers, weight, etc.) to
    auto-fill the rework form.
    """
    result = rework_service.validate_tag(
        barcode=body.barcode,
        supplier_code=body.supplier_code,
    )
    if not result.success:
        raise HTTPException(status_code=404, detail=result.message)
    return result


# ── 2. Get Print Details  ─────────────────────────────────────────
@router.post("/print-details", response_model=ReworkGetPrintDetailsResponse)
def get_print_details(body: ReworkGetPrintDetailsRequest, user: dict = Depends(get_current_user)):
    """
    **Get last 3 rework print records for a supplier part + lot.**

    SP call: `PRC_Print_Rework_Kanban @TYPE = 'GET_PRINT_DETAILS'`
    """
    result = rework_service.get_print_details(
        supplier_part_no=body.supplier_part_no,
        lot_no_1=body.lot_no_1,
        supplier_code=body.supplier_code,
    )
    if not result.success:
        raise HTTPException(status_code=404, detail=result.message)
    return result


# ── 3. Get Last Print Details  ────────────────────────────────────
@router.post("/last-print-details", response_model=ReworkGetLastPrintResponse)
def get_last_print_details(body: ReworkGetLastPrintRequest, user: dict = Depends(get_current_user)):
    """
    **Get last running serial number and tag counts.**

    SP call: `PRC_Print_Rework_Kanban @TYPE = 'GET_LAST_PRINT_DETAILS'`
    """
    result = rework_service.get_last_print_details(
        supplier_part_no=body.supplier_part_no,
    )
    if not result.success:
        raise HTTPException(status_code=404, detail=result.message)
    return result


# ── 4. Rework Print  ─────────────────────────────────────────────
@router.post("/print", response_model=ReworkPrintResponse)
def rework_print(body: ReworkPrintRequest, user: dict = Depends(get_current_user)):
    """
    **Print a rework traceability tag.**

    SP call: `PRC_Print_Rework_Kanban @TYPE = 'KANBAN_PRINT'`

    The SP:
      1. Generates a new running serial number & barcode.
      2. Archives the old tag to `TT_Kanban_Print_Rework_His`.
      3. Inserts a new rework tag into `TT_Kanban_Print` (PrintType='Rework').
      4. Discards (deletes) the old barcode.
      5. Returns the new barcode, serial, tag counts, etc.
    """
    result = rework_service.rework_print(
        barcode=body.barcode,
        company_code=body.company_code,
        plant_code=body.plant_code,
        station_no=body.station_no,
        supplier_code=body.supplier_code,
        customer_code=body.customer_code,
        supplier_part_no=body.supplier_part_no,
        part_no=body.part_no,
        lot_no_1=body.lot_no_1,
        lot_no_2=body.lot_no_2,
        tag_type=body.tag_type,
        weight=body.weight,
        qty=body.qty,
        is_mixed_lot=body.is_mixed_lot,
        running_sn_no=body.running_sn_no,
        rm_material=body.rm_material,
        printed_by=body.printed_by,
        gross_weight=body.gross_weight,
    )
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return result


# ── 5. Get Reprint Parameter  ────────────────────────────────────
@router.post("/reprint-parameter", response_model=ReworkReprintParamResponse)
def get_reprint_parameter(body: ReworkReprintParamRequest, user: dict = Depends(get_current_user)):
    """
    **Get lot structure parameters for reprint.**

    SP call: `PRC_Print_Rework_Kanban @TYPE = 'GET_REPRINT_PARAMETER'`
    """
    result = rework_service.get_reprint_parameter(
        supplier_part_no=body.supplier_part_no,
    )
    if not result.success:
        raise HTTPException(status_code=404, detail=result.message)
    return result
