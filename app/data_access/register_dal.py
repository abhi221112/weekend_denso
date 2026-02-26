"""
Repository layer – calls SP [dbo].[PRC_UserSupplier_EndUser]
for user/supervisor registration (INSERT, UPDATE, DELETE, SELECT).
"""

from app.utils.database import get_db_connection
from app.utils.password_utils import hash_password
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _row_to_dict(cursor, row):
    """Convert a pyodbc Row to a plain dict using cursor.description."""
    if row is None:
        return None
    columns = [col[0] for col in cursor.description]
    return dict(zip(columns, row))


def _rows_to_list(cursor, rows):
    """Convert multiple pyodbc Rows to a list of dicts."""
    if not rows:
        return []
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in rows]


def _fetch_sp_result(cursor):
    """
    After executing an SP that does INSERT/UPDATE/DELETE followed by
    SELECT 'Y' AS RESULT, pyodbc may see the DML row-count as the
    first result-set. Skip forward with nextset() until we find a
    result-set that has rows (cursor.description is not None).
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
# 1.  INSERT – Register a new user or supervisor
# ─────────────────────────────────────────────────────────────────
def register_user(
    user_id: str,
    user_name: str,
    password: str,
    supplier_plant_code: str,
    supplier_code: str,
    group_id: int,
    created_by: str,
    denso_plant: str = None,
    packing_station: str = None,
    email_id: str = None,
    supplier_mac_id: str = None,
) -> dict | None:
    """
    Calls SP with @Type = 'INSERT'.
    Inserts a new row into TM_Supplier_End_User.
    Returns {'RESULT': 'Y'} on success, or error message if user exists.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        logger.info("DAL: register_user for user_id=%s", user_id)
        cursor.execute(
            """
            SET NOCOUNT ON;
            EXEC [dbo].[PRC_UserSupplier_EndUser]
                @Type               = 'INSERT',
                @UserID             = ?,
                @UserName           = ?,
                @Password           = ?,
                @SupplierPlantCode  = ?,
                @SupplierCode       = ?,
                @GroupID            = ?,
                @CreatedBy          = ?,
                @DensoPlant         = ?,
                @PackingStation     = ?,
                @EmailId            = ?,
                @SupplierMacID      = ?
            """,
            user_id,
            user_name,
            hash_password(password),
            supplier_plant_code,
            supplier_code,
            group_id,
            created_by,
            denso_plant or "",
            packing_station or "",
            email_id or "",
            supplier_mac_id or "",
        )
        result = _fetch_sp_result(cursor)
        conn.commit()

        # The SP's INSERT ignores @SupplierCode (reads from a mapping
        # table instead) and omits EmailId entirely.  Patch both with
        # a direct UPDATE so the values supplied by the caller are
        # actually persisted.
        if result and result.get("RESULT") == "Y":
            cursor.execute(
                """
                UPDATE TM_Supplier_End_User
                   SET SupplierCode = ?,
                       EmailId      = ?
                 WHERE UserID = ?
                """,
                supplier_code or "",
                email_id or "",
                user_id,
            )
            conn.commit()

        return result
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────
# 2.  UPDATE – Update an existing user
# ─────────────────────────────────────────────────────────────────
def update_user(
    user_id: str,
    user_name: str,
    password: str,
    supplier_plant_code: str,
    supplier_code: str,
    group_id: int,
    created_by: str,
    email_id: str = None,
) -> dict | None:
    """
    Calls SP with @Type = 'UPDATE'.
    Updates the user row in TM_Supplier_End_User.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        logger.info("DAL: update_user for user_id=%s", user_id)
        cursor.execute(
            """
            SET NOCOUNT ON;
            EXEC [dbo].[PRC_UserSupplier_EndUser]
                @Type               = 'UPDATE',
                @UserID             = ?,
                @UserName           = ?,
                @Password           = ?,
                @SupplierPlantCode  = ?,
                @SupplierCode       = ?,
                @GroupID            = ?,
                @CreatedBy          = ?,
                @EmailId            = ?
            """,
            user_id,
            user_name,
            hash_password(password),
            supplier_plant_code,
            supplier_code,
            group_id,
            created_by,
            email_id or "",
        )
        result = _fetch_sp_result(cursor)
        conn.commit()

        # SP UPDATE also overrides SupplierCode from mapping table.
        # Patch with the caller's value.
        if result and result.get("RESULT") == "Y" and supplier_code:
            cursor.execute(
                """
                UPDATE TM_Supplier_End_User
                   SET SupplierCode = ?
                 WHERE UserID = ?
                """,
                supplier_code,
                user_id,
            )
            conn.commit()

        return result
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────
# 3.  DELETE – Remove a user
# ─────────────────────────────────────────────────────────────────
def delete_user(user_id: str) -> dict | None:
    """
    Calls SP with @Type = 'DELETE'.
    Deletes user from TM_Supplier_End_User.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        logger.info("DAL: delete_user for user_id=%s", user_id)
        cursor.execute(
            """
            SET NOCOUNT ON;
            EXEC [dbo].[PRC_UserSupplier_EndUser]
                @Type   = 'DELETE',
                @UserID = ?
            """,
            user_id,
        )
        result = _fetch_sp_result(cursor)
        conn.commit()
        return result
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────
# 4.  SELECT – Get all users (for admin listing)
# ─────────────────────────────────────────────────────────────────
def get_all_users(created_by: str) -> list[dict]:
    """
    Calls SP with @Type = 'SELECT'.
    Returns all users created by the given admin/supervisor.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        logger.info("DAL: get_all_users (created_by=%s)", created_by)
        cursor.execute(
            """
            EXEC [dbo].[PRC_UserSupplier_EndUser]
                @Type       = 'SELECT',
                @CreatedBy  = ?
            """,
            created_by,
        )
        rows = cursor.fetchall()
        return _rows_to_list(cursor, rows)
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────
# 5.  SELECT_GROUP – Get available groups (User, Supervisor, TL)
# ─────────────────────────────────────────────────────────────────
def get_user_groups() -> list[dict]:
    """
    Calls SP with @Type = 'SELECT_GROUP'.
    Returns available GroupID/GroupName pairs.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        logger.info("DAL: get_user_groups")
        cursor.execute(
            """
            EXEC [dbo].[PRC_UserSupplier_EndUser]
                @Type = 'SELECT_GROUP'
            """
        )
        rows = cursor.fetchall()
        return _rows_to_list(cursor, rows)
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────
# 6.  Get_Plant – Get available plant codes
# ─────────────────────────────────────────────────────────────────
def get_plants(created_by: str) -> list[dict]:
    """
    Calls SP with @Type = 'Get_Plant'.
    Returns available PlantCode/PlantName pairs.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        logger.info("DAL: get_plants (created_by=%s)", created_by)
        cursor.execute(
            """
            EXEC [dbo].[PRC_UserSupplier_EndUser]
                @Type       = 'Get_Plant',
                @CreatedBy  = ?
            """,
            created_by,
        )
        rows = cursor.fetchall()
        return _rows_to_list(cursor, rows)
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────
# 7.  Get_Packing_Station – Get stations for a plant
# ─────────────────────────────────────────────────────────────────
def get_packing_stations(plant_code: str, supplier_code: str) -> list[dict]:
    """
    Calls SP with @Type = 'Get_Packing_Station'.
    Returns available packing stations for the given plant.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        logger.info("DAL: get_packing_stations for plant=%s", plant_code)
        cursor.execute(
            """
            EXEC [dbo].[PRC_UserSupplier_EndUser]
                @Type               = 'Get_Packing_Station',
                @SupplierPlantCode  = ?,
                @SupplierCode       = ?
            """,
            plant_code,
            supplier_code,
        )
        rows = cursor.fetchall()
        return _rows_to_list(cursor, rows)
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────
# 8.  UPDATEPASSWORD – Change user password
# ─────────────────────────────────────────────────────────────────
def change_password(user_id: str, old_password: str, new_password: str) -> dict | None:
    """
    Calls SP with @Type = 'UPDATEPASSWORD'.
    Verifies old password, sets new password (both hashed).
    Returns {'RESULT': 'Y'} on success, or error message.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        logger.info("DAL: change_password for user_id=%s", user_id)
        cursor.execute(
            """
            SET NOCOUNT ON;
            EXEC [dbo].[PRC_UserSupplier_EndUser]
                @Type         = 'UPDATEPASSWORD',
                @UserID       = ?,
                @Password     = ?,
                @NewPassword  = ?
            """,
            user_id,
            hash_password(old_password),
            hash_password(new_password),
        )
        result = _fetch_sp_result(cursor)
        conn.commit()
        return result
    finally:
        conn.close()
