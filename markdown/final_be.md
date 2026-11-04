# Final Backend Documentation & Integration Reference

## 1. Brief Explanation of the Backend Project

This project is a high-performance **FastAPI (Python 3.11+, Synchronous SQLAlchemy 2.0 with `pyodbc`)** backend service designed to expose an existing **metadata-driven SQL Server ERP** database to modern client applications (such as Flutter apps or web portals).

### Key Architectural Principles:
- **No Per-Screen Code:** All screens, grids, forms, pickers, variables, commands, and permissions are defined as configuration rows inside SQL Server database tables (`[System].[Form.*]`). The backend is a generic renderer and engine that reads this metadata, serves it as JSON, and executes generic CRUD and commands accordingly.
- **Database as Source of Truth:** The ERP database schema and config rows remain entirely unchanged. Writes go strictly through the generic save engine to base tables and configured commands.
- **Security & Roles:** Server-side role enforcement based on tokens (`_USERID`, `_USERLOGIN`, `_CCID`, roles). Fails closed.
- **SQL Safety:** Never concatenate values into SQL. All parameters are bound (`?`), and identifiers are quoted.

---

## 2. API Endpoint List

| Method & Path | Purpose |
|---|---|
| `POST /v1/auth/login` | Authenticate user credentials and return JWT tokens |
| `POST /v1/auth/refresh` | Refresh access token using refresh token |
| `POST /v1/auth/logout` | Invalidate current user session |
| `GET /v1/me` | Get current authenticated user details and roles |
| `GET /v1/menu` | Retrieve navigation menu items visible to the user |
| `GET /v1/meta/browser/{hdrId}` | Retrieve browser/list screen metadata & filters |
| `GET /v1/meta/form/{hdrId}` | Retrieve form metadata (tabs, fields, embedded grids) |
| `GET /v1/meta/grid/{hdrId}` | Retrieve standalone grid metadata |
| `GET /v1/meta/picker/{hdrId}` | Retrieve picker columns & metadata |
| `GET /v1/browsers/{hdrId}/rows` | Fetch paginated browser rows with filters & sorting |
| `GET /v1/forms/{hdrId}/new` | Get a blank record pre-filled with default values |
| `GET /v1/forms/{hdrId}/records/{recordId}` | Get an existing record with its child grids |
| `POST /v1/forms/{hdrId}/records` | Create a new record (save engine) |
| `PUT /v1/forms/{hdrId}/records/{recordId}` | Update an existing record |
| `DELETE /v1/forms/{hdrId}/records/{recordId}` | Delete a record (or 501 if disabled) |
| `GET /v1/grids/{hdrId}/rows` | Fetch rows for a standalone grid |
| `GET /v1/pickers/{hdrId}/rows` | Search/fetch picker rows |
| `GET /v1/forms/{hdrId}/fields/{name}/options` | Fetch options for comboboxes / query pickers |
| `POST /v1/screens/{hdrId}/commands/{cmdId}/run` | Execute a toolbar command |
| `GET /v1/admin/lint` | Config linter report (Admin only) |
| `POST /v1/admin/cache/refresh` | Invalidate config cache (Admin only) |
| `GET /health` | Service liveness check |
| `GET /health/db` | Database connectivity check |

---

## 3. Endpoint Explanations & Sample Requests / Responses

### A. Authentication
#### `POST /v1/auth/login`
- **Purpose:** Authenticates user login and returns JWT tokens and user context.
- **Request:**
  ```http
  POST /v1/auth/login
  Content-Type: application/json

  {
    "login": "komang",
    "password": "secretpassword"
  }
  ```
- **Response (`200 OK`):**
  ```json
  {
    "accessToken": "eyJhbGciOiJIUzI1NiIsIn...",
    "refreshToken": "eyJhbGciOiJIUzI1NiIsIn...",
    "expiresIn": 1800,
    "user": {
      "id": 29,
      "login": "komang",
      "name": "Komang",
      "roles": ["General"],
      "ccId": 1,
      "divId": null,
      "wareId": 1
    }
  }
  ```

---

### B. Navigation Menu
#### `GET /v1/menu`
- **Purpose:** Returns the ERP menu tree filtered by the user's roles.
- **Request:**
  ```http
  GET /v1/menu
  Authorization: Bearer <token>
  ```
- **Response (`200 OK`):**
  ```json
  [
    {
      "id": 128,
      "code": "Browser.Sales.Order",
      "caption": "Sales Order",
      "type": "BROWSER",
      "children": []
    }
  ]
  ```

---

### C. Metadata
#### `GET /v1/meta/browser/{hdrId}`
- **Purpose:** Returns schema columns, required/optional filters (`ADate`, `BDate`, etc.), layout hints, and allowed commands for a browser screen.
- **Request:**
  ```http
  GET /v1/meta/browser/128
  Authorization: Bearer <token>
  ```
- **Response (`200 OK`):**
  ```json
  {
    "hdrId": 128,
    "code": "Browser.Sales.Order",
    "caption": "Sales Order",
    "schemaVersion": "a41f09c2",
    "rowKey": "doc_id",
    "dateColumn": "doc_date",
    "detailCode": "Form.Sales.Order",
    "detailHdrId": 145,
    "canAdd": true,
    "canRemove": false,
    "style": "Fit",
    "columns": [
      { "name": "doc_id", "caption": "Doc Id", "type": "integer", "hidden": true, "scale": 0, "width": 100 },
      { "name": "doc_no", "caption": "Doc No", "type": "text", "hidden": false, "scale": 0, "width": 100 },
      { "name": "doc_date", "caption": "Date", "type": "date", "hidden": false, "scale": 0, "width": 100 }
    ],
    "filters": [
      { "name": "ADate", "label": "Date From", "type": "date", "default": "2026-01-01", "required": true, "hidden": false },
      { "name": "BDate", "label": "Date To", "type": "date", "default": "2026-12-31", "required": true, "hidden": false }
    ],
    "layout": { "title": "doc_no", "date": "doc_date", "subtitle": "cust_desc" },
    "commands": []
  }
  ```

---

### D. Browser Data Rows
#### `GET /v1/browsers/{hdrId}/rows`
- **Purpose:** Fetches paginated browser data rows based on filter parameters, search query (`q`), sorting (`sort`), and keyset pagination (`cursor`, `pageSize`).
- **Request:**
  ```http
  GET /v1/browsers/128/rows?ADate=2026-01-01&BDate=2026-12-31&pageSize=50
  Authorization: Bearer <token>
  ```
- **Response (`200 OK`):**
  ```json
  {
    "items": [
      {
        "doc_id": 1001,
        "doc_no": "SO-2026-001",
        "doc_date": "2026-03-15",
        "doc_grandtotal": 150000.00
      }
    ],
    "pageSize": 50,
    "hasMore": false,
    "nextCursor": null
  }
  ```

---

### E. Forms & CRUD
#### `GET /v1/forms/{hdrId}/new`
- **Purpose:** Returns a new blank record pre-filled with default expressions and session variables.
#### `POST /v1/forms/{hdrId}/records`
- **Purpose:** Creates/saves a new document record.
- **Request:**
  ```http
  POST /v1/forms/145/records
  Authorization: Bearer <token>
  Content-Type: application/json

  {
    "doc_date": "2026-03-29",
    "cust_id": 12,
    "doc_total": 500000
  }
  ```
- **Response (`200 OK`):**
  ```json
  {
    "success": true,
    "recordId": 1024,
    "message": "Record saved successfully"
  }
  ```

---

## 4. Expected Integration Flow on the Front-End Side

1. **Authenticate:** Client logs in via `POST /v1/auth/login` and stores the `accessToken`.
2. **Load Menu:** Client requests `GET /v1/menu` to render the navigation drawer/sidebar.
3. **Fetch Metadata:** When a user clicks a menu item (e.g., Browser ID `128`), client calls `GET /v1/meta/browser/128` to inspect columns, required filters (`ADate`, `BDate`), permissions (`canAdd`), and layout.
4. **Query Rows:** Client calls `GET /v1/browsers/128/rows?ADate=...&BDate=...` passing required filters and renders the list using the dynamic layout/columns metadata.
5. **Drill Down / Add:** 
   - Tapping a row opens the detail form (`GET /v1/meta/form/{detailHdrId}` and `GET /v1/forms/{detailHdrId}/records/{recordId}`).
   - Tapping "Add" loads a blank form (`GET /v1/forms/{detailHdrId}/new`) and saves via `POST /v1/forms/{detailHdrId}/records`.
