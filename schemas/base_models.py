"""
Core data models for the Trip Planner ADK application.
"""

from datetime import datetime, date as date_type
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, validator
from decimal import Decimal


class GroupType(str, Enum):
    """Types of travel groups."""
    SOLO = "solo"
    FAMILY = "family"
    FRIENDS = "friends"
    COUPLE = "couple"
    BUSINESS = "business"


class BudgetRange(str, Enum):
    """Budget ranges for trip planning."""
    BUDGET = "budget"
    MODERATE = "moderate"
    LUXURY = "luxury"
    PREMIUM = "premium"


class POICategory(str, Enum):
    """Categories of Points of Interest."""
    RESTAURANT = "restaurant"
    ATTRACTION = "attraction"
    MUSEUM = "museum"
    PARK = "park"
    SHOPPING = "shopping"
    NIGHTLIFE = "nightlife"
    ACCOMMODATION = "accommodation"
    TRANSPORT = "transport"
    ENTERTAINMENT = "entertainment"
    RELIGIOUS = "religious"
    BEACH = "beach"
    ADVENTURE = "adventure"


class TransportMode(str, Enum):
    """Available transportation modes."""
    WALKING = "walking"
    DRIVING = "driving"
    PUBLIC_TRANSPORT = "public_transport"
    TAXI = "taxi"
    FLIGHT = "flight"
    TRAIN = "train"
    BIKE = "bike"


class WeatherCondition(str, Enum):
    """Weather condition types."""
    SUNNY = "sunny"
    CLOUDY = "cloudy"
    RAINY = "rainy"
    SNOWY = "snowy"
    STORMY = "stormy"
    FOGGY = "foggy"


class BookingStatus(str, Enum):
    """Booking status types."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class Coordinates(BaseModel):
    """Geographic coordinates."""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")


class Address(BaseModel):
    """Physical address information."""
    street: Optional[str] = None
    city: str = Field(..., description="City name")
    state: Optional[str] = None
    country: str = Field(..., description="Country name")
    postal_code: Optional[str] = None
    formatted_address: Optional[str] = None