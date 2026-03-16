"""
Comprehensive seed script – populates ALL tables required to test
every API endpoint end-to-end with the existing DEMO_USER account.

DEMO_USER config (from login response):
  user_id        = DEMO_USER
  supplier_code  = DEMO
  plant_code     = DM1  (SupplierPlantCode)
  packing_station= Station-1
  group_id       = 5  (EOL User)

Run once:  python seed_all_data.py

Tables populated:
  1.  TM_Supplier_GROUP               – Groups for DEMO supplier
  2.  TM_Supplier_GROUP_RIGHTS        – Screen permissions
  3.  TM_Group                        – Global groups (for admin login path)
  4.  TM_Supplier_Plant               – Plants for DEMO
  5.  TM_Supplier_Plant_Station_Mapping – Stations
  6.  TM_SuppUser_SuppCode_Mapping    – Admin user ↔ supplier mapping
  7.  TM_Supplier_UserMaster          – Admin user (IsSupplier='Y')
  8.  tbShiftMaster                   – Shifts for DEMO
  9.  TM_SUPPLIER_MASTER              – Supplier name (VNDNR/VNAME)
  10. TM_Company                      – Company master
  11. TM_Item_Master_A                – Denso parts (description)
  12. TM_Item_Master_B                – Denso parts (lot size)
  13. TM_DensoPart_And_SupplierCode_Mapping – Denso ↔ supplier link
  14. TM_DnhaPart_And_SupplierPart_Mapping  – Supplier part details
  15. TM_Supplier_Station_Part_Mapping      – Parts at each station
  16. TM_Supplier_Lot_Structure             – Lot structure config
  17. TT_Kanban_Print                 – Sample printed tags (for scan, reprint, etc.)
  18. TM_Supplier_End_User            – Supervisor user for reprint/unlock
  19. TM_Print_Prn                    – (table exists; print-prn inserts here)

After running you can test ALL endpoints with DEMO_USER's access_token.
"""

import sys
import os
from datetime import datetime, timedelta

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
        if "2627" in msg or "2601" in msg or "already exists" in msg.lower():
            print(f"  (skipped - already exists)")
        else:
            raise


def seed():
    conn = get_db_connection()
    cursor = conn.cursor()

    print("=" * 70)
    print("  COMPREHENSIVE SEED: All data for DEMO_USER testing")
    print("=" * 70)

    # ════════════════════════════════════════════════════════════════
    # 1. TM_Supplier_GROUP - Groups for DEMO supplier
    # ════════════════════════════════════════════════════════════════
    print("\n[1/18] TM_Supplier_GROUP ...")
    groups = [
        ("DEMO", "EOL User",    1),
        ("DEMO", "Supervisor",  1),
        ("DEMO", "TL",          1),
    ]
    for sc, gname, active in groups:
        run_sql(cursor, """
            IF NOT EXISTS (SELECT 1 FROM TM_Supplier_GROUP WHERE GroupName = ? AND SupplierCode = ?)
            BEGIN
                INSERT INTO TM_Supplier_GROUP (SupplierCode, GroupName, IsActive, CreatedOn, CreatedBy)
                VALUES (?, ?, ?, GETDATE(), 'SEED')
            END
        """, (gname, sc, sc, gname, active))
        print(f"  + {sc}/{gname}")
    conn.commit()

    # Fetch GroupIDs - search across all supplier codes since groups may exist under different codes
    cursor.execute("SELECT GroupID, GroupName FROM TM_Supplier_GROUP WHERE GroupName IN ('EOL User', 'Supervisor', 'TL')")
    group_map = {}
    for row in cursor.fetchall():
        group_map[row[1]] = row[0]
    print(f"  Group IDs: {group_map}")

    eol_group_id = group_map.get("EOL User", 5)
    sup_group_id = group_map.get("Supervisor", 6)
    tl_group_id  = group_map.get("TL", 7)

    # ════════════════════════════════════════════════════════════════
    # 2. TM_Supplier_GROUP_RIGHTS - Screen permissions
    # ════════════════════════════════════════════════════════════════
    print("\n[2/18] TM_Supplier_GROUP_RIGHTS ...")
    # ScreenIds: 2002=User Admin, 2003=Common, 3001=Tag Print, 3002=Model Change
    for gname in ["EOL User", "Supervisor", "TL"]:
        for sid in [2002, 2003, 3001, 3002]:
            run_sql(cursor, """
                IF NOT EXISTS (
                    SELECT 1 FROM TM_Supplier_GROUP_RIGHTS
                    WHERE GroupID = ? AND ScreenId = ? AND SupplierCode = ?
                )
                BEGIN
                    INSERT INTO TM_Supplier_GROUP_RIGHTS
                        (SupplierCode, GroupID, ScreenId, [View], [Add], [Update], [Delete], CreatedOn, CreatedBy)
                    VALUES (?, ?, ?, 1, 1, 1, 1, GETDATE(), 'SEED')
                END
            """, (gname, sid, "DEMO",  "DEMO", gname, sid))
            print(f"  + DEMO/{gname} screen {sid}")
    conn.commit()

    # ════════════════════════════════════════════════════════════════
    # 3. TM_Group - Global groups (used by admin login path 1)
    # ════════════════════════════════════════════════════════════════
    print("\n[3/18] TM_Group ...")
    global_groups = [
        (1, "Admin"),
        (2, "Supervisor"),
        (3, "User"),
    ]
    for gid, gname in global_groups:
        # Check if exists first, then insert separately
        cursor.execute("SELECT 1 FROM TM_Group WHERE GroupID = ?", (gid,))
        if cursor.fetchone() is None:
            try:
                cursor.execute("SET IDENTITY_INSERT TM_Group ON")
                cursor.execute("INSERT INTO TM_Group (GroupID, GroupName) VALUES (?, ?)", (gid, gname))
                cursor.execute("SET IDENTITY_INSERT TM_Group OFF")
                print(f"  + GroupID={gid} ({gname})")
            except Exception as e:
                print(f"  (skipped GroupID={gid}: {e})")
                try:
                    cursor.execute("SET IDENTITY_INSERT TM_Group OFF")
                except:
                    pass
        else:
            print(f"  (exists) GroupID={gid} ({gname})")
    conn.commit()

    # ════════════════════════════════════════════════════════════════
    # 4. TM_Supplier_Plant - Plants for DEMO
    # ════════════════════════════════════════════════════════════════
    print("\n[4/18] TM_Supplier_Plant ...")
    plants = [
        ("DM1", "DEMO", "Demo Plant"),
        ("DM2", "DEMO", "Demo Plant 2"),
    ]
    for pc, sc, pn in plants:
        run_sql(cursor, """
            IF NOT EXISTS (SELECT 1 FROM TM_Supplier_Plant WHERE PlantCode = ? AND SupplierCode = ?)
            BEGIN
                INSERT INTO TM_Supplier_Plant (PlantCode, SupplierCode, PlantName, CreatedOn, CreatedBy)
                VALUES (?, ?, ?, GETDATE(), 'SEED')
            END
        """, (pc, sc, pc, sc, pn))
        print(f"  + {pc}/{sc} -> {pn}")
    conn.commit()

    # ════════════════════════════════════════════════════════════════
    # 5. TM_Supplier_Plant_Station_Mapping - Stations
    # ════════════════════════════════════════════════════════════════
    print("\n[5/18] TM_Supplier_Plant_Station_Mapping ...")
    stations = [
        ("DENSO", "DEMO", "DM1", "Station-1"),
        ("DENSO", "DEMO", "DM1", "Station-2"),
        ("DENSO", "DEMO", "DM1", "Station-3"),
        ("DENSO", "DEMO", "DM2", "Station-1"),
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
        """, (pc, sc, stn, ct, sc, pc, stn))
        print(f"  + {pc}/{sc} station {stn}")
    conn.commit()

    # ════════════════════════════════════════════════════════════════
    # 6. TM_SuppUser_SuppCode_Mapping - Admin user mapping
    # ════════════════════════════════════════════════════════════════
    print("\n[6/18] TM_SuppUser_SuppCode_Mapping ...")
    admin_mappings = [
        ("DEMO", "DEMO_ADMIN", "DM1"),
        ("DEMO", "DEMO_ADMIN", "DM2"),
        ("DEMO", "DEMO_USER",  "DM1"),
    ]
    for sc, uid, pc in admin_mappings:
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
        """, (sc, uid, pc, sc, uid, pc))
        print(f"  + {uid} -> {sc} @ {pc}")
    conn.commit()

    # ════════════════════════════════════════════════════════════════
    # 7. TM_Supplier_UserMaster - Admin user (IsSupplier='Y')
    # ════════════════════════════════════════════════════════════════
    print("\n[7/18] TM_Supplier_UserMaster ...")
    admin_pwd = hash_password("Admin@1234")
    run_sql(cursor, """
        IF NOT EXISTS (SELECT 1 FROM TM_Supplier_UserMaster WHERE UserID = 'DEMO_ADMIN')
        BEGIN
            INSERT INTO TM_Supplier_UserMaster
                (SupplierCode, UserID, UserName, Password, GroupID, IsActive,
                 IsSupplier, EmailId, CreatedOn, CreatedBy)
            VALUES ('DEMO', 'DEMO_ADMIN', 'Demo Admin', ?, 1, 1,
                    'Y', 'demo.admin@test.com', GETDATE(), 'SEED')
        END
    """, (admin_pwd,))
    print(f"  + DEMO_ADMIN (password: Admin@1234)")
    conn.commit()

    # ════════════════════════════════════════════════════════════════
    # 8. tbShiftMaster - Shifts for DEMO
    # ════════════════════════════════════════════════════════════════
    print("\n[8/18] tbShiftMaster ...")
    shifts = [
        ("DEMO", "A", "Morning",   "06:00", "14:00"),
        ("DEMO", "B", "Afternoon", "14:00", "22:00"),
        ("DEMO", "C", "Night",     "22:00", "06:00"),
    ]
    for sc, scode, sname, sfrom, sto in shifts:
        run_sql(cursor, """
            IF NOT EXISTS (
                SELECT 1 FROM tbShiftMaster WHERE SupplierCode = ? AND ShiftCode = ?
            )
            BEGIN
                INSERT INTO tbShiftMaster
                    (SupplierCode, ShiftCode, ShiftName, ShiftFrom, ShiftTo, CreatedBy, CreatedOn)
                VALUES (?, ?, ?, ?, ?, 'SEED', GETDATE())
            END
        """, (sc, scode, sc, scode, sname, sfrom, sto))
        print(f"  + {sc} shift {scode} ({sfrom} - {sto})")
    conn.commit()

    # ════════════════════════════════════════════════════════════════
    # 9. TM_SUPPLIER_MASTER - Supplier name (needed by print/scan)
    # ════════════════════════════════════════════════════════════════
    print("\n[9/18] TM_SUPPLIER_MASTER ...")
    suppliers = [
        ("DEMO",   "Demo Supplier Co."),
        ("SUP001", "Supplier One Pvt Ltd"),
        ("SUP002", "Supplier Two Pvt Ltd"),
    ]
    for vndnr, vname in suppliers:
        run_sql(cursor, """
            IF NOT EXISTS (SELECT 1 FROM TM_SUPPLIER_MASTER WHERE VNDNR = ?)
            BEGIN
                INSERT INTO TM_SUPPLIER_MASTER (VNDNR, VNAME) VALUES (?, ?)
            END
        """, (vndnr, vndnr, vname))
        print(f"  + {vndnr} -> {vname}")
    conn.commit()

    # ════════════════════════════════════════════════════════════════
    # 10. TM_Company - Company master (needed by KANBAN_PRINT SP)
    # ════════════════════════════════════════════════════════════════
    print("\n[10/18] TM_Company ...")
    companies = [
        ("COMP01", "Denso Corporation"),
        ("DEMO",   "Demo Company"),
    ]
    for cc, cn in companies:
        run_sql(cursor, """
            IF NOT EXISTS (SELECT 1 FROM TM_Company WHERE CompanyCode = ?)
            BEGIN
                INSERT INTO TM_Company (CompanyCode, CompanyName) VALUES (?, ?)
            END
        """, (cc, cc, cn))
        print(f"  + {cc} -> {cn}")
    conn.commit()

    # ════════════════════════════════════════════════════════════════
    # 11. TM_Item_Master_A - Denso part descriptions
    # ════════════════════════════════════════════════════════════════
    print("\n[11/18] TM_Item_Master_A ...")
    items_a = [
        ("DEMO", "DNHA-DM-001", "BRACKET ASSEMBLY",   "DM-ENG-001", "PC"),
        ("DEMO", "DNHA-DM-002", "SENSOR HOUSING",     "DM-ENG-002", "PC"),
        ("DEMO", "DNHA-DM-003", "CONNECTOR PLATE",    "DM-ENG-003", "PC"),
        ("DEMO", "DNHA-DM-004", "RELAY MODULE",       "DM-ENG-004", "PC"),
    ]
    for cc, itnbr, itdsc, engno, unmsr in items_a:
        run_sql(cursor, """
            IF NOT EXISTS (SELECT 1 FROM TM_Item_Master_A WHERE ITNBR = ?)
            BEGIN
                INSERT INTO TM_Item_Master_A
                    (CompanyCode, ITNBR, ITDSC, ENGNO, UNMSR, CreatedOn, CreatedBy)
                VALUES (?, ?, ?, ?, ?, GETDATE(), 'SEED')
            END
        """, (itnbr, cc, itnbr, itdsc, engno, unmsr))
        print(f"  + {itnbr} ({itdsc})")
    conn.commit()

    # ════════════════════════════════════════════════════════════════
    # 12. TM_Item_Master_B - Denso part lot sizes
    # ════════════════════════════════════════════════════════════════
    print("\n[12/18] TM_Item_Master_B ...")
    items_b = [
        ("DEMO", "DNHA-DM-001", 50),
        ("DEMO", "DNHA-DM-002", 100),
        ("DEMO", "DNHA-DM-003", 75),
        ("DEMO", "DNHA-DM-004", 200),
    ]
    for cc, itnbr, lotsz in items_b:
        run_sql(cursor, """
            IF NOT EXISTS (SELECT 1 FROM TM_Item_Master_B WHERE ITNBR = ?)
            BEGIN
                INSERT INTO TM_Item_Master_B
                    (CompanyCode, ITNBR, LOTSZ, CreatedOn, CreatedBy)
                VALUES (?, ?, ?, GETDATE(), 'SEED')
            END
        """, (itnbr, cc, itnbr, lotsz))
        print(f"  + {itnbr} LotSize={lotsz}")
    conn.commit()

    # ════════════════════════════════════════════════════════════════
    # 13. TM_DensoPart_And_SupplierCode_Mapping
    # ════════════════════════════════════════════════════════════════
    print("\n[13/18] TM_DensoPart_And_SupplierCode_Mapping ...")
    denso_supp = [
        ("DEMO", "DNHA-DM-001", "X", "DEMO", "X"),
        ("DEMO", "DNHA-DM-002", "X", "DEMO", "X"),
        ("DEMO", "DNHA-DM-003", "X", "DEMO", "X"),
        ("DEMO", "DNHA-DM-004", "X", "DEMO", "X"),
    ]
    for cc, dpprtn, s1, s2, s3 in denso_supp:
        run_sql(cursor, """
            IF NOT EXISTS (
                SELECT 1 FROM TM_DensoPart_And_SupplierCode_Mapping
                WHERE DPPRTN = ? AND CompanyCode = ?
            )
            BEGIN
                INSERT INTO TM_DensoPart_And_SupplierCode_Mapping
                    (CompanyCode, DPPRTN, DPG1S1, DPG1S2, DPG1S3, CreatedOn, CreatedBy)
                VALUES (?, ?, ?, ?, ?, GETDATE(), 'SEED')
            END
        """, (dpprtn, cc, cc, dpprtn, s1, s2, s3))
        print(f"  + {dpprtn} -> DPG1S2={s2}")
    conn.commit()

    # ════════════════════════════════════════════════════════════════
    # 14. TM_DnhaPart_And_SupplierPart_Mapping
    # ════════════════════════════════════════════════════════════════
    print("\n[14/18] TM_DnhaPart_And_SupplierPart_Mapping ...")
    dnha_supp = [
        # (SupplierCode, SupplierPart, DNHAPart, PlantCode, Name, LotSize, Weight, CycleTime, TolWeight, Scale, BinWt, BinTolWt, ImageName)
        ("DEMO", "DM-PART-001", "DNHA-DM-001", "DM1", "Bracket Assembly Part",  50.0,  120, 30, 5,  "Scale-A", 8,  2, "dm_part01.png"),
        ("DEMO", "DM-PART-002", "DNHA-DM-002", "DM1", "Sensor Housing Part",   100.0,  250, 45, 10, "Scale-B", 12, 3, "dm_part02.png"),
        ("DEMO", "DM-PART-003", "DNHA-DM-003", "DM1", "Connector Plate Part",   75.0,  180, 35, 7,  "Scale-A", 10, 2, "dm_part03.png"),
        ("DEMO", "DM-PART-004", "DNHA-DM-004", "DM1", "Relay Module Part",     200.0,  300, 60, 15, "Scale-C", 15, 4, "dm_part04.png"),
    ]
    for sc, sp, dnha, pc, spn, ls, wt, ct, tw, ws, bw, btw, img in dnha_supp:
        run_sql(cursor, """
            IF NOT EXISTS (
                SELECT 1 FROM TM_DnhaPart_And_SupplierPart_Mapping
                WHERE SupplierCode = ? AND SupplierPart = ? AND PlantCode = ?
            )
            BEGIN
                INSERT INTO TM_DnhaPart_And_SupplierPart_Mapping
                    (SupplierCode, SupplierPart, DNHAPart, PlantCode,
                     SupplierPartName, SupplierPartLotSize, SupplierPartWeight,
                     PrintCycleTime, ToleranceWeight, WeighingScale,
                     BinWeight, BinToleranceWeight, ImageName,
                     CreatedOn, CreatedBy)
                VALUES (?, ?, ?, ?,
                        ?, ?, ?,
                        ?, ?, ?,
                        ?, ?, ?,
                        GETDATE(), 'SEED')
            END
        """, (sc, sp, pc,
              sc, sp, dnha, pc,
              spn, ls, wt,
              ct, tw, ws,
              bw, btw, img))
        print(f"  + {sp} -> {dnha} (Supplier={sc})")
    conn.commit()

    # ════════════════════════════════════════════════════════════════
    # 15. TM_Supplier_Station_Part_Mapping
    # ════════════════════════════════════════════════════════════════
    print("\n[15/18] TM_Supplier_Station_Part_Mapping ...")
    station_parts = [
        ("DEMO", "DM1", "Station-1", "DM-PART-001"),
        ("DEMO", "DM1", "Station-1", "DM-PART-002"),
        ("DEMO", "DM1", "Station-1", "DM-PART-003"),
        ("DEMO", "DM1", "Station-2", "DM-PART-001"),
        ("DEMO", "DM1", "Station-2", "DM-PART-004"),
        ("DEMO", "DM1", "Station-3", "DM-PART-003"),
        ("DEMO", "DM1", "Station-3", "DM-PART-004"),
    ]
    for sc, pc, stn, pno in station_parts:
        run_sql(cursor, """
            IF NOT EXISTS (
                SELECT 1 FROM TM_Supplier_Station_Part_Mapping
                WHERE SupplierCode = ? AND PlantCode = ? AND Station = ? AND PartNo = ?
            )
            BEGIN
                INSERT INTO TM_Supplier_Station_Part_Mapping
                    (SupplierCode, PlantCode, Station, PartNo, CreatedOn, CreatedBy)
                VALUES (?, ?, ?, ?, GETDATE(), 'SEED')
            END
        """, (sc, pc, stn, pno, sc, pc, stn, pno))
        print(f"  + {stn}/{pc} -> {pno}")
    conn.commit()

    # ════════════════════════════════════════════════════════════════
    # 16. TM_Supplier_Lot_Structure
    # ════════════════════════════════════════════════════════════════
    print("\n[16/18] TM_Supplier_Lot_Structure ...")
    lot_structs = [
        # (SupplierCode, SupplierPart, TotalDigits, Steps, s1d-s6d, s1st-s6st, delim, charFrom, charTo, lockType)
        ("DEMO", "DM-PART-001", 12, 2, 6, 6, 0, 0, 0, 0,
         "Scan", "Enter", "Enter", "Enter", "Enter", "Enter", ",", 1, 12, "Enable"),
        ("DEMO", "DM-PART-002", 10, 2, 5, 5, 0, 0, 0, 0,
         "Scan", "Scan",  "Enter", "Enter", "Enter", "Enter", "-", 1, 10, "Enable"),
        ("DEMO", "DM-PART-003", 15, 3, 5, 5, 5, 0, 0, 0,
         "Scan", "Scan",  "Scan",  "Enter", "Enter", "Enter", "|", 1, 15, "Enable"),
        ("DEMO", "DM-PART-004", 8, 1, 8, 0, 0, 0, 0, 0,
         "Scan", "Enter", "Enter", "Enter", "Enter", "Enter", "", 1, 8, "Disable"),
    ]
    for (sc, sp, td, ns, s1, s2, s3, s4, s5, s6,
         st1, st2, st3, st4, st5, st6, delim, cf, ct, lt) in lot_structs:
        run_sql(cursor, """
            IF NOT EXISTS (
                SELECT 1 FROM TM_Supplier_Lot_Structure
                WHERE SupplierCode = ? AND SupplierPart = ?
            )
            BEGIN
                INSERT INTO TM_Supplier_Lot_Structure
                    (SupplierCode, SupplierPart,
                     TotalNoOfDigits, NoOfSteps,
                     Step_1_Digits, Step_2_Digits, Step_3_Digits,
                     Step_4_Digits, Step_5_Digits, Step_6_Digits,
                     Step_1_ScanType, Step_2_ScanType, Step_3_ScanType,
                     Step_4_ScanType, Step_5_ScanType, Step_6_ScanType,
                     DelimiterType, CharacterLengthFrom, CharacterLengthTo,
                     LotLockType, CreatedOn, CreatedBy)
                VALUES (?, ?,
                        ?, ?,
                        ?, ?, ?,
                        ?, ?, ?,
                        ?, ?, ?,
                        ?, ?, ?,
                        ?, ?, ?,
                        ?, GETDATE(), 'SEED')
            END
        """, (sc, sp,
              sc, sp,
              td, ns,
              s1, s2, s3,
              s4, s5, s6,
              st1, st2, st3,
              st4, st5, st6,
              delim, cf, ct,
              lt))
        print(f"  + {sc}/{sp} -> {td} digits, {ns} steps, Lock={lt}")
    conn.commit()

    # ════════════════════════════════════════════════════════════════
    # 17. TT_Kanban_Print - Sample printed tags
    #     (needed for: scan, reprint, change-lot, print-details,
    #      all-print-details, rework validate-tag, last-print-details)
    # ════════════════════════════════════════════════════════════════
    print("\n[17/18] TT_Kanban_Print ...")

    now = datetime.now()
    tags = [
        # (Barcode, OldBarcode, SupplierPartNo, PartNo, SupplierCode,
        #  LotNo1, LotNo2, Qty, Weight, TagType, RunningSNNo, IsMixedLot, StationNo, PlantCode,
        #  PrintedBy, Shift, PrintType, RM_Material, Grossweight, BinBarcode, BinQty, CompanyCode)
        (
            "DEMO-DM1-001-0001", "",
            "DM-PART-001", "DNHA-DM-001", "DEMO",
            "LOT-2026-A1", "", 50, 120.0, "Normal", "0001", 0, "Station-1", "DM1",
            "DEMO_USER", "A", "Normal", "", 125.5, "BIN-001", 1, "DEMO"
        ),
        (
            "DEMO-DM1-002-0002", "",
            "DM-PART-002", "DNHA-DM-002", "DEMO",
            "LOT-2026-B1", "", 100, 250.0, "Normal", "0002", 0, "Station-1", "DM1",
            "DEMO_USER", "A", "Normal", "", 260.0, "BIN-002", 1, "DEMO"
        ),
        (
            "DEMO-DM1-003-0003", "",
            "DM-PART-003", "DNHA-DM-003", "DEMO",
            "LOT-2026-C1", "LOT-2026-C2", 75, 180.0, "Normal", "0003", 0, "Station-1", "DM1",
            "DEMO_USER", "A", "Normal", "RM-STEEL", 190.0, "BIN-003", 1, "DEMO"
        ),
        (
            "DEMO-DM1-001-0004", "",
            "DM-PART-001", "DNHA-DM-001", "DEMO",
            "LOT-2026-A2", "", 50, 118.0, "Normal", "0004", 0, "Station-2", "DM1",
            "DEMO_USER", "B", "Normal", "", 123.0, "BIN-004", 1, "DEMO"
        ),
        (
            "DEMO-DM1-004-0005", "",
            "DM-PART-004", "DNHA-DM-004", "DEMO",
            "LOT-2026-D1", "", 200, 300.0, "Normal", "0005", 0, "Station-2", "DM1",
            "DEMO_USER", "A", "Normal", "", 310.0, "BIN-005", 1, "DEMO"
        ),
        # A rework tag (PrintType='Rework') for rework endpoints
        (
            "DEMO-DM1-001-RW01", "DEMO-DM1-001-0001",
            "DM-PART-001", "DNHA-DM-001", "DEMO",
            "LOT-2026-A1", "", 50, 120.0, "RWK", "RW01", 0, "Station-1", "DM1",
            "DEMO_USER", "A", "Rework", "", 125.5, "BIN-RW01", 1, "DEMO"
        ),
    ]

    for (barcode, old_bc, sp_no, p_no, sc,
         lot1, lot2, qty, wt, tt, sn, ml, stn, pc,
         pb, shift, pt, rm, gw, bin_bc, bin_qty, comp_code) in tags:
        run_sql(cursor, """
            IF NOT EXISTS (SELECT 1 FROM TT_Kanban_Print WHERE Barcode = ?)
            BEGIN
                INSERT INTO TT_Kanban_Print
                    (Barcode, OldBarcode,
                     SupplierPartNo, PartNo, SupplierCode,
                     LotNo1, LotNo2, Qty, Weight, TagType,
                     RunningSNNo, IsMixedLot, StationNo, PlantCode,
                     PrintedBy, PrintedOn, Shift, PrintType,
                     RM_Material, Grossweight, BinBarcode, BinQty,
                     CompanyCode, Status, DispatchStatus)
                VALUES
                    (?, ?,
                     ?, ?, ?,
                     ?, ?, ?, ?, ?,
                     ?, ?, ?, ?,
                     ?, GETDATE(), ?, ?,
                     ?, ?, ?, ?,
                     ?, 1, 0)
            END
        """, (barcode,
              barcode, old_bc,
              sp_no, p_no, sc,
              lot1, lot2, qty, wt, tt,
              sn, ml, stn, pc,
              pb, shift, pt,
              rm, gw, bin_bc, bin_qty,
              comp_code))
        print(f"  + {barcode} ({sp_no}, Type={pt})")
    conn.commit()

    # ════════════════════════════════════════════════════════════════
    # 18. TM_Supplier_End_User - Supervisor user for reprint/unlock
    # ════════════════════════════════════════════════════════════════
    print("\n[18/18] TM_Supplier_End_User (supervisor) ...")
    supervisor_pwd = hash_password("Super@1234")
    run_sql(cursor, """
        IF NOT EXISTS (SELECT 1 FROM TM_Supplier_End_User WHERE UserID = 'DEMO_SUPER')
        BEGIN
            INSERT INTO TM_Supplier_End_User
                (UserID, USERNAME, PASSWORD, EmailId, GroupID,
                 SupplierCode, DensoPlant, SupplierPlantCode,
                 PackingStation, CreatedBy, CreatedOn)
            VALUES
                ('DEMO_SUPER', 'Demo Supervisor', ?, 'demo.super@test.com', ?,
                 'DEMO', 'DENSO', 'DM1',
                 'Station-1', 'DEMO_ADMIN', GETDATE())
        END
    """, (supervisor_pwd, sup_group_id))
    print(f"  + DEMO_SUPER (password: Super@1234, group: Supervisor/{sup_group_id})")

    # Also ensure DEMO_USER exists as an end user
    demo_user_pwd = hash_password("Test@1234")
    run_sql(cursor, """
        IF NOT EXISTS (SELECT 1 FROM TM_Supplier_End_User WHERE UserID = 'DEMO_USER')
        BEGIN
            INSERT INTO TM_Supplier_End_User
                (UserID, USERNAME, PASSWORD, EmailId, GroupID,
                 SupplierCode, DensoPlant, SupplierPlantCode,
                 PackingStation, CreatedBy, CreatedOn)
            VALUES
                ('DEMO_USER', 'Demo User', ?, 'demo.user@test.com', ?,
                 'DEMO', '', 'DM1',
                 'Station-1', 'DEMO_ADMIN', GETDATE())
        END
    """, (demo_user_pwd, eol_group_id))
    print(f"  + DEMO_USER (password: Test@1234, group: EOL User/{eol_group_id})")

    # Also add a TL user
    tl_pwd = hash_password("TL@1234")
    run_sql(cursor, """
        IF NOT EXISTS (SELECT 1 FROM TM_Supplier_End_User WHERE UserID = 'DEMO_TL')
        BEGIN
            INSERT INTO TM_Supplier_End_User
                (UserID, USERNAME, PASSWORD, EmailId, GroupID,
                 SupplierCode, DensoPlant, SupplierPlantCode,
                 PackingStation, CreatedBy, CreatedOn)
            VALUES
                ('DEMO_TL', 'Demo Team Lead', ?, 'demo.tl@test.com', ?,
                 'DEMO', 'DENSO', 'DM1',
                 'Station-1', 'DEMO_ADMIN', GETDATE())
        END
    """, (tl_pwd, tl_group_id))
    print(f"  + DEMO_TL (password: TL@1234, group: TL/{tl_group_id})")

    conn.commit()

    # ── Summary ──────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("  SEED COMPLETE!")
    print("=" * 70)
    print(f"""
╔══════════════════════════════════════════════════════════════════════╗
║  TEST USERS                                                        ║
╠══════════════════════════════════════════════════════════════════════╣
║  DEMO_USER   / Test@1234    (EOL User,   group={eol_group_id:>3})              ║
║  DEMO_SUPER  / Super@1234   (Supervisor, group={sup_group_id:>3})              ║
║  DEMO_TL     / TL@1234      (TL,         group={tl_group_id:>3})              ║
║  DEMO_ADMIN  / Admin@1234   (Admin, IsSupplier=Y)                  ║
╚══════════════════════════════════════════════════════════════════════╝

╔══════════════════════════════════════════════════════════════════════╗
║  TEST DATA  (Supplier=DEMO, Plant=DM1, Station=Station-1)          ║
╠══════════════════════════════════════════════════════════════════════╣
║  Parts: DM-PART-001, DM-PART-002, DM-PART-003, DM-PART-004        ║
║  Printed Tags: 5 normal + 1 rework                                 ║
║  Shifts: A(06-14), B(14-22), C(22-06)                              ║
╚══════════════════════════════════════════════════════════════════════╝

TEST EVERY ENDPOINT:
────────────────────────────────────────────────────────────────────

TRACEABILITY ENDPOINTS:
  1. POST /api/traceability/login
     {{"user_id": "DEMO_USER", "password": "Test@1234"}}

  2. POST /api/traceability/traceability-user
     {{"user_id": "DEMO_USER", "password": "Test@1234"}}

  3. POST /api/traceability/supervisor-login
     {{"user_id": "DEMO_SUPER", "password": "Super@1234"}}

  4. POST /api/traceability/model-list
     {{"station_no": "Station-1", "plant_code": "DM1", "printed_by": "DEMO_USER"}}

  5. POST /api/traceability/confirm-model
     {{"supplier_part_no": "DM-PART-001", "supplier_code": "DEMO", "plant_code": "DM1", "station_no": "Station-1"}}

  6. POST /api/traceability/lock-fields
     {{"supplier_part_no": "DM-PART-001", "supplier_code": "DEMO", "plant_code": "DM1", "station_no": "Station-1"}}

  7. POST /api/traceability/unlock-fields
     {{"user_id": "DEMO_SUPER", "password": "Super@1234", "supplier_part_no": "DM-PART-001", "supplier_code": "DEMO", "plant_code": "DM1", "station_no": "Station-1"}}

  8. POST /api/traceability/refresh-token
     {{"refresh_token": "<your_refresh_token>"}}

REGISTRATION ENDPOINTS:
  9.  GET  /api/register/groups
  10. GET  /api/register/plants?created_by=DEMO_ADMIN
  11. GET  /api/register/stations?plant_code=DM1&supplier_code=DEMO
  12. GET  /api/register/list?created_by=DEMO_ADMIN
  13. POST /api/register/change-password
      {{"user_id": "DEMO_USER", "old_password": "Test@1234", "new_password": "NewTest@1234"}}

PRINT ENDPOINTS:
  14. POST /api/printing/print
      {{"plant_code": "DM1", "station_no": "Station-1", "supplier_code": "DEMO",
        "supplier_part_no": "DM-PART-001", "part_no": "DNHA-DM-001",
        "lot_no_1": "LOT-NEW-001", "weight": 120.0, "qty": 50, "printed_by": "DEMO_USER"}}

  15. POST /api/printing/scan
      {{"barcode": "DEMO-DM1-001-0001"}}

  16. POST /api/printing/last-print-details
      {{"supplier_code": "DEMO"}}

  17. POST /api/printing/print-details
      {{"supplier_code": "DEMO", "printed_by": "DEMO_USER", "station_no": "Station-1", "plant_code": "DM1"}}

  18. POST /api/printing/all-print-details
      {{"printed_by": "DEMO_USER", "station_no": "Station-1", "plant_code": "DM1"}}

  19. POST /api/printing/change-lot-no
      {{"barcode": "DEMO-DM1-001-0001", "new_lot_no": "LOT-CHANGED-01",
        "supplier_code": "DEMO", "supplier_part_no": "DM-PART-001", "part_no": "DNHA-DM-001"}}

  20. POST /api/printing/print-prn
      {{"prn": "PRN-001", "ip": "192.168.1.100", "port": "9100", "supplier_code": "DEMO"}}

  21. POST /api/printing/shift
      {{"supplier_code": "DEMO"}}

  22. POST /api/printing/validate-admin
      {{"user_id": "DEMO_SUPER", "password": "Super@1234"}}

  23. POST /api/printing/reprint
      {{"supervisor_user_id": "DEMO_SUPER", "supervisor_password": "Super@1234",
        "old_barcode": "DEMO-DM1-002-0002", "plant_code": "DM1", "station_no": "Station-1",
        "supplier_code": "DEMO", "supplier_part_no": "DM-PART-002", "part_no": "DNHA-DM-002",
        "lot_no_1": "LOT-2026-B1", "weight": 250.0, "qty": 100, "printed_by": "DEMO_USER"}}

  24. POST /api/printing/rework-reprint
      {{"supervisor_user_id": "DEMO_SUPER", "supervisor_password": "Super@1234",
        "old_barcode": "DEMO-DM1-001-RW01", "plant_code": "DM1", "station_no": "Station-1",
        "supplier_code": "DEMO", "supplier_part_no": "DM-PART-001", "part_no": "DNHA-DM-001",
        "lot_no_1": "LOT-2026-A1", "weight": 120.0, "qty": 50, "printed_by": "DEMO_USER"}}

  25. POST /api/printing/all-rework-print-details
      {{"printed_by": "DEMO_USER", "station_no": "Station-1", "plant_code": "DM1"}}

  26. GET  /api/printing/image/DM-PART-001
      (Returns 404 unless SupplierPartImage binary is uploaded)

REWORK ENDPOINTS:
  27. POST /api/rework/validate-tag
      {{"barcode": "DEMO-DM1-001-0001", "supplier_code": "DEMO"}}

  28. POST /api/rework/print-details
      {{"supplier_part_no": "DM-PART-001", "lot_no_1": "LOT-2026-A1", "supplier_code": "DEMO"}}

  29. POST /api/rework/last-print-details
      {{"supplier_part_no": "DM-PART-001"}}

  30. POST /api/rework/reprint-parameter
      {{"supplier_part_no": "DM-PART-001"}}

  31. POST /api/rework/print
      {{"barcode": "DEMO-DM1-003-0003", "plant_code": "DM1", "station_no": "Station-1",
        "supplier_code": "DEMO", "supplier_part_no": "DM-PART-003", "part_no": "DNHA-DM-003",
        "lot_no_1": "LOT-2026-C1", "weight": 180.0, "qty": 75, "printed_by": "DEMO_USER"}}
""")

    conn.close()


if __name__ == "__main__":
    seed()
