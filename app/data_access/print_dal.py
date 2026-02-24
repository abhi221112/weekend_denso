"""
Repository layer – DB calls for Print / Re-Print / Get-Image.

All three call the same SP  PRC_PrintKanban  with different @TYPE values,
mirroring exactly what the C# DL_KanbanPrint class does.
"""

from app.utils.database import get_db_connection


def _row_to_dict(cursor, row):
    """Convert a pyodbc Row to a plain dict."""
    if row is None:
        return None
    columns = [col[0] for col in cursor.description]
    return dict(zip(columns, row))


def _fetch_sp_result(cursor):
    """
    Skip forward through result-sets until we find one with data.
    The SP may emit intermediate SELECTs or SET operations.
    """
    while True:
        if cursor.description is not None:
            row = cursor.fetchone()
            if row is not None:
                return _row_to_dict(cursor, row)
        if not cursor.nextset():
            break
    return None


# ─────────────────────────────────────────────────────────────────
# 1.  KANBAN_PRINT  –  Print a new traceability tag
# ─────────────────────────────────────────────────────────────────
def kanban_print(
    *,
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
    old_barcode: str | None = None,
    gross_weight: str | None = None,
) -> dict | None:
    """
    Calls PRC_PrintKanban @Type = 'KANBAN_PRINT'.

    The SP internally:
      - Determines the current shift via dbo.GetShiftTime()
      - Generates a running serial number via PRC_GetRunningSerialReset
      - Builds barcode string(s)
      - INSERTs into TT_Kanban_Print
      - Returns a tilde-delimited Result column + Msg column

    Parameters mirror the C# DL_KanbanPrint.DL_ExecuteTask exactly.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SET NOCOUNT ON;
            EXEC [dbo].[PRC_PrintKanban]
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
                @PrintedBy      = ?,
                @OldBarcode     = ?,
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
            printed_by,
            old_barcode,
            gross_weight,
        )
        return _fetch_sp_result(cursor)
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────
# 2.  KANBAN_RE_PRINT  –  Re-print (replace old barcode with new)
# ─────────────────────────────────────────────────────────────────
def kanban_reprint(
    *,
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
    old_barcode: str,
    gross_weight: str | None = None,
) -> dict | None:
    """
    Calls PRC_PrintKanban @Type = 'KANBAN_RE_PRINT'.

    The SP internally:
      - Copies the old TT_Kanban_Print row to TT_Kanban_Re_Print_History
      - Deletes old barcode row
      - Generates new serial / barcode
      - INSERTs replacement row into TT_Kanban_Print
      - Returns tilde-delimited Result + Msg
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SET NOCOUNT ON;
            EXEC [dbo].[PRC_PrintKanban]
                @TYPE           = 'KANBAN_RE_PRINT',
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
                @PrintedBy      = ?,
                @OldBarcode     = ?,
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
            printed_by,
            old_barcode,
            gross_weight,
        )
        return _fetch_sp_result(cursor)
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────
# 3.  GET_PRINT_IMAGE  –  Supplier part image (binary)
# ─────────────────────────────────────────────────────────────────
def get_print_image(supplier_part: str) -> bytes | None:
    """
    Calls PRC_PrintKanban @Type = 'GET_PRINT_IMAGE'.

    Returns the raw varbinary(max) image data from
    TM_DnhaPart_And_SupplierPart_Mapping.SupplierPartImage.

    Mirrors the C# DL_KanbanPrint.GetImage_Print method which
    uses IDataReader to read the byte[] column.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SET NOCOUNT ON;
            EXEC [dbo].[PRC_PrintKanban]
                @TYPE           = 'GET_PRINT_IMAGE',
                @SupplierPartNo = ?
            """,
            supplier_part,
        )

        # Try to read the image binary from the result
        if cursor.description is not None:
            row = cursor.fetchone()
            if row is not None:
                image_data = row[0]           # SupplierPartImage column
                if image_data is not None:
                    return bytes(image_data)
        return None
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────
# 4.  CHANGE_LOT_NO  –  Update lot number on a printed kanban tag
# ─────────────────────────────────────────────────────────────────
def change_lot_no(
    barcode: str,
    new_lot_no: str,
    supplier_code: str,
    supplier_part_no: str,
    part_no: str,
    modified_by: str | None = None,
) -> dict | None:
    """
    Update the LotNo1 of a specific kanban tag identified by its barcode.
    Returns the updated row (with old and new lot info) or None if not found.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # First fetch the current lot number
        cursor.execute(
            """
            SET NOCOUNT ON;
            SELECT LotNo1 FROM TT_Kanban_Print
            WHERE Barcode = ?
              AND SupplierCode = ?
              AND SupplierPartNo = ?
              AND PartNo = ?
            """,
            barcode, supplier_code, supplier_part_no, part_no,
        )
        row = cursor.fetchone()
        if row is None:
            return None

        old_lot_no = row[0]

        # Update the lot number
        cursor.execute(
            """
            UPDATE TT_Kanban_Print
            SET LotNo1     = ?,
                ModifyBy   = ?,
                ModifyOn   = GETDATE()
            WHERE Barcode       = ?
              AND SupplierCode  = ?
              AND SupplierPartNo = ?
              AND PartNo        = ?
            """,
            new_lot_no, modified_by, barcode, supplier_code, supplier_part_no, part_no,
        )
        conn.commit()

        return {
            "barcode": barcode,
            "old_lot_no": old_lot_no,
            "new_lot_no": new_lot_no,
        }
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────
# 5.  SCAN_BARCODE  –  Look up tag details by scanned barcode
# ─────────────────────────────────────────────────────────────────
def scan_barcode(
    barcode: str,
) -> dict | None:
    """
    Look up a scanned barcode in TT_Kanban_Print and join with
    TM_DnhaPart_And_SupplierPart_Mapping to return all part details
    needed to auto-fill the Supplier Part Details form.

    The barcode is matched against Barcode1 or Barcode2 columns
    in TT_Kanban_Print.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SET NOCOUNT ON;

            SELECT TOP 1
                kp.SupplierPartNo,
                kp.PartNo,
                kp.SupplierCode,
                kp.LotNo1,
                kp.LotNo2,
                kp.Qty,
                kp.Weight,
                kp.TagType,
                kp.Barcode,
                kp.OldBarcode,
                kp.RunningSNNo,
                kp.IsMixedLot,
                kp.StationNo,
                kp.PlantCode,
                kp.PrintedBy,
                kp.RM_Material,
                kp.Grossweight,
                kp.Shift,
                CONVERT(varchar(10), kp.PrintedOn, 103) AS PrintDate,
                CONVERT(varchar(8), kp.PrintedOn, 108) AS PrintTime,
                ISNULL(pm.SupplierPartName, '') AS PartName,
                ISNULL(pm.SupplierPartName, '') AS SupplierPartName,
                ISNULL(pm.SupplierPartLotSize, '0') AS BatchSize,
                ISNULL(pm.SupplierPartWeight, 0) AS PartWeight,
                ISNULL(pm.ToleranceWeight, 0) AS ToleranceWeight,
                ISNULL(sm.VNAME, '') AS SupplierName,
                (
                    SELECT TOP 1 kp2.RunningSNNo
                    FROM TT_Kanban_Print kp2
                    WHERE kp2.SupplierPartNo = kp.SupplierPartNo
                      AND kp2.SupplierCode = kp.SupplierCode
                    ORDER BY kp2.PrintedOn DESC
                ) AS LastTagSerialNo,
                (
                    SELECT COUNT(*)
                    FROM TT_Kanban_Print kp3
                    WHERE kp3.SupplierPartNo = kp.SupplierPartNo
                      AND kp3.SupplierCode = kp.SupplierCode
                ) AS NoOfTagsPrinted,
                (
                    SELECT ISNULL(SUM(kp4.Qty), 0)
                    FROM TT_Kanban_Print kp4
                    WHERE kp4.SupplierPartNo = kp.SupplierPartNo
                      AND kp4.SupplierCode = kp.SupplierCode
                ) AS TotalQtyStockIn
            FROM TT_Kanban_Print kp WITH (NOLOCK)
            LEFT JOIN TM_DnhaPart_And_SupplierPart_Mapping pm WITH (NOLOCK)
                ON pm.SupplierPart = kp.SupplierPartNo
                AND pm.SupplierCode = kp.SupplierCode
            LEFT JOIN TM_SUPPLIER_MASTER sm WITH (NOLOCK)
                ON sm.VNDNR = kp.SupplierCode
            WHERE kp.Barcode = ?
            ORDER BY kp.PrintedOn DESC
            """,
            barcode,
        )

        if cursor.description is not None:
            row = cursor.fetchone()
            if row is not None:
                return _row_to_dict(cursor, row)
        return None
    finally:
        conn.close()
