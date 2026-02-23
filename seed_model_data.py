"""
Seed script – populates tables required by the model-list and
confirm-model APIs (PRC_PrintKanban SP).

Run once:  python seed_model_data.py

Tables populated:
  1. TM_DensoPart_And_SupplierCode_Mapping – Denso part ↔ supplier code
  2. TM_DnhaPart_And_SupplierPart_Mapping  – Supplier part ↔ Denso part
  3. TM_Supplier_Station_Part_Mapping      – Parts available at each station
  4. TM_Item_Master_A                      – Denso part items (name, desc)
  5. TM_Item_Master_B                      – Denso part lot sizes
  6. TM_Supplier_Lot_Structure             – Lot structure config per part

Data chain for GET_SUPPLIERPART:
  testuser01 → CreatedBy=admin01
  admin01 in TM_SuppUser_SuppCode_Mapping → SupplierCode=SUP001
  TM_DensoPart_And_SupplierCode_Mapping  → DPPRTN=DNHA001, DPG1S2=SUP001
  TM_DnhaPart_And_SupplierPart_Mapping   → SupplierPart=SP-PART-01, DNHAPart=DNHA001
  TM_Supplier_Station_Part_Mapping       → PartNo=SP-PART-01, Station=STN01, PlantCode=PLT01
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from app.utils.database import get_db_connection


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
            print(f"  (skipped – already exists)")
        else:
            raise


def seed():
    conn = get_db_connection()
    cursor = conn.cursor()

    print("=" * 60)
    print("  SEEDING MODEL / PRINT-PARAMETER TEST DATA")
    print("=" * 60)

    # ── 1. Item Master A (Denso part info) ────────────────────────
    print("\n[1/6] TM_Item_Master_A ...")
    items_a = [
        ("COMP01", "DNHA001", "PLATE REAR",    "HA229876-0471", "PC"),
        ("COMP01", "DNHA002", "BRACKET ARM",   "HA330122-0832", "PC"),
        ("COMP01", "DNHA003", "COVER FRONT",   "HA441233-0125", "PC"),
    ]
    for cc, itnbr, itdsc, engno, unmsr in items_a:
        run_sql(cursor, """
            IF NOT EXISTS (SELECT 1 FROM TM_Item_Master_A WHERE ITNBR = ?)
            BEGIN
                INSERT INTO TM_Item_Master_A
                    (CompanyCode, ITNBR, ITDSC, ENGNO, UNMSR, CreatedOn, CreatedBy)
                VALUES (?, ?, ?, ?, ?, GETDATE(), 'SEED')
            END
        """, (itnbr,  cc, itnbr, itdsc, engno, unmsr))
        print(f"  + {itnbr} ({itdsc})")
    conn.commit()

    # ── 2. Item Master B (lot sizes) ─────────────────────────────
    print("\n[2/6] TM_Item_Master_B ...")
    items_b = [
        ("COMP01", "DNHA001", 72),
        ("COMP01", "DNHA002", 48),
        ("COMP01", "DNHA003", 100),
    ]
    for cc, itnbr, lotsz in items_b:
        run_sql(cursor, """
            IF NOT EXISTS (SELECT 1 FROM TM_Item_Master_B WHERE ITNBR = ?)
            BEGIN
                INSERT INTO TM_Item_Master_B
                    (CompanyCode, ITNBR, LOTSZ, CreatedOn, CreatedBy)
                VALUES (?, ?, ?, GETDATE(), 'SEED')
            END
        """, (itnbr,  cc, itnbr, lotsz))
        print(f"  + {itnbr} LotSize={lotsz}")
    conn.commit()

    # ── 3. DensoPart ↔ SupplierCode mapping ──────────────────────
    #    CROSS APPLY in SP unpivots DPG1S1/S2/S3 – we put our
    #    supplier code in DPG1S2 so the SP finds it.
    print("\n[3/6] TM_DensoPart_And_SupplierCode_Mapping ...")
    denso_supp = [
        # (CompanyCode, DPPRTN,  DPG1S1,  DPG1S2,   DPG1S3)
        ("COMP01",     "DNHA001", "X",   "SUP001",  "X"),
        ("COMP01",     "DNHA002", "X",   "SUP001",  "X"),
        ("COMP01",     "DNHA003", "X",   "SUP002",  "X"),
    ]
    for cc, dpprtn, s1, s2, s3 in denso_supp:
        run_sql(cursor, """
            IF NOT EXISTS (
                SELECT 1 FROM TM_DensoPart_And_SupplierCode_Mapping
                WHERE DPPRTN = ? AND DPG1S1 = ? AND DPG1S2 = ? AND DPG1S3 = ?
            )
            BEGIN
                INSERT INTO TM_DensoPart_And_SupplierCode_Mapping
                    (CompanyCode, DPPRTN, DPG1S1, DPG1S2, DPG1S3, CreatedOn, CreatedBy)
                VALUES (?, ?, ?, ?, ?, GETDATE(), 'SEED')
            END
        """, (dpprtn, s1, s2, s3,  cc, dpprtn, s1, s2, s3))
        print(f"  + {dpprtn} → DPG1S2={s2}")
    conn.commit()

    # ── 4. DnhaPart ↔ SupplierPart mapping ───────────────────────
    #    SupplierPart is what the user sees in the Model dropdown.
    print("\n[4/6] TM_DnhaPart_And_SupplierPart_Mapping ...")
    dnha_supp = [
        # (SupplierCode, SupplierPart, DNHAPart, PlantCode, SupplierPartName, LotSize, Weight, CycleTime, TolWeight, WeighScale, BinWt, BinTolWt, ImageName)
        ("SUP001", "SP-PART-01", "DNHA001", "PLT01", "Supplier Part 01",  72.0,  150, 30, 5,  "Scale-A", 10, 2, "part01.png"),
        ("SUP001", "SP-PART-02", "DNHA002", "PLT01", "Supplier Part 02",  48.0,  220, 45, 8,  "Scale-B", 15, 3, "part02.png"),
        ("SUP002", "SP-PART-03", "DNHA003", "PLT01", "Supplier Part 03", 100.0,  300, 60, 10, "Not Used", 20, 4, "part03.png"),
    ]
    for sc, sp, dnha, pc, spn, ls, wt, ct, tw, ws, bw, btw, img in dnha_supp:
        run_sql(cursor, """
            IF NOT EXISTS (
                SELECT 1 FROM TM_DnhaPart_And_SupplierPart_Mapping
                WHERE SupplierCode = ? AND SupplierPart = ? AND DNHAPart = ? AND PlantCode = ?
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
        """, (sc, sp, dnha, pc,
              sc, sp, dnha, pc,
              spn, ls, wt,
              ct, tw, ws,
              bw, btw, img))
        print(f"  + {sp} → {dnha} (Supplier={sc})")
    conn.commit()

    # ── 5. Station ↔ Part mapping ────────────────────────────────
    #    The SP joins on PartNo = SupplierPart AND Station/PlantCode.
    print("\n[5/6] TM_Supplier_Station_Part_Mapping ...")
    station_parts = [
        # (SupplierCode, PlantCode, Station, PartNo)
        ("SUP001", "PLT01", "STN01", "SP-PART-01"),
        ("SUP001", "PLT01", "STN01", "SP-PART-02"),
        ("SUP001", "PLT01", "STN02", "SP-PART-01"),
        ("SUP002", "PLT01", "STN01", "SP-PART-03"),
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
        """, (sc, pc, stn, pno,  sc, pc, stn, pno))
        print(f"  + {stn}/{pc} → {pno}")
    conn.commit()

    # ── 6. Lot Structure ─────────────────────────────────────────
    #    GET_PRINT_PARAMETER joins on SupplierCode + SupplierPart.
    print("\n[6/6] TM_Supplier_Lot_Structure ...")
    lot_structs = [
        # (SupplierCode, SupplierPart, TotalDigits, Steps, s1d, s2d, s3d, s4d, s5d, s6d,
        #  s1st, s2st, s3st, s4st, s5st, s6st, delim, charFrom, charTo, lockType)
        ("SUP001", "SP-PART-01", 12, 2, 6, 6, 0, 0, 0, 0,
         "Scan", "Enter", "Enter", "Enter", "Enter", "Enter", ",", 1, 12, "Enable"),
        ("SUP001", "SP-PART-02", 10, 2, 5, 5, 0, 0, 0, 0,
         "Scan", "Scan",  "Enter", "Enter", "Enter", "Enter", "-", 1, 10, "Enable"),
        ("SUP002", "SP-PART-03", 15, 3, 5, 5, 5, 0, 0, 0,
         "Scan", "Scan",  "Scan",  "Enter", "Enter", "Enter", "|", 1, 15, "Disable"),
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
        print(f"  + {sc}/{sp} → {td} digits, {ns} steps")
    conn.commit()

    # ── Summary ──────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  MODEL DATA SEED COMPLETE!")
    print("=" * 60)
    print("""
You can now test:

1. POST /api/traceability/model-list
   {
     "station_no": "STN01",
     "plant_code": "PLT01",
     "printed_by": "testuser01"
   }
   → Should return SP-PART-01, SP-PART-02

2. POST /api/traceability/confirm-model
   {
     "supplier_part_no": "SP-PART-01",
     "supplier_code": "SUP001",
     "plant_code": "PLT01",
     "station_no": "STN01"
   }
   → Should return full part details (PLATE REAR, LotSize=72, etc.)
""")

    conn.close()


if __name__ == "__main__":
    seed()
