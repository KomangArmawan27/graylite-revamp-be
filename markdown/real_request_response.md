# ERP API Request & Response Reference

This document provides formatted and easy-to-read examples of requests and responses for the core ERP API endpoints.

---

## 1. Get Navigation Menu
- **Endpoint:** `GET /v1/menu`
- **Purpose:** Retrieves the navigation menu tree visible to the authenticated user based on their roles.

### Request
```bash
curl -X 'GET' \
  'http://127.0.0.1:8000/v1/menu' \
  -H 'accept: */*' \
  -H 'Authorization: Bearer <TOKEN>'
```

### Response (`200 OK`)
```json
{
  "count": 118,
  "items": [
    {
      "hdrId": 116,
      "code": "Browser.Accounting.Beginning",
      "caption": "Account Beg. Balance",
      "type": "browser",
      "module": "Accounting",
      "group": null,
      "detailHdrId": 118
    },
    {
      "hdrId": 128,
      "code": "Browser.Sales.Order",
      "caption": "Sales Order",
      "type": "browser",
      "module": "Sales",
      "group": null,
      "detailHdrId": 129
    }
  ]
}
```

---

## 2. Get Browser (List) Metadata
- **Endpoint:** `GET /v1/meta/browser/{hdrId}`
- **Purpose:** Retrieves configuration metadata for a browser screen, including columns, filters (`ADate`, `BDate`), layout hints, and permissions.

### Request
```bash
curl -X 'GET' \
  'http://127.0.0.1:8000/v1/meta/browser/128' \
  -H 'accept: */*' \
  -H 'Authorization: Bearer <TOKEN>'
```

### Response (`200 OK`)
```json
{
  "hdrId": 128,
  "code": "Browser.Sales.Order",
  "caption": "Sales Order",
  "schemaVersion": "f8b603a8",
  "rowKey": "doc_id",
  "dateColumn": "doc_date",
  "detailCode": "Form.Sales.Order",
  "detailHdrId": 129,
  "canAdd": false,
  "canRemove": false,
  "style": "Fit",
  "columns": [
    {
      "name": "doc_id",
      "caption": "Doc Id",
      "type": "integer",
      "hidden": true,
      "scale": 0,
      "width": 50
    },
    {
      "name": "doc_no",
      "caption": "Doc.No.",
      "type": "text",
      "hidden": false,
      "scale": 0,
      "width": 75
    },
    {
      "name": "doc_date",
      "caption": "SO Date",
      "type": "date",
      "hidden": false,
      "scale": 0,
      "width": 75
    },
    {
      "name": "cust_desc",
      "caption": "Customer Name",
      "type": "text",
      "hidden": false,
      "scale": 0,
      "width": 350
    },
    {
      "name": "doc_grandtotal",
      "caption": "Total",
      "type": "money",
      "hidden": false,
      "scale": 0,
      "width": 120
    },
    {
      "name": "flow_state",
      "caption": "State",
      "type": "text",
      "hidden": false,
      "scale": 0,
      "width": 100
    }
  ],
  "filters": [
    {
      "name": "ADate",
      "label": "Date From",
      "type": "date",
      "default": "DATEADD(-360,TODAY())",
      "required": true,
      "hidden": false
    },
    {
      "name": "BDate",
      "label": "Date To",
      "type": "date",
      "default": "EDOM(NOW())",
      "required": true,
      "hidden": false
    }
  ],
  "layout": {
    "title": "doc_no",
    "date": "doc_date",
    "subtitle": "cust_desc",
    "badge": ["flow_state"],
    "metrics": ["doc_grandtotal"],
    "details": ["doc_extern"]
  },
  "commands": []
}
```

---

## 3. Get Form Metadata
- **Endpoint:** `GET /v1/meta/form/{hdrId}`
- **Purpose:** Retrieves form structure, tabs, field definitions, widgets, child grids, and schema version.

### Request
```bash
curl -X 'GET' \
  'http://127.0.0.1:8000/v1/meta/form/129' \
  -H 'accept: */*' \
  -H 'Authorization: Bearer <TOKEN>'
```

### Response (`200 OK`)
```json
{
  "hdrId": 129,
  "code": "Form.Sales.Order",
  "caption": "Sales Order",
  "schemaVersion": "18dbdf28",
  "idField": "doc_id",
  "titleFields": ["doc_no"],
  "docHeader": null,
  "canSave": true,
  "journalView": false,
  "tabs": [
    {
      "name": "General",
      "fields": [
        {
          "name": "doc_id",
          "caption": "Doc Id",
          "widget": "text",
          "dataType": "number",
          "readonly": true,
          "hidden": false,
          "update": true,
          "inlineWithPrevious": false
        },
        {
          "name": "doc_no",
          "caption": "SO#",
          "widget": "text",
          "dataType": "text",
          "readonly": true,
          "hidden": false,
          "update": true,
          "inlineWithPrevious": false
        },
        {
          "name": "doc_date",
          "caption": "SO Date",
          "widget": "date",
          "dataType": "text",
          "readonly": false,
          "hidden": false,
          "update": true,
          "inlineWithPrevious": true
        },
        {
          "name": "cust_no",
          "caption": "Cust_no",
          "widget": "picker",
          "dataType": "text",
          "readonly": false,
          "hidden": false,
          "update": false,
          "inlineWithPrevious": false,
          "pickerCode": "Picker.Sales.Customer",
          "pickerHdrId": 131
        },
        {
          "name": "doc_remark",
          "caption": "Remark",
          "widget": "textarea",
          "dataType": "text",
          "readonly": false,
          "hidden": false,
          "update": true,
          "inlineWithPrevious": false
        }
      ]
    }
  ],
  "variables": [
    { "name": "docTotal", "from": "" },
    { "name": "docQty", "from": "" },
    { "name": "DocID", "from": "doc_id" },
    { "name": "CustID", "from": "cust_id" }
  ],
  "grids": {
    "132": {
      "hdrId": 132,
      "code": "Grid.Sales.Order.Detail",
      "caption": "",
      "rowKey": "trans_id",
      "columns": [
        { "name": "trans_id", "caption": "Trans Id", "type": "text", "hidden": true },
        { "name": "item_no", "caption": "Code", "type": "text", "hidden": false },
        { "name": "trans_qty", "caption": "Qty", "type": "text", "scale": 2, "hidden": false },
        { "name": "trans_price", "caption": "Harga", "type": "text", "hidden": false }
      ]
    }
  },
  "defaults": {},
  "commands": [
    { "id": 252, "name": "Print SO", "confirm": "Are you sure you want to process this operation?", "order": 2 },
    { "id": 340, "name": "Create PL", "confirm": "Are you sure you want to process this operation?", "order": 4 }
  ]
}
```

---

## 4. Get Grid Metadata
- **Endpoint:** `GET /v1/meta/grid/{hdrId}`
- **Purpose:** Retrieves column definitions for a standalone grid screen.

### Request
```bash
curl -X 'GET' \
  'http://127.0.0.1:8000/v1/meta/grid/132' \
  -H 'accept: */*' \
  -H 'Authorization: Bearer <TOKEN>'
```

### Response (`200 OK`)
```json
{
  "hdrId": 132,
  "code": "Grid.Sales.Order.Detail",
  "caption": "",
  "rowKey": "trans_id",
  "columns": [
    { "name": "trans_id", "caption": "Trans Id", "type": "text", "hidden": true, "scale": 0, "width": 100 },
    { "name": "doc_id", "caption": "Doc Id", "type": "text", "hidden": true, "scale": 0, "width": 100 },
    { "name": "item_no", "caption": "Code", "type": "text", "hidden": false, "scale": 0, "width": 100, "pickerCode": "Picker.Inventory.Item.brgJadi", "pickerHdrId": 803 },
    { "name": "item_desc", "caption": "Item Name", "type": "text", "hidden": false, "scale": 0, "width": 100 },
    { "name": "trans_qty", "caption": "Qty", "type": "text", "hidden": false, "scale": 2, "width": 100 },
    { "name": "trans_price", "caption": "Harga", "type": "text", "hidden": false, "scale": 0, "width": 100 },
    { "name": "trans_total", "caption": "Total", "type": "text", "hidden": false, "scale": 0, "width": 100 }
  ]
}
```

---

## 5. Get Picker Metadata
- **Endpoint:** `GET /v1/meta/picker/{hdrId}`
- **Purpose:** Retrieves picker columns and search configuration.

### Request
```bash
curl -X 'GET' \
  'http://127.0.0.1:8000/v1/meta/picker/803' \
  -H 'accept: */*' \
  -H 'Authorization: Bearer <TOKEN>'
```

### Response (`200 OK`)
```json
{
  "hdrId": 803,
  "code": "Picker.Inventory.Item.brgJadi",
  "caption": "Inventory Item",
  "columns": [
    { "name": "item_id", "caption": "Item Id", "type": "text", "hidden": false },
    { "name": "item_no", "caption": "Item No", "type": "text", "hidden": false },
    { "name": "item_desc", "caption": "Item Desc", "type": "text", "hidden": false },
    { "name": "item_unit", "caption": "Item Unit", "type": "text", "hidden": false },
    { "name": "trans_price", "caption": "Trans Price", "type": "text", "hidden": false }
  ]
}
```

---

## 6. Get Browser Rows
- **Endpoint:** `GET /v1/browsers/{hdrId}/rows`
- **Purpose:** Fetches paginated browser records with filter query parameters (`ADate`, `BDate`, etc.), search (`q`), and sorting (`sort`).

### Request
```bash
curl -X 'GET' \
  'http://127.0.0.1:8000/v1/browsers/128/rows?ADate=2026-01-01&BDate=2026-12-31' \
  -H 'accept: */*' \
  -H 'Authorization: Bearer <TOKEN>'
```

### Response (`200 OK`)
```json
{
  "items": [
    {
      "doc_id": 220,
      "doc_no": "",
      "doc_extern": "",
      "doc_date": "2026-10-27",
      "doc_deldate": null,
      "docflow_seq": 0,
      "cust_id": 1789,
      "doc_remark": "",
      "doc_qty": "1.0000",
      "doc_total": "0.0000",
      "doc_grandtotal": "0.0000",
      "cust_no": "C.00653",
      "cust_desc": "ABDUL ROCHIM - Lamongan",
      "flow_state": "<div style='color:red'>New Entry</div>"
    }
  ],
  "pageSize": 50,
  "hasMore": false,
  "nextCursor": null,
  "total": null
}
```

---

## 7. Initialize New Record Form
- **Endpoint:** `GET /v1/forms/{hdrId}/new`
- **Purpose:** Returns a blank record payload pre-filled with resolved default values and empty grids.

### Request
```bash
curl -X 'GET' \
  'http://127.0.0.1:8000/v1/forms/129/new' \
  -H 'accept: */*' \
  -H 'Authorization: Bearer <TOKEN>'
```

### Response (`200 OK`)
```json
{
  "header": {
    "cust_id": 1
  },
  "grids": {},
  "schemaVersion": "18dbdf28"
}
```

---

## 8. Create New Record
- **Endpoint:** `POST /v1/forms/{hdrId}/records`
- **Purpose:** Creates and saves a new document record with its header data and schema version.

### Request
```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/v1/forms/129/records' \
  -H 'accept: */*' \
  -H 'Authorization: Bearer <TOKEN>' \
  -H 'Content-Type: application/json' \
  -d '{
    "schemaVersion": "18dbdf28",
    "header": {
      "doc_no": "SO-2026-001",
      "doc_date": "2026-03-29",
      "cust_id": 1,
      "cc_id": 1,
      "doc_total": 840000,
      "doc_remark": "Test Sales Order"
    }
  }'
```

### Response (`200 OK`)
```json
{
  "header": {
    "doc_id": 222,
    "doctype_id": 32,
    "cc_id": 1,
    "doc_no": "SO-2026-001",
    "doc_extern": "",
    "doc_date": "2026-03-29",
    "doc_deldate": null,
    "doc_term": 0,
    "docflow_seq": 0,
    "doc_currency": "IDR",
    "doc_currate": 1,
    "cust_id": 1,
    "sales_id": 1,
    "doc_saletype": 1,
    "doc_remark": "Test Sales Order",
    "doc_total": 840000,
    "doc_vattype": 1,
    "doc_vat": 0,
    "doc_grandtotal": 840000,
    "doc_qty": null,
    "doc_desc": "SO SO-2026-001",
    "ware_id": 1
  },
  "grids": {
    "132": {
      "rows": []
    }
  },
  "schemaVersion": "18dbdf28"
}
```
