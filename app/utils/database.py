import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

DB_SERVER = os.getenv("DB_SERVER", "")
DB_NAME = os.getenv("DB_NAME", "DTraceProddb")
DB_USER = os.getenv("DB_USER", "")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_DRIVER = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")
USE_WINDOWS_AUTH = os.getenv("USE_WINDOWS_AUTH", "true").lower() == "true"

# Build connection string with Windows Auth (recommended) or SQL Auth
if USE_WINDOWS_AUTH or (not DB_USER and not DB_PASSWORD):
    # Windows Authentication (Integrated Security)
    CONNECTION_STRING = (
        f"DRIVER={{{DB_DRIVER}}};"
        f"SERVER={DB_SERVER};"
        f"DATABASE={DB_NAME};"
        f"Trusted_Connection=yes;"
        f"TrustServerCertificate=yes;"
    )
else:
    # SQL Server Authentication
    CONNECTION_STRING = (
        f"DRIVER={{{DB_DRIVER}}};"
        f"SERVER={DB_SERVER};"
        f"DATABASE={DB_NAME};"
        f"UID={DB_USER};"
        f"PWD={DB_PASSWORD};"
        f"TrustServerCertificate=yes;"
    )


def get_db_connection():
    """Get a new database connection."""
    return pyodbc.connect(CONNECTION_STRING)
