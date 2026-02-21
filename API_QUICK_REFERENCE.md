# Traceability Tag Print - API Quick Reference

## 📋 All Required APIs

### 1️⃣ Login - Initial App Authentication
```
POST /api/traceability/login
```
| Property | Value |
|----------|-------|
| **Purpose** | User login (EOL User / Supervisor) |
| **Auth Required** | No |
| **SP Called** | PRC_UserSupplier_EndUser<br/>@Type = 'VALIDATEUSER_PC' |

**Request:**
```json
{
  "user_id": "1111",
  "password": "password"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "user_id": "1111",
    "user_name": "Mukesh",
    "email_id": "email@example.com",
    "supplier_code": "SUPPLIER001",
    "supplier_plant_code": "GN001",
    "packing_station": "Station-1"
  }
}
```

---

### 2️⃣ Get Traceability User - Auto-fill Plant & Line
```
POST /api/traceability/traceability-user
```
| Property | Value |
|----------|-------|
| **Purpose** | Auto-fill Plant and Line fields |
| **Auth Required** | No (uses User ID + Password) |
| **SP Called** | PRC_UserSupplier_EndUser<br/>@Type = 'VALIDATEUSER' |

**Request:**
```json
{
  "user_id": "1111",
  "password": "password"
}
```

**Response:**
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

---

### 3️⃣ Supervisor Login - Model Change Authorization
```
POST /api/traceability/supervisor-login
```
| Property | Value |
|----------|-------|
| **Purpose** | Authenticate supervisor (ScreenId 3002/2003) |
| **Auth Required** | Supervisor rights check |
| **SP Called** | PRC_UserSupplier_EndUser<br/>@Type = 'VALIDATE_DEVICE_SUPERVISOR' |

**Request:**
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
    "supplier_code": "SUPPLIER001"
  }
}
```

---

### 4️⃣ Get Model List - Available Models
```
POST /api/traceability/model-list
```
| Property | Value |
|----------|-------|
| **Purpose** | Get list of models for the supplier part |
| **Auth Required** | Yes (supervisor must be logged in) |
| **SP Called** | PRC_PrintKanban<br/>@Type = 'GET_PRINT_PARAMETER' |

**Request:**
```json
{
  "supplier_part_no": "HA229876-0471",
  "supplier_code": "SUPPLIER001",
  "plant_code": "Gr. Noida",
  "station_no": "Station-1"
}
```

**Response:**
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
      "supplier_part_weight": 9216,
      "weighing_scale": "Yes",
      "ton_lock_type": "Enable"
    }
  ]
}
```

---

### 5️⃣ Confirm Model Selection - Auto-Fill All Fields
```
POST /api/traceability/confirm-model
```
| Property | Value |
|----------|-------|
| **Purpose** | Return model details to auto-fill form |
| **Auto-fills** | Part No., Part Name, Batch Size, Weight, Qty, etc. |
| **SP Called** | PRC_PrintKanban<br/>@Type = 'GET_PRINT_PARAMETER' |

**Request:**
```json
{
  "supplier_part_no": "HA229876-0471",
  "supplier_code": "SUPPLIER001",
  "plant_code": "Gr. Noida",
  "station_no": "Station-1"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Model details loaded successfully",
  "data": {
    "part_no": "HA229876-0471",
    "part_name": "PLATE REAR",
    "supplier_part": "HA229876-0471",
    "lot_size": 72,
    "supplier_part_weight": 9216,
    "bin_qty": 72,
    "weighing_scale": "Yes",
    "lot_lock_type": "Enable"
  }
}
```

**Auto-fill Mapping:**
| UI Field | Response Field |
|----------|---|
| Customer Part No. | `part_no` |
| Part Name | `part_name` |
| Supplier Part No. | `supplier_part` |
| Batch Size | `lot_size` |
| Weight (g) | `supplier_part_weight` |
| Tag Stock In | `bin_qty` |
| Weighing Scale | `weighing_scale` |

---

### 6️⃣ Lock Fields - Make Read-Only
```
POST /api/traceability/lock-fields
```
| Property | Value |
|----------|-------|
| **Purpose** | Lock fields (make read-only, greyed out) |
| **UI Change** | Fields become disabled, Lock icon visible 🔒 |
| **Trigger** | User clicks Lock button |

**Request:**
```json
{
  "supplier_code": "SUPPLIER001",
  "plant_code": "Gr. Noida",
  "station_no": "Station-1"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Fields locked successfully",
  "locked": true
}
```

---

### 7️⃣ Unlock Fields - Make Editable (Requires Supervisor)
```
POST /api/traceability/unlock-fields
```
| Property | Value |
|----------|-------|
| **Purpose** | Unlock fields (make editable) |
| **Requires** | Fresh supervisor authentication |
| **Auth Check** | ScreenId 3002/2003 required |
| **UI Change** | Fields become enabled, Lock icon disappears |
| **Trigger** | User clicks Unlock button → Supervisor Login Dialog |

**Request:**
```json
{
  "user_id": "SUPERVISOR001",
  "password": "supervisor_password",
  "supplier_code": "SUPPLIER001",
  "plant_code": "Gr. Noida",
  "station_no": "Station-1"
}
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Fields unlocked successfully",
  "unlocked": true,
  "supervisor_verified": true,
  "data": {
    "user_id": "SUPERVISOR001",
    "user_name": "Supervisor Name"
  }
}
```

**Response (Failure):**
```json
{
  "success": false,
  "message": "Supervisor authentication failed",
  "unlocked": false,
  "supervisor_verified": false
}
```

---

## 🔄 Complete Workflow Sequence

```
USER FLOW:
Step 1:  Login
         → POST /api/traceability/login
         ← Get user profile

Step 2:  Open Traceability Tab (auto-fill Plant, Line)
         → POST /api/traceability/traceability-user
         ← Plant, Line populated

Step 3:  Click "Model Change" Button
         → POST /api/traceability/supervisor-login
         ← Supervisor authenticated

Step 4:  System fetches available models
         → POST /api/traceability/model-list
         ← Show dropdown with 3 models (HA229876-0471, HA210517-00701U, etc.)

Step 5:  Supervisor selects model & clicks "Confirm"
         → POST /api/traceability/confirm-model
         ← All fields auto-filled:
            - Customer Part No.: HA229876-0471
            - Part Name: PLATE REAR
            - Batch Size: 72
            - Weight (g): 9216
            - Tag Stock In: 3935
            - Total Qty. Stock In: 283320

Step 6:  User clicks "Lock" Button 🔒
         → POST /api/traceability/lock-fields
         ← Fields become READ-ONLY (greyed out)

Step 7:  (Optional) User clicks "Unlock" Button 🔓
         → Supervisor Login Dialog Opens
         → POST /api/traceability/unlock-fields
         ← If supervisor authenticated, fields become EDITABLE
```

---

## 📊 HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| `200` | Success | Endpoint returns data successfully |
| `400` | Bad Request | Invalid parameters, model not found |
| `401` | Unauthorized | Invalid login credentials |
| `403` | Forbidden | Insufficient supervisor rights |
| `500` | Server Error | Database connection error |

---

## ⚡ Key Points

✅ **Auto-fills:**
- Plant & Line: Step 2 auto-fills based on logged-in user
- All form fields: Step 5 auto-fills after model confirmation

✅ **Lock/Unlock:**
- Lock: Makes fields read-only (greyed out)
- Unlock: Requires supervisor re-authentication with ScreenId 3002/2003

✅ **Supervisor-Only:**
- Model Change (Step 3)
- Unlock Fields (Step 7)

✅ **No Unnecessary Calls:**
- Only 7 APIs, each serves specific purpose
- No duplicate or helper endpoints

---

## 🔐 Security Features

1. **Supervisor Authentication:**
   - ScreenId 3002/2003 check on backend
   - Password validation against database
   - Separate supervisor endpoint

2. **Field Locking:**
   - UI disables input when locked
   - Backend enforces read-only state
   - Only supervisor can unlock

3. **Session Integrity:**
   - Supervisor login required for unlock
   - Cannot bypass with API calls
   - Audit trail can be added

---

**API Version:** v1.0  
**Base URL:** `/api/traceability`  
**Content-Type:** `application/json`
