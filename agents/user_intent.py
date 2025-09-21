"""
User Intent and Profile Agent for the Trip Planner ADK application.

This agent analyzes user input to understand intent and extract
trip requirements and preferences.
"""

import logging
from typing import Dict, Any, Optional, List
from adk import LlmAgent
from google.cloud import aiplatform

from schemas import TripRequest, GroupType, BudgetRange, AgentResponse

logger = logging.getLogger(__name__)


class UserIntentAgent(LlmAgent):
    """Agent for understanding user intent and extracting trip requirements."""
    
    def __init__(self, vertex_config: Dict[str, Any]):
        """Initialize the User Intent Agent."""
        super().__init__(
            name="user_intent_agent",
            description="Analyzes user input to understand trip requirements and preferences"
        )
        self.vertex_config = vertex_config
        self.model_name = vertex_config.get("model", "gemini-1.5-pro")
        
        # Initialize Vertex AI
        aiplatform.init(
            project=vertex_config["project_id"],
            location=vertex_config["location"]
        )
        
        logger.info("User Intent Agent initialized")
    
    def analyze_user_input(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """
        Analyze user input to extract trip requirements.
        
        Args:
            user_input: Raw user input text
            context: Additional context from conversation
            
        Returns:
            AgentResponse with extracted trip requirements
        """
        try:
            # Create the prompt for Gemini
            prompt = self._create_intent_analysis_prompt(user_input, context)
            
            # Call Vertex AI Gemini
            response = self._call_vertex_ai(prompt)
            
            if response:
                # Parse the response to extract structured data
                trip_data = self._parse_intent_response(response)
                
                return AgentResponse(
                    agent_name=self.name,
                    success=True,
                    data=trip_data,
                    message="Successfully analyzed user intent"
                )
            else:
                return AgentResponse(
                    agent_name=self.name,
                    success=False,
                    error="Failed to analyze user intent with Vertex AI"
                )
                
        except Exception as e:
            logger.error(f"Error analyzing user input: {e}")
            return AgentResponse(
                agent_name=self.name,
                success=False,
                error=str(e)
            )
    
    def create_trip_request(self, intent_data: Dict[str, Any]) -> Optional[TripRequest]:
        """
        Create a TripRequest object from analyzed intent data.
        
        Args:
            intent_data: Extracted intent data
            
        Returns:
            TripRequest object or None if incomplete data
        """
        try:
            # Validate required fields
            required_fields = ['destination', 'start_date', 'number_of_travelers']
            for field in required_fields:
                if field not in intent_data or not intent_data[field]:
                    logger.warning(f"Missing required field: {field}")
                    return None
            
            # Handle end_date calculation from duration if needed
            end_date = intent_data.get('end_date')
            if not end_date and intent_data.get('duration_days'):
                from datetime import datetime, timedelta
                start_date = datetime.fromisoformat(intent_data['start_date'])
                end_date = (start_date + timedelta(days=intent_data['duration_days'])).isoformat()[:10]
                logger.info(f"Calculated end_date {end_date} from duration {intent_data['duration_days']} days")
            
            if not end_date:
                logger.warning("Missing end_date and duration_days")
                return None
            
            # Map group type
            group_type = GroupType.SOLO
            if intent_data.get('group_type'):
                group_type = GroupType(intent_data['group_type'].lower())
            
            # Map budget range
            budget_range = BudgetRange.MODERATE
            if intent_data.get('budget_range'):
                budget_range = BudgetRange(intent_data['budget_range'].lower())
            
            trip_request = TripRequest(
                destination=intent_data['destination'],
                start_date=intent_data['start_date'],
                end_date=end_date,
                number_of_travelers=intent_data['number_of_travelers'],
                group_type=group_type,
                budget_range=budget_range,
                budget_amount=intent_data.get('budget_amount'),
                special_interests=intent_data.get('special_interests', []),
                accessibility_needs=intent_data.get('accessibility_needs', []),
                dietary_restrictions=intent_data.get('dietary_restrictions', []),
                user_id=intent_data.get('user_id'),
                session_id=intent_data.get('session_id')
            )
            
            logger.info(f"Created trip request for {trip_request.destination}")
            return trip_request
            
        except Exception as e:
            logger.error(f"Error creating trip request: {e}")
            return None
    
    def _create_intent_analysis_prompt(self, user_input: str, context: Optional[Dict[str, Any]]) -> str:
        """Create a prompt for intent analysis."""
        
        # Build context information
        context_info = "No previous context"
        if context:
            context_parts = []
            
            # Include conversation history if available
            if "conversation_history" in context:
                user_messages = context["conversation_history"]
                context_parts.append(f"Previous user messages: {' | '.join(user_messages)}")
            
            if "accumulated_user_input" in context:
                context_parts.append(f"Accumulated input: {context['accumulated_user_input']}")
            
            # Include partial trip data if available
            if "partial_trip_data" in context:
                partial = context["partial_trip_data"]
                if partial:
                    context_parts.append(f"Already collected: {partial}")
            
            if context_parts:
                context_info = " | ".join(context_parts)
        
        prompt = f"""
You are an AI travel planning assistant. Analyze the current user input along with any previous conversation context to extract comprehensive trip planning information.

Current User Input: "{user_input}"

Previous Context: {context_info}

IMPORTANT: When analyzing the input, consider BOTH the current message AND the previous context. Combine information from all sources to build a complete picture.

Extract the following information if available (combine current input with previous context):
1. Destination (city, country, or region)
2. Start date (YYYY-MM-DD format)
3. End date (YYYY-MM-DD format) - can be calculated from start_date + duration
4. Duration (number of days if mentioned separately)
5. Number of travelers (integer)
6. Group type (solo, family, friends, couple, business)
7. Budget range (budget, moderate, luxury, premium)
8. Budget amount (specific dollar amount if mentioned)
9. Special interests (list of activities, attractions, or preferences)
10. Accessibility needs (any mentioned accessibility requirements)
11. Dietary restrictions (any food allergies or dietary preferences)

Return the information in this exact JSON format:
{{
    "destination": "string or null",
    "start_date": "YYYY-MM-DD or null",
    "end_date": "YYYY-MM-DD or null",
    "duration_days": number or null,
    "number_of_travelers": number or null,
    "group_type": "solo/family/friends/couple/business or null",
    "budget_range": "budget/moderate/luxury/premium or null",
    "budget_amount": number or null,
    "special_interests": ["list", "of", "interests"],
    "accessibility_needs": ["list", "of", "needs"],
    "dietary_restrictions": ["list", "of", "restrictions"],
    "confidence": number between 0 and 1,
    "missing_info": ["list", "of", "missing", "required", "fields"],
    "clarifying_questions": ["list", "of", "questions", "to", "ask", "user"]
}}

Examples of combining information:
- If previous context has "Paris" and current input says "3 days", combine them
- If previous context has "I want to go to Italy" and current input says "2 people", both should be extracted
- If previous context has partial budget info and current input clarifies, use the most recent/complete information

Be thorough in extracting information and smart about combining current input with previous context. Only mark information as missing if it's truly not available from either source.
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
    
    def _parse_intent_response(self, response: str) -> Dict[str, Any]:
        """Parse the Gemini response to extract structured data."""
        try:
            import json
            
            # Try to extract JSON from the response
            start = response.find('{')
            end = response.rfind('}') + 1
            
            if start != -1 and end != 0:
                json_str = response[start:end]
                data = json.loads(json_str)
                return data
            else:
                logger.error("No valid JSON found in response")
                return {}
                
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error parsing intent response: {e}")
            return {}
    
    def validate_trip_requirements(self, trip_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate extracted trip requirements and identify missing information.
        
        Args:
            trip_data: Extracted trip data
            
        Returns:
            Validation results with missing fields and suggestions
        """
        validation_result = {
            "is_complete": True,
            "missing_required": [],
            "missing_optional": [],
            "validation_errors": [],
            "suggestions": []
        }
        
        # Check required fields
        required_fields = {
            "destination": "Where would you like to travel?",
            "number_of_travelers": "How many people will be traveling?"
        }
        
        # Check for date information (either start_date + end_date OR start_date + duration_days)
        has_start_date = bool(trip_data.get("start_date"))
        has_end_date = bool(trip_data.get("end_date"))
        has_duration = bool(trip_data.get("duration_days"))
        
        if not has_start_date:
            validation_result["missing_required"].append("start_date")
            validation_result["suggestions"].append("When would you like to start your trip?")
            validation_result["is_complete"] = False
        
        if not has_end_date and not has_duration:
            validation_result["missing_required"].append("end_date_or_duration")
            validation_result["suggestions"].append("When would you like to end your trip, or how many days would you like to travel?")
            validation_result["is_complete"] = False
        
        for field, question in required_fields.items():
            if not trip_data.get(field):
                validation_result["missing_required"].append(field)
                validation_result["suggestions"].append(question)
                validation_result["is_complete"] = False
        
        # Check optional but helpful fields
        optional_fields = {
            "group_type": "What type of group are you traveling with?",
            "budget_range": "What's your budget range for this trip?",
            "special_interests": "Do you have any specific interests or activities you'd like to include?"
        }
        
        for field, question in optional_fields.items():
            if not trip_data.get(field):
                validation_result["missing_optional"].append(field)
        
        # Validate date logic
        if trip_data.get("start_date") and trip_data.get("end_date"):
            try:
                from datetime import datetime
                start = datetime.fromisoformat(trip_data["start_date"])
                end = datetime.fromisoformat(trip_data["end_date"])
                
                if end <= start:
                    validation_result["validation_errors"].append("End date must be after start date")
                    validation_result["is_complete"] = False
                
                # Check if dates are in the past
                now = datetime.now()
                if start < now:
                    validation_result["validation_errors"].append("Start date cannot be in the past")
                    validation_result["is_complete"] = False
                    
            except ValueError:
                validation_result["validation_errors"].append("Invalid date format")
                validation_result["is_complete"] = False
        
        # Validate number of travelers
        if trip_data.get("number_of_travelers"):
            try:
                num_travelers = int(trip_data["number_of_travelers"])
                if num_travelers <= 0:
                    validation_result["validation_errors"].append("Number of travelers must be positive")
                    validation_result["is_complete"] = False
                elif num_travelers > 20:
                    validation_result["suggestions"].append("Large groups may require special arrangements")
            except (ValueError, TypeError):
                validation_result["validation_errors"].append("Number of travelers must be a valid number")
                validation_result["is_complete"] = False
        
        return validation_result
    
    def generate_clarifying_questions(self, trip_data: Dict[str, Any]) -> List[str]:
        """
        Generate clarifying questions based on incomplete or ambiguous data.
        
        Args:
            trip_data: Extracted trip data
            
        Returns:
            List of clarifying questions
        """
        questions = []
        
        validation = self.validate_trip_requirements(trip_data)
        
        # Add questions for missing required fields
        questions.extend(validation["suggestions"])
        
        # Add specific clarifying questions based on what's available
        if trip_data.get("destination") and not trip_data.get("special_interests"):
            questions.append(f"What would you like to do in {trip_data['destination']}? (sightseeing, food, adventure, etc.)")
        
        if trip_data.get("group_type") == "family" and not trip_data.get("accessibility_needs"):
            questions.append("Are there any children or elderly travelers who might need special accommodations?")
        
        if trip_data.get("budget_amount") and not trip_data.get("budget_range"):
            budget_amount = trip_data["budget_amount"]
            if budget_amount < 500:
                trip_data["budget_range"] = "budget"
            elif budget_amount < 2000:
                trip_data["budget_range"] = "moderate"
            elif budget_amount < 5000:
                trip_data["budget_range"] = "luxury"
            else:
                trip_data["budget_range"] = "premium"
        
        return questions[:3]  # Limit to 3 most important questions