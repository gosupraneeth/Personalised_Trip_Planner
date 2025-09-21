"""
Firestore tool for the Trip Planner ADK application.

This tool provides functionality to store and retrieve trip data,
user sessions, and itineraries using Google Firestore.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from google.cloud import firestore
from adk import Tool

from schemas import TripRequest, Itinerary, SessionData, BookingBasket

logger = logging.getLogger(__name__)


class FirestoreTool(Tool):
    """Firestore tool for session and trip data persistence."""
    
    def __init__(self, project_id: str, database: str = "(default)"):
        """Initialize Firestore tool."""
        super().__init__("firestore_tool", "Firestore database integration for data persistence")
        self.project_id = project_id
        self.database = database
        self.client = None
        
        try:
            self.client = firestore.Client(project=project_id, database=database)
            logger.info(f"Firestore tool initialized for project {project_id}")
        except Exception as e:
            logger.error(f"Failed to initialize Firestore client: {e}")
    
    def execute(self, operation: str, **kwargs) -> Any:
        """Execute Firestore operations."""
        if operation == "save_session":
            return self.save_session(**kwargs)
        elif operation == "get_session":
            return self.get_session(**kwargs)
        elif operation == "save_itinerary":
            return self.save_itinerary(**kwargs)
        else:
            raise ValueError(f"Unknown operation: {operation}")
    
    def save_session(self, session_data: SessionData) -> bool:
        """
        Save session data to Firestore.
        
        Args:
            session_data: Session data to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            doc_ref = self.client.collection('sessions').document(session_data.session_id)
            
            # Convert to dict for Firestore
            session_dict = session_data.dict()
            session_dict['last_activity'] = datetime.utcnow()
            
            doc_ref.set(session_dict, merge=True)
            logger.info(f"Saved session {session_data.session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving session {session_data.session_id}: {e}")
            return False
    
    def get_session(self, session_id: str) -> Optional[SessionData]:
        """
        Retrieve session data from Firestore.
        
        Args:
            session_id: Session ID to retrieve
            
        Returns:
            SessionData object or None if not found
        """
        try:
            doc_ref = self.client.collection('sessions').document(session_id)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                # Convert back to SessionData object
                return SessionData(**data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving session {session_id}: {e}")
            return None
    
    def save_itinerary(self, itinerary: Itinerary) -> bool:
        """
        Save itinerary to Firestore.
        
        Args:
            itinerary: Itinerary to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            doc_ref = self.client.collection('itineraries').document(itinerary.id)
            
            # Convert to dict for Firestore
            itinerary_dict = itinerary.dict()
            itinerary_dict['updated_at'] = datetime.utcnow()
            
            doc_ref.set(itinerary_dict, merge=True)
            logger.info(f"Saved itinerary {itinerary.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving itinerary {itinerary.id}: {e}")
            return False
    
    def get_itinerary(self, itinerary_id: str) -> Optional[Itinerary]:
        """
        Retrieve itinerary from Firestore.
        
        Args:
            itinerary_id: Itinerary ID to retrieve
            
        Returns:
            Itinerary object or None if not found
        """
        try:
            doc_ref = self.client.collection('itineraries').document(itinerary_id)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                return Itinerary(**data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving itinerary {itinerary_id}: {e}")
            return None
    
    def save_booking_basket(self, basket: BookingBasket) -> bool:
        """
        Save booking basket to Firestore.
        
        Args:
            basket: Booking basket to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            doc_ref = self.client.collection('booking_baskets').document(basket.id)
            
            # Convert to dict for Firestore
            basket_dict = basket.dict()
            
            doc_ref.set(basket_dict, merge=True)
            logger.info(f"Saved booking basket {basket.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving booking basket {basket.id}: {e}")
            return False
    
    def get_booking_basket(self, basket_id: str) -> Optional[BookingBasket]:
        """
        Retrieve booking basket from Firestore.
        
        Args:
            basket_id: Basket ID to retrieve
            
        Returns:
            BookingBasket object or None if not found
        """
        try:
            doc_ref = self.client.collection('booking_baskets').document(basket_id)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                return BookingBasket(**data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving booking basket {basket_id}: {e}")
            return None
    
    def get_user_itineraries(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get itineraries for a user.
        
        Args:
            user_id: User ID
            limit: Maximum number of itineraries to return
            
        Returns:
            List of itinerary data
        """
        try:
            query = (self.client.collection('itineraries')
                    .where('trip_request.user_id', '==', user_id)
                    .order_by('created_at', direction=firestore.Query.DESCENDING)
                    .limit(limit))
            
            docs = query.stream()
            itineraries = []
            
            for doc in docs:
                itinerary_data = doc.to_dict()
                itinerary_data['id'] = doc.id
                itineraries.append(itinerary_data)
            
            logger.info(f"Retrieved {len(itineraries)} itineraries for user {user_id}")
            return itineraries
            
        except Exception as e:
            logger.error(f"Error retrieving itineraries for user {user_id}: {e}")
            return []
    
    def search_itineraries(
        self,
        destination: Optional[str] = None,
        group_type: Optional[str] = None,
        budget_range: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search itineraries by filters.
        
        Args:
            destination: Destination filter
            group_type: Group type filter
            budget_range: Budget range filter
            limit: Maximum number of results
            
        Returns:
            List of matching itinerary data
        """
        try:
            query = self.client.collection('itineraries')
            
            if destination:
                query = query.where('trip_request.destination', '==', destination)
            
            if group_type:
                query = query.where('trip_request.group_type', '==', group_type)
            
            if budget_range:
                query = query.where('trip_request.budget_range', '==', budget_range)
            
            query = query.order_by('created_at', direction=firestore.Query.DESCENDING).limit(limit)
            
            docs = query.stream()
            itineraries = []
            
            for doc in docs:
                itinerary_data = doc.to_dict()
                itinerary_data['id'] = doc.id
                itineraries.append(itinerary_data)
            
            logger.info(f"Found {len(itineraries)} itineraries matching search criteria")
            return itineraries
            
        except Exception as e:
            logger.error(f"Error searching itineraries: {e}")
            return []
    
    def save_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """
        Save user preferences.
        
        Args:
            user_id: User ID
            preferences: User preferences dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            doc_ref = self.client.collection('users').document(user_id)
            
            preferences_data = {
                'preferences': preferences,
                'updated_at': datetime.utcnow()
            }
            
            doc_ref.set(preferences_data, merge=True)
            logger.info(f"Saved preferences for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving preferences for user {user_id}: {e}")
            return False
    
    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """
        Get user preferences.
        
        Args:
            user_id: User ID
            
        Returns:
            User preferences dictionary
        """
        try:
            doc_ref = self.client.collection('users').document(user_id)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                return data.get('preferences', {})
            
            return {}
            
        except Exception as e:
            logger.error(f"Error retrieving preferences for user {user_id}: {e}")
            return {}
    
    def log_user_activity(self, user_id: str, activity: str, details: Dict[str, Any]) -> bool:
        """
        Log user activity.
        
        Args:
            user_id: User ID
            activity: Activity type
            details: Activity details
            
        Returns:
            True if successful, False otherwise
        """
        try:
            activity_data = {
                'user_id': user_id,
                'activity': activity,
                'details': details,
                'timestamp': datetime.utcnow()
            }
            
            self.client.collection('user_activities').add(activity_data)
            logger.info(f"Logged activity '{activity}' for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error logging activity for user {user_id}: {e}")
            return False
    
    def cleanup_expired_sessions(self, hours: int = 24) -> int:
        """
        Clean up expired sessions.
        
        Args:
            hours: Hours after which sessions are considered expired
            
        Returns:
            Number of sessions cleaned up
        """
        try:
            cutoff_time = datetime.utcnow().replace(
                hour=datetime.utcnow().hour - hours
            )
            
            query = (self.client.collection('sessions')
                    .where('last_activity', '<', cutoff_time))
            
            docs = query.stream()
            deleted_count = 0
            
            for doc in docs:
                doc.reference.delete()
                deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} expired sessions")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {e}")
            return 0