"""
Itinerary and planning data models.
"""

from datetime import datetime, date as date_type
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from decimal import Decimal

from .poi_models import POI
from .weather_transport_models import WeatherInfo, TransportOption
from .trip_models import TripRequest


class ItineraryItem(BaseModel):
    """Single item in the itinerary."""
    day: int = Field(..., gt=0, description="Day number of the trip")
    time_slot: str = Field(..., description="Time slot (e.g., '09:00-11:00')")
    poi: POI = Field(..., description="Point of interest to visit")
    estimated_duration: int = Field(..., gt=0, description="Estimated duration in minutes")
    transport_to_next: Optional[TransportOption] = None
    notes: Optional[str] = None
    cost_estimate: Optional[Decimal] = Field(None, ge=0, description="Estimated cost for this item")


class DayPlan(BaseModel):
    """Plan for a single day of the trip."""
    day: int = Field(..., gt=0, description="Day number of the trip")
    date: date_type = Field(..., description="Date of this day")
    items: List[ItineraryItem] = Field(..., description="Itinerary items for this day")
    weather: Optional[WeatherInfo] = None
    total_estimated_cost: Decimal = Field(default=Decimal('0'), ge=0, description="Total estimated cost for the day")
    notes: Optional[str] = None


class Itinerary(BaseModel):
    """Complete trip itinerary."""
    id: str = Field(..., description="Unique itinerary identifier")
    trip_request: TripRequest = Field(..., description="Original trip request")
    days: List[DayPlan] = Field(..., description="Daily plans")
    total_cost: Decimal = Field(default=Decimal('0'), ge=0, description="Total trip cost")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    version: int = Field(default=1, description="Itinerary version")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @validator('days')
    def validate_days(cls, v, values):
        if 'trip_request' in values:
            expected_days = values['trip_request'].duration_days
            if len(v) != expected_days:
                raise ValueError(f'Expected {expected_days} days, got {len(v)}')
        return v