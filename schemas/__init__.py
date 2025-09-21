"""
Schema definitions for the Trip Planner ADK application.

This module exports all data models used throughout the trip planning workflow.
"""

# Export all models from sub-modules
from .base_models import (
    GroupType,
    BudgetRange,
    POICategory,
    TransportMode,
    WeatherCondition,
    BookingStatus,
    Coordinates,
    Address
)

from .trip_models import TripRequest

from .poi_models import POI

from .weather_transport_models import (
    WeatherInfo,
    TransportOption
)

from .itinerary_models import (
    ItineraryItem,
    DayPlan,
    Itinerary
)

from .booking_models import (
    BookingItem,
    BookingBasket,
    PaymentInfo
)

from .agent_models import (
    AgentResponse,
    SessionData
)

__all__ = [
    # Base enums and models
    "GroupType",
    "BudgetRange", 
    "POICategory",
    "TransportMode",
    "WeatherCondition",
    "BookingStatus",
    "Coordinates",
    "Address",
    
    # Trip models
    "TripRequest",
    
    # POI models
    "POI",
    
    # Weather and transport models
    "WeatherInfo",
    "TransportOption",
    
    # Itinerary models
    "ItineraryItem",
    "DayPlan",
    "Itinerary",
    
    # Booking models
    "BookingItem",
    "BookingBasket", 
    "PaymentInfo",
    
    # Agent models
    "AgentResponse",
    "SessionData"
]