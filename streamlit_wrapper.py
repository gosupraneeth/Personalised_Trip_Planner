"""
Streamlit Integration Wrapper
Handles async operations and provides a clean interface between Streamlit and the ADK app.
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class StreamlitTripPlannerWrapper:
    """Wrapper to handle async operations for Streamlit integration."""
    
    def __init__(self):
        self.app = None
        self._loop = None
    
    def initialize(self):
        """Initialize the trip planner application."""
        try:
            # Import the actual app instance from app.py
            from app import app
            self.app = app
            logger.info("✅ Trip planner initialized successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to initialize trip planner: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_system_status(self) -> Dict[str, bool]:
        """Get system status information."""
        if not self.app:
            return {
                'trip_planner': False,
                'maps_api': False,
                'weather_api': False,
                'ai_agents': False
            }
        
        # Check if app has tools attribute
        tools = getattr(self.app, 'tools', {})
        agents = getattr(self.app, 'agents', {})
        
        return {
            'trip_planner': True,
            'maps_api': bool(tools.get('maps')),
            'weather_api': bool(tools.get('weather')),
            'ai_agents': len(agents) > 0
        }
    
    def process_message_sync(self, message: str, session_id: Optional[str] = None) -> str:
        """Process message synchronously for Streamlit."""
        if not self.app:
            return "❌ Trip planner not initialized"
        
        try:
            # Create a new event loop if needed
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Create session object for ADK
            class StreamlitSession:
                def __init__(self, session_id=None):
                    self.id = session_id or f"streamlit_{int(loop.time())}"
                    self.user_id = "streamlit_user"
            
            session = StreamlitSession(session_id)
            
            # Run the async function
            if loop.is_running():
                # If loop is already running, we need to handle it differently
                return self._run_in_thread(message, session)
            else:
                return loop.run_until_complete(
                    self.app.process_user_input(message, session)
                )
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            import traceback
            traceback.print_exc()
            return f"❌ Sorry, I encountered an error: {str(e)}"
    
    def _run_in_thread(self, message: str, session) -> str:
        """Run async function in a separate thread when event loop is already running."""
        import threading
        import queue
        
        result_queue = queue.Queue()
        exception_queue = queue.Queue()
        
        def run_async():
            try:
                # Create new event loop for this thread
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                
                # Import app in the thread
                from app import app
                
                result = new_loop.run_until_complete(
                    app.process_user_input(message, session)
                )
                result_queue.put(result)
                
            except Exception as e:
                exception_queue.put(e)
            finally:
                new_loop.close()
        
        thread = threading.Thread(target=run_async)
        thread.start()
        thread.join(timeout=60)  # 60 second timeout for trip planning
        
        if not exception_queue.empty():
            error = exception_queue.get()
            logger.error(f"Thread error: {error}")
            return f"❌ Error: {str(error)}"
        
        if not result_queue.empty():
            return result_queue.get()
        
        return "❌ Request timed out. Please try a simpler request."

class SimpleTripPlannerWrapper:
    """Simple wrapper for Streamlit compatibility."""
    
    def __init__(self):
        self.wrapper = StreamlitTripPlannerWrapper()
        self.available = self.wrapper.initialize()
    
    def process_message(self, message: str) -> Dict[str, Any]:
        """Process a message and return structured result."""
        if not self.available:
            return {
                "success": False,
                "response": "Trip planner not available",
                "error": "System not initialized"
            }
        
        try:
            response = self.wrapper.process_message_sync(message)
            return {
                "success": True,
                "response": response,
                "method": "ADK System"
            }
        except Exception as e:
            return {
                "success": False,
                "response": f"Error processing request: {str(e)}",
                "error": str(e)
            }

# Global wrapper instance
_wrapper = None

def get_trip_planner_wrapper() -> StreamlitTripPlannerWrapper:
    """Get or create the global wrapper instance."""
    global _wrapper
    if _wrapper is None:
        _wrapper = StreamlitTripPlannerWrapper()
        _wrapper.initialize()
    return _wrapper