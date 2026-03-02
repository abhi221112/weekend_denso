"""
Pydantic schemas for the Print / Re-Print / Get-Image endpoints.

SP: PRC_PrintKanban
  @TYPE = 'KANBAN_PRINT'      → Print a new traceability tag
  @TYPE = 'KANBAN_RE_PRINT'   → Re-print (requires supervisor auth + old barcode)
  @TYPE = 'GET_PRINT_IMAGE'   → Return binary supplier-part image

The SP Result column for Print / Re-Print is a tilde-delimited string:
  Y~SupplierName~Traceability Tag~SerialNo~CompanyName~TagType~PrintDate
   ~BarcodeLot1~BarcodeLot2~SerialNo2~PrintTime~CountTags~TotalTags
"""

from pydantic import BaseModel
from typing import Optional, List


# ── Print Request ─────────────────────────────────────────────────

class KanbanPrintRequest(BaseModel):
    """
    Request body for KANBAN_PRINT.
    Maps to the C# controller's header parameters → SP params.
    """
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
    old_barcode: Optional[str] = None
    gross_weight: Optional[str] = None


# ── Re-Print Request ─────────────────────────────────────────────

class KanbanRePrintRequest(BaseModel):
    """
    Request body for KANBAN_RE_PRINT.
    Includes supervisor credentials + the old barcode to replace.
    """
    # Supervisor auth (required before re-print)
    supervisor_user_id: str
    supervisor_password: str

    # Print parameters
    plant_code: str
    station_no: str
    supplier_code: str
    supplier_part_no: str
    part_no: str
    lot_no_1: str
    weight: float
    qty: int
    printed_by: str
    old_barcode: str                      # ← required for re-print
    company_code: Optional[str] = None
    customer_code: Optional[str] = None
    lot_no_2: Optional[str] = ""
    tag_type: Optional[str] = None
    is_mixed_lot: Optional[bool] = False
    running_sn_no: Optional[str] = None
    rm_material: Optional[str] = None
    gross_weight: Optional[str] = None


# ── Print / Re-Print Response ────────────────────────────────────

class PrintResultData(BaseModel):
    """Parsed tilde-delimited Result column from the SP."""
    supplier_name: Optional[str] = None
    traceability: Optional[str] = None
    serial_no: Optional[str] = None
    company_name: Optional[str] = None
    tag_type: Optional[str] = None
    print_date: Optional[str] = None
    barcode_lot1: Optional[str] = None
    barcode_lot2: Optional[str] = None
    serial_no_2: Optional[str] = None
    print_time: Optional[str] = None
    no_of_tags_stock_in: Optional[int] = None
    total_qty_stock_in: Optional[int] = None


class KanbanPrintResponse(BaseModel):
    success: bool
    message: str
    data: Optional[PrintResultData] = None


# ── Get Image Request / Response ─────────────────────────────────

class GetImageRequest(BaseModel):
    """Query parameter model – supplier_part is passed as path param."""
    pass  # supplier_part comes from path


class GetImageResponse(BaseModel):
    """Only used for error responses; success returns raw bytes."""
    success: bool
    message: str


# ── Scan Barcode Request / Response ──────────────────────────────

class ScanBarcodeRequest(BaseModel):
    """Request body for barcode scan – only barcode is needed."""
    barcode: str


class ScanBarcodeData(BaseModel):
    """All fields returned after a successful barcode scan to auto-fill the form."""
    # Part identification
    part_no: Optional[str] = None
    part_name: Optional[str] = None
    supplier_part_no: Optional[str] = None
    supplier_name: Optional[str] = None
    supplier_code: Optional[str] = None

    # Supplier Part Details
    batch_size: Optional[int] = None
    weight: Optional[float] = None
    is_mixed_lot: Optional[bool] = False

    # Lot numbers
    lot_no_1: Optional[str] = None
    lot_no_2: Optional[str] = None
    quantity: Optional[int] = None

    # Tag / Serial info
    last_tag_serial_no: Optional[str] = None
    no_of_tags_printed: Optional[int] = None
    total_qty_stock_in: Optional[int] = None

    # Barcode strings
    barcode_lot1: Optional[str] = None
    barcode_lot2: Optional[str] = None

    # Additional metadata
    tag_type: Optional[str] = None
    shift: Optional[str] = None
    print_date: Optional[str] = None
    print_time: Optional[str] = None
    station_no: Optional[str] = None
    plant_code: Optional[str] = None
    tolerance_weight: Optional[float] = None
    gross_weight: Optional[str] = None
    rm_material: Optional[str] = None


class ScanBarcodeResponse(BaseModel):
    """Response after scanning a barcode."""
    success: bool
    message: str
    data: Optional[ScanBarcodeData] = None


# ── Change Lot Number Request / Response ─────────────────────────

class ChangeLotNoRequest(BaseModel):
    """
    Request body for changing the lot number on a printed kanban tag.
    The barcode identifies the tag, and new_lot_no replaces the current lot.
    """
    barcode: str
    new_lot_no: str
    supplier_code: str
    supplier_part_no: str
    part_no: str
    modified_by: Optional[str] = None


class ChangeLotNoResponse(BaseModel):
    """Response after changing the lot number."""
    success: bool
    message: str
    barcode: Optional[str] = None
    old_lot_no: Optional[str] = None
    new_lot_no: Optional[str] = None


# ── Get Print Details Request / Response ──────────────────────────

class GetPrintDetailsRequest(BaseModel):
    """
    Request body for GET_PRINT_DETAILS.
    Returns the top 3 recent prints for a specific supplier/printer/station.
    """
    supplier_code: str
    printed_by: str
    station_no: str
    plant_code: str


class PrintDetailItem(BaseModel):
    """Single row returned by GET_PRINT_DETAILS."""
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


class GetPrintDetailsResponse(BaseModel):
    """Response for GET_PRINT_DETAILS – returns up to 3 recent prints."""
    success: bool
    message: str
    data: Optional[List[PrintDetailItem]] = None


# ── Get All Print Details Request / Response ─────────────────────

class GetAllPrintDetailsRequest(BaseModel):
    """
    Request body for GET_ALL_PRINT_DETAILS.
    Returns all undispatched prints for a station/plant.
    """
    printed_by: str
    station_no: str
    plant_code: str


class AllPrintDetailItem(BaseModel):
    """Single row returned by GET_ALL_PRINT_DETAILS."""
    plant_code: Optional[str] = None
    station_no: Optional[str] = None
    shift: Optional[str] = None
    lot_no_1: Optional[str] = None
    lot_no_2: Optional[str] = None
    printed_by: Optional[str] = None
    print_date: Optional[str] = None
    traceability: Optional[str] = None
    tag_type: Optional[str] = None
    supplier_name: Optional[str] = None
    barcode: Optional[str] = None
    company_name: Optional[str] = None
    supplier_part_no: Optional[str] = None
    part_no: Optional[str] = None
    weight: Optional[int] = None
    pack_size: Optional[int] = None
    part_name: Optional[str] = None
    running_sn_no: Optional[str] = None
    supplier_code: Optional[str] = None
    gross_weight: Optional[float] = None
    weighing_scale: Optional[str] = None
    lot_type: Optional[str] = None
    bin_barcode: Optional[str] = None
    bin_qty: Optional[int] = None


class GetAllPrintDetailsResponse(BaseModel):
    """Response for GET_ALL_PRINT_DETAILS – all undispatched prints."""
    success: bool
    message: str
    data: Optional[List[AllPrintDetailItem]] = None


# ── Get Last Print Details Request / Response ─────────────────────

class GetLastPrintDetailsRequest(BaseModel):
    """Request body for GET_LAST_PRINT_DETAILS – summary of last print run."""
    supplier_code: str


class LastPrintDetailsData(BaseModel):
    """Data returned by GET_LAST_PRINT_DETAILS."""
    running_sn_no: Optional[str] = None
    count_no_of_tags: Optional[int] = None
    total_no_of_tags: Optional[int] = None


class GetLastPrintDetailsResponse(BaseModel):
    """Response for GET_LAST_PRINT_DETAILS."""
    success: bool
    message: str
    data: Optional[LastPrintDetailsData] = None


# ── Print PRN Request / Response ─────────────────────────────────

class PrintPrnRequest(BaseModel):
    """
    Request body for PRINT_PRN – logs a print/reprint event.
    SP maps: PRN=@CustomerCode, IP=@PlantCode, Port=@StationNo, SupplierCode=@SupplierCode.
    """
    prn: str               # PRN identifier (maps to @CustomerCode)
    ip: str                # IP address (maps to @PlantCode)
    port: str              # Port (maps to @StationNo)
    supplier_code: str     # Supplier code


class PrintPrnResponse(BaseModel):
    """Response for PRINT_PRN."""
    success: bool
    message: str


# ── Kanban Rework Re-Print Request / Response ────────────────────

class KanbanReworkRePrintRequest(BaseModel):
    """
    Request body for KANBAN_REWORK_RE_PRINT.
    Rework reprint with new tag – requires supervisor auth + old barcode.
    Same params as KANBAN_RE_PRINT but creates a 'Rework' PrintType with 'RWK' TagType.
    """
    # Supervisor auth (required before rework re-print)
    supervisor_user_id: str
    supervisor_password: str

    # Print parameters
    plant_code: str
    station_no: str
    supplier_code: str
    supplier_part_no: str
    part_no: str
    lot_no_1: str
    weight: float
    qty: int
    printed_by: str
    old_barcode: str                      # ← required for rework re-print
    company_code: Optional[str] = None
    customer_code: Optional[str] = None
    lot_no_2: Optional[str] = ""
    tag_type: Optional[str] = None
    is_mixed_lot: Optional[bool] = False
    running_sn_no: Optional[str] = None
    rm_material: Optional[str] = None
    gross_weight: Optional[str] = None


# ── Get All Rework Print Details Request / Response ──────────────

class GetAllReworkPrintDetailsRequest(BaseModel):
    """
    Request body for GET_ALL_REWORK_PRINT_DETAILS.
    Returns all undispatched rework prints for a station/plant.
    """
    printed_by: str
    station_no: str
    plant_code: str


class ReworkPrintDetailItem(BaseModel):
    """Single row returned by GET_ALL_REWORK_PRINT_DETAILS."""
    plant_code: Optional[str] = None
    station_no: Optional[str] = None
    shift: Optional[str] = None
    lot_no_1: Optional[str] = None
    lot_no_2: Optional[str] = None
    printed_by: Optional[str] = None
    print_date: Optional[str] = None
    traceability: Optional[str] = None
    tag_type: Optional[str] = None
    supplier_name: Optional[str] = None
    barcode: Optional[str] = None
    company_name: Optional[str] = None
    supplier_part_no: Optional[str] = None
    part_no: Optional[str] = None
    weight: Optional[int] = None
    pack_size: Optional[int] = None
    part_name: Optional[str] = None
    running_sn_no: Optional[str] = None
    supplier_code: Optional[str] = None
    gross_weight: Optional[float] = None
    weighing_scale: Optional[str] = None


class GetAllReworkPrintDetailsResponse(BaseModel):
    """Response for GET_ALL_REWORK_PRINT_DETAILS – all undispatched rework prints."""
    success: bool
    message: str
    data: Optional[List[ReworkPrintDetailItem]] = None


# ── Validate User Admin Request / Response ───────────────────────

class ValidateUserAdminRequest(BaseModel):
    """
    Request body for VALIDATEUSER_ADMIN – supervisor login for unlock/reprint.
    """
    user_id: str
    password: str


class ValidateUserAdminData(BaseModel):
    """User data returned on successful VALIDATEUSER_ADMIN."""
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    email_id: Optional[str] = None
    group_id: Optional[int] = None
    group_name: Optional[str] = None
    is_supplier: Optional[str] = None
    supplier_code: Optional[str] = None
    denso_plant: Optional[str] = None
    supplier_plant_code: Optional[str] = None
    packing_station: Optional[str] = None


class ValidateUserAdminResponse(BaseModel):
    """Response for VALIDATEUSER_ADMIN."""
    success: bool
    message: str
    data: Optional[ValidateUserAdminData] = None


# ── Get Shift Request / Response ───────────────────────────────

class GetShiftRequest(BaseModel):
    """Request body for GET_SHIFT – current shift for a supplier."""
    supplier_code: str


class ShiftData(BaseModel):
    """Shift information returned by GET_SHIFT."""
    shift: Optional[str] = None
    shift_from: Optional[str] = None
    shift_to: Optional[str] = None


class GetShiftResponse(BaseModel):
    """Response for GET_SHIFT."""
    success: bool
    message: str
    data: Optional[ShiftData] = None
