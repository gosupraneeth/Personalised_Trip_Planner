"""
Trip Planner Agent for ADK Web UI.

This agent serves as the root agent for the Trip Planner application,
providing a simple interface for trip planning interactions.
"""

from google.adk.agents import Agent


def get_trip_suggestions(destination: str, duration: str = "3 days") -> dict:
    """Get trip suggestions for a destination.
    
    Args:
        destination (str): The destination city or location
        duration (str): Duration of the trip (e.g., "3 days", "1 week")
    
    Returns:
        dict: Trip suggestions and recommendations
    """
    return {
        "status": "success",
        "destination": destination,
        "duration": duration,
        "suggestions": f"Here are some great suggestions for your {duration} trip to {destination}:\n"
                      f"• Visit the main attractions and landmarks\n"
                      f"• Try local cuisine and restaurants\n"
                      f"• Explore cultural sites and museums\n"
                      f"• Check the weather forecast for your travel dates\n"
                      f"• Book accommodations in advance"
    }


def get_weather_info(city: str) -> dict:
    """Get current weather information for a city.
    
    Args:
        city (str): The city name
    
    Returns:
        dict: Weather information
    """
    # This is a simple mock - in a real implementation, 
    # you would integrate with your actual weather service
    return {
        "status": "success",
        "city": city,
        "weather": f"Current weather in {city}: Partly cloudy, 22°C (72°F). Perfect for sightseeing!"
    }


def find_attractions(location: str, category: str = "all") -> dict:
    """Find attractions in a specific location.
    
    Args:
        location (str): The location to search for attractions
        category (str): Category of attractions (all, museums, restaurants, parks, etc.)
    
    Returns:
        dict: List of attractions
    """
    return {
        "status": "success",
        "location": location,
        "category": category,
        "attractions": f"Top {category} attractions in {location}:\n"
                      f"• Historical landmarks and monuments\n"
                      f"• Popular museums and galleries\n"
                      f"• Scenic parks and outdoor spaces\n"
                      f"• Highly-rated restaurants and cafes\n"
                      f"• Local markets and shopping areas"
    }


# Create the root agent that ADK will discover
root_agent = Agent(
    name="trip_planner_agent",
    model="gemini-2.0-flash",
    description="AI-powered trip planning assistant that helps you plan personalized trips",
    instruction=(
        "You are a helpful trip planning assistant. You can help users plan trips, "
        "get weather information, find attractions, and provide travel recommendations. "
        "Always be friendly, informative, and provide practical travel advice."
    ),
    tools=[get_trip_suggestions, get_weather_info, find_attractions],
)