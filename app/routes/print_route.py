"""
Routes for Print / Re-Print / Get-Image.

Endpoints:
  POST /api/printing/print              → KANBAN_PRINT
  POST /api/printing/reprint            → KANBAN_RE_PRINT (supervisor auth first)
  GET  /api/printing/image/{supplier_part} → GET_PRINT_IMAGE (binary image)
"""

from fastapi import APIRouter, HTTPException, Response, Depends

from app.schemas.print_schema import (
    KanbanPrintRequest,
    KanbanPrintResponse,
    KanbanRePrintRequest,
    GetImageResponse,
    ScanBarcodeRequest,
    ScanBarcodeResponse,
    ChangeLotNoRequest,
    ChangeLotNoResponse,
    GetLastPrintDetailsRequest,
    GetLastPrintDetailsResponse,
)
from app.services import print_service
from app.utils.jwt_handler import get_current_user
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/printing",
    tags=["Print / Re-Print / Get-Image"],
)


# ── 1. Print  ──────────────────────────────────────────────────────
@router.post("/print", response_model=KanbanPrintResponse)
def print_tag(body: KanbanPrintRequest, user: dict = Depends(get_current_user)):
    """
    **Print a new traceability tag (QR/Barcode).**

    SP call: `PRC_PrintKanban @TYPE = 'KANBAN_PRINT'`

    The SP generates a running serial number, builds barcode string(s),
    inserts a row into `TT_Kanban_Print`, and returns the tag data
    (supplier name, serial, barcode, print date/time, count/total).
    """
    logger.info("Print tag request: supplier_part=%s, lot=%s", body.supplier_part_no, body.lot_no_1)
    result = print_service.print_tag(
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
        old_barcode=body.old_barcode,
        gross_weight=body.gross_weight,
    )
    if not result.success:
        logger.warning("Print tag failed: %s", result.message)
        raise HTTPException(status_code=400, detail=result.message)
    logger.info("Print tag successful for supplier_part=%s", body.supplier_part_no)
    return result


# ── 2. Re-Print  ───────────────────────────────────────────────────
@router.post("/reprint", response_model=KanbanPrintResponse)
def reprint_tag(body: KanbanRePrintRequest, user: dict = Depends(get_current_user)):
    """
    **Re-print a traceability tag (supervisor authentication required).**

    Flow:
      1. Validate supervisor credentials.
      2. Copy old tag to `TT_Kanban_Re_Print_History`.
      3. Delete old barcode from `TT_Kanban_Print`.
      4. Generate new serial / barcode and insert replacement.

    SP call: `PRC_PrintKanban @TYPE = 'KANBAN_RE_PRINT'`
    """
    logger.info("Reprint tag request: old_barcode=%s, supervisor=%s", body.old_barcode, body.supervisor_user_id)
    result = print_service.reprint_tag(
        supervisor_user_id=body.supervisor_user_id,
        supervisor_password=body.supervisor_password,
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
        old_barcode=body.old_barcode,
        gross_weight=body.gross_weight,
    )
    if not result.success:
        logger.warning("Reprint tag failed: %s", result.message)
        raise HTTPException(status_code=400, detail=result.message)
    logger.info("Reprint tag successful for old_barcode=%s", body.old_barcode)
    return result


# ── 3. Get Image  ──────────────────────────────────────────────────
@router.get(
    "/image/{supplier_part}",
    responses={
        200: {"content": {"image/jpeg": {}}, "description": "Supplier part image"},
        404: {"model": GetImageResponse, "description": "No image found"},
    },
)
def get_image(supplier_part: str, user: dict = Depends(get_current_user)):
    """
    **Retrieve the supplier-part image (binary).**

    Returns the raw image stored in
    `TM_DnhaPart_And_SupplierPart_Mapping.SupplierPartImage`.

    SP call: `PRC_PrintKanban @TYPE = 'GET_PRINT_IMAGE'`
    """
    logger.info("Fetching image for supplier_part=%s", supplier_part)
    image_bytes = print_service.get_image(supplier_part)
    if image_bytes is None:
        logger.warning("No image found for supplier_part=%s", supplier_part)
        raise HTTPException(
            status_code=404,
            detail="No image found for the given supplier part",
        )
    return Response(content=image_bytes, media_type="image/jpeg")


# ── 4. Change Lot Number  ──────────────────────────────────────────
@router.post("/change-lot-no", response_model=ChangeLotNoResponse)
def change_lot_no(body: ChangeLotNoRequest, user: dict = Depends(get_current_user)):
    """
    **Change the lot number on a printed kanban tag.**

    Identifies the tag by its barcode, supplier code, supplier part no,
    and part no, then updates LotNo1 to the new value.
    """
    result = print_service.change_lot_no(
        barcode=body.barcode,
        new_lot_no=body.new_lot_no,
        supplier_code=body.supplier_code,
        supplier_part_no=body.supplier_part_no,
        part_no=body.part_no,
        modified_by=body.modified_by,
    )
    if not result.success:
        logger.warning("Change lot no failed: %s", result.message)
        raise HTTPException(status_code=404, detail=result.message)
    logger.info("Lot number changed for barcode=%s", body.barcode)
    return result


# ── 5. Last Print Details  ──────────────────────────────────────────
@router.post("/last-print-details", response_model=GetLastPrintDetailsResponse)
def last_print_details(body: GetLastPrintDetailsRequest, user: dict = Depends(get_current_user)):
    """
    **Get the last print summary for a supplier.**

    Returns the latest running serial number, count of distinct bin barcodes
    (active, undispatched), and total number of tags.

    SP call: `PRC_PrintKanban @TYPE = 'GET_LAST_PRINT_DETAILS'`
    """
    logger.info("Last print details request: supplier_code=%s", body.supplier_code)
    result = print_service.get_last_print_details(supplier_code=body.supplier_code)
    if not result.success:
        logger.warning("Last print details not found: %s", result.message)
        raise HTTPException(status_code=404, detail=result.message)
    logger.info("Last print details retrieved for supplier_code=%s", body.supplier_code)
    return result


# ── 6. Scan Barcode  ───────────────────────────────────────────────
@router.post("/scan", response_model=ScanBarcodeResponse)
def scan_barcode(body: ScanBarcodeRequest, user: dict = Depends(get_current_user)):
    """Scan a barcode and return all tag details to auto-fill the form."""
    logger.info("Scanning barcode: %s", body.barcode)
    result = print_service.scan_barcode(barcode=body.barcode)
    if not result.success:
        logger.warning("Scan barcode failed for barcode=%s: %s", body.barcode, result.message)
        raise HTTPException(status_code=404, detail=result.message)
    logger.info("Barcode scanned successfully: %s", body.barcode)
    return result
