"""
Service layer – business logic for user/supervisor registration.
Maps raw SP results → typed response models.
"""

from app.data_access import register_dal
from app.models.supplier_end_user import (
    SupplierEndUserCreate,
    SupplierEndUserUpdate,
    SupplierEndUserData,
    ChangePasswordRequest,
)


class SupplierEndUserService:
    """Handles registration, update, delete, and listing of end users."""

    # ─────────────────────────────────────────────────────────────
    # 1.  Create (Register) user / supervisor
    # ─────────────────────────────────────────────────────────────
    def create_user(self, user_data: SupplierEndUserCreate) -> dict:
        """
        Register a new Supplier End User or Supervisor.
        Calls SP @Type = 'INSERT'.
        """
        try:
            result = register_dal.register_user(
                user_id=user_data.user_id,
                user_name=user_data.user_name,
                password=user_data.password,
                supplier_plant_code=user_data.supplier_plant_code,
                supplier_code=user_data.supplier_code or "",
                group_id=user_data.group_id,
                created_by=user_data.created_by or "",
                denso_plant=user_data.denso_plant,
                packing_station=user_data.packing_station,
                email_id=user_data.email_id,
                supplier_mac_id=user_data.supplier_mac_id,
            )

            if result is None:
                return {
                    "success": False,
                    "message": "No response from database",
                    "result": "N",
                }

            db_result = result.get("RESULT", "N")

            if db_result == "Y":
                return {
                    "success": True,
                    "message": "User registered successfully",
                    "result": "Y",
                    "data": {
                        "user_id": user_data.user_id,
                        "user_name": user_data.user_name,
                        "group_id": user_data.group_id,
                        "supplier_plant_code": user_data.supplier_plant_code,
                    },
                }
            else:
                # SP returns error message in RESULT column for duplicates
                return {
                    "success": False,
                    "message": db_result,
                    "result": "N",
                }

        except Exception as e:
            return {
                "success": False,
                "message": f"Registration failed: {str(e)}",
                "result": "N",
            }

    # ─────────────────────────────────────────────────────────────
    # 2.  Update user
    # ─────────────────────────────────────────────────────────────
    def update_user(
        self, user_id: str, user_data: SupplierEndUserUpdate, supplier_code: str
    ) -> dict:
        """Update an existing user. Calls SP @Type = 'UPDATE'."""
        try:
            result = register_dal.update_user(
                user_id=user_id,
                user_name=user_data.user_name or "",
                password=user_data.password or "",
                supplier_plant_code=user_data.supplier_plant_code or "",
                supplier_code=supplier_code,
                group_id=user_data.group_id or 0,
                created_by=user_data.updated_by or "",
                email_id=user_data.email_id,
            )

            if result is None:
                return {"success": False, "message": "No response from database"}

            if result.get("RESULT") == "Y":
                return {"success": True, "message": "User updated successfully"}
            else:
                return {"success": False, "message": result.get("RESULT", "Update failed")}

        except Exception as e:
            return {"success": False, "message": f"Update failed: {str(e)}"}

    # ─────────────────────────────────────────────────────────────
    # 3.  Delete user
    # ─────────────────────────────────────────────────────────────
    def delete_user(self, user_id: str, supplier_code: str) -> dict:
        """Delete a user. Calls SP @Type = 'DELETE'."""
        try:
            result = register_dal.delete_user(user_id)

            if result is None:
                return {"success": False, "message": "No response from database"}

            if result.get("RESULT") == "Y":
                return {"success": True, "message": "User deleted successfully"}
            else:
                return {"success": False, "message": result.get("RESULT", "Delete failed")}

        except Exception as e:
            return {"success": False, "message": f"Delete failed: {str(e)}"}

    # ─────────────────────────────────────────────────────────────
    # 4.  Get all users
    # ─────────────────────────────────────────────────────────────
    def get_all_users(self, supplier_code: str, created_by: str) -> dict:
        """Get all users. Calls SP @Type = 'SELECT'."""
        try:
            rows = register_dal.get_all_users(created_by)

            users = []
            for row in rows:
                users.append({
                    "user_id": row.get("UserID", ""),
                    "user_name": row.get("UserName", ""),
                    "supplier_plant_code": row.get("SupplierPlantCode", ""),
                    "group_id": row.get("GroupID"),
                    "group_name": row.get("GroupName", ""),
                    "created_by": row.get("CreatedBy", ""),
                    "created_on": row.get("CreatedOn", ""),
                })

            return {
                "success": True,
                "message": f"Found {len(users)} user(s)",
                "result": "Y",
                "total_records": len(users),
                "data": users,
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to fetch users: {str(e)}",
                "data": [],
            }

    # ─────────────────────────────────────────────────────────────
    # 5.  Get single user
    # ─────────────────────────────────────────────────────────────
    def get_user(self, user_id: str, supplier_code: str) -> dict:
        """Get a single user by ID from the user list."""
        try:
            rows = register_dal.get_all_users("")
            for row in rows:
                if row.get("UserID") == user_id:
                    return {
                        "success": True,
                        "message": "User found",
                        "data": {
                            "user_id": row.get("UserID", ""),
                            "user_name": row.get("UserName", ""),
                            "supplier_plant_code": row.get("SupplierPlantCode", ""),
                            "group_id": row.get("GroupID"),
                            "group_name": row.get("GroupName", ""),
                            "created_by": row.get("CreatedBy", ""),
                            "created_on": row.get("CreatedOn", ""),
                        },
                    }
            return {"success": False, "message": "User not found"}

        except Exception as e:
            return {"success": False, "message": f"Failed: {str(e)}"}

    # ─────────────────────────────────────────────────────────────
    # 6.  Get groups (for dropdown)
    # ─────────────────────────────────────────────────────────────
    def get_groups(self) -> dict:
        """Get available user groups. Calls SP @Type = 'SELECT_GROUP'."""
        try:
            rows = register_dal.get_user_groups()
            groups = [
                {"group_id": r.get("GroupID"), "group_name": r.get("GroupName", "")}
                for r in rows
            ]
            return {
                "success": True,
                "message": f"Found {len(groups)} group(s)",
                "data": groups,
            }
        except Exception as e:
            return {"success": False, "message": f"Failed: {str(e)}", "data": []}

    # ─────────────────────────────────────────────────────────────
    # 7.  Get plants (for dropdown)
    # ─────────────────────────────────────────────────────────────
    def get_plants(self, created_by: str) -> dict:
        """Get available plants. Calls SP @Type = 'Get_Plant'."""
        try:
            rows = register_dal.get_plants(created_by)
            plants = [
                {"plant_code": r.get("PlantCode", ""), "plant_name": r.get("PlantName", "")}
                for r in rows
            ]
            return {
                "success": True,
                "message": f"Found {len(plants)} plant(s)",
                "data": plants,
            }
        except Exception as e:
            return {"success": False, "message": f"Failed: {str(e)}", "data": []}

    # ─────────────────────────────────────────────────────────────
    # 8.  Get packing stations (for dropdown)
    # ─────────────────────────────────────────────────────────────
    def get_packing_stations(self, plant_code: str, supplier_code: str) -> dict:
        """Get packing stations for a plant. Calls SP @Type = 'Get_Packing_Station'."""
        try:
            rows = register_dal.get_packing_stations(plant_code, supplier_code)
            stations = [
                {"station_no": r.get("StationNo", ""), "station_name": r.get("StationName", "")}
                for r in rows
            ]
            return {
                "success": True,
                "message": f"Found {len(stations)} station(s)",
                "data": stations,
            }
        except Exception as e:
            return {"success": False, "message": f"Failed: {str(e)}", "data": []}

    # ─────────────────────────────────────────────────────────────
    # 9.  Change password
    # ─────────────────────────────────────────────────────────────
    def change_password(self, data: ChangePasswordRequest) -> dict:
        """
        Change user password.
        Calls SP @Type = 'UPDATEPASSWORD' (old password verified by SP).
        """
        try:
            if data.old_password == data.new_password:
                return {
                    "success": False,
                    "message": "New password cannot be the same as the old password",
                }

            result = register_dal.change_password(
                user_id=data.user_id,
                old_password=data.old_password,
                new_password=data.new_password,
            )

            if result is None:
                return {"success": False, "message": "No response from database"}

            db_result = result.get("RESULT", "N")

            if db_result == "Y":
                return {"success": True, "message": "Password changed successfully"}
            else:
                return {"success": False, "message": db_result}

        except Exception as e:
            return {"success": False, "message": f"Password change failed: {str(e)}"}
