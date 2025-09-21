"""
Main Orchestrator Agent for the Trip Planner ADK application.

This agent coordinates the entire trip planning workflow by managing
and calling other specialized agents in the correct sequence.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid
from adk import LlmAgent
from google.cloud import aiplatform

from schemas import (
    TripRequest, Itinerary, SessionData, AgentResponse,
    POI, WeatherInfo, BookingBasket
)
from agents.user_intent import UserIntentAgent
from agents.place_finder import PlaceFinderAgent
from agents.weather import WeatherAgent
from agents.itinerary_planner import ItineraryPlannerAgent
from tools import MapsApiTool, WeatherApiTool, BigQueryTool, FirestoreTool

logger = logging.getLogger(__name__)


class OrchestratorAgent(LlmAgent):
    """Main orchestrator agent that coordinates the trip planning workflow."""
    
    def __init__(self, vertex_config: Dict[str, Any]):
        """Initialize the Orchestrator Agent."""
        super().__init__(
            name="orchestrator_agent",
            description="Coordinates the complete trip planning workflow"
        )
        self.vertex_config = vertex_config
        self.model_name = vertex_config.get("model", "gemini-1.5-pro")
        
        # Initialize Vertex AI
        aiplatform.init(
            project=vertex_config["project_id"],
            location=vertex_config["location"]
        )
        
        # Initialize sub-agents
        self.user_intent_agent = UserIntentAgent(vertex_config)
        self.place_finder_agent = PlaceFinderAgent(vertex_config)
        self.weather_agent = WeatherAgent(vertex_config)
        self.itinerary_planner_agent = ItineraryPlannerAgent(vertex_config)
        
        logger.info("Orchestrator Agent initialized")
    
    def plan_trip(
        self,
        user_input: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        tools: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        Execute the complete trip planning workflow.
        
        Args:
            user_input: User's trip planning request
            session_id: Session identifier
            user_id: User identifier
            tools: Dictionary of tool instances
            
        Returns:
            AgentResponse with complete trip plan
        """
        try:
            # Generate session ID if not provided
            if not session_id:
                session_id = str(uuid.uuid4())
            
            # Try to retrieve existing session data or create new one
            session_data = self._get_or_create_session_data(
                session_id, user_id, user_input, tools
            )
            
            # Step 1: Analyze user intent and extract trip requirements
            logger.info(f"Step 1: Analyzing user intent for session {session_id}")
            
            # Get accumulated context from previous conversation
            accumulated_context = self._build_accumulated_context(session_data)
            
            intent_response = self.user_intent_agent.analyze_user_input(
                user_input, 
                context=accumulated_context
            )
            
            if not intent_response.success:
                return self._create_error_response("Failed to understand trip requirements", intent_response.error)
            
            # Merge new trip data with existing partial data (if any)
            trip_data = self._merge_trip_data(session_data, intent_response.data)
            
            # Validate merged trip requirements
            validation = self.user_intent_agent.validate_trip_requirements(trip_data)
            
            # Update session data with accumulated trip information
            session_data.agent_context['partial_trip_data'] = trip_data
            session_data.agent_context['validation_status'] = validation
            
            if not validation["is_complete"]:
                # Save session data with partial trip information
                if tools and "firestore" in tools:
                    tools["firestore"].save_session(session_data)
                
                # Generate clarifying questions based on what's still missing
                questions = self.user_intent_agent.generate_clarifying_questions(trip_data)
                
                return AgentResponse(
                    agent_name=self.name,
                    success=False,
                    data={
                        "clarifying_questions": questions,
                        "partial_data": trip_data,
                        "missing_fields": validation["missing_required"],
                        "session_id": session_id,
                        "conversation_count": len(session_data.conversation_history)
                    },
                    message="Need more information to create your trip plan",
                    error="Incomplete trip requirements"
                )
            
            # Create trip request
            trip_request = self.user_intent_agent.create_trip_request(trip_data)
            if not trip_request:
                return self._create_error_response("Failed to create trip request", "Invalid trip data")
            
            session_data.trip_request = trip_request
            
            # Step 2: Find places of interest
            logger.info(f"Step 2: Finding places for {trip_request.destination}")
            places_response = self._find_places(trip_request, tools)
            
            if not places_response.success:
                return self._create_error_response("Failed to find places", places_response.error)
            
            pois = [POI(**poi_data) for poi_data in places_response.data["places"]]
            
            # Step 3: Get weather information
            logger.info(f"Step 3: Getting weather forecast for {trip_request.destination}")
            weather_response = self._get_weather_info(trip_request, tools)
            
            weather_data = []
            if weather_response.success:
                weather_data = [WeatherInfo(**w) for w in weather_response.data["weather_forecast"]]
            
            # Step 4: Filter and rank places based on weather
            if weather_data:
                logger.info("Step 4: Filtering places based on weather")
                weather_filtered_pois = self._filter_places_by_weather(pois, weather_data, trip_request)
            else:
                weather_filtered_pois = pois
            
            # Step 5: Create itinerary
            logger.info("Step 5: Creating itinerary")
            itinerary_response = self._create_itinerary(
                trip_request, 
                weather_filtered_pois, 
                weather_data, 
                tools
            )
            
            if not itinerary_response.success:
                return self._create_error_response("Failed to create itinerary", itinerary_response.error)
            
            itinerary = Itinerary(**itinerary_response.data["itinerary"])
            session_data.current_itinerary = itinerary
            
            # Step 6: Save session data
            if tools and "firestore" in tools:
                tools["firestore"].save_session(session_data)
                tools["firestore"].save_itinerary(itinerary)
            
            # Step 7: Generate final recommendations and summary
            final_response = self._generate_final_response(
                itinerary, 
                weather_response.data if weather_response.success else None,
                session_data
            )
            
            return final_response
            
        except Exception as e:
            logger.error(f"Error in trip planning workflow: {e}")
            return self._create_error_response("Trip planning workflow failed", str(e))
    
    def refine_itinerary(
        self,
        session_id: str,
        user_feedback: str,
        tools: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """
        Refine an existing itinerary based on user feedback.
        
        Args:
            session_id: Session identifier
            user_feedback: User's feedback and requested changes
            tools: Dictionary of tool instances
            
        Returns:
            AgentResponse with refined itinerary
        """
        try:
            # Retrieve session data
            if not tools or "firestore" not in tools:
                return self._create_error_response("Session management not available", "Missing Firestore tool")
            
            session_data = tools["firestore"].get_session(session_id)
            if not session_data or not session_data.current_itinerary:
                return self._create_error_response("Session not found", "Invalid session ID")
            
            # Analyze feedback to understand requested changes
            feedback_analysis = self._analyze_feedback(user_feedback, session_data)
            
            if feedback_analysis["type"] == "places":
                # User wants different places
                return self._modify_places(session_data, feedback_analysis, tools)
            elif feedback_analysis["type"] == "schedule":
                # User wants schedule changes
                return self._modify_schedule(session_data, feedback_analysis, tools)
            elif feedback_analysis["type"] == "budget":
                # User wants budget adjustments
                return self._adjust_budget(session_data, feedback_analysis, tools)
            else:
                # General optimization
                return self._optimize_itinerary(session_data, tools)
                
        except Exception as e:
            logger.error(f"Error refining itinerary: {e}")
            return self._create_error_response("Failed to refine itinerary", str(e))
    
    def _find_places(self, trip_request: TripRequest, tools: Optional[Dict[str, Any]]) -> AgentResponse:
        """Find places of interest for the trip."""
        if not tools or "maps" not in tools or "bigquery" not in tools:
            return AgentResponse(
                agent_name=self.name,
                success=False,
                error="Required tools not available"
            )
        
        return self.place_finder_agent.find_places(
            trip_request=trip_request,
            maps_tool=tools["maps"],
            bigquery_tool=tools["bigquery"]
        )
    
    def _get_weather_info(self, trip_request: TripRequest, tools: Optional[Dict[str, Any]]) -> AgentResponse:
        """Get weather information for the trip."""
        if not tools or "weather" not in tools:
            # Weather is optional, return empty response
            return AgentResponse(
                agent_name=self.name,
                success=False,
                error="Weather tool not available"
            )
        
        return self.weather_agent.analyze_weather_for_trip(
            trip_request=trip_request,
            weather_tool=tools["weather"]
        )
    
    def _filter_places_by_weather(
        self, 
        pois: List[POI], 
        weather_data: List[WeatherInfo], 
        trip_request: TripRequest
    ) -> List[POI]:
        """Filter and organize places based on weather conditions."""
        weather_filtered = self.weather_agent.filter_activities_by_weather(
            pois=pois,
            weather_data=weather_data,
            trip_request=trip_request
        )
        
        # Combine all suitable activities
        suitable_pois = []
        suitable_pois.extend(weather_filtered.get("all_weather_activities", []))
        suitable_pois.extend(weather_filtered.get("sunny_day_activities", []))
        suitable_pois.extend(weather_filtered.get("indoor_activities", []))
        
        # Remove duplicates while preserving order
        seen = set()
        unique_pois = []
        for poi in suitable_pois:
            if poi.id not in seen:
                unique_pois.append(poi)
                seen.add(poi.id)
        
        return unique_pois
    
    def _create_itinerary(
        self,
        trip_request: TripRequest,
        pois: List[POI],
        weather_data: List[WeatherInfo],
        tools: Optional[Dict[str, Any]]
    ) -> AgentResponse:
        """Create the trip itinerary."""
        maps_tool = tools.get("maps") if tools else None
        
        return self.itinerary_planner_agent.create_itinerary(
            trip_request=trip_request,
            pois=pois,
            weather_data=weather_data,
            maps_tool=maps_tool
        )
    
    def _generate_final_response(
        self,
        itinerary: Itinerary,
        weather_data: Optional[Dict[str, Any]],
        session_data: SessionData
    ) -> AgentResponse:
        """Generate the final response with complete trip plan."""
        try:
            # Create comprehensive response
            response_data = {
                "itinerary": itinerary.dict(),
                "session_id": session_data.session_id,
                "trip_summary": {
                    "destination": itinerary.trip_request.destination,
                    "duration": len(itinerary.days),
                    "total_cost": float(itinerary.total_cost),
                    "activities_count": sum(len(day.items) for day in itinerary.days),
                    "group_type": itinerary.trip_request.group_type.value,
                    "budget_range": itinerary.trip_request.budget_range.value
                }
            }
            
            # Add weather information if available
            if weather_data:
                response_data["weather_summary"] = weather_data.get("weather_analysis", {})
            
            # Generate AI-powered trip insights
            insights = self._generate_trip_insights(itinerary, weather_data)
            response_data["ai_insights"] = insights
            
            # Create success message
            message = f"✈️ Your {len(itinerary.days)}-day trip to {itinerary.trip_request.destination} is ready! "
            message += f"We've planned {sum(len(day.items) for day in itinerary.days)} amazing activities "
            message += f"with an estimated total cost of ${itinerary.total_cost:.2f}."
            
            return AgentResponse(
                agent_name=self.name,
                success=True,
                data=response_data,
                message=message
            )
            
        except Exception as e:
            logger.error(f"Error generating final response: {e}")
            return self._create_error_response("Failed to generate final response", str(e))
    
    def _generate_trip_insights(
        self,
        itinerary: Itinerary,
        weather_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate AI-powered insights about the trip."""
        try:
            # Create prompt for insights
            prompt = self._create_insights_prompt(itinerary, weather_data)
            
            # Call Vertex AI
            response = self._call_vertex_ai(prompt)
            
            if response:
                return self._parse_insights_response(response)
            else:
                return self._generate_fallback_insights(itinerary)
                
        except Exception as e:
            logger.error(f"Error generating trip insights: {e}")
            return self._generate_fallback_insights(itinerary)
    
    def _create_insights_prompt(
        self,
        itinerary: Itinerary,
        weather_data: Optional[Dict[str, Any]]
    ) -> str:
        """Create prompt for trip insights."""
        itinerary_summary = f"Destination: {itinerary.trip_request.destination}\n"
        itinerary_summary += f"Duration: {len(itinerary.days)} days\n"
        itinerary_summary += f"Budget: {itinerary.trip_request.budget_range.value}\n"
        itinerary_summary += f"Group: {itinerary.trip_request.group_type.value}\n"
        itinerary_summary += f"Total Cost: ${itinerary.total_cost}\n\n"
        
        for day in itinerary.days:
            itinerary_summary += f"Day {day.day}: {len(day.items)} activities, ${day.total_estimated_cost} cost\n"
        
        weather_summary = ""
        if weather_data:
            weather_summary = f"Weather: {weather_data.get('weather_analysis', {}).get('overall_assessment', 'Variable conditions')}\n"
        
        prompt = f"""
Analyze this travel itinerary and provide insights and recommendations:

{itinerary_summary}
{weather_summary}

Provide insights in JSON format:
{{
    "highlights": ["top 3 highlights of this trip"],
    "budget_analysis": "analysis of the budget and value",
    "timing_recommendations": ["recommendations about timing and pacing"],
    "local_tips": ["local tips and cultural insights"],
    "optimization_suggestions": ["suggestions to improve the itinerary"],
    "must_do": ["absolute must-do activities from the itinerary"],
    "hidden_gems": ["potential hidden gems or local experiences to consider"]
}}
"""
        return prompt
    
    def _call_vertex_ai(self, prompt: str) -> Optional[str]:
        """Call Vertex AI Gemini model."""
        try:
            from vertexai.generative_models import GenerativeModel
            
            model = GenerativeModel(self.model_name)
            response = model.generate_content(prompt)
            
            if response and response.text:
                return response.text.strip()
            
            return None
            
        except Exception as e:
            logger.error(f"Error calling Vertex AI: {e}")
            return None
    
    def _parse_insights_response(self, response: str) -> Dict[str, Any]:
        """Parse AI insights response."""
        try:
            import json
            
            start = response.find('{')
            end = response.rfind('}') + 1
            
            if start != -1 and end != 0:
                json_str = response[start:end]
                return json.loads(json_str)
            
            return {}
            
        except Exception as e:
            logger.error(f"Error parsing insights response: {e}")
            return {}
    
    def _generate_fallback_insights(self, itinerary: Itinerary) -> Dict[str, Any]:
        """Generate basic insights as fallback."""
        return {
            "highlights": [
                f"Exploring {itinerary.trip_request.destination}",
                f"{len(itinerary.days)}-day adventure",
                "Mix of cultural and recreational activities"
            ],
            "budget_analysis": f"Total estimated cost of ${itinerary.total_cost} for {itinerary.trip_request.number_of_travelers} travelers",
            "timing_recommendations": ["Allow flexibility for spontaneous discoveries", "Consider local meal times"],
            "local_tips": ["Research local customs", "Learn basic local phrases"],
            "optimization_suggestions": ["Book popular attractions in advance", "Keep backup indoor activities"],
            "must_do": ["Visit top-rated attractions", "Try local cuisine"],
            "hidden_gems": ["Explore local markets", "Connect with locals for recommendations"]
        }
    
    def _analyze_feedback(self, feedback: str, session_data: SessionData) -> Dict[str, Any]:
        """Analyze user feedback to understand requested changes."""
        feedback_lower = feedback.lower()
        
        # Simple keyword-based analysis (could be enhanced with AI)
        if any(word in feedback_lower for word in ["place", "attraction", "restaurant", "activity", "visit"]):
            return {"type": "places", "details": feedback}
        elif any(word in feedback_lower for word in ["time", "schedule", "early", "late", "morning", "evening"]):
            return {"type": "schedule", "details": feedback}
        elif any(word in feedback_lower for word in ["cost", "budget", "expensive", "cheap", "price"]):
            return {"type": "budget", "details": feedback}
        else:
            return {"type": "general", "details": feedback}
    
    def _modify_places(
        self,
        session_data: SessionData,
        feedback_analysis: Dict[str, Any],
        tools: Dict[str, Any]
    ) -> AgentResponse:
        """Modify places in the itinerary based on feedback."""
        # This would involve re-running place finding with modified criteria
        # For now, return a placeholder response
        return AgentResponse(
            agent_name=self.name,
            success=True,
            message="Place modifications not yet implemented",
            data={"modification_type": "places", "feedback": feedback_analysis["details"]}
        )
    
    def _modify_schedule(
        self,
        session_data: SessionData,
        feedback_analysis: Dict[str, Any],
        tools: Dict[str, Any]
    ) -> AgentResponse:
        """Modify schedule in the itinerary based on feedback."""
        # This would involve re-arranging times and activities
        return AgentResponse(
            agent_name=self.name,
            success=True,
            message="Schedule modifications not yet implemented",
            data={"modification_type": "schedule", "feedback": feedback_analysis["details"]}
        )
    
    def _adjust_budget(
        self,
        session_data: SessionData,
        feedback_analysis: Dict[str, Any],
        tools: Dict[str, Any]
    ) -> AgentResponse:
        """Adjust budget and activities based on feedback."""
        # This would involve filtering activities by price
        return AgentResponse(
            agent_name=self.name,
            success=True,
            message="Budget adjustments not yet implemented",
            data={"modification_type": "budget", "feedback": feedback_analysis["details"]}
        )
    
    def _optimize_itinerary(self, session_data: SessionData, tools: Dict[str, Any]) -> AgentResponse:
        """Optimize the existing itinerary."""
        if not session_data.current_itinerary:
            return self._create_error_response("No itinerary to optimize", "Session has no current itinerary")
        
        maps_tool = tools.get("maps")
        if maps_tool:
            return self.itinerary_planner_agent.optimize_itinerary(
                session_data.current_itinerary,
                maps_tool
            )
        else:
            return AgentResponse(
                agent_name=self.name,
                success=True,
                message="Optimization requires Maps API access",
                data={"current_itinerary": session_data.current_itinerary.dict()}
            )
    
    def _create_error_response(self, message: str, error: str) -> AgentResponse:
        """Create a standardized error response."""
        return AgentResponse(
            agent_name=self.name,
            success=False,
            message=message,
            error=error
        )
    
    def _get_or_create_session_data(
        self, 
        session_id: str, 
        user_id: Optional[str], 
        user_input: str, 
        tools: Optional[Dict[str, Any]]
    ) -> SessionData:
        """Get existing session data or create new one."""
        existing_session = None
        
        # Try to retrieve existing session data
        if tools and "firestore" in tools:
            try:
                existing_session = tools["firestore"].get_session(session_id)
            except Exception as e:
                logger.warning(f"Could not retrieve existing session {session_id}: {e}")
        
        if existing_session:
            # Add current user input to conversation history
            existing_session.conversation_history.append({
                "timestamp": datetime.utcnow().isoformat(),
                "user_input": user_input,
                "agent": "user"
            })
            
            # Update last activity
            existing_session.last_activity = datetime.utcnow()
            
            logger.info(f"Retrieved existing session {session_id} with {len(existing_session.conversation_history)} messages")
            return existing_session
        else:
            # Create new session data
            logger.info(f"Creating new session data for {session_id}")
            return SessionData(
                session_id=session_id,
                user_id=user_id,
                conversation_history=[{
                    "timestamp": datetime.utcnow().isoformat(),
                    "user_input": user_input,
                    "agent": "user"
                }]
            )
    
    def _build_accumulated_context(self, session_data: SessionData) -> Dict[str, Any]:
        """Build accumulated context from conversation history and partial data."""
        context = session_data.agent_context.copy()
        
        # Add conversation history context
        if session_data.conversation_history:
            user_messages = [
                msg["user_input"] for msg in session_data.conversation_history 
                if msg.get("agent") == "user"
            ]
            context["conversation_history"] = user_messages
            context["accumulated_user_input"] = " ".join(user_messages)
        
        # Include partial trip data if available
        if "partial_trip_data" in context:
            logger.info(f"Found partial trip data in context: {context['partial_trip_data']}")
        
        return context
    
    def _merge_trip_data(self, session_data: SessionData, new_trip_data: Dict[str, Any]) -> Dict[str, Any]:
        """Merge new trip data with existing partial data."""
        # Get existing partial data from context
        existing_data = session_data.agent_context.get("partial_trip_data", {})
        
        # Start with existing data
        merged_data = existing_data.copy()
        
        # Update with new data (new data takes precedence)
        for key, value in new_trip_data.items():
            if value is not None and value != "":  # Only update if new value is meaningful
                merged_data[key] = value
        
        logger.info(f"Merged trip data: existing fields {list(existing_data.keys())}, new fields {list(new_trip_data.keys())}, merged fields {list(merged_data.keys())}")
        
        return merged_data
    
    def get_workflow_status(self, session_id: str, tools: Optional[Dict[str, Any]]) -> AgentResponse:
        """
        Get the current status of a trip planning workflow.
        
        Args:
            session_id: Session identifier
            tools: Dictionary of tool instances
            
        Returns:
            AgentResponse with workflow status
        """
        try:
            if not tools or "firestore" not in tools:
                return self._create_error_response("Session management not available", "Missing Firestore tool")
            
            session_data = tools["firestore"].get_session(session_id)
            print('session_data',session_data)
            if not session_data:
                return self._create_error_response("Session not found", "Invalid session ID")
            
            status_data = {
                "session_id": session_id,
                "user_id": session_data.user_id,
                "created_at": session_data.created_at.isoformat(),
                "last_activity": session_data.last_activity.isoformat(),
                "is_active": session_data.is_active,
                "has_trip_request": session_data.trip_request is not None,
                "has_itinerary": session_data.current_itinerary is not None,
                "conversation_history_length": len(session_data.conversation_history)
            }
            
            if session_data.trip_request:
                status_data["trip_details"] = {
                    "destination": session_data.trip_request.destination,
                    "start_date": session_data.trip_request.start_date.isoformat(),
                    "duration_days": session_data.trip_request.duration_days,
                    "group_type": session_data.trip_request.group_type.value
                }
            
            if session_data.current_itinerary:
                status_data["itinerary_summary"] = {
                    "total_cost": float(session_data.current_itinerary.total_cost),
                    "total_activities": sum(len(day.items) for day in session_data.current_itinerary.days),
                    "version": session_data.current_itinerary.version
                }
            
            return AgentResponse(
                agent_name=self.name,
                success=True,
                data=status_data,
                message="Workflow status retrieved successfully"
            )
            
        except Exception as e:
            logger.error(f"Error getting workflow status: {e}")
            return self._create_error_response("Failed to get workflow status", str(e))