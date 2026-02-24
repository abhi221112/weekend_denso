"""
Repository layer – validation queries for the Traceability Tag Print flow.

The SP [dbo].[PRC_UserSupplier_EndUser] has structural bugs in the
VALIDATEUSER_PC / VALIDATEUSER / VALIDATE_DEVICE_SUPERVISOR paths:
  - A dangling BEGIN/END block always returns 'N' regardless of outcome.
  - INNER JOINs to TM_Supplier_Plant cause 0-row results when plant
    data is not fully configured for the user.

To avoid these issues the three login helpers execute direct SQL with
LEFT JOINs, replicating the SP logic without the bugs.
"""

from app.utils.database import get_db_connection
from app.utils.password_utils import hash_password


def _row_to_dict(cursor, row):
    """Convert a pyodbc Row to a plain dict using cursor.description."""
    if row is None:
        return None
    columns = [col[0] for col in cursor.description]
    return dict(zip(columns, row))


def _fetch_sp_result(cursor):
    """
    The SPs often do INSERT/UPDATE followed by SELECT, or have
    multiple SELECT statements (some may return 0 rows).  Skip
    forward through result-sets until we find one with actual data.
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
# 1.  VALIDATEUSER_PC  –  initial app login
# ─────────────────────────────────────────────────────────────────
def validate_user_pc(user_id: str, password: str) -> dict | None:
    """
    Replaces SP @Type = 'VALIDATEUSER_PC'.

    Logic:
      1. Check TM_Supplier_UserMaster (admin / IsSupplier='Y') first.
         If found, verify they have a TM_SuppUser_SuppCode_Mapping row.
      2. Otherwise check TM_Supplier_End_User.
         Uses LEFT JOIN to TM_Supplier_Plant so login succeeds even
         when plant mapping is not configured yet.
    """
    hashed_pwd = hash_password(password)
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # ── Path 1: Supplier-admin users ─────────────────────────
        cursor.execute(
            """
            SELECT 'Y' AS RESULT,
                   um.UserID, um.USERNAME, um.PASSWORD, um.EmailId,
                   um.GroupID, gm.GroupName, um.IsSupplier,
                   '' AS SupplierCode, '' AS DensoPlant,
                   '' AS SupplierPlantCode, '' AS PackingStation,
                   '' AS PlantName
            FROM TM_Supplier_UserMaster um WITH (NOLOCK)
            INNER JOIN TM_Group gm ON um.GroupID = gm.GroupID
            WHERE um.UserID = ?
              AND um.Password = ?
              AND ISNULL(um.IsSupplier, '') = 'Y'
            """,
            user_id,
            hashed_pwd,
        )
        row = cursor.fetchone()
        if row:
            # Must also have a supplier-code mapping
            cur2 = conn.cursor()
            cur2.execute(
                "SELECT 1 FROM TM_SuppUser_SuppCode_Mapping WHERE UserID = ?",
                user_id,
            )
            if cur2.fetchone():
                return _row_to_dict(cursor, row)
            return {"RESULT": "N", "MSG": "No User mapped with supplier"}

        # ── Path 2: End users (LEFT JOIN to plant table) ─────────
        cursor.execute(
            """
            SELECT TOP 1
                   'Y' AS RESULT,
                   um.UserID, um.USERNAME, um.PASSWORD, um.EmailId,
                   um.GroupID, gm.GroupName,
                   'N' AS IsSupplier,
                   um.SupplierCode, um.DensoPlant,
                   um.SupplierPlantCode, um.PackingStation,
                   ISNULL(P.PlantName, '') AS PlantName
            FROM TM_Supplier_End_User um WITH (NOLOCK)
            INNER JOIN TM_Supplier_GROUP gm ON um.GroupID = gm.GroupID
            LEFT JOIN (
                SELECT DISTINCT PlantCode, PlantName, SupplierCode
                FROM TM_Supplier_Plant
            ) P ON P.PlantCode = um.SupplierPlantCode
                AND (
                    ',' + LTRIM(RTRIM(um.SupplierCode)) + ','
                    LIKE '%,' + LTRIM(RTRIM(P.SupplierCode)) + ',%'
                )
            WHERE um.UserID = ?
              AND um.Password = ?
            """,
            user_id,
            hashed_pwd,
        )
        row = cursor.fetchone()
        if row:
            return _row_to_dict(cursor, row)

        return None
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────
# 2.  VALIDATEUSER  –  traceability tag screen auto-fill
# ─────────────────────────────────────────────────────────────────
def validate_user(user_id: str, password: str) -> dict | None:
    """
    Replaces SP @Type = 'VALIDATEUSER'.
    Returns user row with Plant, PackingStation etc. for auto-fill.
    Uses LEFT JOIN to TM_Supplier_Plant so it works even when
    plant data is not fully configured.
    """
    hashed_pwd = hash_password(password)
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # Check group rights first
        cursor.execute(
            """
            SET NOCOUNT ON;

            DECLARE @gID varchar(20), @gName varchar(100);
            SELECT @gID = GroupID
            FROM TM_Supplier_End_User
            WHERE UserID = ? AND Password = ?;
            SELECT @gName = GroupName
            FROM TM_Supplier_GROUP
            WHERE GroupID = @gID;

            IF EXISTS (
                SELECT 1 FROM TM_Supplier_GROUP_RIGHTS
                WHERE GroupID = @gName AND [View] = 1
                  AND ScreenId IN ('3001','2003')
            )
            BEGIN
                SELECT TOP 1
                       um.SupplierCode,
                       um.SupplierPlantCode,
                       ISNULL(um.PackingStation, '') AS PackingStation,
                       um.UserID, um.USERNAME,
                       ISNULL(P.PlantName, '') AS PASSWORD,
                       um.EmailId, um.GroupID, gm.GroupName,
                       um.CreatedBy,
                       CONVERT(varchar(10), um.CreatedOn, 103) AS CreatedOn
                FROM TM_Supplier_End_User um WITH (NOLOCK)
                INNER JOIN TM_Supplier_GROUP gm ON um.GroupID = gm.GroupID
                LEFT JOIN (
                    SELECT DISTINCT PlantCode, PlantName
                    FROM TM_Supplier_Plant
                ) P ON P.PlantCode = um.SupplierPlantCode
                WHERE um.UserID = ? AND um.Password = ?
            END
            """,
            user_id,
            hashed_pwd,
            user_id,
            hashed_pwd,
        )
        result = _fetch_sp_result(cursor)
        if result is None:
            return None
        return result
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────
# 3.  VALIDATE_DEVICE_SUPERVISOR  –  supervisor auth for model change
# ─────────────────────────────────────────────────────────────────
def validate_device_supervisor(user_id: str, password: str) -> dict | None:
    """
    Replaces SP @Type = 'VALIDATE_DEVICE_SUPERVISOR'.
    Returns supervisor info if credentials are valid and user has rights.
    Uses LEFT JOIN to TM_Supplier_Plant.
    """
    hashed_pwd = hash_password(password)
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SET NOCOUNT ON;

            DECLARE @gID1 varchar(20), @gName1 varchar(100);
            SELECT @gID1 = GroupID
            FROM TM_Supplier_End_User
            WHERE UserID = ? AND Password = ?;
            SELECT @gName1 = GroupName
            FROM TM_Supplier_GROUP
            WHERE GroupID = @gID1;

            IF EXISTS (
                SELECT 1 FROM TM_Supplier_GROUP_RIGHTS
                WHERE GroupID = @gName1 AND [View] = 1
                  AND ScreenId IN ('3002','2003')
            )
            BEGIN
                SELECT TOP 1
                       ISNULL(um.SupplierCode, '') AS SupplierCode,
                       um.SupplierPlantCode,
                       um.PackingStation,
                       um.UserID, um.USERNAME,
                       ISNULL(P.PlantName, '') AS PlantName,
                       um.EmailId, um.GroupID, gm.GroupName,
                       um.CreatedBy,
                       CONVERT(varchar(10), um.CreatedOn, 103) AS CreatedOn
                FROM TM_Supplier_End_User um WITH (NOLOCK)
                INNER JOIN TM_Supplier_GROUP gm ON um.GroupID = gm.GroupID
                LEFT JOIN (
                    SELECT DISTINCT PlantCode, PlantName
                    FROM TM_Supplier_Plant
                ) P ON P.PlantCode = um.SupplierPlantCode
                WHERE um.UserID = ? AND um.Password = ?
            END
            """,
            user_id,
            hashed_pwd,
            user_id,
            hashed_pwd,
        )
        result = _fetch_sp_result(cursor)
        if result is None:
            return None
        return result
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────
# 4a.  GET_SUPPLIERPART  –  model dropdown list (after supervisor login)
# ─────────────────────────────────────────────────────────────────
def get_supplier_parts(
    station_no: str,
    plant_code: str,
    printed_by: str,
) -> list[dict] | None:
    """
    Calls PRC_PrintKanban SP with @Type = 'GET_SUPPLIERPART'.
    Returns list of SupplierPart numbers for the Model Change dropdown.
    Parameters match the SP: @StationNo, @PlantCode, @PrintedBy (logged-in user).
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SET NOCOUNT ON;
            EXEC [dbo].[PRC_PrintKanban]
                @Type       = 'GET_SUPPLIERPART',
                @StationNo  = ?,
                @PlantCode  = ?,
                @PrintedBy  = ?
            """,
            station_no,
            plant_code,
            printed_by,
        )
        rows = cursor.fetchall()
        if not rows:
            return None
        return [_row_to_dict(cursor, row) for row in rows]
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────
# 4b.  GET_PRINT_PARAMETER  –  auto-fill after model selection
# ─────────────────────────────────────────────────────────────────
def get_print_parameter(
    supplier_part_no: str,
    supplier_code: str,
    plant_code: str,
    station_no: str,
) -> list[dict] | None:
    """
    Calls PRC_PrintKanban SP with @Type = 'GET_PRINT_PARAMETER'.
    Returns full part details for auto-filling the form after
    the supervisor selects a SupplierPart from the dropdown.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SET NOCOUNT ON;
            EXEC [dbo].[PRC_PrintKanban]
                @Type            = 'GET_PRINT_PARAMETER',
                @SupplierPartNo  = ?,
                @SupplierCode    = ?,
                @PlantCode       = ?,
                @StationNo       = ?
            """,
            supplier_part_no,
            supplier_code,
            plant_code,
            station_no,
        )
        rows = cursor.fetchall()
        if not rows:
            return None
        return [_row_to_dict(cursor, row) for row in rows]
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────
# 5.  GET_SHIFT  –  fetch current shift
# ─────────────────────────────────────────────────────────────────
def get_shift(supplier_code: str) -> dict | None:
    """
    Calls PRC_PrintKanban SP with @Type = 'GET_SHIFT'.
    Returns current shift information (Shift, ShiftFrom, ShiftTo).
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            EXEC [dbo].[PRC_PrintKanban]
                @Type            = 'GET_SHIFT',
                @SupplierCode    = ?
            """,
            supplier_code,
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return _row_to_dict(cursor, row)
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────
# 6.  Lock/Unlock Field State Management
# ─────────────────────────────────────────────────────────────────

# In-memory storage for field lock states (keyed by supplier_part_no)
_field_lock_states = {}


def get_lot_lock_type(supplier_part_no: str) -> str | None:
    """
    Query TM_Supplier_Lot_Structure to get the LotLockType for a
    given SupplierPart.  Returns 'Enable', 'Disable', or 'STANDARD'.
    The SP GET_PRINT_PARAMETER joins on both SupplierCode and
    SupplierPart; here we only need the SupplierPart to look it up.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT TOP 1 ISNULL(LotLockType, 'Enable') AS LotLockType
            FROM TM_Supplier_Lot_Structure
            WHERE SupplierPart = ?
            """,
            supplier_part_no,
        )
        row = cursor.fetchone()
        if row:
            return row[0]
        return None
    finally:
        conn.close()


def lock_fields(
    supplier_part_no: str,
    supplier_code: str,
    plant_code: str,
    station_no: str,
) -> tuple[bool, str | None]:
    """
    Lock fields to make them read-only.
    First checks LotLockType from DB:
      - 'Disable' → lock is not allowed, return (False, 'Disable')
      - 'Enable' / 'STANDARD' → lock is allowed
    Returns (success: bool, lot_lock_type: str).
    """
    lot_lock_type = get_lot_lock_type(supplier_part_no)

    if lot_lock_type is None:
        return False, None

    if lot_lock_type == "Disable":
        return False, lot_lock_type

    lock_key = f"{supplier_part_no}:{supplier_code}:{plant_code}:{station_no}"
    _field_lock_states[lock_key] = {
        "locked": True,
        "locked_at": str(__import__("datetime").datetime.now()),
        "lot_lock_type": lot_lock_type,
    }
    return True, lot_lock_type


def unlock_fields(
    supplier_part_no: str,
    supplier_code: str,
    plant_code: str,
    station_no: str,
) -> bool:
    """
    Unlock fields to make them editable.
    Returns True if successfully unlocked.
    """
    lock_key = f"{supplier_part_no}:{supplier_code}:{plant_code}:{station_no}"
    if lock_key in _field_lock_states:
        del _field_lock_states[lock_key]
    return True


def is_fields_locked(
    supplier_part_no: str,
    supplier_code: str,
    plant_code: str,
    station_no: str,
) -> bool:
    """
    Check if fields are currently locked.
    Returns True if locked, False if unlocked.
    """
    lock_key = f"{supplier_part_no}:{supplier_code}:{plant_code}:{station_no}"
    return lock_key in _field_lock_states and _field_lock_states[lock_key].get("locked", False)
