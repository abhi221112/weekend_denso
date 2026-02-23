"""
Service layer – business logic for Rework Traceability Tag.

Rework KANBAN_PRINT result parsing
-----------------------------------
The SP returns:
  Result:  'Y~Barcode~PrintTime~SerialNo~CountTags~TotalTags~TagType~PrintDate'
  Msg:     'QR Tag Printed Successfully!'
"""

from app.repositories import rework_repo
from app.schemas.rework_schema import (
    ReworkValidateTagResponse,
    ReworkValidateTagData,
    ReworkGetPrintDetailsResponse,
    ReworkPrintDetailItem,
    ReworkGetLastPrintResponse,
    ReworkLastPrintData,
    ReworkPrintResponse,
    ReworkPrintResultData,
    ReworkReprintParamResponse,
    ReworkReprintParamData,
)


# ─────────────────────────────────────────────────────────────────
#  Helper – parse rework print result
# ─────────────────────────────────────────────────────────────────
def _parse_rework_result(row: dict) -> tuple[bool, str, ReworkPrintResultData | None]:
    """
    Parse the rework SP result row.
    Result format: Y~Barcode~PrintTime~SerialNo~CountTags~TotalTags~TagType~PrintDate
    """
    if row is None:
        return False, "No result from stored procedure", None

    result_str = str(row.get("Result", row.get("RESULT", "")))
    msg = str(row.get("Msg", row.get("MSG", "")))

    if not result_str.startswith("Y"):
        return False, result_str or msg or "Rework print failed", None

    parts = result_str.split("~")

    def _safe(idx, default=""):
        return parts[idx] if idx < len(parts) else default

    def _safe_int(idx, default=0):
        try:
            return int(parts[idx]) if idx < len(parts) else default
        except (ValueError, TypeError):
            return default

    data = ReworkPrintResultData(
        barcode=_safe(1),
        print_time=_safe(2),
        serial_no=_safe(3),
        no_of_tags_stock_in=_safe_int(4),
        total_qty_stock_in=_safe_int(5),
        tag_type=_safe(6),
        print_date=_safe(7),
    )

    return True, msg or "QR Tag Printed Successfully!", data


# ─────────────────────────────────────────────────────────────────
# 1.  Validate Tag – scan barcode for rework
# ─────────────────────────────────────────────────────────────────
def validate_tag(
    barcode: str,
    supplier_code: str | None = None,
) -> ReworkValidateTagResponse:
    """Validate a barcode for rework and return tag details."""
    row = rework_repo.validate_tag(
        barcode=barcode,
        supplier_code=supplier_code,
    )

    if row is None:
        return ReworkValidateTagResponse(
            success=False,
            message="No tag found for the scanned barcode",
            data=None,
        )

    result_str = str(row.get("Result", ""))
    if result_str.startswith("N"):
        msg = row.get("Msg", "Tag does not exist or has been dispatched")
        return ReworkValidateTagResponse(
            success=False,
            message=msg,
            data=None,
        )

    def _float(val):
        try:
            return float(val) if val is not None else None
        except (ValueError, TypeError):
            return None

    def _int(val):
        try:
            return int(val) if val is not None else None
        except (ValueError, TypeError):
            return None

    data = ReworkValidateTagData(
        supplier_code=row.get("SupplierCode"),
        supplier_name=row.get("VNAME"),
        supplier_part_no=row.get("SupplierPartNo"),
        supplier_part_name=row.get("SupplierPartName"),
        part_no=row.get("PartNo"),
        part_description=row.get("ITDSC"),
        lot_no_1=row.get("LotNo1"),
        lot_no_2=row.get("LotNo2"),
        tag_type=row.get("TagType"),
        weight=_float(row.get("Weight")),
        running_sn_no=row.get("RunningSNNo"),
        barcode=row.get("Barcode"),
        pack_size=_int(row.get("PackSize")),
        qty=_int(row.get("Qty")),
        shift=row.get("Shift"),
        traceability=row.get("Traceability"),
        tag_type_label=row.get("RWK") if row.get("RWK") else "RWK",
        company_name=row.get("CompanyName"),
        print_date=row.get("PrintDate"),
        supplier_part_image=None,  # binary – not serialised
        tolerance_weight=_float(row.get("ToleranceWeight")),
        weighing_scale=row.get("WeighingScale"),
        image_name=row.get("ImageName"),
        bin_weight=_float(row.get("BinWeight")),
        bin_tolerance_weight=_float(row.get("BinToleranceWeight")),
    )

    return ReworkValidateTagResponse(
        success=True,
        message="Tag validated successfully – details auto-filled",
        data=data,
    )


# ─────────────────────────────────────────────────────────────────
# 2.  Get Print Details – last 3 rework prints
# ─────────────────────────────────────────────────────────────────
def get_print_details(
    supplier_part_no: str,
    lot_no_1: str,
    supplier_code: str | None = None,
) -> ReworkGetPrintDetailsResponse:
    """Return last 3 rework print details for a part + lot."""
    rows = rework_repo.get_print_details(
        supplier_part_no=supplier_part_no,
        lot_no_1=lot_no_1,
        supplier_code=supplier_code,
    )

    if not rows:
        return ReworkGetPrintDetailsResponse(
            success=False,
            message="No rework print records found",
            data=None,
        )

    def _float(val):
        try:
            return float(val) if val is not None else None
        except (ValueError, TypeError):
            return None

    def _int(val):
        try:
            return int(val) if val is not None else None
        except (ValueError, TypeError):
            return None

    items = []
    for r in rows:
        items.append(ReworkPrintDetailItem(
            plant_code=r.get("PlantCode"),
            station_no=r.get("StationNo"),
            shift=r.get("Shift"),
            lot_no_1=r.get("LotNo1"),
            lot_no_2=r.get("LotNo2"),
            running_sn_no=r.get("RunningSNNo"),
            printed_by=r.get("PrintedBy"),
            printed_on=str(r.get("PrintedOn")) if r.get("PrintedOn") else None,
            print_date=r.get("PrintDate"),
            traceability=r.get("Traceability"),
            tag_type=r.get("TagTypeA"),
            supplier_name=r.get("VNAME"),
            barcode=r.get("Barcode"),
            company_name=r.get("CompanyName"),
            supplier_part_no=r.get("SupplierPartNo"),
            part_no=r.get("PartNo"),
            weight=_float(r.get("Weight")),
            pack_size=_int(r.get("PackSize")),
            weighing_scale=r.get("WeighingScale"),
            gross_weight=_float(r.get("Grossweight")),
        ))

    return ReworkGetPrintDetailsResponse(
        success=True,
        message=f"Found {len(items)} rework print record(s)",
        data=items,
    )


# ─────────────────────────────────────────────────────────────────
# 3.  Get Last Print Details – serial & tag counts
# ─────────────────────────────────────────────────────────────────
def get_last_print_details(
    supplier_part_no: str,
) -> ReworkGetLastPrintResponse:
    """Return last serial no & tag counts."""
    row = rework_repo.get_last_print_details(supplier_part_no)

    if row is None:
        return ReworkGetLastPrintResponse(
            success=False,
            message="No print records found for this supplier part",
            data=None,
        )

    def _int(val):
        try:
            return int(val) if val is not None else None
        except (ValueError, TypeError):
            return None

    data = ReworkLastPrintData(
        running_sn_no=row.get("RunningSNNo"),
        count_no_of_tags=_int(row.get("CountNoOfTage")),
        total_no_of_tags=_int(row.get("TotalNoOfTage")),
    )

    return ReworkGetLastPrintResponse(
        success=True,
        message="Last print details retrieved",
        data=data,
    )


# ─────────────────────────────────────────────────────────────────
# 4.  Rework Print (KANBAN_PRINT)
# ─────────────────────────────────────────────────────────────────
def rework_print(
    *,
    barcode: str,
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
    gross_weight: str | None,
) -> ReworkPrintResponse:
    """Execute rework KANBAN_PRINT SP and return parsed response."""
    row = rework_repo.rework_print(
        barcode=barcode,
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
        gross_weight=gross_weight,
    )

    success, msg, data = _parse_rework_result(row)
    return ReworkPrintResponse(success=success, message=msg, data=data)


# ─────────────────────────────────────────────────────────────────
# 5.  Get Reprint Parameter – lot structure
# ─────────────────────────────────────────────────────────────────
def get_reprint_parameter(
    supplier_part_no: str,
) -> ReworkReprintParamResponse:
    """Return lot structure parameters for reprint."""
    row = rework_repo.get_reprint_parameter(supplier_part_no)

    if row is None:
        return ReworkReprintParamResponse(
            success=False,
            message="No reprint parameters found for this supplier part",
            data=None,
        )

    def _float(val):
        try:
            return float(val) if val is not None else None
        except (ValueError, TypeError):
            return None

    def _int(val):
        try:
            return int(val) if val is not None else None
        except (ValueError, TypeError):
            return None

    data = ReworkReprintParamData(
        total_no_of_digits=_int(row.get("TotalNoOfDigits")),
        no_of_steps=_int(row.get("NoOfSteps")),
        step_1_digits=_int(row.get("Step_1_Digits")),
        step_2_digits=_int(row.get("Step_2_Digits")),
        step_3_digits=_int(row.get("Step_3_Digits")),
        step_4_digits=_int(row.get("Step_4_Digits")),
        step_5_digits=_int(row.get("Step_5_Digits")),
        step_6_digits=_int(row.get("Step_6_Digits")),
        supplier_code=row.get("SupplierCode"),
        tolerance_weight=_float(row.get("ToleranceWeight")),
        weighing_scale=row.get("WeighingScale"),
        bin_weight=_float(row.get("BinWeight")),
        bin_tolerance_weight=_float(row.get("BinToleranceWeight")),
    )

    return ReworkReprintParamResponse(
        success=True,
        message="Reprint parameters retrieved",
        data=data,
    )
