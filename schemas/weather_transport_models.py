"""
Weather and transport data models.
"""

from datetime import datetime, date as date_type
from typing import Optional
from pydantic import BaseModel, Field
from decimal import Decimal

from .base_models import WeatherCondition, TransportMode


class WeatherInfo(BaseModel):
    """Weather information for a specific date and location."""
    date: date_type = Field(..., description="Date of weather forecast")
    condition: WeatherCondition = Field(..., description="Weather condition")
    temperature_high: float = Field(..., description="High temperature in Celsius")
    temperature_low: float = Field(..., description="Low temperature in Celsius")
    humidity: Optional[int] = Field(None, ge=0, le=100, description="Humidity percentage")
    precipitation_chance: Optional[int] = Field(None, ge=0, le=100, description="Precipitation chance percentage")
    wind_speed: Optional[float] = Field(None, ge=0, description="Wind speed in km/h")
    uv_index: Optional[int] = Field(None, ge=0, le=11, description="UV index")
    is_suitable_for_outdoor: bool = Field(default=True, description="Whether suitable for outdoor activities")


class TransportOption(BaseModel):
    """Transportation option between two locations."""
    mode: TransportMode = Field(..., description="Transportation mode")
    duration_minutes: int = Field(..., gt=0, description="Travel duration in minutes")
    distance_km: float = Field(..., gt=0, description="Distance in kilometers")
    cost: Optional[Decimal] = Field(None, ge=0, description="Transportation cost")
    provider: Optional[str] = None
    route_description: Optional[str] = None
    departure_time: Optional[datetime] = None
    arrival_time: Optional[datetime] = None