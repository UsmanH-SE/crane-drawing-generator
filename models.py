from typing import List
from pydantic import BaseModel, Field, field_validator


class DesignBase(BaseModel):
    """Base fields and validations for crane designs."""
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Design name (non-empty, max 100 characters)",
        examples=["Warehouse EOT Crane - Bay 1"],
    )
    span_m: float = Field(
        ...,
        ge=5.0,
        le=30.0,
        description="Girder span in meters (5 to 30)",
        examples=[16.5],
    )
    capacity_t: float = Field(
        ...,
        ge=1.0,
        le=20.0,
        description="Crane capacity in metric tonnes (1 to 20)",
        examples=[10.0],
    )
    lift_height_m: float = Field(
        ...,
        ge=3.0,
        le=15.0,
        description="Lift height in meters (3 to 15)",
        examples=[7.5],
    )
    girder_height_mm: int = Field(
        ...,
        ge=300,
        le=1500,
        description="Girder height in millimeters (300 to 1500)",
        examples=[800],
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("name must not be empty or whitespace only")
        if len(trimmed) > 100:
            raise ValueError("name must not exceed 100 characters")
        return trimmed


class DesignCreate(DesignBase):
    """Request payload for creating a new design."""
    pass


class DesignUpdate(DesignBase):
    """Request payload for updating an existing design."""
    pass


class DesignResponse(DesignBase):
    """Response model for a saved crane design."""
    id: int = Field(..., description="Unique design ID")
    created_at: str = Field(..., description="Creation timestamp (UTC ISO format)")
    updated_at: str = Field(..., description="Last update timestamp (UTC ISO format)")


class CalculationRequest(BaseModel):
    """Request payload for drawing dimension calculations (no name needed)."""
    span_m: float = Field(
        ...,
        ge=5.0,
        le=30.0,
        description="Girder span in meters (5 to 30)",
        examples=[16.5],
    )
    capacity_t: float = Field(
        ...,
        ge=1.0,
        le=20.0,
        description="Crane capacity in metric tonnes (1 to 20)",
        examples=[10.0],
    )
    lift_height_m: float = Field(
        ...,
        ge=3.0,
        le=15.0,
        description="Lift height in meters (3 to 15)",
        examples=[7.5],
    )
    girder_height_mm: int = Field(
        ...,
        ge=300,
        le=1500,
        description="Girder height in millimeters (300 to 1500)",
        examples=[800],
    )


class CalculationResponse(BaseModel):
    """Drawing numbers and notes returned by the calculation endpoint."""
    girder_length_m: float = Field(..., description="Equal to span_m (definition, not a formula)")
    hook_height_m: float = Field(..., description="Equal to lift_height_m (user input)")
    girder_height_mm: int = Field(..., description="Girder height from user input")
    trolley_position_m: float = Field(..., description="span_m / 2")
    end_truck_width_mm: int = Field(800, description="Fixed placeholder value")
    capacity_t: float = Field(..., description="Crane capacity from user input")
    trolley_position_note: str = Field(
        "assumption: trolley shown at centre of span",
        description="Note regarding trolley positioning",
    )
    end_truck_width_note: str = Field(
        "estimate: fixed placeholder value, no source, to be confirmed with engineers",
        description="Note regarding end truck width estimate",
    )
    notes: List[str] = Field(
        ...,
        description="Explanations for each drawing value, clearly labeling assumptions and estimates",
    )
