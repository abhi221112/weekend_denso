from app.utils.database import get_db_connection

conn = get_db_connection()
c = conn.cursor()

# Test directly through repo layer
from app.repositories import rework_repo
r = rework_repo.validate_tag(barcode='KB202602050002')
print("Repo result:", r)
print()

# If repo returned None, test the service
from app.services import rework_service
r2 = rework_service.validate_tag(barcode='KB202602050002')
print("Service result:", r2)

conn.close()
