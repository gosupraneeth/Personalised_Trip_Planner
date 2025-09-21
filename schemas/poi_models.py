"""
Point of Interest (POI) data models.
"""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from decimal import Decimal

from .base_models import POICategory, GroupType, Coordinates, Address


class POI(BaseModel):
    """Point of Interest data structure."""
    id: str = Field(..., description="Unique POI identifier")
    name: str = Field(..., description="POI name")
    description: Optional[str] = None
    category: POICategory = Field(..., description="POI category")
    coordinates: Coordinates = Field(..., description="Geographic coordinates")
    address: Address = Field(..., description="Address information")
    rating: Optional[float] = Field(None, ge=0, le=5, description="Average rating (0-5)")
    review_count: int = Field(default=0, ge=0, description="Number of reviews")
    price_level: Optional[int] = Field(None, ge=1, le=4, description="Price level (1-4)")
    opening_hours: Optional[Dict[str, str]] = Field(default_factory=dict, description="Opening hours by day")
    website: Optional[str] = None
    phone: Optional[str] = None
    photos: List[str] = Field(default_factory=list, description="Photo URLs")
    amenities: List[str] = Field(default_factory=list, description="Available amenities")
    suitable_for_groups: List[GroupType] = Field(default_factory=list, description="Suitable group types")
    estimated_visit_duration: Optional[int] = Field(None, description="Estimated visit duration in minutes")
    popularity_score: Optional[float] = Field(None, ge=0, le=100, description="Popularity score")
    accessibility_features: List[str] = Field(default_factory=list, description="Accessibility features")