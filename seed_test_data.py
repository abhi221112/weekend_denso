"""
Seed script – inserts dummy data into the local SQL Server so that
every API endpoint can be tested end-to-end.

Run once:  python seed_test_data.py

Tables populated:
  1. TM_Supplier_GROUP             – EOL User, Supervisor, TL
  2. TM_Supplier_GROUP_RIGHTS      – Screen permissions per group
  3. TM_Supplier_Plant             – PLT01 / PLT02 plants
  4. TM_Supplier_Plant_Station_Mapping – Packing stations
  5. TM_SuppUser_SuppCode_Mapping  – Admin user ↔ supplier-code link
  6. TM_Supplier_UserMaster        – Admin / supervisor (IsSupplier='Y')
  7. tbShiftMaster                 – Shift definitions
  8. TM_Supplier_End_User          – Cleaned up (old test rows removed)

After running this script you can:
  • POST /api/register/groups   → see 3 groups
  • POST /api/register/plants   → see 2 plants
  • POST /api/register/stations → see stations for PLT01/SUP001
  • POST /api/register/user     → register a user
  • POST /api/traceability/login → login with that user
"""

import sys, os

# Add project root so we can import app.utils
sys.path.insert(0, os.path.dirname(__file__))

from app.utils.database import get_db_connection
from app.utils.password_utils import hash_password


def run_sql(cursor, sql, params=None):
    """Execute a statement, ignoring duplicate-key errors."""
    try:
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
    except Exception as e:
        msg = str(e)
        # Ignore duplicate key / already exists
        if "2627" in msg or "2601" in msg or "already exists" in msg.lower():
            print(f"  (skipped – already exists)")
        else:
            raise


def seed():
    conn = get_db_connection()
    cursor = conn.cursor()

    print("=" * 60)
    print("  SEEDING TEST DATA INTO DTraceProddb")
    print("=" * 60)

    # ── 1. Groups ────────────────────────────────────────────────
    print("\n[1/8] TM_Supplier_GROUP ...")
    groups = [
        ("SUP001", "EOL User",    1),
        ("SUP001", "Supervisor",  1),
        ("SUP001", "TL",          1),
    ]
    for sc, gname, active in groups:
        run_sql(cursor, """
            SET IDENTITY_INSERT TM_Supplier_GROUP OFF;
            IF NOT EXISTS (SELECT 1 FROM TM_Supplier_GROUP WHERE GroupName = ?)
            BEGIN
                INSERT INTO TM_Supplier_GROUP (SupplierCode, GroupName, IsActive, CreatedOn, CreatedBy)
                VALUES (?, ?, ?, GETDATE(), 'SEED')
            END
        """, (gname, sc, gname, active))
        print(f"  + {gname}")
    conn.commit()

    # Fetch the generated GroupIDs for later use
    cursor.execute("SELECT GroupID, GroupName FROM TM_Supplier_GROUP")
    group_map = {}
    for row in cursor.fetchall():
        group_map[row[1]] = row[0]
    print(f"  Group IDs: {group_map}")

    # ── 2. Group Rights ──────────────────────────────────────────
    print("\n[2/8] TM_Supplier_GROUP_RIGHTS ...")
    # ScreenIds: 2002=User Admin, 2003=Common, 3001=Tag Print, 3002=Model Change
    screen_rights = []
    # EOL User  → View on 3001, 2003
    eol_name = "EOL User"
    sup_name = "Supervisor"
    tl_name  = "TL"
    for gname in [eol_name, sup_name, tl_name]:
        for sid in [2002, 2003, 3001, 3002]:
            can_view = 1
            screen_rights.append(("SUP001", gname, sid, can_view))

    for sc, gid_str, sid, v in screen_rights:
        run_sql(cursor, """
            IF NOT EXISTS (
                SELECT 1 FROM TM_Supplier_GROUP_RIGHTS
                WHERE GroupID = ? AND ScreenId = ? AND SupplierCode = ?
            )
            BEGIN
                INSERT INTO TM_Supplier_GROUP_RIGHTS
                    (SupplierCode, GroupID, ScreenId, [View], [Add], [Update], [Delete], CreatedOn, CreatedBy)
                VALUES (?, ?, ?, ?, 1, 1, 1, GETDATE(), 'SEED')
            END
        """, (gid_str, sid, sc,   sc, gid_str, sid, v))
        print(f"  + {gid_str} screen {sid}")
    conn.commit()

    # ── 3. Plants ────────────────────────────────────────────────
    print("\n[3/8] TM_Supplier_Plant ...")
    plants = [
        ("PLT01", "SUP001", "Plant 01 - Noida"),
        ("PLT01", "SUP002", "Plant 01 - Noida"),
        ("PLT02", "SUP001", "Plant 02 - Gurgaon"),
        ("PLT02", "SUP003", "Plant 02 - Gurgaon"),
    ]
    for pc, sc, pn in plants:
        run_sql(cursor, """
            IF NOT EXISTS (SELECT 1 FROM TM_Supplier_Plant WHERE PlantCode = ? AND SupplierCode = ?)
            BEGIN
                INSERT INTO TM_Supplier_Plant (PlantCode, SupplierCode, PlantName, CreatedOn, CreatedBy)
                VALUES (?, ?, ?, GETDATE(), 'SEED')
            END
        """, (pc, sc,   pc, sc, pn))
        print(f"  + {pc} / {sc} → {pn}")
    conn.commit()

    # ── 4. Packing Stations ──────────────────────────────────────
    print("\n[4/8] TM_Supplier_Plant_Station_Mapping ...")
    stations = [
        ("DENSO", "SUP001", "PLT01", "STN01"),
        ("DENSO", "SUP001", "PLT01", "STN02"),
        ("DENSO", "SUP001", "PLT01", "STN03"),
        ("DENSO", "SUP002", "PLT01", "STN01"),
        ("DENSO", "SUP001", "PLT02", "STN01"),
        ("DENSO", "SUP001", "PLT02", "STN02"),
    ]
    for ct, sc, pc, stn in stations:
        run_sql(cursor, """
            IF NOT EXISTS (
                SELECT 1 FROM TM_Supplier_Plant_Station_Mapping
                WHERE PlantCode = ? AND SupplierCode = ? AND StationNo = ?
            )
            BEGIN
                INSERT INTO TM_Supplier_Plant_Station_Mapping
                    (CustomerType, SupplierCode, PlantCode, StationNo, CreatedOn, CreatedBy)
                VALUES (?, ?, ?, ?, GETDATE(), 'SEED')
            END
        """, (pc, sc, stn,   ct, sc, pc, stn))
        print(f"  + {pc}/{sc} station {stn}")
    conn.commit()

    # ── 5. Admin user → supplier-code mapping ────────────────────
    print("\n[5/8] TM_SuppUser_SuppCode_Mapping ...")
    mappings = [
        ("SUP001", "admin01", "PLT01"),
        ("SUP002", "admin01", "PLT01"),
        ("SUP001", "admin01", "PLT02"),
    ]
    for sc, uid, pc in mappings:
        run_sql(cursor, """
            IF NOT EXISTS (
                SELECT 1 FROM TM_SuppUser_SuppCode_Mapping
                WHERE SupplierCode = ? AND UserID = ? AND PlantCode = ?
            )
            BEGIN
                INSERT INTO TM_SuppUser_SuppCode_Mapping
                    (SupplierCode, UserID, PlantCode, CreatedOn, CreatedBy)
                VALUES (?, ?, ?, GETDATE(), 'SEED')
            END
        """, (sc, uid, pc,   sc, uid, pc))
        print(f"  + {uid} → {sc} @ {pc}")
    conn.commit()

    # ── 6. Admin / Supplier UserMaster ───────────────────────────
    print("\n[6/8] TM_Supplier_UserMaster ...")
    admin_pwd = hash_password("admin@123")
    run_sql(cursor, """
        IF NOT EXISTS (SELECT 1 FROM TM_Supplier_UserMaster WHERE UserID = 'admin01')
        BEGIN
            INSERT INTO TM_Supplier_UserMaster
                (SupplierCode, UserID, UserName, Password, GroupID, IsActive,
                 IsSupplier, CreatedOn, CreatedBy)
            VALUES ('SUP001', 'admin01', 'Admin User', ?, 1, 1,
                    'Y', GETDATE(), 'SEED')
        END
    """, (admin_pwd,))
    print(f"  + admin01 (password: admin@123)")
    conn.commit()

    # ── 7. Shift Master ──────────────────────────────────────────
    print("\n[7/8] tbShiftMaster ...")
    shifts = [
        ("SUP001", "A", "A", "06:00", "14:00"),
        ("SUP001", "B", "B", "14:00", "22:00"),
        ("SUP001", "C", "C", "22:00", "06:00"),
    ]
    for sc, scode, sname, sfrom, sto in shifts:
        run_sql(cursor, """
            IF NOT EXISTS (
                SELECT 1 FROM tbShiftMaster WHERE SupplierCode = ? AND ShiftName = ?
            )
            BEGIN
                INSERT INTO tbShiftMaster
                    (SupplierCode, ShiftCode, ShiftName, ShiftFrom, ShiftTo, CreatedBy, CreatedOn)
                VALUES (?, ?, ?, ?, ?, 'SEED', GETDATE())
            END
        """, (sc, sname,   sc, scode, sname, sfrom, sto))
        print(f"  + {sc} shift {sname} ({sfrom} - {sto})")
    conn.commit()

    # ── 8. Clean up old test end-users ───────────────────────────
    print("\n[8/8] Cleaning old test end-users ...")
    cursor.execute("""
        DELETE FROM TM_Supplier_End_User
        WHERE UserID IN ('aaa01', 'test01', 'final01')
    """)
    deleted = cursor.rowcount
    conn.commit()
    print(f"  Removed {deleted} old test row(s)")

    # ── Summary ──────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  SEED COMPLETE!")
    print("=" * 60)
    print("""
You can now test the full flow:

1. GET  /api/register/groups
   → Returns: EOL User, Supervisor, TL (with GroupIDs)

2. GET  /api/register/plants?created_by=admin01
   → Returns: PLT01, PLT02

3. GET  /api/register/stations?plant_code=PLT01&supplier_code=SUP001
   → Returns: STN01, STN02, STN03

4. POST /api/register/user
   {
     "user_id": "testuser01",
     "user_name": "Test User",
     "password": "pass@123",
     "supplier_plant_code": "PLT01",
     "supplier_code": "SUP001",
     "denso_plant": "DENSO",
     "packing_station": "STN01",
     "group_id": """ + str(group_map.get("EOL User", 1)) + """,
     "email_id": "test@example.com",
     "created_by": "admin01"
   }

5. POST /api/traceability/login
   { "user_id": "testuser01", "password": "pass@123" }
   → Should return success with user data

6. POST /api/traceability/login  (admin user)
   { "user_id": "admin01", "password": "admin@123" }
   → Should return success with IsSupplier='Y'
""")

    conn.close()


if __name__ == "__main__":
    seed()
