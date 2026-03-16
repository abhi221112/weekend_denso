"""Quick script to update CharacterLengthFrom/To for DM-PART-006."""
from app.utils.database import get_db_connection

conn = get_db_connection()
cursor = conn.cursor()

cursor.execute(
    "UPDATE TM_Supplier_Lot_Structure "
    "SET CharacterLengthFrom = 1, CharacterLengthTo = 17 "
    "WHERE SupplierCode = 'DEMO' AND SupplierPart = 'DM-PART-006'"
)
print(f"Rows updated: {cursor.rowcount}")
conn.commit()

cursor.execute(
    "SELECT CharacterLengthFrom, CharacterLengthTo "
    "FROM TM_Supplier_Lot_Structure "
    "WHERE SupplierCode = 'DEMO' AND SupplierPart = 'DM-PART-006'"
)
row = cursor.fetchone()
if row:
    print(f"Verified: CharacterLengthFrom={row[0]}, CharacterLengthTo={row[1]}")
else:
    print("No record found")

conn.close()
