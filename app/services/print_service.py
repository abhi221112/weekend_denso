"""
Service layer – business logic for Print / Re-Print / Get-Image.

Print result parsing
--------------------
The SP KANBAN_PRINT and KANBAN_RE_PRINT return two columns:
  Result:  'Y~SupplierName~Traceability Tag~0000001~COMP01~NEW~22/02/2026 15:00
            ~BARCODE_LOT1~BARCODE_LOT2~SERIAL2~15:00:00~5~360'
  Msg:     'QR Tag Printed Successfully!'

The Result column is split on '~' to populate PrintResultData.
"""

from app.repositories import print_repo
from app.repositories import traceability_repo
from app.schemas.print_schema import (
    KanbanPrintResponse,
    PrintResultData,
)


# ─────────────────────────────────────────────────────────────────
#  Helper – parse the tilde-delimited Result column
# ─────────────────────────────────────────────────────────────────
def _parse_print_result(row: dict) -> tuple[bool, str, PrintResultData | None]:
    """
    Parse the SP result row into (success, message, data).
    Returns (False, msg, None) on error.
    """
    if row is None:
        return False, "No result from stored procedure", None

    result_str = str(row.get("Result", row.get("RESULT", "")))
    msg = str(row.get("Msg", row.get("MSG", "")))

    if not result_str.startswith("Y"):
        return False, result_str or msg or "Print failed", None

    parts = result_str.split("~")
    # Parts layout (index):
    #  0: 'Y'
    #  1: SupplierName
    #  2: Traceability (e.g. 'Traceability Tag')
    #  3: SerialNo
    #  4: CompanyName / CustomerName
    #  5: TagType ('NEW')
    #  6: PrintDate
    #  7: BarcodeLot1
    #  8: BarcodeLot2 (may be empty)  — only in KANBAN_PRINT
    #  9: SerialNo2 (may be empty)    — only in KANBAN_PRINT
    # 10: PrintTime  (HH:mm:ss)       — index 8 in RE_PRINT
    # 11: CountNoOfTags                — index 9 in RE_PRINT
    # 12: TotalQtyStockIn             — index 10 in RE_PRINT

    def _safe(idx, default=""):
        return parts[idx] if idx < len(parts) else default

    def _safe_int(idx, default=0):
        try:
            return int(parts[idx]) if idx < len(parts) else default
        except (ValueError, TypeError):
            return default

    # Determine layout: KANBAN_PRINT has 13 parts, RE_PRINT has 11
    if len(parts) >= 13:
        # KANBAN_PRINT layout
        data = PrintResultData(
            supplier_name=_safe(1),
            traceability=_safe(2),
            serial_no=_safe(3),
            company_name=_safe(4),
            tag_type=_safe(5),
            print_date=_safe(6),
            barcode_lot1=_safe(7),
            barcode_lot2=_safe(8) or None,
            serial_no_2=_safe(9) or None,
            print_time=_safe(10),
            no_of_tags_stock_in=_safe_int(11),
            total_qty_stock_in=_safe_int(12),
        )
    elif len(parts) >= 11:
        # KANBAN_RE_PRINT layout (no lot2 / serial2 fields)
        data = PrintResultData(
            supplier_name=_safe(1),
            traceability=_safe(2),
            serial_no=_safe(3),
            company_name=_safe(4),
            tag_type=_safe(5),
            print_date=_safe(6),
            barcode_lot1=_safe(7),
            barcode_lot2=None,
            serial_no_2=None,
            print_time=_safe(8),
            no_of_tags_stock_in=_safe_int(9),
            total_qty_stock_in=_safe_int(10),
        )
    else:
        # Minimal / unknown layout – still success
        data = PrintResultData(
            supplier_name=_safe(1),
            traceability=_safe(2),
            serial_no=_safe(3),
            barcode_lot1=_safe(7) if len(parts) > 7 else None,
        )

    return True, msg or "QR Tag Printed Successfully!", data


# ─────────────────────────────────────────────────────────────────
# 1.  Print (KANBAN_PRINT)
# ─────────────────────────────────────────────────────────────────
def print_tag(
    *,
    company_code: str | None,
    plant_code: str,
    station_no: str,
    supplier_code: str,
    customer_code: str | None,
    supplier_part_no: str,
    part_no: str,
    lot_no_1: str,
    lot_no_2: str | None,
    tag_type: str | None,
    weight: float | None,
    qty: int | None,
    is_mixed_lot: bool,
    running_sn_no: str | None,
    rm_material: str | None,
    printed_by: str,
    old_barcode: str | None,
    gross_weight: str | None,
) -> KanbanPrintResponse:
    """Execute KANBAN_PRINT SP and return parsed response."""
    row = print_repo.kanban_print(
        company_code=company_code,
        plant_code=plant_code,
        station_no=station_no,
        supplier_code=supplier_code,
        customer_code=customer_code,
        supplier_part_no=supplier_part_no,
        part_no=part_no,
        lot_no_1=lot_no_1,
        lot_no_2=lot_no_2,
        tag_type=tag_type,
        weight=weight,
        qty=qty,
        is_mixed_lot=is_mixed_lot,
        running_sn_no=running_sn_no,
        rm_material=rm_material,
        printed_by=printed_by,
        old_barcode=old_barcode,
        gross_weight=gross_weight,
    )

    success, msg, data = _parse_print_result(row)
    return KanbanPrintResponse(success=success, message=msg, data=data)


# ─────────────────────────────────────────────────────────────────
# 2.  Re-Print (KANBAN_RE_PRINT) – supervisor auth first
# ─────────────────────────────────────────────────────────────────
def reprint_tag(
    *,
    supervisor_user_id: str,
    supervisor_password: str,
    company_code: str | None,
    plant_code: str,
    station_no: str,
    supplier_code: str,
    customer_code: str | None,
    supplier_part_no: str,
    part_no: str,
    lot_no_1: str,
    lot_no_2: str | None,
    tag_type: str | None,
    weight: float | None,
    qty: int | None,
    is_mixed_lot: bool,
    running_sn_no: str | None,
    rm_material: str | None,
    printed_by: str,
    old_barcode: str,
    gross_weight: str | None,
) -> KanbanPrintResponse:
    """
    1. Validate supervisor credentials (same check as model-change).
    2. If valid, execute KANBAN_RE_PRINT SP.
    """
    # ── Step 1: supervisor auth ──────────────────────────────────
    sup_row = traceability_repo.validate_device_supervisor(
        supervisor_user_id, supervisor_password
    )
    if sup_row is None or not sup_row.get("SupplierPlantCode"):
        return KanbanPrintResponse(
            success=False,
            message="Supervisor authentication failed or insufficient rights",
            data=None,
        )

    # ── Step 2: call the SP ──────────────────────────────────────
    row = print_repo.kanban_reprint(
        company_code=company_code,
        plant_code=plant_code,
        station_no=station_no,
        supplier_code=supplier_code,
        customer_code=customer_code,
        supplier_part_no=supplier_part_no,
        part_no=part_no,
        lot_no_1=lot_no_1,
        lot_no_2=lot_no_2,
        tag_type=tag_type,
        weight=weight,
        qty=qty,
        is_mixed_lot=is_mixed_lot,
        running_sn_no=running_sn_no,
        rm_material=rm_material,
        printed_by=printed_by,
        old_barcode=old_barcode,
        gross_weight=gross_weight,
    )

    success, msg, data = _parse_print_result(row)
    return KanbanPrintResponse(success=success, message=msg, data=data)


# ─────────────────────────────────────────────────────────────────
# 3.  Get Image (GET_PRINT_IMAGE)
# ─────────────────────────────────────────────────────────────────
def get_image(supplier_part: str) -> bytes | None:
    """Return raw image bytes or None if not found."""
    return print_repo.get_print_image(supplier_part)


# ─────────────────────────────────────────────────────────────────
# 4.  Change Lot Number – update lot on a printed kanban tag
# ─────────────────────────────────────────────────────────────────
def change_lot_no(
    barcode: str,
    new_lot_no: str,
    supplier_code: str,
    supplier_part_no: str,
    part_no: str,
    modified_by: str | None = None,
):
    """
    Change the lot number for an existing kanban tag.
    Returns a ChangeLotNoResponse.
    """
    from app.schemas.print_schema import ChangeLotNoResponse

    result = print_repo.change_lot_no(
        barcode=barcode,
        new_lot_no=new_lot_no,
        supplier_code=supplier_code,
        supplier_part_no=supplier_part_no,
        part_no=part_no,
        modified_by=modified_by,
    )

    if result is None:
        return ChangeLotNoResponse(
            success=False,
            message="No tag found for the given barcode and supplier details",
        )

    return ChangeLotNoResponse(
        success=True,
        message="Lot number changed successfully",
        barcode=result["barcode"],
        old_lot_no=result["old_lot_no"],
        new_lot_no=result["new_lot_no"],
    )


# ─────────────────────────────────────────────────────────────────
# 5.  Scan Barcode – auto-fill form from scanned barcode
# ─────────────────────────────────────────────────────────────────
def scan_barcode(
    barcode: str,
    supplier_code: str | None = None,
    plant_code: str | None = None,
    station_no: str | None = None,
    supplier_part_no: str | None = None,
):
    """
    Look up a scanned barcode and return all part details
    to auto-fill the Supplier Part Details form.
    """
    from app.schemas.print_schema import ScanBarcodeResponse, ScanBarcodeData

    row = print_repo.scan_barcode(
        barcode=barcode,
        supplier_code=supplier_code,
        plant_code=plant_code,
        station_no=station_no,
        supplier_part_no=supplier_part_no,
    )

    if row is None:
        return ScanBarcodeResponse(
            success=False,
            message="No tag found for the scanned barcode",
            data=None,
        )

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

    data = ScanBarcodeData(
        part_no=row.get("PartNo"),
        part_name=row.get("PartName") or row.get("SupplierPartName"),
        supplier_part_no=row.get("SupplierPartNo"),
        supplier_name=row.get("SupplierName"),
        supplier_code=row.get("SupplierCode"),
        batch_size=_int(row.get("BatchSize")),
        weight=_float(row.get("Weight") or row.get("PartWeight")),
        is_mixed_lot=bool(row.get("IsMixedLot")),
        lot_no_1=row.get("LotNo1"),
        lot_no_2=row.get("LotNo2"),
        quantity=_int(row.get("Qty")),
        last_tag_serial_no=row.get("LastTagSerialNo"),
        no_of_tags_printed=_int(row.get("NoOfTagsPrinted")),
        total_qty_stock_in=_int(row.get("TotalQtyStockIn")),
        barcode_lot1=row.get("Barcode"),
        barcode_lot2=row.get("OldBarcode"),
        tag_type=row.get("TagType"),
        shift=row.get("Shift"),
        print_date=row.get("PrintDate"),
        print_time=row.get("PrintTime"),
        station_no=row.get("StationNo"),
        plant_code=row.get("PlantCode"),
        tolerance_weight=_float(row.get("ToleranceWeight")),
        gross_weight=str(row.get("Grossweight")) if row.get("Grossweight") else None,
        rm_material=row.get("RM_Material"),
    )

    return ScanBarcodeResponse(
        success=True,
        message="Barcode scanned successfully – details auto-filled",
        data=data,
    )
