"""
Pydantic models for Supplier End User registration (User & Supervisor).
Maps to DB table: [dbo].[TM_Supplier_End_User]
"""

from pydantic import BaseModel, Field
from typing import Optional


# ── Request Models ────────────────────────────────────────────────

class SupplierEndUserCreate(BaseModel):
    """Request body to register a new Supplier End User or Supervisor."""
    user_id: str = Field(..., min_length=1, max_length=50, description="Unique User ID")
    user_name: str = Field(..., min_length=1, max_length=50, description="Full name of the user")
    password: str = Field(..., min_length=4, max_length=50, description="User password")
    supplier_plant_code: str = Field(..., min_length=1, max_length=20, description="Plant code (e.g. PLANT01)")
    supplier_code: Optional[str] = Field(None, max_length=100, description="Supplier code (auto-filled from admin)")
    denso_plant: Optional[str] = Field(None, max_length=20, description="Denso plant code")
    packing_station: Optional[str] = Field(None, max_length=50, description="Packing station")
    group_id: int = Field(..., description="Group ID (determines user/supervisor role)")
    email_id: Optional[str] = Field(None, max_length=100, description="Email address")
    supplier_mac_id: Optional[str] = Field(None, max_length=50, description="Supplier MAC ID")
    created_by: Optional[str] = Field(None, max_length=20, description="Created by (auto-set)")


class SupplierEndUserUpdate(BaseModel):
    """Request body to update an existing Supplier End User."""
    user_name: Optional[str] = Field(None, max_length=50)
    password: Optional[str] = Field(None, max_length=50)
    supplier_plant_code: Optional[str] = Field(None, max_length=20)
    supplier_code: Optional[str] = Field(None, max_length=100)
    denso_plant: Optional[str] = Field(None, max_length=20)
    packing_station: Optional[str] = Field(None, max_length=50)
    group_id: Optional[int] = None
    email_id: Optional[str] = Field(None, max_length=100)
    supplier_mac_id: Optional[str] = Field(None, max_length=50)
    updated_by: Optional[str] = Field(None, max_length=20)


class ChangePasswordRequest(BaseModel):
    """Request body to change a user's password."""
    user_id: str = Field(..., min_length=1, max_length=50, description="User ID")
    old_password: str = Field(..., min_length=4, max_length=50, description="Current password")
    new_password: str = Field(..., min_length=4, max_length=50, description="New password")


# ── Response Models ───────────────────────────────────────────────

class SupplierEndUserData(BaseModel):
    """User data returned from DB."""
    user_id: str
    user_name: Optional[str] = None
    supplier_plant_code: Optional[str] = None
    supplier_code: Optional[str] = None
    denso_plant: Optional[str] = None
    packing_station: Optional[str] = None
    group_id: Optional[int] = None
    group_name: Optional[str] = None
    email_id: Optional[str] = None
    is_active: Optional[bool] = True
    created_by: Optional[str] = None
    created_on: Optional[str] = None


class SupplierEndUserResponse(BaseModel):
    """Standard response for a single user operation."""
    success: bool
    message: str
    result: Optional[str] = None
    data: Optional[SupplierEndUserData] = None


class SupplierEndUserList(BaseModel):
    """Response containing a list of users."""
    success: bool
    message: str
    total_records: int = 0
    data: Optional[list[SupplierEndUserData]] = None
