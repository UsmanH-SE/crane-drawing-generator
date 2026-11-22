# Parametric Overhead Crane Drawing Generator - Backend

FastAPI backend for parametric overhead crane designs and drawing dimension calculations.

## Tech Stack
- **Python 3.10+**
- **FastAPI** (REST API framework)
- **SQLite** (Standard library `sqlite3`, zero external database setup)
- **Pydantic v2** (Request/response schemas & data validation)
- **Uvicorn** (ASGI server)

---

## Project Structure
```
d:/crane-drawing-generator/
├── main.py          # FastAPI application & route handlers
├── database.py      # SQLite connection & CRUD operations
├── models.py        # Pydantic validation & response schemas
├── requirements.txt # Python dependencies
└── README.md        # Documentation and running instructions
```

---

## Setup & Running Locally

### Step 1: Install Dependencies
Open your terminal in the project directory and run:
```bash
pip install -r requirements.txt
```

### Step 2: Start the Backend Server
Start the Uvicorn server with hot reloading enabled:
```bash
python -m uvicorn main:app --reload
```
*(Or `uvicorn main:app --reload` if your Python Scripts folder is in your system PATH)*

The API will be available at:
- **API Base URL:** `http://127.0.0.1:8000`
- **Interactive Swagger Docs:** `http://127.0.0.1:8000/docs`
- **ReDoc:** `http://127.0.0.1:8000/redoc`

---

## Database Schema

The database table `designs` is automatically initialized on application startup in `cranes.db`:

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `INTEGER` | `PRIMARY KEY AUTOINCREMENT` | Unique design identifier |
| `name` | `TEXT` | `NOT NULL` | Design name (1-100 characters) |
| `span_m` | `REAL` | `NOT NULL` | Crane girder span in meters (5.0 - 30.0) |
| `capacity_t` | `REAL` | `NOT NULL` | Crane rated capacity in tonnes (1.0 - 20.0) |
| `lift_height_m` | `REAL` | `NOT NULL` | Crane lift height in meters (3.0 - 15.0) |
| `girder_height_mm` | `INTEGER` | `NOT NULL` | Girder height in millimeters (300 - 1500) |
| `created_at` | `TEXT` | `NOT NULL` | ISO 8601 UTC creation timestamp |
| `updated_at` | `TEXT` | `NOT NULL` | ISO 8601 UTC update timestamp |

---

## Validation Rules

- `name`: Non-empty string, max 100 characters.
- `span_m`: Float between `5.0` and `30.0`.
- `capacity_t`: Float between `1.0` and `20.0`.
- `lift_height_m`: Float between `3.0` and `15.0`.
- `girder_height_mm`: Integer between `300` and `1500`.

Invalid requests return HTTP `422 Unprocessable Entity` with field-level validation errors.
Non-existent IDs return HTTP `404 Not Found`.

---

## API Endpoints Overview

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check endpoint returning `{"status": "ok"}` |
| `POST` | `/api/designs` | Create a new crane design |
| `GET` | `/api/designs` | List all crane designs (newest first) |
| `GET` | `/api/designs/{id}` | Get a single crane design by ID (404 if not found) |
| `PUT` | `/api/designs/{id}` | Update a crane design by ID (404 if not found) |
| `POST` | `/api/calculate` | Compute drawing numbers from 4 inputs (stateless) |

---

## Example Requests (cURL)

### 1. Health Check
```bash
curl -X GET "http://127.0.0.1:8000/api/health"
```

### 2. Calculate Drawing Numbers
```bash
curl -X POST "http://127.0.0.1:8000/api/calculate" \
  -H "Content-Type: application/json" \
  -d '{
    "span_m": 18.0,
    "capacity_t": 10.0,
    "lift_height_m": 8.0,
    "girder_height_mm": 900
  }'
```

### 3. Create a Design
```bash
curl -X POST "http://127.0.0.1:8000/api/designs" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Heavy Duty Factory Crane",
    "span_m": 22.5,
    "capacity_t": 15.0,
    "lift_height_m": 9.0,
    "girder_height_mm": 1100
  }'
```

### 4. List All Designs
```bash
curl -X GET "http://127.0.0.1:8000/api/designs"
```

### 5. Get Design by ID
```bash
curl -X GET "http://127.0.0.1:8000/api/designs/1"
```

### 6. Update Design by ID
```bash
curl -X PUT "http://127.0.0.1:8000/api/designs/1" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Heavy Duty Factory Crane - Rev 2",
    "span_m": 24.0,
    "capacity_t": 15.0,
    "lift_height_m": 9.5,
    "girder_height_mm": 1200
  }'
```
