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
    """
    Request body for barcode scan.
    The scanned barcode string is used to look up all part details
    and auto-fill the Supplier Part Details form.
    """
    barcode: str
    supplier_code: Optional[str] = None
    plant_code: Optional[str] = None
    station_no: Optional[str] = None
    supplier_part_no: Optional[str] = None


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
