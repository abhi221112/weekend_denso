"""
Seed script – adds a NEW supplier part (DM-PART-005) for DEMO_USER
with barcode delimiter "|", scan type "Scan", and defined char from/to.

DEMO_USER config:
  user_id         = DEMO_USER
  supplier_code   = DEMO
  plant_code      = DM1
  packing_station = Station-1
  group_id        = 5 (EOL User)

NEW PART:
  SupplierPart    = DM-PART-005
  DNHAPart        = DNHA-DM-005
  Delimiter       = |
  Scan Type       = Scan (all steps)
  CharFrom        = 1
  CharTo          = 30

BARCODE FORMAT (uses "|" delimiter):
  DEMO|DM1|DMPART005|LOT2026E1|0006

Tables populated:
  1. TM_Item_Master_A              – DNHA-DM-005 Denso part description
  2. TM_Item_Master_B              – DNHA-DM-005 lot size
  3. TM_DensoPart_And_SupplierCode_Mapping – DNHA-DM-005 → DEMO
  4. TM_DnhaPart_And_SupplierPart_Mapping  – DM-PART-005 → DNHA-DM-005
  5. TM_Supplier_Station_Part_Mapping      – DM-PART-005 at Station-1
  6. TM_Supplier_Lot_Structure             – Scan/"|"/charFrom=1/charTo=30
  7. TT_Kanban_Print                       – Sample tags with "|" barcode

Run:  python seed_new_part_data.py
"""

import sys
import os
from datetime import datetime

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
            print(f"  (skipped - already exists)")
        else:
            raise


def seed():
    conn = get_db_connection()
    cursor = conn.cursor()

    print("=" * 70)
    print("  SEED: New Part DM-PART-005 for DEMO_USER")
    print("  Barcode delimiter = |  |  Scan type = Scan  |  CharFrom=1, CharTo=30")
    print("=" * 70)

    # ════════════════════════════════════════════════════════════════
    # 1. TM_Item_Master_A – Denso part description
    # ════════════════════════════════════════════════════════════════
    print("\n[1/7] TM_Item_Master_A ...")
    run_sql(cursor, """
        IF NOT EXISTS (SELECT 1 FROM TM_Item_Master_A WHERE ITNBR = 'DNHA-DM-005')
        BEGIN
            INSERT INTO TM_Item_Master_A
                (CompanyCode, ITNBR, ITDSC, ENGNO, UNMSR, CreatedOn, CreatedBy)
            VALUES ('DEMO', 'DNHA-DM-005', 'VALVE ASSEMBLY', 'DM-ENG-005', 'PC', GETDATE(), 'SEED')
        END
    """)
    print("  + DNHA-DM-005 (VALVE ASSEMBLY)")
    conn.commit()

    # ════════════════════════════════════════════════════════════════
    # 2. TM_Item_Master_B – Lot size
    # ════════════════════════════════════════════════════════════════
    print("\n[2/7] TM_Item_Master_B ...")
    run_sql(cursor, """
        IF NOT EXISTS (SELECT 1 FROM TM_Item_Master_B WHERE ITNBR = 'DNHA-DM-005')
        BEGIN
            INSERT INTO TM_Item_Master_B
                (CompanyCode, ITNBR, LOTSZ, CreatedOn, CreatedBy)
            VALUES ('DEMO', 'DNHA-DM-005', 60, GETDATE(), 'SEED')
        END
    """)
    print("  + DNHA-DM-005 LotSize=60")
    conn.commit()

    # ════════════════════════════════════════════════════════════════
    # 3. TM_DensoPart_And_SupplierCode_Mapping
    # ════════════════════════════════════════════════════════════════
    print("\n[3/7] TM_DensoPart_And_SupplierCode_Mapping ...")
    run_sql(cursor, """
        IF NOT EXISTS (
            SELECT 1 FROM TM_DensoPart_And_SupplierCode_Mapping
            WHERE DPPRTN = 'DNHA-DM-005' AND CompanyCode = 'DEMO'
        )
        BEGIN
            INSERT INTO TM_DensoPart_And_SupplierCode_Mapping
                (CompanyCode, DPPRTN, DPG1S1, DPG1S2, DPG1S3, CreatedOn, CreatedBy)
            VALUES ('DEMO', 'DNHA-DM-005', 'X', 'DEMO', 'X', GETDATE(), 'SEED')
        END
    """)
    print("  + DNHA-DM-005 -> DPG1S2=DEMO")
    conn.commit()

    # ════════════════════════════════════════════════════════════════
    # 4. TM_DnhaPart_And_SupplierPart_Mapping
    # ════════════════════════════════════════════════════════════════
    print("\n[4/7] TM_DnhaPart_And_SupplierPart_Mapping ...")
    run_sql(cursor, """
        IF NOT EXISTS (
            SELECT 1 FROM TM_DnhaPart_And_SupplierPart_Mapping
            WHERE SupplierCode = 'DEMO' AND SupplierPart = 'DM-PART-005' AND PlantCode = 'DM1'
        )
        BEGIN
            INSERT INTO TM_DnhaPart_And_SupplierPart_Mapping
                (SupplierCode, SupplierPart, DNHAPart, PlantCode,
                 SupplierPartName, SupplierPartLotSize, SupplierPartWeight,
                 PrintCycleTime, ToleranceWeight, WeighingScale,
                 BinWeight, BinToleranceWeight, ImageName,
                 CreatedOn, CreatedBy)
            VALUES ('DEMO', 'DM-PART-005', 'DNHA-DM-005', 'DM1',
                    'Valve Assembly Part', 60.0, 200,
                    40, 8, 'Scale-A',
                    12, 3, 'dm_part05.png',
                    GETDATE(), 'SEED')
        END
    """)
    print("  + DM-PART-005 -> DNHA-DM-005 (Supplier=DEMO, Plant=DM1)")
    conn.commit()

    # ════════════════════════════════════════════════════════════════
    # 5. TM_Supplier_Station_Part_Mapping
    # ════════════════════════════════════════════════════════════════
    print("\n[5/7] TM_Supplier_Station_Part_Mapping ...")
    station_parts = [
        ("DEMO", "DM1", "Station-1", "DM-PART-005"),
        ("DEMO", "DM1", "Station-2", "DM-PART-005"),
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
    # 6. TM_Supplier_Lot_Structure
    #    - Scan type  = Scan (all steps)
    #    - Delimiter  = |
    #    - CharFrom   = 1
    #    - CharTo     = 30
    #    - 3 steps: 10|10|10 digits
    # ════════════════════════════════════════════════════════════════
    print("\n[6/7] TM_Supplier_Lot_Structure ...")
    run_sql(cursor, """
        IF NOT EXISTS (
            SELECT 1 FROM TM_Supplier_Lot_Structure
            WHERE SupplierCode = 'DEMO' AND SupplierPart = 'DM-PART-005'
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
            VALUES ('DEMO', 'DM-PART-005',
                    30, 3,
                    10, 10, 10,
                    0, 0, 0,
                    'Scan', 'Scan', 'Scan',
                    'Enter', 'Enter', 'Enter',
                    '|', 1, 30,
                    'Enable', GETDATE(), 'SEED')
        END
    """)
    print("  + DEMO/DM-PART-005 -> 30 digits, 3 steps (Scan|Scan|Scan), Delim='|', Char 1-30, Lock=Enable")
    conn.commit()

    # ════════════════════════════════════════════════════════════════
    # 7. TT_Kanban_Print – Sample tags with "|" barcode format
    #
    #    Barcode format:  DEMO|DM1|DMPART005|<LotNo>|<Serial>
    #    These tags are usable across ALL APIs:
    #      - /api/printing/scan
    #      - /api/printing/print-details
    #      - /api/printing/all-print-details
    #      - /api/printing/change-lot-no
    #      - /api/printing/reprint
    #      - /api/printing/rework-reprint
    #      - /api/printing/all-rework-print-details
    #      - /api/printing/last-print-details
    #      - /api/rework/validate-tag
    #      - /api/rework/print-details
    #      - /api/rework/last-print-details
    #      - /api/rework/print
    # ════════════════════════════════════════════════════════════════
    print("\n[7/7] TT_Kanban_Print (barcode with '|' delimiter) ...")

    tags = [
        # Tag 1: Normal print – Station-1, Shift A
        {
            "barcode":          "DEMO|DM1|DMPART005|LOT2026E1|0006",
            "old_barcode":      "",
            "supplier_part_no": "DM-PART-005",
            "part_no":          "DNHA-DM-005",
            "supplier_code":    "DEMO",
            "lot_no_1":         "LOT2026E1",
            "lot_no_2":         "",
            "qty":              60,
            "weight":           200.0,
            "tag_type":         "Normal",
            "running_sn_no":    "0006",
            "is_mixed_lot":     0,
            "station_no":       "Station-1",
            "plant_code":       "DM1",
            "printed_by":       "DEMO_USER",
            "shift":            "A",
            "print_type":       "Normal",
            "rm_material":      "",
            "gross_weight":     210.0,
            "bin_barcode":      "BIN-006",
            "bin_qty":          1,
            "company_code":     "DEMO",
        },
        # Tag 2: Normal print – Station-1, Shift B, different lot
        {
            "barcode":          "DEMO|DM1|DMPART005|LOT2026E2|0007",
            "old_barcode":      "",
            "supplier_part_no": "DM-PART-005",
            "part_no":          "DNHA-DM-005",
            "supplier_code":    "DEMO",
            "lot_no_1":         "LOT2026E2",
            "lot_no_2":         "",
            "qty":              60,
            "weight":           198.0,
            "tag_type":         "Normal",
            "running_sn_no":    "0007",
            "is_mixed_lot":     0,
            "station_no":       "Station-1",
            "plant_code":       "DM1",
            "printed_by":       "DEMO_USER",
            "shift":            "B",
            "print_type":       "Normal",
            "rm_material":      "",
            "gross_weight":     208.0,
            "bin_barcode":      "BIN-007",
            "bin_qty":          1,
            "company_code":     "DEMO",
        },
        # Tag 3: Normal print – Station-2, Shift A
        {
            "barcode":          "DEMO|DM1|DMPART005|LOT2026E1|0008",
            "old_barcode":      "",
            "supplier_part_no": "DM-PART-005",
            "part_no":          "DNHA-DM-005",
            "supplier_code":    "DEMO",
            "lot_no_1":         "LOT2026E1",
            "lot_no_2":         "",
            "qty":              60,
            "weight":           202.0,
            "tag_type":         "Normal",
            "running_sn_no":    "0008",
            "is_mixed_lot":     0,
            "station_no":       "Station-2",
            "plant_code":       "DM1",
            "printed_by":       "DEMO_USER",
            "shift":            "A",
            "print_type":       "Normal",
            "rm_material":      "RM-VALVE",
            "gross_weight":     212.0,
            "bin_barcode":      "BIN-008",
            "bin_qty":          1,
            "company_code":     "DEMO",
        },
        # Tag 4: Rework tag – for rework endpoints
        {
            "barcode":          "DEMO|DM1|DMPART005|LOT2026E1|RW03",
            "old_barcode":      "DEMO|DM1|DMPART005|LOT2026E1|0006",
            "supplier_part_no": "DM-PART-005",
            "part_no":          "DNHA-DM-005",
            "supplier_code":    "DEMO",
            "lot_no_1":         "LOT2026E1",
            "lot_no_2":         "",
            "qty":              60,
            "weight":           200.0,
            "tag_type":         "RWK",
            "running_sn_no":    "RW03",
            "is_mixed_lot":     0,
            "station_no":       "Station-1",
            "plant_code":       "DM1",
            "printed_by":       "DEMO_USER",
            "shift":            "A",
            "print_type":       "Rework",
            "rm_material":      "",
            "gross_weight":     210.0,
            "bin_barcode":      "BIN-RW03",
            "bin_qty":          1,
            "company_code":     "DEMO",
        },
    ]

    for tag in tags:
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
        """, (
            tag["barcode"],
            tag["barcode"], tag["old_barcode"],
            tag["supplier_part_no"], tag["part_no"], tag["supplier_code"],
            tag["lot_no_1"], tag["lot_no_2"], tag["qty"], tag["weight"], tag["tag_type"],
            tag["running_sn_no"], tag["is_mixed_lot"], tag["station_no"], tag["plant_code"],
            tag["printed_by"], tag["shift"], tag["print_type"],
            tag["rm_material"], tag["gross_weight"], tag["bin_barcode"], tag["bin_qty"],
            tag["company_code"],
        ))
        print(f"  + {tag['barcode']}  (Part={tag['supplier_part_no']}, Type={tag['print_type']})")
    conn.commit()

    conn.close()

    # ── Summary ──────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("  SEED COMPLETE!")
    print("=" * 70)
    print("""
+-----------------------------------------------------------------------+
|  NEW PART: DM-PART-005  (VALVE ASSEMBLY)                              |
+-----------------------------------------------------------------------+
|  Supplier Code   : DEMO                                               |
|  DNHA Part       : DNHA-DM-005                                        |
|  Plant Code      : DM1                                                |
|  Stations        : Station-1, Station-2                                |
|  Lot Size        : 60                                                  |
|  Weight          : 200                                                 |
+-----------------------------------------------------------------------+
|  LOT STRUCTURE                                                         |
|  TotalDigits     : 30                                                  |
|  NoOfSteps       : 3                                                   |
|  Step 1          : 10 digits, ScanType = Scan                          |
|  Step 2          : 10 digits, ScanType = Scan                          |
|  Step 3          : 10 digits, ScanType = Scan                          |
|  Delimiter       : |                                                   |
|  CharacterFrom   : 1                                                   |
|  CharacterTo     : 30                                                  |
|  LotLockType     : Enable                                              |
+-----------------------------------------------------------------------+
|  BARCODES (delimiter = "|")                                            |
|  1. DEMO|DM1|DMPART005|LOT2026E1|0006  (Normal, Station-1, Shift A)   |
|  2. DEMO|DM1|DMPART005|LOT2026E2|0007  (Normal, Station-1, Shift B)   |
|  3. DEMO|DM1|DMPART005|LOT2026E1|0008  (Normal, Station-2, Shift A)   |
|  4. DEMO|DM1|DMPART005|LOT2026E1|RW03  (Rework, Station-1, Shift A)   |
+-----------------------------------------------------------------------+

TEST ALL ENDPOINTS WITH NEW PART (use DEMO_USER access_token):
─────────────────────────────────────────────────────────────────────

TRACEABILITY ENDPOINTS:
  1. POST /api/traceability/model-list
     {"station_no": "Station-1", "plant_code": "DM1", "printed_by": "DEMO_USER"}
     → Should now include DM-PART-005

  2. POST /api/traceability/confirm-model
     {"supplier_part_no": "DM-PART-005", "supplier_code": "DEMO", "plant_code": "DM1", "station_no": "Station-1"}
     → Returns: VALVE ASSEMBLY, LotSize=60, Delimiter='|', ScanType=Scan, CharFrom=1, CharTo=30

  3. POST /api/traceability/lock-fields
     {"supplier_part_no": "DM-PART-005", "supplier_code": "DEMO", "plant_code": "DM1", "station_no": "Station-1"}

  4. POST /api/traceability/unlock-fields
     {"user_id": "DEMO_SUPER", "password": "Super@1234", "supplier_part_no": "DM-PART-005",
      "supplier_code": "DEMO", "plant_code": "DM1", "station_no": "Station-1"}

PRINT ENDPOINTS:
  5. POST /api/printing/print
     {"plant_code": "DM1", "station_no": "Station-1", "supplier_code": "DEMO",
      "supplier_part_no": "DM-PART-005", "part_no": "DNHA-DM-005",
      "lot_no_1": "LOT-NEW-005", "weight": 200.0, "qty": 60, "printed_by": "DEMO_USER"}

  6. POST /api/printing/scan
     {"barcode": "DEMO|DM1|DMPART005|LOT2026E1|0006"}

  7. POST /api/printing/last-print-details
     {"supplier_code": "DEMO"}

  8. POST /api/printing/print-details
     {"supplier_code": "DEMO", "printed_by": "DEMO_USER", "station_no": "Station-1", "plant_code": "DM1"}

  9. POST /api/printing/all-print-details
     {"printed_by": "DEMO_USER", "station_no": "Station-1", "plant_code": "DM1"}

 10. POST /api/printing/change-lot-no
     {"barcode": "DEMO|DM1|DMPART005|LOT2026E1|0006", "new_lot_no": "LOT-CHANGED-05",
      "supplier_code": "DEMO", "supplier_part_no": "DM-PART-005", "part_no": "DNHA-DM-005"}

 11. POST /api/printing/shift
     {"supplier_code": "DEMO"}

 12. POST /api/printing/validate-admin
     {"user_id": "DEMO_SUPER", "password": "Super@1234"}

 13. POST /api/printing/reprint
     {"supervisor_user_id": "DEMO_SUPER", "supervisor_password": "Super@1234",
      "old_barcode": "DEMO|DM1|DMPART005|LOT2026E2|0007", "plant_code": "DM1",
      "station_no": "Station-1", "supplier_code": "DEMO",
      "supplier_part_no": "DM-PART-005", "part_no": "DNHA-DM-005",
      "lot_no_1": "LOT2026E2", "weight": 198.0, "qty": 60, "printed_by": "DEMO_USER"}

 14. POST /api/printing/rework-reprint
     {"supervisor_user_id": "DEMO_SUPER", "supervisor_password": "Super@1234",
      "old_barcode": "DEMO|DM1|DMPART005|LOT2026E1|RW03", "plant_code": "DM1",
      "station_no": "Station-1", "supplier_code": "DEMO",
      "supplier_part_no": "DM-PART-005", "part_no": "DNHA-DM-005",
      "lot_no_1": "LOT2026E1", "weight": 200.0, "qty": 60, "printed_by": "DEMO_USER"}

 15. POST /api/printing/all-rework-print-details
     {"printed_by": "DEMO_USER", "station_no": "Station-1", "plant_code": "DM1"}

 16. GET  /api/printing/image/DM-PART-005

REWORK ENDPOINTS:
 17. POST /api/rework/validate-tag
     {"barcode": "DEMO|DM1|DMPART005|LOT2026E1|0006", "supplier_code": "DEMO"}

 18. POST /api/rework/print-details
     {"supplier_part_no": "DM-PART-005", "lot_no_1": "LOT2026E1", "supplier_code": "DEMO"}

 19. POST /api/rework/last-print-details
     {"supplier_part_no": "DM-PART-005"}

 20. POST /api/rework/reprint-parameter
     {"supplier_part_no": "DM-PART-005"}

 21. POST /api/rework/print
     {"barcode": "DEMO|DM1|DMPART005|LOT2026E1|0008", "plant_code": "DM1",
      "station_no": "Station-2", "supplier_code": "DEMO",
      "supplier_part_no": "DM-PART-005", "part_no": "DNHA-DM-005",
      "lot_no_1": "LOT2026E1", "weight": 202.0, "qty": 60, "printed_by": "DEMO_USER"}
""")


if __name__ == "__main__":
    seed()
