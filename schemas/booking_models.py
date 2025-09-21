"""
Booking and payment data models.
"""

from datetime import datetime, date as date_type
from typing import List, Optional
from pydantic import BaseModel, Field
from decimal import Decimal

from .base_models import BookingStatus


class BookingItem(BaseModel):
    """Individual booking item."""
    id: str = Field(..., description="Unique booking item identifier")
    poi_id: str = Field(..., description="Associated POI identifier")
    booking_type: str = Field(..., description="Type of booking (e.g., 'accommodation', 'activity')")
    name: str = Field(..., description="Booking item name")
    date: date_type = Field(..., description="Booking date")
    time: Optional[str] = None
    quantity: int = Field(default=1, gt=0, description="Number of bookings")
    unit_price: Decimal = Field(..., ge=0, description="Price per unit")
    total_price: Decimal = Field(..., ge=0, description="Total price")
    provider: Optional[str] = None
    confirmation_number: Optional[str] = None
    cancellation_policy: Optional[str] = None
    status: BookingStatus = Field(default=BookingStatus.PENDING, description="Booking status")


class BookingBasket(BaseModel):
    """Collection of booking items for a trip."""
    id: str = Field(..., description="Unique basket identifier")
    itinerary_id: str = Field(..., description="Associated itinerary identifier")
    items: List[BookingItem] = Field(..., description="Booking items")
    subtotal: Decimal = Field(default=Decimal('0'), ge=0, description="Subtotal amount")
    taxes: Decimal = Field(default=Decimal('0'), ge=0, description="Tax amount")
    fees: Decimal = Field(default=Decimal('0'), ge=0, description="Additional fees")
    total: Decimal = Field(default=Decimal('0'), ge=0, description="Total amount")
    currency: str = Field(default="USD", description="Currency code")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    expires_at: Optional[datetime] = None


class PaymentInfo(BaseModel):
    """Payment information and status."""
    id: str = Field(..., description="Unique payment identifier")
    booking_basket_id: str = Field(..., description="Associated booking basket identifier")
    amount: Decimal = Field(..., gt=0, description="Payment amount")
    currency: str = Field(default="USD", description="Currency code")
    payment_method: str = Field(..., description="Payment method (e.g., 'card', 'paypal')")
    status: str = Field(..., description="Payment status")
    transaction_id: Optional[str] = None
    provider_transaction_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Payment timestamp")
    failure_reason: Optional[str] = None