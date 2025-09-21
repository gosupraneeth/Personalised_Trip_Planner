"""
Google Maps API tool for the Trip Planner ADK application.

This tool provides functionality to search for places, get place details,
and calculate distances using Google Maps API.
"""

import logging
from typing import List, Dict, Any, Optional
import googlemaps
from adk import Tool

from schemas import POI, POICategory, Coordinates, Address

logger = logging.getLogger(__name__)


class MapsApiTool(Tool):
    """Google Maps API tool for place discovery and location services."""
    
    def __init__(self, api_key: str):
        """Initialize the Maps API tool."""
        super().__init__("maps_api_tool", "Google Maps API integration for places and locations")
        self.api_key = api_key
        self.client = None
        
        try:
            self.client = googlemaps.Client(key=api_key)
            logger.info("Google Maps API tool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Google Maps client: {e}")
    
    def execute(self, operation: str, **kwargs) -> Any:
        """Execute Maps API operations."""
        if operation == "search_nearby_places":
            return self.search_nearby_places(**kwargs)
        elif operation == "get_place_details":
            return self.get_place_details(**kwargs)
        elif operation == "calculate_distance":
            return self.calculate_distance(**kwargs)
        else:
            raise ValueError(f"Unknown operation: {operation}")
    
    def search_nearby_places(
        self,
        location: str,
        radius: int = 5000,
        place_type: Optional[str] = None,
        keyword: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for nearby places around a location.
        
        Args:
            location: Location to search around (e.g., "Tokyo, Japan")
            radius: Search radius in meters (default 5000)
            place_type: Type of place to search for (e.g., "restaurant", "tourist_attraction")
            keyword: Keyword to filter results
            
        Returns:
            List of place data from Google Maps API
        """
        try:
            # First, geocode the location to get coordinates
            geocode_result = self.client.geocode(location)
            if not geocode_result:
                logger.error(f"Could not geocode location: {location}")
                return []
            
            lat_lng = geocode_result[0]['geometry']['location']
            
            # Search for nearby places
            places_result = self.client.places_nearby(
                location=lat_lng,
                radius=radius,
                type=place_type,
                keyword=keyword
            )
            
            logger.info(f"Found {len(places_result.get('results', []))} places near {location}")
            return places_result.get('results', [])
            
        except Exception as e:
            logger.error(f"Error searching places near {location}: {e}")
            return []
    
    def get_place_details(self, place_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific place.
        
        Args:
            place_id: Google Places API place ID
            
        Returns:
            Detailed place information or None if not found
        """
        try:
            fields = [
                'place_id', 'name', 'formatted_address', 'geometry',
                'rating', 'user_ratings_total', 'price_level',
                'opening_hours', 'website', 'formatted_phone_number',
                'photos', 'types', 'reviews'
            ]
            
            result = self.client.place(
                place_id=place_id,
                fields=fields
            )
            
            if result.get('status') == 'OK':
                return result.get('result')
            else:
                logger.error(f"Error getting place details for {place_id}: {result.get('status')}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting place details for {place_id}: {e}")
            return None
    
    def convert_to_poi(self, google_place: Dict[str, Any]) -> POI:
        """
        Convert Google Places API result to POI schema.
        
        Args:
            google_place: Place data from Google Places API
            
        Returns:
            POI object
        """
        try:
            # Extract coordinates
            geometry = google_place.get('geometry', {})
            location = geometry.get('location', {})
            coordinates = Coordinates(
                latitude=location.get('lat', 0.0),
                longitude=location.get('lng', 0.0)
            )
            
            # Extract address
            address_components = google_place.get('address_components', [])
            formatted_address = google_place.get('formatted_address', '')
            
            # Parse address components
            address_data = self._parse_address_components(address_components, formatted_address)
            address = Address(**address_data)
            
            # Map Google place types to our POI categories
            category = self._map_place_type_to_category(google_place.get('types', []))
            
            # Extract photos
            photos = []
            if 'photos' in google_place:
                for photo in google_place['photos'][:5]:  # Limit to 5 photos
                    photo_ref = photo.get('photo_reference')
                    if photo_ref:
                        photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={photo_ref}&key={self.api_key}"
                        photos.append(photo_url)
            
            # Extract opening hours
            opening_hours = {}
            if 'opening_hours' in google_place and 'weekday_text' in google_place['opening_hours']:
                for day_hours in google_place['opening_hours']['weekday_text']:
                    day, hours = day_hours.split(': ', 1)
                    opening_hours[day.lower()] = hours
            
            return POI(
                id=google_place.get('place_id', ''),
                name=google_place.get('name', ''),
                description=self._extract_description(google_place),
                category=category,
                coordinates=coordinates,
                address=address,
                rating=google_place.get('rating'),
                review_count=google_place.get('user_ratings_total', 0),
                price_level=google_place.get('price_level'),
                opening_hours=opening_hours,
                website=google_place.get('website'),
                phone=google_place.get('formatted_phone_number'),
                photos=photos,
                amenities=self._extract_amenities(google_place)
            )
            
        except Exception as e:
            logger.error(f"Error converting Google place to POI: {e}")
            raise
    
    def _parse_address_components(self, components: List[Dict], formatted_address: str) -> Dict[str, Any]:
        """Parse Google Places address components."""
        address_data = {
            'formatted_address': formatted_address,
            'city': '',
            'country': ''
        }
        
        for component in components:
            types = component.get('types', [])
            long_name = component.get('long_name', '')
            
            if 'street_number' in types:
                address_data['street'] = long_name
            elif 'route' in types:
                street = address_data.get('street', '')
                address_data['street'] = f"{street} {long_name}".strip()
            elif 'locality' in types or 'administrative_area_level_2' in types:
                address_data['city'] = long_name
            elif 'administrative_area_level_1' in types:
                address_data['state'] = long_name
            elif 'country' in types:
                address_data['country'] = long_name
            elif 'postal_code' in types:
                address_data['postal_code'] = long_name
        
        return address_data
    
    def _map_place_type_to_category(self, place_types: List[str]) -> POICategory:
        """Map Google place types to POI categories."""
        type_mapping = {
            'restaurant': POICategory.RESTAURANT,
            'food': POICategory.RESTAURANT,
            'meal_takeaway': POICategory.RESTAURANT,
            'cafe': POICategory.RESTAURANT,
            'tourist_attraction': POICategory.ATTRACTION,
            'amusement_park': POICategory.ATTRACTION,
            'aquarium': POICategory.ATTRACTION,
            'zoo': POICategory.ATTRACTION,
            'museum': POICategory.MUSEUM,
            'art_gallery': POICategory.MUSEUM,
            'park': POICategory.PARK,
            'shopping_mall': POICategory.SHOPPING,
            'store': POICategory.SHOPPING,
            'night_club': POICategory.NIGHTLIFE,
            'bar': POICategory.NIGHTLIFE,
            'lodging': POICategory.ACCOMMODATION,
            'subway_station': POICategory.TRANSPORT,
            'train_station': POICategory.TRANSPORT,
            'airport': POICategory.TRANSPORT,
            'movie_theater': POICategory.ENTERTAINMENT,
            'church': POICategory.RELIGIOUS,
            'mosque': POICategory.RELIGIOUS,
            'temple': POICategory.RELIGIOUS,
            'hindu_temple': POICategory.RELIGIOUS
        }
        
        for place_type in place_types:
            if place_type in type_mapping:
                return type_mapping[place_type]
        
        # Default to attraction if no specific mapping found
        return POICategory.ATTRACTION
    
    def _extract_description(self, google_place: Dict[str, Any]) -> Optional[str]:
        """Extract description from Google place data."""
        # Try to get description from reviews
        reviews = google_place.get('reviews', [])
        if reviews:
            # Use the first review as description (truncated)
            first_review = reviews[0].get('text', '')
            if len(first_review) > 200:
                return first_review[:200] + "..."
            return first_review
        
        return None
    
    def _extract_amenities(self, google_place: Dict[str, Any]) -> List[str]:
        """Extract amenities from Google place types."""
        amenity_mapping = {
            'wheelchair_accessible_entrance': 'Wheelchair Accessible',
            'delivery': 'Delivery Available',
            'takeout': 'Takeout Available',
            'reservable': 'Reservations Available',
            'serves_beer': 'Serves Alcohol',
            'serves_wine': 'Serves Wine',
            'serves_breakfast': 'Breakfast',
            'serves_lunch': 'Lunch',
            'serves_dinner': 'Dinner',
            'outdoor_seating': 'Outdoor Seating',
            'wifi': 'Free WiFi',
            'parking': 'Parking Available'
        }
        
        amenities = []
        place_types = google_place.get('types', [])
        
        for place_type in place_types:
            if place_type in amenity_mapping:
                amenities.append(amenity_mapping[place_type])
        
        return amenities
    
    def calculate_distance_matrix(
        self,
        origins: List[str],
        destinations: List[str],
        mode: str = "driving"
    ) -> Dict[str, Any]:
        """
        Calculate distance and duration between multiple points.
        
        Args:
            origins: List of origin addresses or coordinates
            destinations: List of destination addresses or coordinates
            mode: Travel mode ("driving", "walking", "transit", "bicycling")
            
        Returns:
            Distance matrix data
        """
        try:
            result = self.client.distance_matrix(
                origins=origins,
                destinations=destinations,
                mode=mode,
                units="metric"
            )
            return result
            
        except Exception as e:
            logger.error(f"Error calculating distance matrix: {e}")
            return {}
    
    def get_directions(
        self,
        origin: str,
        destination: str,
        mode: str = "driving"
    ) -> List[Dict[str, Any]]:
        """
        Get directions between two points.
        
        Args:
            origin: Starting point
            destination: Ending point
            mode: Travel mode
            
        Returns:
            Directions data
        """
        try:
            result = self.client.directions(
                origin=origin,
                destination=destination,
                mode=mode
            )
            return result
            
        except Exception as e:
            logger.error(f"Error getting directions from {origin} to {destination}: {e}")
            return []