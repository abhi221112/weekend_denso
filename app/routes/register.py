"""
Routes for User & Supervisor registration.

Endpoints:
  POST   /api/register/user              → Register a new end user
  POST   /api/register/supervisor        → Register a new supervisor
  POST   /api/register/change-password   → Change user/supervisor password
  PUT    /api/register/{user_id}         → Update user/supervisor
  DELETE /api/register/{user_id}         → Delete user/supervisor
  GET    /api/register/list              → List all users
  GET    /api/register/groups            → Get available groups (for dropdown)
  GET    /api/register/plants            → Get available plants (for dropdown)
  GET    /api/register/stations          → Get packing stations (for dropdown)
"""

from fastapi import APIRouter, HTTPException, Depends

from app.models.supplier_end_user import (
    SupplierEndUserCreate,
    SupplierEndUserUpdate,
    ChangePasswordRequest,
)
from app.services.supplier_end_user_service import SupplierEndUserService
from app.utils.jwt_handler import get_current_user
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/register",
    tags=["User & Supervisor Registration"],
)

service = SupplierEndUserService()


# ── 1. Register User ───────────────────────────────────────────────
@router.post("/user", response_model=dict)
def register_user(body: SupplierEndUserCreate):
    """
    **Register a new End User**

    Creates a new supplier end user in `TM_Supplier_End_User`.
    The `group_id` determines the user role (EOL User, etc.).

    SP call: `PRC_UserSupplier_EndUser @Type = 'INSERT'`

    Sample request:
    ```json
    {
        "user_id": "USR001",
        "user_name": "John Doe",
        "password": "Pass@123",
        "supplier_plant_code": "PLANT01",
        "group_id": 1,
        "email_id": "john@supplier.com",
        "packing_station": "STATION_01"
    }
    ```
    """
    logger.info("Registering new user: %s", body.user_id)
    result = service.create_user(body)
    if not result["success"]:
        logger.warning("User registration failed for %s: %s", body.user_id, result["message"])
        raise HTTPException(status_code=400, detail=result["message"])
    logger.info("User registered successfully: %s", body.user_id)
    return result


# ── 2. Register Supervisor ────────────────────────────────────────
@router.post("/supervisor", response_model=dict)
def register_supervisor(body: SupplierEndUserCreate, user: dict = Depends(get_current_user)):
    """
    **Register a new Supervisor**

    Creates a new supervisor in `TM_Supplier_End_User`.
    The `group_id` must correspond to a supervisor group
    (typically the group with ScreenId 3002/2003 rights).

    SP call: `PRC_UserSupplier_EndUser @Type = 'INSERT'`

    Sample request:
    ```json
    {
        "user_id": "SUP001",
        "user_name": "Jane Smith",
        "password": "SuperPass@123",
        "supplier_plant_code": "PLANT01",
        "group_id": 2,
        "email_id": "jane@supplier.com",
        "packing_station": "STATION_01"
    }
    ```
    """
    # Same SP, different group_id determines supervisor role
    logger.info("Registering new supervisor: %s", body.user_id)
    result = service.create_user(body)
    if not result["success"]:
        logger.warning("Supervisor registration failed for %s: %s", body.user_id, result["message"])
        raise HTTPException(status_code=400, detail=result["message"])
    logger.info("Supervisor registered successfully: %s", body.user_id)
    return result


# ── 3. Change Password ─────────────────────────────────────────────
@router.post("/change-password", response_model=dict)
def change_password(body: ChangePasswordRequest, user: dict = Depends(get_current_user)):
    """
    **Change password for a User or Supervisor**

    Verifies the old password, then updates to the new password.
    Both passwords are stored as SHA-256 hashes in the database.

    SP call: `PRC_UserSupplier_EndUser @Type = 'UPDATEPASSWORD'`

    Sample request:
    ```json
    {
        "user_id": "USR001",
        "old_password": "OldPass@123",
        "new_password": "NewPass@456"
    }
    ```
    """
    logger.info("Password change requested for user_id=%s", body.user_id)
    result = service.change_password(body)
    if not result["success"]:
        logger.warning("Password change failed for %s: %s", body.user_id, result["message"])
        raise HTTPException(status_code=400, detail=result["message"])
    logger.info("Password changed successfully for user_id=%s", body.user_id)
    return result


# ── 4. Update User/Supervisor ─────────────────────────────────────
@router.put("/{user_id}", response_model=dict)
def update_user(user_id: str, body: SupplierEndUserUpdate, user: dict = Depends(get_current_user)):
    """
    **Update an existing User or Supervisor**

    SP call: `PRC_UserSupplier_EndUser @Type = 'UPDATE'`
    """
    logger.info("Updating user: %s", user_id)
    result = service.update_user(user_id, body, body.supplier_code or "")
    if not result["success"]:
        logger.warning("User update failed for %s: %s", user_id, result["message"])
        raise HTTPException(status_code=400, detail=result["message"])
    logger.info("User updated successfully: %s", user_id)
    return result


# ── 5. Delete User/Supervisor ─────────────────────────────────────
@router.delete("/{user_id}", response_model=dict)
def delete_user(user_id: str, user: dict = Depends(get_current_user)):
    """
    **Delete a User or Supervisor**

    SP call: `PRC_UserSupplier_EndUser @Type = 'DELETE'`
    """
    logger.info("Deleting user: %s", user_id)
    result = service.delete_user(user_id, "")
    if not result["success"]:
        logger.warning("User deletion failed for %s: %s", user_id, result["message"])
        raise HTTPException(status_code=400, detail=result["message"])
    logger.info("User deleted successfully: %s", user_id)
    return result


# ── 5. List All Users ─────────────────────────────────────────────
@router.get("/list", response_model=dict)
def list_users(created_by: str = "", user: dict = Depends(get_current_user)):
    """
    **List all registered Users & Supervisors**

    SP call: `PRC_UserSupplier_EndUser @Type = 'SELECT'`

    Query params:
    - `created_by`: Filter by creator user ID (optional)
    """
    logger.info("Listing users (created_by=%s)", created_by)
    result = service.get_all_users("", created_by)
    return result


# ── 6. Get Groups (dropdown) ──────────────────────────────────────
@router.get("/groups", response_model=dict)
def get_groups(user: dict = Depends(get_current_user)):
    """
    **Get available user groups**

    Returns GroupID/GroupName pairs for the registration dropdown.
    Use GroupID when registering a user or supervisor.

    SP call: `PRC_UserSupplier_EndUser @Type = 'SELECT_GROUP'`
    """
    logger.info("Fetching user groups")
    result = service.get_groups()
    return result


# ── 7. Get Plants (dropdown) ──────────────────────────────────────
@router.get("/plants", response_model=dict)
def get_plants(created_by: str = "", user: dict = Depends(get_current_user)):
    """
    **Get available plant codes**

    Returns PlantCode/PlantName pairs for the registration dropdown.

    SP call: `PRC_UserSupplier_EndUser @Type = 'Get_Plant'`
    """
    logger.info("Fetching plants (created_by=%s)", created_by)
    result = service.get_plants(created_by)
    return result


# ── 8. Get Packing Stations (dropdown) ────────────────────────────
@router.get("/stations", response_model=dict)
def get_packing_stations(plant_code: str, supplier_code: str, user: dict = Depends(get_current_user)):
    """
    **Get packing stations for a plant**

    Returns StationNo/StationName pairs for the registration dropdown.

    SP call: `PRC_UserSupplier_EndUser @Type = 'Get_Packing_Station'`
    """
    logger.info("Fetching packing stations for plant=%s, supplier=%s", plant_code, supplier_code)
    result = service.get_packing_stations(plant_code, supplier_code)
    return result
