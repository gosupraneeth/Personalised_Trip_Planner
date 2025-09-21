"""
Trip request and core trip data models.
"""

from datetime import date as date_type
from typing import List, Optional
from pydantic import BaseModel, Field, validator
from decimal import Decimal

from .base_models import GroupType, BudgetRange


class TripRequest(BaseModel):
    """Initial trip request from the user."""
    destination: str = Field(..., description="Primary destination city/location")
    start_date: date_type = Field(..., description="Trip start date")
    end_date: date_type = Field(..., description="Trip end date")
    number_of_travelers: int = Field(..., gt=0, description="Number of travelers")
    group_type: GroupType = Field(..., description="Type of travel group")
    budget_range: BudgetRange = Field(..., description="Budget range for the trip")
    budget_amount: Optional[Decimal] = Field(None, gt=0, description="Specific budget amount")
    special_interests: List[str] = Field(default_factory=list, description="Special interests or preferences")
    accessibility_needs: List[str] = Field(default_factory=list, description="Accessibility requirements")
    dietary_restrictions: List[str] = Field(default_factory=list, description="Dietary restrictions")
    user_id: Optional[str] = Field(None, description="User identifier")
    session_id: Optional[str] = Field(None, description="Session identifier")
    
    @validator('end_date')
    def validate_dates(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v
    
    @property
    def duration_days(self) -> int:
        """Calculate trip duration in days."""
        return (self.end_date - self.start_date).days + 1