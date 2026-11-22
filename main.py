from contextlib import asynccontextmanager
from typing import List
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

import database
from models import (
    CalculationRequest,
    CalculationResponse,
    DesignCreate,
    DesignResponse,
    DesignUpdate,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database and tables on startup
    database.init_db()
    yield


app = FastAPI(
    title="Parametric Overhead Crane Drawing Generator API",
    description="Backend service for parametric crane design storage and drawing number calculation.",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for potential frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(
    "/api/health",
    tags=["Health"],
    summary="Health check endpoint",
)
def get_health():
    """Return service health status."""
    return {"status": "ok"}


@app.post(
    "/api/designs",
    response_model=DesignResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Designs"],
    summary="Create a new crane design",
)
def create_design(payload: DesignCreate):
    """Save a new crane design and return the stored record with ID and timestamps."""
    design = database.create_design(
        name=payload.name,
        span_m=payload.span_m,
        capacity_t=payload.capacity_t,
        lift_height_m=payload.lift_height_m,
        girder_height_mm=payload.girder_height_mm,
    )
    return design


@app.get(
    "/api/designs",
    response_model=List[DesignResponse],
    tags=["Designs"],
    summary="List all crane designs",
)
def list_designs():
    """Retrieve all crane designs, sorted newest first."""
    return database.get_all_designs()


@app.get(
    "/api/designs/{id}",
    response_model=DesignResponse,
    tags=["Designs"],
    summary="Get a single crane design by ID",
)
def get_design(id: int):
    """Retrieve a single crane design by ID, or return 404 if not found."""
    design = database.get_design_by_id(id)
    if not design:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Design with id {id} not found",
        )
    return design


@app.put(
    "/api/designs/{id}",
    response_model=DesignResponse,
    tags=["Designs"],
    summary="Update an existing crane design",
)
def update_design(id: int, payload: DesignUpdate):
    """Update an existing crane design by ID, or return 404 if not found."""
    updated = database.update_design(
        design_id=id,
        name=payload.name,
        span_m=payload.span_m,
        capacity_t=payload.capacity_t,
        lift_height_m=payload.lift_height_m,
        girder_height_mm=payload.girder_height_mm,
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Design with id {id} not found",
        )
    return updated


@app.post(
    "/api/calculate",
    response_model=CalculationResponse,
    tags=["Calculation"],
    summary="Calculate drawing dimensions",
)
def calculate_drawing_dimensions(payload: CalculationRequest):
    """Calculate drawing dimensions from crane inputs without persisting data.
    
    Rules applied:
    - girder_length_m = span_m (definition, not a formula)
    - hook_height_m = lift_height_m (user input)
    - girder_height_mm = user input
    - trolley_position_m = span_m / 2 (assumption: trolley shown at centre of span)
    - end_truck_width_mm = 800 (estimate: fixed placeholder value, to be confirmed with engineers)
    - capacity_t = user input
    """
    girder_length_m = payload.span_m
    hook_height_m = payload.lift_height_m
    girder_height_mm = payload.girder_height_mm
    trolley_position_m = round(payload.span_m / 2.0, 4)
    end_truck_width_mm = 800
    capacity_t = payload.capacity_t

    notes = [
        f"girder_length_m: {girder_length_m} m (definition: equal to span_m, not a formula)",
        f"hook_height_m: {hook_height_m} m (user input: equal to lift_height_m)",
        f"girder_height_mm: {girder_height_mm} mm (user input)",
        f"trolley_position_m: {trolley_position_m} m (assumption: trolley shown at centre of span)",
        f"end_truck_width_mm: {end_truck_width_mm} mm (estimate: fixed placeholder value, no source, to be confirmed with engineers)",
        f"capacity_t: {capacity_t} t (user input)",
    ]

    return CalculationResponse(
        girder_length_m=girder_length_m,
        hook_height_m=hook_height_m,
        girder_height_mm=girder_height_mm,
        trolley_position_m=trolley_position_m,
        end_truck_width_mm=end_truck_width_mm,
        capacity_t=capacity_t,
        trolley_position_note="assumption: trolley shown at centre of span",
        end_truck_width_note="estimate: fixed placeholder value, no source, to be confirmed with engineers",
        notes=notes,
    )
