"""
Main ADK Application for the Personalized Trip Planner.

This file configures and runs the multi-agent trip planning application
using Google's Agent Development Kit (ADK).
"""

import os
import logging
from typing import Dict, Any, Optional
from adk import AdkApp, Session, Tool, Agent
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import our core agents
from agents.orchestrator import OrchestratorAgent
from agents.user_intent import UserIntentAgent
from agents.place_finder import PlaceFinderAgent
from agents.weather import WeatherAgent
from agents.itinerary_planner import ItineraryPlannerAgent

# Import all our tools
from tools.maps_api import MapsApiTool
from tools.weather_api import WeatherApiTool
from tools.bigquery_tool import BigQueryTool
from tools.firestore_tool import FirestoreTool
from tools.payment_tool import PaymentTool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TripPlannerApp(AdkApp):
    """Main ADK application for trip planning."""
    
    def __init__(self):
        """Initialize the Trip Planner ADK application."""
        super().__init__(
            name="trip_planner",
            description="AI-powered personalized trip planning assistant"
        )
        
        # Configuration
        self.config = self._load_configuration()
        
        # Initialize tools
        self.tools = self._initialize_tools()
        
        # Initialize agents
        self.agents = self._initialize_agents()
        
        # Register everything with ADK
        self._register_tools()
        self._register_agents()
        
        logger.info("Trip Planner ADK application initialized")
    
    def _load_configuration(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        config = {
            # Google Cloud Configuration
            "project_id": os.getenv("GOOGLE_CLOUD_PROJECT", "your-project-id"),
            "location": os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
            
            # Vertex AI Configuration
            "vertex_ai": {
                "project_id": os.getenv("GOOGLE_CLOUD_PROJECT", "your-project-id"),
                "location": os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
                "model": os.getenv("VERTEX_AI_MODEL", "gemini-1.5-pro")
            },
            
            # API Keys
            "google_maps_api_key": os.getenv("GOOGLE_MAPS_API_KEY"),
            "openweather_api_key": os.getenv("OPENWEATHER_API_KEY"),
            "stripe_api_key": os.getenv("STRIPE_API_KEY"),
            
            # BigQuery Configuration
            "bigquery": {
                "dataset_id": os.getenv("BIGQUERY_DATASET_ID", "trip_planner"),
                "location": os.getenv("BIGQUERY_LOCATION", "US")
            },
            
            # Firestore Configuration
            "firestore": {
                "database": os.getenv("FIRESTORE_DATABASE", "(default)")
            }
        }
        
        # Debug: Print loaded configuration (without sensitive data)
        logger.info(f"Loaded configuration:")
        logger.info(f"  Project ID: {config['project_id']}")
        logger.info(f"  Location: {config['location']}")
        logger.info(f"  Maps API Key: {'***' + config['google_maps_api_key'][-4:] if config['google_maps_api_key'] else 'Not set'}")
        logger.info(f"  Weather API Key: {'***' + config['openweather_api_key'][-4:] if config['openweather_api_key'] else 'Not set'}")
        
        # Validate required configuration
        required_keys = ["google_maps_api_key", "openweather_api_key"]
        missing_keys = [key for key in required_keys if not config.get(key)]
        
        if missing_keys:
            logger.warning(f"Missing configuration for: {missing_keys}")
        
        return config
    
    def _initialize_tools(self) -> Dict[str, Tool]:
        """Initialize all tools for the application."""
        tools = {}
        
        try:
            # Maps API Tool
            if self.config.get("google_maps_api_key"):
                tools["maps"] = MapsApiTool(self.config["google_maps_api_key"])
                logger.info("Maps API tool initialized")
            else:
                logger.warning("Maps API tool not initialized - missing API key")
            
            # Weather API Tool
            if self.config.get("openweather_api_key"):
                tools["weather"] = WeatherApiTool(self.config["openweather_api_key"])
                logger.info("Weather API tool initialized")
            else:
                logger.warning("Weather API tool not initialized - missing API key")
            
            # BigQuery Tool
            tools["bigquery"] = BigQueryTool(
                project_id=self.config["project_id"],
                dataset_id=self.config["bigquery"]["dataset_id"],
                location=self.config["bigquery"]["location"]
            )
            logger.info("BigQuery tool initialized")
            
            # Firestore Tool
            tools["firestore"] = FirestoreTool(
                project_id=self.config["project_id"],
                database=self.config["firestore"]["database"]
            )
            logger.info("Firestore tool initialized")
            
            # Payment Tool
            if self.config.get("stripe_api_key"):
                tools["payment"] = PaymentTool(self.config["stripe_api_key"])
                logger.info("Payment tool initialized")
            else:
                logger.warning("Payment tool not initialized - missing API key")
            
        except Exception as e:
            logger.error(f"Error initializing tools: {e}")
        
        return tools
    
    def _initialize_agents(self) -> Dict[str, Agent]:
        """Initialize all agents for the application."""
        agents = {}
        
        try:
            vertex_config = self.config["vertex_ai"]
            
            # Initialize our core agents
            agents["orchestrator"] = OrchestratorAgent(vertex_config)
            agents["user_intent"] = UserIntentAgent(vertex_config)
            agents["place_finder"] = PlaceFinderAgent(vertex_config)
            agents["weather"] = WeatherAgent(vertex_config)
            agents["itinerary_planner"] = ItineraryPlannerAgent(vertex_config)
            
            logger.info(f"Initialized {len(agents)} agents")
            
        except Exception as e:
            logger.error(f"Error initializing agents: {e}")
        
        return agents
    
    def _register_tools(self):
        """Register tools with the ADK application."""
        for tool_name in list(self.tools.keys()):
            try:
                tool_instance = self.tools[tool_name]
                self.add_tool(tool_instance)
                logger.info(f"Registered tool: {tool_name}")
            except Exception as e:
                logger.error(f"Error registering tool {tool_name}: {e}")
    
    def _register_agents(self):
        """Register agents with the ADK application."""
        for agent_name in list(self.agents.keys()):
            try:
                agent_instance = self.agents[agent_name]
                self.add_agent(agent_instance)
                logger.info(f"Registered agent: {agent_name}")
            except Exception as e:
                logger.error(f"Error registering agent {agent_name}: {e}")
    
    async def process_user_input(self, user_input: str, session: Session) -> str:
        """
        Process user input through the trip planning workflow.
        
        Args:
            user_input: User's message/request
            session: ADK session object
            
        Returns:
            Response message
        """
        try:
            # Get the orchestrator agent
            orchestrator = self.agents.get("orchestrator")
            if not orchestrator:
                return "Trip planning system not available. Please try again later."
            
            # Extract session information
            session_id = session.id if hasattr(session, 'id') else None
            user_id = session.user_id if hasattr(session, 'user_id') else None
            
            # Check if this is a refinement request (has existing session)
            is_refinement = self._is_refinement_request(user_input, session_id)
            
            if is_refinement and session_id:
                # Handle itinerary refinement
                response = orchestrator.refine_itinerary(
                    session_id=session_id,
                    user_feedback=user_input,
                    tools=self.tools
                )
            else:
                # Handle new trip planning request
                response = orchestrator.plan_trip(
                    user_input=user_input,
                    session_id=session_id,
                    user_id=user_id,
                    tools=self.tools
                )
            
            # Format response for user
            return self._format_response(response)
            
        except Exception as e:
            logger.error(f"Error processing user input: {e}")
            return "I apologize, but I encountered an error while planning your trip. Please try again."
    
    def _is_refinement_request(self, user_input: str, session_id: Optional[str]) -> bool:
        """Check if the user input is a refinement request for existing itinerary."""
        if not session_id:
            return False
        
        # Check if session has existing itinerary
        firestore_tool = self.tools.get("firestore")
        if firestore_tool:
            try:
                session_data = firestore_tool.get_session(session_id)
                if session_data and session_data.current_itinerary:
                    # Check for refinement keywords
                    refinement_keywords = [
                        "change", "modify", "different", "instead", "replace",
                        "earlier", "later", "cheaper", "expensive", "add", "remove"
                    ]
                    user_input_lower = user_input.lower()
                    return any(keyword in user_input_lower for keyword in refinement_keywords)
            except Exception as e:
                logger.error(f"Error checking for refinement request: {e}")
        
        return False
    
    def _format_response(self, agent_response) -> str:
        """Format agent response for user display."""
        try:
            if not agent_response.success:
                # Handle error responses
                if agent_response.data and "clarifying_questions" in agent_response.data:
                    # Need more information
                    questions = agent_response.data["clarifying_questions"]
                    message = "I need a bit more information to create your perfect trip:\n\n"
                    for i, question in enumerate(questions, 1):
                        message += f"{i}. {question}\n"
                    return message
                else:
                    return f"❌ {agent_response.message or 'Something went wrong'}"
            
            # Handle successful responses
            data = agent_response.data
            message = f"✅ {agent_response.message}\n\n"
            
            # Add itinerary summary if available
            if "itinerary" in data:
                itinerary = data["itinerary"]
                message += f"📍 **Destination:** {itinerary['trip_request']['destination']}\n"
                message += f"📅 **Duration:** {len(itinerary['days'])} days\n"
                message += f"💰 **Total Estimated Cost:** ${float(itinerary['total_cost']):.2f}\n"
                message += f"🎯 **Activities:** {sum(len(day['items']) for day in itinerary['days'])}\n\n"
                
                # Add daily breakdown
                message += "📋 **Daily Itinerary:**\n"
                for day in itinerary['days']:
                    message += f"**Day {day['day']}** ({len(day['items'])} activities, ${day['total_estimated_cost']:.2f})\n"
                    for item in day['items'][:3]:  # Show first 3 activities
                        message += f"  • {item['title']} ({item['start_time']} - {item['end_time']})\n"
                    if len(day['items']) > 3:
                        message += f"  • ... and {len(day['items']) - 3} more activities\n"
                    message += "\n"
            
            # Add AI insights if available
            if "ai_insights" in data and data["ai_insights"]:
                insights = data["ai_insights"]
                if "highlights" in insights and insights["highlights"]:
                    message += "✨ **Trip Highlights:**\n"
                    for highlight in insights["highlights"]:
                        message += f"  • {highlight}\n"
                    message += "\n"
            
            # Add session information
            if "session_id" in data:
                message += f"🔗 **Session ID:** `{data['session_id']}` (save this to modify your trip later)\n"
            
            return message
            
        except Exception as e:
            logger.error(f"Error formatting response: {e}")
            return "Your trip has been planned successfully! However, I had trouble displaying the details. Please check your session."
    
    def get_session_status(self, session_id: str) -> str:
        """Get status of a planning session."""
        try:
            orchestrator = self.agents.get("orchestrator")
            if not orchestrator:
                return "Session management not available."
            
            response = orchestrator.get_workflow_status(session_id, self.tools)
            
            if not response.success:
                return f"❌ {response.message}"
            
            data = response.data
            status_message = f"📊 **Session Status**\n"
            status_message += f"🆔 **Session ID:** {data['session_id']}\n"
            status_message += f"📅 **Created:** {data['created_at']}\n"
            status_message += f"🔄 **Active:** {'Yes' if data['is_active'] else 'No'}\n"
            
            if data['has_trip_request'] and "trip_details" in data:
                trip = data["trip_details"]
                status_message += f"📍 **Destination:** {trip['destination']}\n"
                status_message += f"📅 **Start Date:** {trip['start_date']}\n"
                status_message += f"⏰ **Duration:** {trip['duration_days']} days\n"
            
            if data['has_itinerary'] and "itinerary_summary" in data:
                summary = data["itinerary_summary"]
                status_message += f"💰 **Total Cost:** ${summary['total_cost']:.2f}\n"
                status_message += f"🎯 **Activities:** {summary['total_activities']}\n"
            
            return status_message
            
        except Exception as e:
            logger.error(f"Error getting session status: {e}")
            return "Error retrieving session status."


# Create the main application instance
app = TripPlannerApp()


# ADK entry points
def create_app():
    """ADK entry point for creating the application."""
    return app


async def handle_message(user_input: str, session: Session) -> str:
    """ADK entry point for handling user messages."""
    return await app.process_user_input(user_input, session)


# For local development and testing
if __name__ == "__main__":
    import asyncio
    
    async def test_app():
        """Test the application locally."""
        print("🚀 Trip Planner ADK Application")
        print("=" * 50)
        
        # Create a mock session
        class MockSession:
            def __init__(self):
                self.id = "test-session-123"
                self.user_id = "test-user-456"
        
        session = MockSession()
        
        # Test user inputs
        test_inputs = [
            "I want to plan a 3-day trip to Paris for 2 adults, budget around $2000, interested in art and food",
            "Can you make it cheaper?",
            "Add more museums instead of restaurants"
        ]
        
        for i, user_input in enumerate(test_inputs, 1):
            print(f"\n[Test {i}] User: {user_input}")
            print("-" * 50)
            
            try:
                response = await app.process_user_input(user_input, session)
                print(f"Assistant: {response}")
            except Exception as e:
                print(f"Error: {e}")
            
            print("\n" + "=" * 50)
        
        # Test session status
        print(f"\n[Session Status]")
        print("-" * 50)
        status = app.get_session_status(session.id)
        print(status)
    
    # Run the test
    asyncio.run(test_app())