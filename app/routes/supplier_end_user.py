from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Optional, List
from app.models.supplier_end_user import (
    SupplierEndUserCreate,
    SupplierEndUserUpdate,
    SupplierEndUserResponse,
    SupplierEndUserList
)
from app.services.supplier_end_user_service import SupplierEndUserService

router = APIRouter(
    prefix="/api/supplier-end-user",
    tags=["Supplier End User"],
    responses={404: {"description": "Not found"}},
)

service = SupplierEndUserService()


# Mock authentication - In production, use proper JWT/OAuth2
async def get_current_user(
    x_user_id: str = Header(None),
    x_supplier_code: str = Header(None),
    x_group_name: str = Header(None)
) -> dict:
    """
    Get current user from headers
    In production, use fastapi.security for proper authentication
    """
    if not x_user_id or not x_supplier_code:
        raise HTTPException(status_code=401, detail="Missing authentication headers")
    
    return {
        "user_id": x_user_id,
        "supplier_code": x_supplier_code,
        "group_name": x_group_name or ""
    }


@router.post("/register", response_model=dict)
async def register_user(
    user_data: SupplierEndUserCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Register a new supplier end user
    This endpoint replaces the btnSave_Click with DbType='INSERT'
    
    Equivalent to ASP.NET code:
    ```csharp
    btnSave.Text != "Update"  // true for INSERT
    _plObj.DbType = "INSERT"
    ```
    
    Request Headers:
    - X-User-ID: Current user ID (from session)
    - X-Supplier-Code: Supplier code (from session)
    - X-Group-Name: Group name (from session)
    """
    # Authorization check
    if not current_user.get("user_id"):
        raise HTTPException(status_code=403, detail="Unauthorized action attempted")
    
    # Set created_by from current user
    user_data.created_by = current_user["user_id"]
    user_data.supplier_code = current_user["supplier_code"]
    
    # Call service to create user
    result = service.create_user(user_data)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result


@router.put("/{user_id}", response_model=dict)
async def update_user(
    user_id: str,
    user_data: SupplierEndUserUpdate,
    current_user: dict = Depends(get_current_user)
):
    
    if not current_user.get("user_id"):
        raise HTTPException(status_code=403, detail="Unauthorized action attempted")
    
    # Set updated_by from current user
    user_data.updated_by = current_user["user_id"]
    
    # Call service to update user
    result = service.update_user(
        user_id,
        user_data,
        current_user["supplier_code"]
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result


@router.delete("/{user_id}", response_model=dict)
async def delete_user(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
   
    if not current_user.get("user_id"):
        raise HTTPException(status_code=403, detail="Unauthorized action attempted")
    
    # Call service to delete user
    result = service.delete_user(
        user_id,
        current_user["supplier_code"]
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result


@router.get("/list", response_model=dict)
async def get_users(
    current_user: dict = Depends(get_current_user)
):
    """
    Get all supplier end users
    This endpoint replaces the GetUser() method called from Page_Load
    
    Equivalent to ASP.NET code:
    ```csharp
    _plObj.DbType = "Select"
    CommonHelper.dtBindData = _blObj.BL_ExecuteTask(_plObj)
    CommonHelper.BindGrid(gvMaster, DT)
    ```
    
    Request Headers:
    - X-User-ID: Current user ID (from session)
    - X-Supplier-Code: Supplier code (from session)
    """
    # Call service to fetch all users
    result = service.get_all_users(
        current_user["supplier_code"],
        current_user["user_id"]
    )
    
    return result


@router.get("/{user_id}", response_model=dict)
async def get_user(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific supplier end user by ID
    This endpoint is used when editing a user
    
    Path Parameters:
    - user_id: User ID to fetch
    
    Request Headers:
    - X-User-ID: Current user ID (from session)
    - X-Supplier-Code: Supplier code (from session)
    """
    result = service.get_user(
        user_id,
        current_user["supplier_code"]
    )
    
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["message"])
    
    return result


@router.get("/search/by-column", response_model=dict)
async def search_users(
    column_name: str,
    search_value: str,
    current_user: dict = Depends(get_current_user)
):
 
    # Fetch all users first
    result = service.get_all_users(
        current_user["supplier_code"],
        current_user["user_id"]
    )
    
    if not result["success"]:
        return result
    
    users = result.get("data", [])
    
    # Filter results based on search
    filtered_users = []
    for user in users:
        if column_name in user:
            user_value = str(user[column_name]).lower()
            search_val = search_value.lower()
            
            if search_val in user_value:
                filtered_users.append(user)
    
    return {
        "success": True,
        "message": f"Found {len(filtered_users)} records",
        "result": "Y",
        "total_records": len(filtered_users),
        "search_column": column_name,
        "search_value": search_value,
        "data": filtered_users
    }
