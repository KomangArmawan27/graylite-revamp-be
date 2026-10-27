# Front-End Integration Guide

This guide outlines the standard integration flow for building a client application (Flutter, Web, etc.) against the metadata-driven ERP API (`/v1`).

---

## Core Principles

1. **Metadata-Driven UI:** There is no hardcoded per-screen logic. The UI structure, columns, form fields, filters, and actions are rendered dynamically from the metadata endpoints (`/v1/meta/...`).
2. **Naming Conventions:**
   - **Meta properties use `camelCase`** (e.g., `schemaVersion`, `dateColumn`, `detailHdrId`).
   - **Row and field data use database column names verbatim** (e.g., `doc_id`, `doc_no`, `trans_qty`).
3. **Authentication:** All `/v1/` endpoints (except login) require an `Authorization: Bearer <accessToken>` header.
4. **Pagination:** List endpoints use keyset (cursor) paging (`pageSize`, `cursor`, `q`, `sort`).

---

## Standard Application Flow

### Step 1: Authentication & User Session
- **Login:** Send credentials to `POST /v1/auth/login`.
  - Request: `{ "login": "username", "password": "..." }`
  - Response: Returns `accessToken`, `refreshToken`, and user info (`user.id`, `user.login`, `user.roles`, `ccId`, etc.).
- **Verify Session (Optional):** Call `GET /v1/me` to get current user details and permissions.
- **Refresh Token:** Use `POST /v1/auth/refresh` when the access token expires.
- **Logout:** Call `POST /v1/auth/logout`.

### Step 2: Navigation & Menu
- **Fetch Menu:** Call `GET /v1/menu`.
- **Render Menu:** Display the tree/list of navigation items returned by the server. Each item provides an `hdrId` (or screen code) corresponding to a browser, form, report, or dashboard.

### Step 3: Opening a Browser (List View)
When the user taps a menu item of type `BROWSER`:
1. **Fetch Browser Metadata:** Call `GET /v1/meta/browser/{hdrId}`.
   - Response contains:
     - `columns`: Column definitions (name, caption, type, width, visibility).
     - `filters`: Dynamic filters required or optional for this browser (e.g., `ADate`, `BDate`), including default values and requirement status (`required: true/false`).
     - `layout`: UI rendering hints (`title`, `date`, `subtitle`, `badge`, `metrics`, `details`).
     - `canAdd` / `canRemove`: Permission flags.
     - `detailCode` / `detailHdrId`: Target form ID when tapping a row or adding a record.
     - `commands`: Allowed toolbar actions for the user.
2. **Fetch Browser Rows:** Call `GET /v1/browsers/{hdrId}/rows` with required filter parameters and pagination options.
   - Example: `GET /v1/browsers/128/rows?ADate=2026-01-01&BDate=2026-12-31&pageSize=50`
   - Response: `{ "items": [...], "pageSize": 50, "hasMore": true, "nextCursor": "..." }`

### Step 4: Viewing, Creating, or Editing Records (Forms)
When the user taps a row (view/edit) or taps "Add" (`canAdd == true`):
1. **Fetch Form Metadata:** Call `GET /v1/meta/form/{detailHdrId}`.
   - Returns tabs, field definitions, widgets (`col_uitype`), pickers, formulas, and embedded grids.
2. **Fetch Field Options (for comboboxes/pickers):** If a field uses `combobox`, `comboquery`, or `xcomboquery`, call `GET /v1/forms/{hdrId}/fields/{name}/options`.
3. **Load Record Data:**
   - **For New Record:** Call `GET /v1/forms/{detailHdrId}/new` to obtain a blank record pre-filled with default values and server-side session expressions.
   - **For Existing Record:** Call `GET /v1/forms/{detailHdrId}/records/{recordId}` to load header fields and embedded grid rows.
4. **Save Record:**
   - **Create:** `POST /v1/forms/{detailHdrId}/records` with payload matching database field names.
   - **Update:** `PUT /v1/forms/{detailHdrId}/records/{recordId}`.

### Step 5: Standalone Grids & Pickers
- **Grids:** Fetch standalone grid data via `GET /v1/grids/{hdrId}/rows?parentId={id}` or associated filters.
- **Pickers:** Search picker records via `GET /v1/pickers/{hdrId}/rows?q={query}`.

### Step 6: Executing Toolbar Commands
- When the user clicks a command button returned in browser/form metadata, execute it via:
  - `POST /v1/screens/{hdrId}/commands/{cmdId}/run`

---

## Error Handling

All error responses follow a standard envelope:
```json
{
  "error": {
    "code": "invalid_filter",
    "message": "Required filter 'ADate' is missing",
    "requestId": "27cfba58115a4cf6a4587d4fd93dba41",
    "details": [
      {
        "field": "ADate",
        "code": "required",
        "problem": "Required filter missing"
      }
    ]
  }
}
```
- Handle HTTP status codes (`400 ValidationFailed`, `401 Unauthorized`, `403 Forbidden`, `404 NotFound`, `500 InternalError`) gracefully in your UI client.
