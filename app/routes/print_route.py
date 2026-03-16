"""
Routes for Print / Re-Print / Get-Image.

Endpoints:
  POST /api/printing/print              → KANBAN_PRINT
  POST /api/printing/reprint            → KANBAN_RE_PRINT (supervisor auth first)
  GET  /api/printing/image/{supplier_part} → GET_PRINT_IMAGE (binary image)
"""

from fastapi import APIRouter, HTTPException, Request, Response, Depends

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
    GetPrintDetailsRequest,
    GetPrintDetailsResponse,
    GetAllPrintDetailsRequest,
    GetAllPrintDetailsResponse,
    PrintPrnRequest,
    PrintPrnResponse,
    KanbanReworkRePrintRequest,
    GetAllReworkPrintDetailsRequest,
    GetAllReworkPrintDetailsResponse,
    ValidateUserAdminRequest,
    ValidateUserAdminResponse,
    GetShiftRequest,
    GetShiftResponse,
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
    response_model=GetImageResponse,
    responses={
        404: {"model": GetImageResponse, "description": "No image found"},
    },
)
def get_image(supplier_part: str, request: Request, user: dict = Depends(get_current_user)):
    """
    **Retrieve the supplier-part image URL.**

    Returns a JSON response with the static image URL that the
    frontend can use directly in an `<img>` tag.
    """
    logger.info("Fetching image for supplier_part=%s", supplier_part)
    image_url = print_service.get_image_url(supplier_part, request)
    if image_url is None:
        logger.warning("No image found for supplier_part=%s", supplier_part)
        raise HTTPException(
            status_code=404,
            detail="No image found for the given supplier part",
        )
    return GetImageResponse(success=True, message="Image loaded successfully", image_url=image_url)


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


# ── 7. Get Print Details  ──────────────────────────────────────────
@router.post("/print-details", response_model=GetPrintDetailsResponse)
def get_print_details(body: GetPrintDetailsRequest, user: dict = Depends(get_current_user)):
    """
    **Get the top 3 recent print details for a supplier.**

    Returns the latest prints filtered by supplier code, printed-by user,
    station, and plant. The SP handles both regular supplier and
    other-customer supplier branches.

    SP call: `PRC_PrintKanban @TYPE = 'GET_PRINT_DETAILS'`
    """
    logger.info(
        "Print details request: supplier=%s, printer=%s, station=%s",
        body.supplier_code, body.printed_by, body.station_no,
    )
    result = print_service.get_print_details(
        supplier_code=body.supplier_code,
        printed_by=body.printed_by,
        station_no=body.station_no,
        plant_code=body.plant_code,
    )
    if not result.success:
        logger.warning("Print details not found: %s", result.message)
        raise HTTPException(status_code=404, detail=result.message)
    logger.info("Print details retrieved for supplier=%s", body.supplier_code)
    return result


# ── 8. Get All Print Details  ──────────────────────────────────────
@router.post("/all-print-details", response_model=GetAllPrintDetailsResponse)
def get_all_print_details(body: GetAllPrintDetailsRequest, user: dict = Depends(get_current_user)):
    """
    **Get all undispatched print details for a station/plant.**

    Returns all active (undispatched) kanban prints from both regular
    and other-customer suppliers, ordered by running serial number
    descending.

    SP call: `PRC_PrintKanban @TYPE = 'GET_ALL_PRINT_DETAILS'`
    """
    logger.info(
        "All print details request: printer=%s, station=%s, plant=%s",
        body.printed_by, body.station_no, body.plant_code,
    )
    result = print_service.get_all_print_details(
        printed_by=body.printed_by,
        station_no=body.station_no,
        plant_code=body.plant_code,
    )
    if not result.success:
        logger.warning("All print details not found: %s", result.message)
        raise HTTPException(status_code=404, detail=result.message)
    logger.info("All print details retrieved for station=%s", body.station_no)
    return result


# ── 9. Print PRN  ────────────────────────────────────────────────
@router.post("/print-prn", response_model=PrintPrnResponse)
def print_prn(body: PrintPrnRequest, user: dict = Depends(get_current_user)):
    """
    **Log a print/reprint event to TM_Print_Prn.**

    Inserts a row with the PRN identifier, IP address, port, and supplier code.

    SP call: `PRC_PrintKanban @TYPE = 'PRINT_PRN'`
    """
    logger.info("Print PRN request: prn=%s, ip=%s, supplier=%s", body.prn, body.ip, body.supplier_code)
    result = print_service.print_prn(
        prn=body.prn,
        ip=body.ip,
        port=body.port,
        supplier_code=body.supplier_code,
    )
    if not result.success:
        logger.warning("Print PRN failed: %s", result.message)
        raise HTTPException(status_code=400, detail=result.message)
    logger.info("Print PRN logged for supplier=%s", body.supplier_code)
    return result


# ── 10. Rework Re-Print  ────────────────────────────────────────
@router.post("/rework-reprint", response_model=KanbanPrintResponse)
def rework_reprint_tag(body: KanbanReworkRePrintRequest, user: dict = Depends(get_current_user)):
    """
    **Rework re-print a traceability tag with a new tag (supervisor auth required).**

    Flow:
      1. Validate supervisor credentials.
      2. Copy old tag to `TT_Kanban_Re_Print_History`.
      3. Delete old barcode from `TT_Kanban_Print`.
      4. Generate new serial / barcode with PrintType='Rework' and TagType='RWK'.

    SP call: `PRC_PrintKanban @TYPE = 'KANBAN_REWORK_RE_PRINT'`
    """
    logger.info("Rework reprint request: old_barcode=%s, supervisor=%s", body.old_barcode, body.supervisor_user_id)
    result = print_service.rework_reprint_tag(
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
        logger.warning("Rework reprint failed: %s", result.message)
        raise HTTPException(status_code=400, detail=result.message)
    logger.info("Rework reprint successful for old_barcode=%s", body.old_barcode)
    return result


# ── 11. Get All Rework Print Details  ────────────────────────────
@router.post("/all-rework-print-details", response_model=GetAllReworkPrintDetailsResponse)
def get_all_rework_print_details(body: GetAllReworkPrintDetailsRequest, user: dict = Depends(get_current_user)):
    """
    **Get all undispatched rework print details for a station/plant.**

    Returns all active (undispatched) rework kanban prints
    (PrintType='Rework') from both regular and other-customer suppliers,
    ordered by running serial number descending.

    SP call: `PRC_PrintKanban @TYPE = 'GET_ALL_REWORK_PRINT_DETAILS'`
    """
    logger.info(
        "All rework print details request: printer=%s, station=%s, plant=%s",
        body.printed_by, body.station_no, body.plant_code,
    )
    result = print_service.get_all_rework_print_details(
        printed_by=body.printed_by,
        station_no=body.station_no,
        plant_code=body.plant_code,
    )
    if not result.success:
        logger.warning("All rework print details not found: %s", result.message)
        raise HTTPException(status_code=404, detail=result.message)
    logger.info("All rework print details retrieved for station=%s", body.station_no)
    return result


# ── 12. Validate User Admin  ───────────────────────────────────
@router.post("/validate-admin", response_model=ValidateUserAdminResponse)
def validate_user_admin(body: ValidateUserAdminRequest, user: dict = Depends(get_current_user)):
    """
    **Validate a supervisor/admin user for unlock/reprint operations.**

    Checks the user's group rights (ScreenId='2002') and returns
    user details on success.

    SP call: `PRC_UserSupplier_EndUser @TYPE = 'VALIDATEUSER_ADMIN'`
    """
    logger.info("Validate admin request: user_id=%s", body.user_id)
    result = print_service.validate_user_admin(
        user_id=body.user_id,
        password=body.password,
    )
    if not result.success:
        logger.warning("Validate admin failed: %s", result.message)
        raise HTTPException(status_code=401, detail=result.message)
    logger.info("Admin validated: user_id=%s", body.user_id)
    return result


# ── 13. Get Shift  ──────────────────────────────────────────────
@router.post("/shift", response_model=GetShiftResponse)
def get_shift(body: GetShiftRequest, user: dict = Depends(get_current_user)):
    """
    **Get the current shift information for a supplier.**

    Determines the current shift based on server time using
    `dbo.GetShiftTime()`. Returns shift name, shift start time,
    and shift end time.

    SP call: `PRC_PrintKanban @TYPE = 'GET_SHIFT'`
    """
    logger.info("Get shift request: supplier_code=%s", body.supplier_code)
    result = print_service.get_shift(supplier_code=body.supplier_code)
    if not result.success:
        logger.warning("Get shift failed: %s", result.message)
        raise HTTPException(status_code=404, detail=result.message)
    logger.info("Shift retrieved for supplier_code=%s", body.supplier_code)
    return result
