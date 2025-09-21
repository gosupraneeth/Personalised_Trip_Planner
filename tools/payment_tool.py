"""
Payment tool for the Trip Planner ADK application.

This tool provides functionality to process payments and handle
booking transactions using Stripe (mock implementation).
"""

import logging
from typing import Dict, Any, Optional
from decimal import Decimal
import stripe
from adk import Tool

from schemas import PaymentInfo, BookingBasket

logger = logging.getLogger(__name__)


class PaymentTool(Tool):
    """Stripe payment processing tool for booking transactions."""
    
    def __init__(self, stripe_secret_key: str):
        """Initialize the Payment tool."""
        super().__init__("payment_tool", "Stripe payment processing integration")
        self.stripe_secret_key = stripe_secret_key
        
        try:
            stripe.api_key = stripe_secret_key
            logger.info("Stripe payment tool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Stripe: {e}")
    
    def execute(self, operation: str, **kwargs) -> Any:
        """Execute Payment operations."""
        if operation == "create_payment_intent":
            return self.create_payment_intent(**kwargs)
        elif operation == "process_booking_payment":
            return self.process_booking_payment(**kwargs)
        elif operation == "refund_payment":
            return self.refund_payment(**kwargs)
        else:
            raise ValueError(f"Unknown operation: {operation}")
    
    def create_payment_intent(
        self,
        amount: Decimal,
        currency: str = "usd",
        description: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a Stripe payment intent.
        
        Args:
            amount: Payment amount
            currency: Currency code
            description: Payment description
            metadata: Additional metadata
            
        Returns:
            Payment intent data or None if error
        """
        try:
            # Convert amount to cents for Stripe
            amount_cents = int(amount * 100)
            
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency.lower(),
                description=description,
                metadata=metadata or {},
                automatic_payment_methods={"enabled": True}
            )
            
            logger.info(f"Created payment intent {intent.id} for {amount} {currency}")
            return {
                "id": intent.id,
                "client_secret": intent.client_secret,
                "amount": amount,
                "currency": currency,
                "status": intent.status
            }
            
        except Exception as e:
            logger.error(f"Error creating payment intent: {e}")
            return None
    
    def confirm_payment(self, payment_intent_id: str) -> Optional[Dict[str, Any]]:
        """
        Confirm a payment intent.
        
        Args:
            payment_intent_id: Payment intent ID to confirm
            
        Returns:
            Payment confirmation data or None if error
        """
        try:
            intent = stripe.PaymentIntent.confirm(payment_intent_id)
            
            logger.info(f"Confirmed payment intent {payment_intent_id}")
            return {
                "id": intent.id,
                "status": intent.status,
                "amount": intent.amount / 100,  # Convert back from cents
                "currency": intent.currency,
                "charges": [
                    {
                        "id": charge.id,
                        "status": charge.status,
                        "receipt_url": charge.receipt_url
                    } for charge in intent.charges.data
                ]
            }
            
        except Exception as e:
            logger.error(f"Error confirming payment {payment_intent_id}: {e}")
            return None
    
    def process_booking_payment(
        self,
        booking_basket: BookingBasket,
        payment_method: str = "card"
    ) -> PaymentInfo:
        """
        Process payment for a booking basket.
        
        Args:
            booking_basket: Booking basket to pay for
            payment_method: Payment method to use
            
        Returns:
            Payment information object
        """
        try:
            # Create payment intent
            intent_data = self.create_payment_intent(
                amount=booking_basket.total,
                currency=booking_basket.currency,
                description=f"Trip booking payment for basket {booking_basket.id}",
                metadata={
                    "basket_id": booking_basket.id,
                    "itinerary_id": booking_basket.itinerary_id
                }
            )
            
            if not intent_data:
                return PaymentInfo(
                    id="",
                    booking_basket_id=booking_basket.id,
                    amount=booking_basket.total,
                    currency=booking_basket.currency,
                    payment_method=payment_method,
                    status="failed",
                    failure_reason="Failed to create payment intent"
                )
            
            # For demo purposes, automatically confirm the payment
            # In a real implementation, this would wait for user confirmation
            confirmation = self.confirm_payment(intent_data["id"])
            
            if confirmation and confirmation["status"] == "succeeded":
                return PaymentInfo(
                    id=f"pay_{intent_data['id']}",
                    booking_basket_id=booking_basket.id,
                    amount=booking_basket.total,
                    currency=booking_basket.currency,
                    payment_method=payment_method,
                    status="succeeded",
                    transaction_id=intent_data["id"],
                    provider_transaction_id=confirmation["charges"][0]["id"] if confirmation["charges"] else None
                )
            else:
                return PaymentInfo(
                    id=f"pay_{intent_data['id']}",
                    booking_basket_id=booking_basket.id,
                    amount=booking_basket.total,
                    currency=booking_basket.currency,
                    payment_method=payment_method,
                    status="failed",
                    transaction_id=intent_data["id"],
                    failure_reason="Payment confirmation failed"
                )
                
        except Exception as e:
            logger.error(f"Error processing booking payment: {e}")
            return PaymentInfo(
                id="",
                booking_basket_id=booking_basket.id,
                amount=booking_basket.total,
                currency=booking_basket.currency,
                payment_method=payment_method,
                status="failed",
                failure_reason=str(e)
            )
    
    def refund_payment(
        self,
        payment_intent_id: str,
        amount: Optional[Decimal] = None,
        reason: str = "requested_by_customer"
    ) -> Optional[Dict[str, Any]]:
        """
        Refund a payment.
        
        Args:
            payment_intent_id: Payment intent ID to refund
            amount: Refund amount (None for full refund)
            reason: Refund reason
            
        Returns:
            Refund data or None if error
        """
        try:
            # Get the payment intent to find the charge
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            if not intent.charges.data:
                logger.error(f"No charges found for payment intent {payment_intent_id}")
                return None
            
            charge_id = intent.charges.data[0].id
            refund_params = {
                "charge": charge_id,
                "reason": reason
            }
            
            if amount:
                refund_params["amount"] = int(amount * 100)  # Convert to cents
            
            refund = stripe.Refund.create(**refund_params)
            
            logger.info(f"Created refund {refund.id} for payment {payment_intent_id}")
            return {
                "id": refund.id,
                "amount": refund.amount / 100,  # Convert back from cents
                "currency": refund.currency,
                "status": refund.status,
                "reason": refund.reason
            }
            
        except Exception as e:
            logger.error(f"Error refunding payment {payment_intent_id}: {e}")
            return None
    
    def get_payment_status(self, payment_intent_id: str) -> Optional[str]:
        """
        Get the status of a payment.
        
        Args:
            payment_intent_id: Payment intent ID
            
        Returns:
            Payment status or None if error
        """
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            return intent.status
            
        except Exception as e:
            logger.error(f"Error getting payment status for {payment_intent_id}: {e}")
            return None
    
    def calculate_booking_fees(self, subtotal: Decimal, currency: str = "usd") -> Dict[str, Decimal]:
        """
        Calculate fees for a booking.
        
        Args:
            subtotal: Booking subtotal
            currency: Currency code
            
        Returns:
            Dictionary with fee breakdown
        """
        try:
            # Calculate service fee (5% of subtotal)
            service_fee = subtotal * Decimal("0.05")
            
            # Calculate tax (10% of subtotal)
            tax = subtotal * Decimal("0.10")
            
            # Calculate payment processing fee (2.9% + $0.30)
            processing_fee = (subtotal * Decimal("0.029")) + Decimal("0.30")
            
            total_fees = service_fee + processing_fee
            total_taxes = tax
            total = subtotal + total_fees + total_taxes
            
            return {
                "subtotal": subtotal,
                "service_fee": service_fee,
                "processing_fee": processing_fee,
                "total_fees": total_fees,
                "tax": tax,
                "total_taxes": total_taxes,
                "total": total
            }
            
        except Exception as e:
            logger.error(f"Error calculating booking fees: {e}")
            return {
                "subtotal": subtotal,
                "service_fee": Decimal("0"),
                "processing_fee": Decimal("0"),
                "total_fees": Decimal("0"),
                "tax": Decimal("0"),
                "total_taxes": Decimal("0"),
                "total": subtotal
            }
    
    def validate_payment_method(self, payment_method_id: str) -> bool:
        """
        Validate a payment method.
        
        Args:
            payment_method_id: Payment method ID to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            payment_method = stripe.PaymentMethod.retrieve(payment_method_id)
            return payment_method.id is not None
            
        except Exception as e:
            logger.error(f"Error validating payment method {payment_method_id}: {e}")
            return False
    
    def create_mock_successful_payment(
        self,
        booking_basket: BookingBasket
    ) -> PaymentInfo:
        """
        Create a mock successful payment for testing.
        
        Args:
            booking_basket: Booking basket to create payment for
            
        Returns:
            Mock successful payment info
        """
        return PaymentInfo(
            id=f"pay_mock_{booking_basket.id}",
            booking_basket_id=booking_basket.id,
            amount=booking_basket.total,
            currency=booking_basket.currency,
            payment_method="card",
            status="succeeded",
            transaction_id=f"pi_mock_{booking_basket.id}",
            provider_transaction_id=f"ch_mock_{booking_basket.id}"
        )
    
    def create_mock_failed_payment(
        self,
        booking_basket: BookingBasket,
        failure_reason: str = "card_declined"
    ) -> PaymentInfo:
        """
        Create a mock failed payment for testing.
        
        Args:
            booking_basket: Booking basket
            failure_reason: Reason for failure
            
        Returns:
            Mock failed payment info
        """
        return PaymentInfo(
            id=f"pay_mock_fail_{booking_basket.id}",
            booking_basket_id=booking_basket.id,
            amount=booking_basket.total,
            currency=booking_basket.currency,
            payment_method="card",
            status="failed",
            transaction_id=f"pi_mock_fail_{booking_basket.id}",
            failure_reason=failure_reason
        )