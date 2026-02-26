"""
Repository layer – DB calls for Rework Traceability Tag.

All calls use SP  PRC_Print_Rework_Kanban  with different @TYPE values.
"""

from app.utils.database import get_db_connection
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _row_to_dict(cursor, row):
    """Convert a pyodbc Row to a plain dict."""
    if row is None:
        return None
    columns = [col[0] for col in cursor.description]
    return dict(zip(columns, row))


def _fetch_sp_result(cursor):
    """
    Skip forward through result-sets until we find one with data.
    """
    while True:
        if cursor.description is not None:
            row = cursor.fetchone()
            if row is not None:
                return _row_to_dict(cursor, row)
        if not cursor.nextset():
            break
    return None


def _fetch_all_rows(cursor):
    """
    Fetch all rows from the first result-set that has data.
    """
    while True:
        if cursor.description is not None:
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            if rows:
                return [dict(zip(columns, r)) for r in rows]
        if not cursor.nextset():
            break
    return []


# ─────────────────────────────────────────────────────────────────
# 1.  VALIDATE_TAG  –  Validate barcode & return tag details
# ─────────────────────────────────────────────────────────────────
def validate_tag(
    barcode: str,
    supplier_code: str | None = None,
) -> dict | None:
    """
    Calls PRC_Print_Rework_Kanban @TYPE = 'VALIDATE_TAG'.
    Returns tag details for auto-fill or None/error row.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        logger.info("DAL: validate_tag for barcode=%s", barcode)
        cursor.execute(
            """
            SET NOCOUNT ON;
            EXEC [dbo].[PRC_Print_Rework_Kanban]
                @TYPE         = 'VALIDATE_TAG',
                @Barcode      = ?,
                @SupplierCode = ?
            """,
            barcode,
            supplier_code,
        )
        return _fetch_sp_result(cursor)
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────
# 2.  GET_PRINT_DETAILS  –  Last 3 rework prints for part + lot
# ─────────────────────────────────────────────────────────────────
def get_print_details(
    supplier_part_no: str,
    lot_no_1: str,
    supplier_code: str | None = None,
) -> list[dict]:
    """
    Calls PRC_Print_Rework_Kanban @TYPE = 'GET_PRINT_DETAILS'.
    Returns up to 3 rows of recent rework prints.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        logger.info("DAL: get_print_details for part=%s, lot=%s", supplier_part_no, lot_no_1)
        cursor.execute(
            """
            SET NOCOUNT ON;
            EXEC [dbo].[PRC_Print_Rework_Kanban]
                @TYPE           = 'GET_PRINT_DETAILS',
                @SupplierPartNo = ?,
                @LotNo1         = ?,
                @SupplierCode   = ?
            """,
            supplier_part_no,
            lot_no_1,
            supplier_code,
        )
        return _fetch_all_rows(cursor)
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────
# 3.  GET_LAST_PRINT_DETAILS  –  Last serial & tag counts
# ─────────────────────────────────────────────────────────────────
def get_last_print_details(
    supplier_part_no: str,
) -> dict | None:
    """
    Calls PRC_Print_Rework_Kanban @TYPE = 'GET_LAST_PRINT_DETAILS'.
    Returns last running serial no & tag counts.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        logger.info("DAL: get_last_print_details for part=%s", supplier_part_no)
        cursor.execute(
            """
            SET NOCOUNT ON;
            EXEC [dbo].[PRC_Print_Rework_Kanban]
                @TYPE           = 'GET_LAST_PRINT_DETAILS',
                @SupplierPartNo = ?
            """,
            supplier_part_no,
        )
        return _fetch_sp_result(cursor)
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────
# 4.  KANBAN_PRINT (Rework)  –  Print rework tag
# ─────────────────────────────────────────────────────────────────
def rework_print(
    *,
    barcode: str,
    company_code: str | None = None,
    plant_code: str,
    station_no: str,
    supplier_code: str,
    customer_code: str | None = None,
    supplier_part_no: str,
    part_no: str,
    lot_no_1: str,
    lot_no_2: str | None = "",
    tag_type: str | None = None,
    weight: float | None = None,
    qty: int | None = None,
    is_mixed_lot: bool = False,
    running_sn_no: str | None = None,
    rm_material: str | None = None,
    printed_by: str,
    gross_weight: str | None = None,
) -> dict | None:
    """
    Calls PRC_Print_Rework_Kanban @TYPE = 'KANBAN_PRINT'.

    The SP:
      - Generates new running serial & barcode
      - Archives old tag to TT_Kanban_Print_Rework_His
      - Inserts new rework tag into TT_Kanban_Print
      - Deletes old barcode
      - Returns tilde-delimited Result + Msg
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        logger.info("DAL: rework_print for barcode=%s, part=%s", barcode, supplier_part_no)
        cursor.execute(
            """
            SET NOCOUNT ON;
            EXEC [dbo].[PRC_Print_Rework_Kanban]
                @TYPE           = 'KANBAN_PRINT',
                @CompanyCode    = ?,
                @PlantCode      = ?,
                @StationNo      = ?,
                @SupplierCode   = ?,
                @CustomerCode   = ?,
                @SupplierPartNo = ?,
                @PartNo         = ?,
                @LotNo1         = ?,
                @LotNo2         = ?,
                @TagType        = ?,
                @Weight         = ?,
                @Qty            = ?,
                @IsMixedLot     = ?,
                @RunningSNNo    = ?,
                @RM_Material    = ?,
                @Barcode        = ?,
                @PrintedBy      = ?,
                @Grossweight    = ?
            """,
            company_code,
            plant_code,
            station_no,
            supplier_code,
            customer_code,
            supplier_part_no,
            part_no,
            lot_no_1,
            lot_no_2 or "",
            tag_type,
            weight,
            qty,
            1 if is_mixed_lot else 0,
            running_sn_no,
            rm_material,
            barcode,
            printed_by,
            gross_weight,
        )
       
        return _fetch_sp_result(cursor)
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────
# 5.  GET_REPRINT_PARAMETER  –  Lot structure parameters
# ─────────────────────────────────────────────────────────────────
def get_reprint_parameter(
    supplier_part_no: str,
) -> dict | None:
    """
    Calls PRC_Print_Rework_Kanban @TYPE = 'GET_REPRINT_PARAMETER'.
    Returns lot structure info.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        logger.info("DAL: get_reprint_parameter for part=%s", supplier_part_no)
        cursor.execute(
            """
            SET NOCOUNT ON;
            EXEC [dbo].[PRC_Print_Rework_Kanban]
                @TYPE           = 'GET_REPRINT_PARAMETER',
                @SupplierPartNo = ?
            """,
            supplier_part_no,
        )
        return _fetch_sp_result(cursor)
    finally:
        conn.close()
