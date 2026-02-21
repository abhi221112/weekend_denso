# Traceability Tag Print - API Documentation

## Overview
This document describes the complete API flow for the Traceability Tag Print workflow based on the provided screenshots. The workflow supports model selection with supervisor authentication and field locking/unlocking.

---

## API Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                   TRACEABILITY TAG WORKFLOW                      │
└─────────────────────────────────────────────────────────────────┘

Step 1: User Login
├── POST /api/traceability/login
└── Returns: User profile with plant & line info

Step 2: Open Traceability Tab (Auto-fill Plant/Line)
├── POST /api/traceability/traceability-user
└── Returns: Plant, Line, SupplierCode auto-filled

Step 3: Click "Model Change" → Supervisor Auth
├── POST /api/traceability/supervisor-login
└── Requires: Supervisor credentials with rights (ScreenId 3002/2003)

Step 4: Get Model List (after supervisor auth)
├── POST /api/traceability/model-list
└── Returns: Available models for selection

Step 5: Select Model & Click Confirm
├── POST /api/traceability/confirm-model
└── Returns: All field values (Auto-fill: Customer Part No., Part Name, etc.)

Step 6: Click Lock Button (Optional)
├── POST /api/traceability/lock-fields
└── Result: Fields become READ-ONLY (greyed out)

Step 7: Click Unlock Button (if locked)
├── POST /api/traceability/unlock-fields
├── Requires: Supervisor authentication again
└── Result: Fields become EDITABLE
```

---

## API Endpoints

### 1. Login (Initial App Login)
**Endpoint:** `POST /api/traceability/login`

**Purpose:** D-TRACE Users login (EOL User / EOL Supervisor)

**Request Body:**
```json
{
  "user_id": "1111",
  "password": "password123"
}
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "user_id": "1111",
    "user_name": "Mukesh",
    "email_id": "mukesh@example.com",
    "group_name": "EOL User",
    "supplier_code": "SUPPLIER001",
    "denso_plant": "Gr. Noida",
    "supplier_plant_code": "GN001",
    "packing_station": "Station-1",
    "plant_name": "Gr. Noida"
  }
}
```

**Stored Procedure:** `[dbo].[PRC_UserSupplier_EndUser] @Type = 'VALIDATEUSER_PC'`

---

### 2. Get Traceability User Details (Auto-fill Plant/Line)
**Endpoint:** `POST /api/traceability/traceability-user`

**Purpose:** Auto-fill Plant and Line when user opens Traceability Tag screen

**Request Body:**
```json
{
  "user_id": "1111",
  "password": "password123"
}
```

**Response (Success):**
```json
{
  "success": true,
  "message": "User details fetched",
  "data": {
    "supplier_code": "SUPPLIER001",
    "supplier_plant_code": "GN001",
    "packing_station": "Station-1",
    "user_id": "1111",
    "user_name": "Mukesh",
    "plant_name": "Gr. Noida"
  }
}
```

**Fields Auto-filled in UI:**
- Plant: `denso_plant`
- Line: `packing_station` (PackingStation)

**Stored Procedure:** `[dbo].[PRC_UserSupplier_EndUser] @Type = 'VALIDATEUSER'`

---

### 3. Supervisor Login (Model Change Authorization)
**Endpoint:** `POST /api/traceability/supervisor-login`

**Purpose:** Authenticate supervisor when "Model Change" button is clicked

**Request Body:**
```json
{
  "user_id": "SUPERVISOR001",
  "password": "supervisor_password"
}
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Supervisor validated",
  "data": {
    "user_id": "SUPERVISOR001",
    "user_name": "Supervisor Name",
    "group_name": "SUPERVISOR",
    "supplier_code": "SUPPLIER001",
    "packing_station": "Station-1"
  }
}
```

**Response (Failure - Invalid Credentials):**
```json
{
  "success": false,
  "message": "Supervisor authentication failed or insufficient rights"
}
```

**Authorization:** Only users with ScreenId 3002/2003 can authenticate as supervisors

**Stored Procedure:** `[dbo].[PRC_UserSupplier_EndUser] @Type = 'VALIDATE_DEVICE_SUPERVISOR'`

---

### 4. Get Available Models
**Endpoint:** `POST /api/traceability/model-list`

**Purpose:** Get list of all available models/parts after supervisor authentication

**Request Body:**
```json
{
  "supplier_part_no": "HA229876-0471",
  "supplier_code": "SUPPLIER001",
  "plant_code": "Gr. Noida",
  "station_no": "Station-1"
}
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Found 3 model(s)",
  "data": [
    {
      "supplier_part": "HA229876-0471",
      "supplier_part_name": "PLATE REAR",
      "part_no": "HA229876-0471",
      "part_name": "PLATE REAR",
      "lot_size": 72,
      "supplier_part_lot_size": "72",
      "supplier_part_weight": 9216,
      "bin_qty": 72,
      "tolerance_weight": null,
      "weighing_scale": "Yes",
      "batch_size": 72,
      "weight_g": 9216,
      "lot_lock_type": "Enable",
      "total_no_of_digits": 0,
      "no_of_steps": 0
    },
    {
      "supplier_part": "HA210517-00701U",
      "part_name": "DIFFERENT PART",
      ...
    }
  ]
}
```

**UI Display:**
The supervisor will see a dropdown/list showing:
- Part Name
- Supplier Part No.
- Model Details

**Stored Procedure:** `[dbo].[PRC_PrintKanban] @Type = 'GET_PRINT_PARAMETER'`

---

### 5. Confirm Model Selection (Auto-fill All Fields)
**Endpoint:** `POST /api/traceability/confirm-model`

**Purpose:** When supervisor selects a model and clicks "Confirm", auto-fill all form fields

**Request Body:**
```json
{
  "supplier_part_no": "HA229876-0471",
  "supplier_code": "SUPPLIER001",
  "plant_code": "Gr. Noida",
  "station_no": "Station-1"
}
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Model details loaded successfully",
  "data": {
    "supplier_part": "HA229876-0471",
    "supplier_part_name": "PLATE REAR",
    "part_no": "HA229876-0471",
    "part_name": "PLATE REAR",
    "lot_size": 72,
    "supplier_part_lot_size": "72",
    "supplier_part_weight": 9216,
    "bin_qty": 72,
    "tolerance_weight": null,
    "weighing_scale": "Yes",
    "image_name": null,
    "supplied_code": "SUPPLIER001",
    "batch_size": 72,
    "weight_g": 9216,
    "qty": null,
    "lot_lock_type": "Enable",
    "total_no_of_digits": 0,
    "no_of_steps": 0,
    "step_1_scan_type": "Enter",
    "step_2_scan_type": "Enter",
    "delimiter_type": "Enter",
    "character_length_from": 0,
    "character_length_to": 0
  }
}
```

**Fields Auto-filled in UI (from response):**
| UI Field | Source Field |
|----------|---|
| Customer Part No. | `part_no` |
| Part Name | `part_name` |
| Supplier Part No. | `supplier_part` |
| Batch Size | `lot_size` |
| Weight (g) | `supplier_part_weight` |
| Tag Stock In | `bin_qty` |
| Weighing Scale | `weighing_scale` |
| Model Lock Type | `lot_lock_type` |

**Stored Procedure:** `[dbo].[PRC_PrintKanban] @Type = 'GET_PRINT_PARAMETER'`

---

### 6. Lock Fields (Make Read-Only)
**Endpoint:** `POST /api/traceability/lock-fields`

**Purpose:** Lock form fields to make them read-only (greyed out)

**UI Trigger:** User clicks the **Lock** button 🔒

**Request Body:**
```json
{
  "supplier_code": "SUPPLIER001",
  "plant_code": "Gr. Noida",
  "station_no": "Station-1"
}
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Fields locked successfully",
  "locked": true,
  "data": {
    "supplier_code": "SUPPLIER001",
    "plant_code": "Gr. Noida",
    "station_no": "Station-1"
  }
}
```

**UI State Change:**
- ✅ Fields become READ-ONLY (greyed out, cannot edit)
- ✅ Lock icon appears (🔒 visibility icon)
- ✅ Unlock button becomes visible

---

### 7. Unlock Fields (Requires Supervisor Auth)
**Endpoint:** `POST /api/traceability/unlock-fields`

**Purpose:** Unlock form fields to make them editable (requires supervisor login)

**UI Trigger:** User clicks the **Unlock** button 🔓 → Supervisor Login Dialog Opens

**Request Body:**
```json
{
  "user_id": "SUPERVISOR001",
  "password": "supervisor_password",
  "supplier_code": "SUPPLIER001",
  "plant_code": "Gr. Noida",
  "station_no": "Station-1"
}
```

**Response (Success - Supervisor Authenticated):**
```json
{
  "success": true,
  "message": "Fields unlocked successfully",
  "unlocked": true,
  "supervisor_verified": true,
  "data": {
    "user_id": "SUPERVISOR001",
    "user_name": "Supervisor Name",
    "email_id": "supervisor@example.com",
    "supplier_code": "SUPPLIER001",
    "packing_station": "Station-1"
  }
}
```

**Response (Failure - Invalid Supervisor Credentials):**
```json
{
  "success": false,
  "message": "Supervisor authentication failed",
  "unlocked": false,
  "supervisor_verified": false
}
```

**UI State Change (on success):**
- ✅ Fields become EDITABLE (no longer greyed out)
- ✅ Lock icon disappears
- ✅ User can now modify field values
- ✅ Unlock button changes back to Lock button

**Security:**
- Only users with supervisor rights (ScreenId 3002/2003) can unlock fields
- Supervisor credentials are verified before unlocking
- Attempt history is logged

---

## Workflow Summary

### Happy Path (Complete Workflow)
```
1. User logs in              → /login
2. Opens Traceability Tab   → /traceability-user (auto-fills Plant, Line)
3. Clicks "Model Change"    → /supervisor-login (supervisor auth)
4. Gets model list          → /model-list
5. Selects model, clicks    
   "Confirm"                → /confirm-model (auto-fills all fields)
6. Clicks Lock button       → /lock-fields (makes fields read-only)
7. Wants to edit, clicks    
   Unlock                   → /unlock-fields (requires supervisor auth again)
```

---

## Database Schema Reference

### Stored Procedures Used

| SP Name | @Type Value | Purpose |
|---------|------------|---------|
| `[dbo].[PRC_UserSupplier_EndUser]` | `VALIDATEUSER_PC` | Initial app login |
| `[dbo].[PRC_UserSupplier_EndUser]` | `VALIDATEUSER` | Get user traceability details |
| `[dbo].[PRC_UserSupplier_EndUser]` | `VALIDATE_DEVICE_SUPERVISOR` | Supervisor authentication |
| `[dbo].[PRC_PrintKanban]` | `GET_PRINT_PARAMETER` | Get model list & details |

### Key Tables
- `TM_Supplier_End_User` - Supplier end users
- `TM_DnhaPart_And_SupplierPart_Mapping` - Part mappings
- `TM_Supplier_Lot_Structure` - Lot/batch structure
- `TM_Supplier_Station_Part_Mapping` - Station-part mappings
- `TM_Company` - Company master
- `TM_Supplier_Customer` - Customer-supplier relationships

---

## Error Handling

### Common Error Responses

**Invalid Credentials:**
```json
{
  "success": false,
  "message": "Invalid user ID or password"
}
```

**Insufficient Rights:**
```json
{
  "success": false,
  "message": "Supervisor authentication failed or insufficient rights"
}
```

**Model Not Found:**
```json
{
  "success": false,
  "message": "No models found for this supplier part"
}
```

**Field State Error:**
```json
{
  "success": false,
  "message": "Failed to lock fields"
}
```

---

## Request/Response Headers

**Standard Headers (all requests):**
```
Content-Type: application/json
Accept: application/json
```

**HTTP Status Codes:**
- `200 OK` - Successful request
- `400 Bad Request` - Invalid parameters or business logic error
- `401 Unauthorized` - Invalid credentials for initial login
- `403 Forbidden` - Insufficient permissions (supervisor required, etc.)
- `404 Not Found` - Resource not found

---

## Security Notes

1. **Supervisor-Only Operations:**
   - Model Change requires supervisor login
   - Unlock Fields requires fresh supervisor authentication
   - Only users with ScreenId 3002/2003 can perform supervisor actions

2. **Field Locking:**
   - Locked fields prevent accidental data modification
   - Read-only state is enforced both in UI and API validation
   - Only supervisors can unlock

3. **Authentication:**
   - Credentials are validated against database
   - Session should be maintained for efficient user experience
   - Password transmission should use HTTPS

---

## Integration Notes

### Frontend Implementation
1. After `/supervisor-login` success, enable "Model Change" button
2. Call `/model-list` and display dropdown of available models
3. After model selection and `/confirm-model` call, auto-populate all fields
4. Lock/unlock features should toggle field edit states
5. Validation should prevent field edits when locked

### BLocker Flow
The APIs can be called in sequence as per the workflow without any blocking conditions.

---

## Example Usage (cURL)

```bash
# 1. Login
curl -X POST http://localhost:8000/api/traceability/login \
  -H "Content-Type: application/json" \
  -d '{"user_id":"1111", "password":"password123"}'

# 2. Get Traceability User Details
curl -X POST http://localhost:8000/api/traceability/traceability-user \
  -H "Content-Type: application/json" \
  -d '{"user_id":"1111", "password":"password123"}'

# 3. Supervisor Login
curl -X POST http://localhost:8000/api/traceability/supervisor-login \
  -H "Content-Type: application/json" \
  -d '{"user_id":"SUPERVISOR001", "password":"supervisor_password"}'

# 4. Get Model List
curl -X POST http://localhost:8000/api/traceability/model-list \
  -H "Content-Type: application/json" \
  -d '{
    "supplier_part_no": "HA229876-0471",
    "supplier_code": "SUPPLIER001",
    "plant_code": "Gr. Noida",
    "station_no": "Station-1"
  }'

# 5. Confirm Model Selection
curl -X POST http://localhost:8000/api/traceability/confirm-model \
  -H "Content-Type: application/json" \
  -d '{
    "supplier_part_no": "HA229876-0471",
    "supplier_code": "SUPPLIER001",
    "plant_code": "Gr. Noida",
    "station_no": "Station-1"
  }'

# 6. Lock Fields
curl -X POST http://localhost:8000/api/traceability/lock-fields \
  -H "Content-Type: application/json" \
  -d '{
    "supplier_code": "SUPPLIER001",
    "plant_code": "Gr. Noida",
    "station_no": "Station-1"
  }'

# 7. Unlock Fields
curl -X POST http://localhost:8000/api/traceability/unlock-fields \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "SUPERVISOR001",
    "password": "supervisor_password",
    "supplier_code": "SUPPLIER001",
    "plant_code": "Gr. Noida",
    "station_no": "Station-1"
  }'
```

---

**Document Version:** 1.0  
**Last Updated:** 2026-02-20  
**Author:** GitHub Copilot
