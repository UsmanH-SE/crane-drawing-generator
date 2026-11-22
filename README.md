# Parametric Overhead Crane Drawing Generator

## What this is
This is a concept drawing tool for a single girder Electric Overhead Traveling (EOT) crane.
The user enters span, capacity, lift height, and girder height. The app calculates key drawing numbers, renders a dimensioned 2D SVG drawing, and lets the user save, reopen, and edit designs.

Concept drawing only — not for manufacturing.

## How to run
1. Install Python 3.10 or newer.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start the server:
   ```bash
   python -m uvicorn main:app --reload
   ```
4. Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser. (The interactive API documentation is available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)).

*Note: If the plain `uvicorn` command is not recognised on Windows because the Python Scripts folder is not on PATH, use `python -m uvicorn` as shown above.*

## Inputs and ranges
All inputs use metric units and are validated on the backend:

| Input | Unit | Allowed Range | Description |
|---|---|---|---|
| Span | m | 5 to 30 | Width the crane girder covers, entered by the user |
| Capacity | tonnes (t) | 1 to 20 | Crane capacity entered by the user |
| Lift Height | m | 3 to 15 | Maximum vertical travel of the hook |
| Girder Height | mm | 300 to 1500 | Main beam cross-section height (integer) |

## API endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Returns service health status `{"status": "ok"}`. |
| `POST` | `/api/calculate` | Takes the 4 crane inputs, returns drawing dimensions and notes without saving. |
| `POST` | `/api/designs` | Validates and saves a new crane design to the SQLite database. |
| `GET` | `/api/designs` | Returns all saved crane designs, sorted newest first. |
| `GET` | `/api/designs/{id}` | Returns a single design by ID, or 404 if not found. |
| `PUT` | `/api/designs/{id}` | Updates an existing design by ID, or 404 if not found. |

## Stack and why
- **Python + FastAPI**: I know Python well. FastAPI provides automatic data validation with Pydantic and clear error messages when an input is invalid.
- **SQLite**: Standard library module (`sqlite3`). It uses a single local file (`cranes.db`), requires zero setup or external database server, and keeps saved designs intact across server restarts.
- **Plain HTML, CSS, and JavaScript with SVG**: Requires no build step or node tooling. SVG scales cleanly at any screen resolution and renders fast in any browser.
- **Uvicorn**: Standard, lightweight ASGI server to run the FastAPI application.

## How the drawing numbers are decided
- **Girder length**: Equals the span (this is by definition, not a formula).
- **Hook height**: Equals the lift height (taken directly from user input).
- **Girder height**: Taken directly from user input (I did not invent any beam sizing formulas or standard tables).
- **Trolley position**: Shown at the centre of the span (`span_m / 2`), which is my chosen assumption for concept visualization.
- **End truck width**: Fixed placeholder value of 800 mm, clearly labelled as an estimate with no source, to be confirmed with engineers.

## Known limitations
- Single girder top-running EOT cranes only.
- No real engineering formulas, deflection limits, or structural load calculations.
- 2D views only (no 3D model).
- Trolley position is fixed at the centre of the span.
- End truck width is a fixed estimate.
- No user accounts or authentication.

## Time spent
About 5 hours of focused work, spread across one day (22 November 2026).
