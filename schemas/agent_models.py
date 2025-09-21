"""
Agent and session data models.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from .trip_models import TripRequest
from .itinerary_models import Itinerary
from .booking_models import BookingBasket


class AgentResponse(BaseModel):
    """Standard response format for agents."""
    agent_name: str = Field(..., description="Name of the responding agent")
    success: bool = Field(..., description="Whether the operation was successful")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    message: Optional[str] = Field(None, description="Response message")
    error: Optional[str] = Field(None, description="Error message if unsuccessful")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class SessionData(BaseModel):
    """Session data for maintaining conversation state."""
    session_id: str = Field(..., description="Unique session identifier")
    user_id: Optional[str] = None
    trip_request: Optional[TripRequest] = None
    current_itinerary: Optional[Itinerary] = None
    current_basket: Optional[BookingBasket] = None
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list, description="Conversation history")
    agent_context: Dict[str, Any] = Field(default_factory=dict, description="Context shared between agents")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Session creation timestamp")
    last_activity: datetime = Field(default_factory=datetime.utcnow, description="Last activity timestamp")
    is_active: bool = Field(default=True, description="Whether session is active")