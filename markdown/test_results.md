# Integration Test Results against Real Endpoints

## Get Menu
- **Method/URL:** `GET /v1/menu`
- **Status Code:** `500`
- **Response:**
```json
{
  "error": {
    "code": "internal_error",
    "message": "An unexpected database error occurred",
    "requestId": "e13e67e2ae8a4b8292086a59b7f82701",
    "details": []
  }
}
```

## Get Browser Meta (128)
- **Method/URL:** `GET /v1/meta/browser/128`
- **Status Code:** `500`
- **Response:**
```json
{
  "error": {
    "code": "internal_error",
    "message": "An unexpected database error occurred",
    "requestId": "4218266f8b0a4bb99a55ff384c8e9f66",
    "details": []
  }
}
```

## Get Form Meta (129)
- **Method/URL:** `GET /v1/meta/form/129`
- **Status Code:** `500`
- **Response:**
```json
{
  "error": {
    "code": "internal_error",
    "message": "An unexpected database error occurred",
    "requestId": "422288f1dd8348ec8313eaf7a4569997",
    "details": []
  }
}
```

## Get Grid Meta (132)
- **Method/URL:** `GET /v1/meta/grid/132`
- **Status Code:** `500`
- **Response:**
```json
{
  "error": {
    "code": "internal_error",
    "message": "An unexpected database error occurred",
    "requestId": "ebd7e19d4aff459792d1c2ffb3c3cf44",
    "details": []
  }
}
```

## Get Picker Meta (803)
- **Method/URL:** `GET /v1/meta/picker/803`
- **Status Code:** `500`
- **Response:**
```json
{
  "error": {
    "code": "internal_error",
    "message": "An unexpected database error occurred",
    "requestId": "c0931fc4516c46b39e94ee8c0e836fd7",
    "details": []
  }
}
```

## Get Browser Rows (128)
- **Method/URL:** `GET /v1/browsers/128/rows?ADate=2026-01-01&BDate=2026-12-31`
- **Status Code:** `500`
- **Response:**
```json
{
  "error": {
    "code": "internal_error",
    "message": "An unexpected database error occurred",
    "requestId": "47c482fe1b0c409ba4943a3d666cd487",
    "details": []
  }
}
```

## Get New Form (129)
- **Method/URL:** `GET /v1/forms/129/new`
- **Status Code:** `500`
- **Response:**
```json
{
  "error": {
    "code": "internal_error",
    "message": "An unexpected database error occurred",
    "requestId": "1b82592680d74f00b9b753231b2dd46e",
    "details": []
  }
}
```

## Create Record with Idempotency
- **Method/URL:** `POST /v1/forms/129/records`
- **Status Code:** `500`
- **Response:**
```json
{
  "error": {
    "code": "internal_error",
    "message": "An unexpected database error occurred",
    "requestId": "804009bce75b411f8bbef903835ff7c9",
    "details": []
  }
}
```

## Idempotent Replay
- **Method/URL:** `POST /v1/forms/129/records`
- **Status Code:** `500`
- **Response:**
```json
{
  "error": {
    "code": "internal_error",
    "message": "An unexpected database error occurred",
    "requestId": "290273360f5a411595ece9c571bf4b72",
    "details": []
  }
}
```

