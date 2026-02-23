"""
Pydantic schemas for the Rework Traceability Tag endpoints.

SP: PRC_Print_Rework_Kanban
  @TYPE = 'VALIDATE_TAG'          → Validate barcode & return tag details
  @TYPE = 'GET_PRINT_DETAILS'     → Last 3 rework prints for a part+lot
  @TYPE = 'GET_LAST_PRINT_DETAILS'→ Last serial no & tag counts
  @TYPE = 'KANBAN_PRINT'          → Print rework tag (new barcode, discard old)
  @TYPE = 'GET_REPRINT_PARAMETER' → Lot structure parameters

Rework KANBAN_PRINT Result column (tilde-delimited):
  Y~Barcode~PrintTime~SerialNo~CountTags~TotalTags~TagType~PrintDate
"""

from pydantic import BaseModel
from typing import Optional, List


# ── VALIDATE_TAG  ─────────────────────────────────────────────────

class ReworkValidateTagRequest(BaseModel):
    """Scan / validate an existing barcode for rework."""
    barcode: str
    supplier_code: Optional[str] = None


class ReworkValidateTagData(BaseModel):
    """Fields returned after validating a barcode for rework."""
    supplier_code: Optional[str] = None
    supplier_name: Optional[str] = None
    supplier_part_no: Optional[str] = None
    supplier_part_name: Optional[str] = None
    part_no: Optional[str] = None
    part_description: Optional[str] = None
    lot_no_1: Optional[str] = None
    lot_no_2: Optional[str] = None
    tag_type: Optional[str] = None
    weight: Optional[float] = None
    running_sn_no: Optional[str] = None
    barcode: Optional[str] = None
    pack_size: Optional[int] = None
    qty: Optional[int] = None
    shift: Optional[str] = None
    traceability: Optional[str] = None
    tag_type_label: Optional[str] = None
    company_name: Optional[str] = None
    print_date: Optional[str] = None
    supplier_part_image: Optional[str] = None
    tolerance_weight: Optional[float] = None
    weighing_scale: Optional[str] = None
    image_name: Optional[str] = None
    bin_weight: Optional[float] = None
    bin_tolerance_weight: Optional[float] = None


class ReworkValidateTagResponse(BaseModel):
    """Response after validating a barcode for rework."""
    success: bool
    message: str
    data: Optional[ReworkValidateTagData] = None


# ── GET_PRINT_DETAILS  ───────────────────────────────────────────

class ReworkGetPrintDetailsRequest(BaseModel):
    """Get last 3 rework prints for a part + lot."""
    supplier_part_no: str
    lot_no_1: str
    supplier_code: Optional[str] = None


class ReworkPrintDetailItem(BaseModel):
    """Single row from GET_PRINT_DETAILS."""
    plant_code: Optional[str] = None
    station_no: Optional[str] = None
    shift: Optional[str] = None
    lot_no_1: Optional[str] = None
    lot_no_2: Optional[str] = None
    running_sn_no: Optional[str] = None
    printed_by: Optional[str] = None
    printed_on: Optional[str] = None
    print_date: Optional[str] = None
    traceability: Optional[str] = None
    tag_type: Optional[str] = None
    supplier_name: Optional[str] = None
    barcode: Optional[str] = None
    company_name: Optional[str] = None
    supplier_part_no: Optional[str] = None
    part_no: Optional[str] = None
    weight: Optional[float] = None
    pack_size: Optional[int] = None
    weighing_scale: Optional[str] = None
    gross_weight: Optional[float] = None


class ReworkGetPrintDetailsResponse(BaseModel):
    """Response with last 3 rework print details."""
    success: bool
    message: str
    data: Optional[List[ReworkPrintDetailItem]] = None


# ── GET_LAST_PRINT_DETAILS  ──────────────────────────────────────

class ReworkGetLastPrintRequest(BaseModel):
    """Get last serial + tag counts for a supplier part."""
    supplier_part_no: str


class ReworkLastPrintData(BaseModel):
    """Last running serial + tag counts."""
    running_sn_no: Optional[str] = None
    count_no_of_tags: Optional[int] = None
    total_no_of_tags: Optional[int] = None


class ReworkGetLastPrintResponse(BaseModel):
    """Response with last print info."""
    success: bool
    message: str
    data: Optional[ReworkLastPrintData] = None


# ── KANBAN_PRINT (Rework)  ───────────────────────────────────────

class ReworkPrintRequest(BaseModel):
    """
    Request body for rework KANBAN_PRINT.
    The old barcode is required – a new barcode is generated
    and the old tag is archived to TT_Kanban_Print_Rework_His.
    """
    barcode: str                              # old barcode to rework
    plant_code: str
    station_no: str
    supplier_code: str
    supplier_part_no: str
    part_no: str
    lot_no_1: str
    weight: float
    qty: int
    printed_by: str
    company_code: Optional[str] = None
    customer_code: Optional[str] = None
    lot_no_2: Optional[str] = ""
    tag_type: Optional[str] = None
    is_mixed_lot: Optional[bool] = False
    running_sn_no: Optional[str] = None
    rm_material: Optional[str] = None
    gross_weight: Optional[str] = None


class ReworkPrintResultData(BaseModel):
    """Parsed tilde-delimited Result from rework KANBAN_PRINT SP.
    Format: Y~Barcode~PrintTime~SerialNo~CountTags~TotalTags~TagType~PrintDate
    """
    barcode: Optional[str] = None
    print_time: Optional[str] = None
    serial_no: Optional[str] = None
    no_of_tags_stock_in: Optional[int] = None
    total_qty_stock_in: Optional[int] = None
    tag_type: Optional[str] = None
    print_date: Optional[str] = None


class ReworkPrintResponse(BaseModel):
    """Response after rework print."""
    success: bool
    message: str
    data: Optional[ReworkPrintResultData] = None


# ── GET_REPRINT_PARAMETER  ───────────────────────────────────────

class ReworkReprintParamRequest(BaseModel):
    """Get lot structure parameters for a supplier part."""
    supplier_part_no: str


class ReworkReprintParamData(BaseModel):
    """Lot structure info for reprint parameter."""
    total_no_of_digits: Optional[int] = None
    no_of_steps: Optional[int] = None
    step_1_digits: Optional[int] = None
    step_2_digits: Optional[int] = None
    step_3_digits: Optional[int] = None
    step_4_digits: Optional[int] = None
    step_5_digits: Optional[int] = None
    step_6_digits: Optional[int] = None
    supplier_code: Optional[str] = None
    tolerance_weight: Optional[float] = None
    weighing_scale: Optional[str] = None
    bin_weight: Optional[float] = None
    bin_tolerance_weight: Optional[float] = None


class ReworkReprintParamResponse(BaseModel):
    """Response with reprint parameters."""
    success: bool
    message: str
    data: Optional[ReworkReprintParamData] = None
