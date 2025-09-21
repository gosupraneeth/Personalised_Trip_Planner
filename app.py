"""
Main ADK Application for the Personalized Trip Planner.

This file configures and runs the multi-agent trip planning application
using Google's Agent Development Kit (ADK).
"""

import os
import logging
from typing import Dict, Any, Optional, List
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
    
    def ensure_session_registered(self, session: Session) -> Session:
        """Ensure session is properly registered with the application."""
        # Register with app's session store
        if hasattr(session, 'id') and session.id not in self.sessions:
            self.sessions[session.id] = session
            logger.info(f"Registered session {session.id} with application")
        
        # Always try to save to Firestore for orchestrator compatibility
        firestore_tool = self.tools.get("firestore")
        if firestore_tool and hasattr(session, 'id'):
            try:
                # Check if session already exists in Firestore
                existing_session = firestore_tool.get_session(session.id)
                if not existing_session:
                    from schemas import SessionData
                    from datetime import datetime
                    
                    # Create SessionData object for Firestore
                    session_data = SessionData(
                        session_id=session.id,
                        user_id=getattr(session, 'user_id', 'unknown'),
                        created_at=datetime.utcnow(),
                        conversation_history=[]
                    )
                    
                    # Save to Firestore
                    result = firestore_tool.save_session(session_data)
                    if result:
                        logger.info(f"Saved session {session.id} to Firestore")
                    else:
                        logger.warning(f"Failed to save session {session.id} to Firestore")
                    
            except Exception as e:
                logger.warning(f"Failed to save session to Firestore: {e}")
                    
        return session
    
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
            # Ensure session is registered with the app
            session = self.ensure_session_registered(session)
            
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
    
    def get_user_sessions(self, user_id: str, limit: Optional[int] = None, active_only: bool = False) -> List[Dict[str, Any]]:
        """
        Get all sessions for a specific user.
        
        Args:
            user_id: User ID to retrieve sessions for
            limit: Maximum number of sessions to return
            active_only: If True, only return active sessions
            
        Returns:
            List of session dictionaries
        """
        try:
            firestore_tool = self.tools.get("firestore")
            if not firestore_tool:
                logger.error("Firestore tool not available")
                return []
            
            sessions = firestore_tool.get_user_sessions(user_id, limit, active_only)
            
            # Convert to dictionary format for easier consumption
            session_list = []
            for session in sessions:
                session_dict = {
                    "session_id": session.session_id,
                    "user_id": session.user_id,
                    "created_at": session.created_at.isoformat() if session.created_at else None,
                    "last_activity": session.last_activity.isoformat() if session.last_activity else None,
                    "is_active": session.is_active,
                    "has_trip_request": session.trip_request is not None,
                    "has_itinerary": session.current_itinerary is not None,
                    "conversation_length": len(session.conversation_history)
                }
                
                # Add trip details if available
                if session.trip_request:
                    session_dict["destination"] = session.trip_request.destination
                    session_dict["start_date"] = session.trip_request.start_date.isoformat() if session.trip_request.start_date else None
                    session_dict["duration_days"] = session.trip_request.duration_days
                
                session_list.append(session_dict)
            
            return session_list
            
        except Exception as e:
            logger.error(f"Error retrieving user sessions: {e}")
            return []
    
    def get_user_latest_session(self, user_id: str) -> Optional[Session]:
        """
        Get the most recent session for a user and load it into the app.
        
        Args:
            user_id: User ID to get latest session for
            
        Returns:
            Session object or None if not found
        """
        try:
            firestore_tool = self.tools.get("firestore")
            if not firestore_tool:
                logger.error("Firestore tool not available")
                return None
            
            session_data = firestore_tool.get_user_latest_session(user_id)
            if session_data:
                # Create ADK Session object
                session = Session(session_id=session_data.session_id, user_id=session_data.user_id)
                
                # Register with app
                self.sessions[session_data.session_id] = session
                
                logger.info(f"Loaded latest session {session_data.session_id} for user {user_id}")
                return session
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting user latest session: {e}")
            return None
    
    def format_user_sessions_summary(self, user_id: str) -> str:
        """
        Get a formatted summary of all sessions for a user.
        
        Args:
            user_id: User ID to get sessions summary for
            
        Returns:
            Formatted string with session summary
        """
        try:
            sessions = self.get_user_sessions(user_id)
            
            if not sessions:
                return f"👤 **User {user_id}**\n❌ No sessions found."
            
            # Get user info
            firestore_tool = self.tools.get("firestore")
            user_info = firestore_tool.get_user_info(user_id) if firestore_tool else None
            
            summary = f"👤 **User {user_id}**\n"
            summary += f"📊 **Total Sessions:** {len(sessions)}\n"
            
            if user_info:
                if 'last_activity' in user_info:
                    summary += f"⏰ **Last Activity:** {user_info['last_activity']}\n"
            
            active_sessions = [s for s in sessions if s['is_active']]
            summary += f"🔄 **Active Sessions:** {len(active_sessions)}\n\n"
            
            summary += "📋 **Recent Sessions:**\n"
            for i, session in enumerate(sessions[:5], 1):  # Show top 5 recent sessions
                status_icon = "🟢" if session['is_active'] else "🔴"
                summary += f"{status_icon} **{session['session_id'][:8]}...** "
                
                if session.get('destination'):
                    summary += f"({session['destination']}) "
                
                summary += f"- {session['last_activity'][:10]}\n"
            
            if len(sessions) > 5:
                summary += f"... and {len(sessions) - 5} more sessions\n"
            
            return summary
            
        except Exception as e:
            logger.error(f"Error formatting user sessions summary: {e}")
            return f"❌ Error retrieving sessions for user {user_id}"


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
    import sys
    from adk import Session as AdkSession
    
    async def interactive_session():
        """Interactive session for single user trip planning."""
        print("🚀 Trip Planner - Interactive Mode")
        print("=" * 50)
        print("Welcome to your AI-powered trip planning assistant!")
        print("Type 'quit', 'exit', or 'bye' to end the session.")
        print("Type 'help' for available commands.")
        print("=" * 50)
        
        # Get user ID
        try:
            user_id = input("\n👤 Enter your user ID (or press Enter for default): ").strip()
        except EOFError:
            user_id = ""
        
        if not user_id:
            user_id = "default-user"
        
        print(f"Hello {user_id}! Let's plan your perfect trip!")
        
        # Check for existing sessions for this user
        existing_sessions = app.get_user_sessions(user_id, limit=3, active_only=True)
        
        session = None
        if existing_sessions:
            print(f"\n📋 Found {len(existing_sessions)} active session(s) for you:")
            for i, sess in enumerate(existing_sessions, 1):
                created = sess['created_at'][:10] if sess.get('created_at') else 'Unknown'
                destination = sess.get('destination', 'No destination set')
                print(f"  {i}. Session {sess['session_id'][:8]}... - {destination} ({created})")
            
            choice = input(f"\nWould you like to continue an existing session? (1-{len(existing_sessions)}/new): ").strip().lower()
            
            if choice.isdigit() and 1 <= int(choice) <= len(existing_sessions):
                selected_session = existing_sessions[int(choice) - 1]
                # Load the existing session
                session = app.get_user_latest_session(user_id)
                if session and session.id == selected_session['session_id']:
                    print(f"✅ Continuing session {session.id[:8]}...")
                else:
                    # Create session object from session data
                    session = Session(session_id=selected_session['session_id'], user_id=user_id)
                    app.sessions[session.id] = session
                    print(f"✅ Loaded session {session.id[:8]}...")
        
        # Create new session if none selected
        if not session:
            print("🆕 Creating a new session...")
            session = app.create_session(user_id=user_id)
            session = app.ensure_session_registered(session)
            print(f"✅ Created new session {session.id[:8]}...")
        
        print(f"\n🎯 Session ID: {session.id}")
        print("You can use this session ID to continue later.")
        print("\n" + "=" * 50)
        
        # Interactive loop
        conversation_count = 0
        while True:
            try:
                # Get user input
                try:
                    user_input = input(f"\n[{conversation_count + 1}] You: ").strip()
                except EOFError:
                    print("\n👋 Input stream ended. Goodbye!")
                    break
                
                if not user_input:
                    continue
                
                # Check for exit commands
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("\n👋 Thanks for using Trip Planner! Have a great trip!")
                    break
                
                # Check for help command
                if user_input.lower() == 'help':
                    print("\n📋 Available commands:")
                    print("  - Type your trip planning request naturally")
                    print("  - 'sessions' - View your recent sessions")
                    print("  - 'status' - Check current session status")
                    print("  - 'clear' - Start a new session")
                    print("  - 'help' - Show this help")
                    print("  - 'quit', 'exit', 'bye' - End session")
                    continue
                
                # Check for special commands
                if user_input.lower() == 'sessions':
                    summary = app.format_user_sessions_summary(user_id)
                    print(f"\n{summary}")
                    continue
                
                if user_input.lower() == 'status':
                    status = app.get_session_status(session.id)
                    print(f"\n{status}")
                    continue
                
                if user_input.lower() == 'clear':
                    session = app.create_session(user_id=user_id)
                    session = app.ensure_session_registered(session)
                    print(f"🆕 Created new session {session.id[:8]}...")
                    conversation_count = 0
                    continue
                
                # Process the trip planning request
                print(f"\n🤖 Assistant: Processing your request...")
                
                response = await app.process_user_input(user_input, session)
                print(f"\n🤖 Assistant: {response}")
                
                conversation_count += 1
                
            except KeyboardInterrupt:
                print("\n\n👋 Session interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                print("Please try again or type 'help' for assistance.")
    
    async def test_multi_user_sessions():
        """Test the application with multiple users (for development/testing)."""
        print("🚀 Trip Planner ADK Application - Multi-User Test Mode")
        print("=" * 50)
        
        # Test multiple users with sessions
        test_users = ["user-123", "user-456", "user-789"]
        all_sessions = {}
        
        # Create sessions for different users
        for user_id in test_users:
            print(f"\n👤 Creating session for {user_id}")
            session = app.create_session(user_id=user_id)
            session = app.ensure_session_registered(session)
            all_sessions[user_id] = session
            print(f"✅ Created session {session.id[:8]}... for {user_id}")
        
        # Test user session retrieval
        print(f"\n📋 Testing user session management")
        print("-" * 50)
        
        for user_id in test_users:
            sessions = app.get_user_sessions(user_id)
            print(f"User {user_id}: {len(sessions)} sessions")
            
            latest_session = app.get_user_latest_session(user_id)
            if latest_session:
                print(f"  Latest session: {latest_session.id[:8]}...")
        
        # Test trip planning with one user
        test_user = test_users[0]
        session = all_sessions[test_user]
        
        print(f"\n🎯 Testing trip planning for {test_user}")
        print("-" * 50)
        
        # Test user inputs for this specific user
        test_inputs = [
            "I want to plan a 3-day trip to Paris for 2 adults, budget around $2000, interested in art and food",
            "Can you make it cheaper?",
            "Add more museums instead of restaurants"
        ]
        
        for i, user_input in enumerate(test_inputs, 1):
            print(f"\n[Test {i}] User {test_user}: {user_input}")
            print("-" * 30)
            
            try:
                response = await app.process_user_input(user_input, session)
                print(f"Assistant: {response}")
            except Exception as e:
                print(f"Error: {e}")
                import traceback
                traceback.print_exc()
            
            print("\n" + "=" * 50)
        
        # Test user sessions summary
        print(f"\n📊 User Sessions Summary")
        print("-" * 50)
        for user_id in test_users:
            summary = app.format_user_sessions_summary(user_id)
            print(summary)
            print("-" * 30)
        
        # Test session status for the main test user
        print(f"\n🔍 Session Status for {test_user}")
        print("-" * 50)
        status = app.get_session_status(session.id)
        print(status)
    
    async def main():
        """Main entry point - choose between interactive and test mode."""
        # Check command line arguments
        if len(sys.argv) > 1:
            if sys.argv[1] in ['--test', '-t', '--multi-user', '-m']:
                await test_multi_user_sessions()
            elif sys.argv[1] in ['--help', '-h']:
                print("🚀 Trip Planner ADK Application")
                print("=" * 50)
                print("Usage:")
                print("  python app.py                    # Interactive mode (default)")
                print("  python app.py --test            # Multi-user test mode")
                print("  python app.py --multi-user      # Multi-user test mode")
                print("  python app.py --help            # Show this help")
                print("\nInteractive mode commands:")
                print("  - Type your trip planning requests naturally")
                print("  - 'sessions' - View your sessions")
                print("  - 'status' - Check session status")
                print("  - 'clear' - Start new session")
                print("  - 'help' - Show help")
                print("  - 'quit' - Exit")
            else:
                print(f"❌ Unknown argument: {sys.argv[1]}")
                print("Use --help for usage information")
        else:
            # Default: interactive mode
            await interactive_session()
    
    # Run the application
    asyncio.run(main())