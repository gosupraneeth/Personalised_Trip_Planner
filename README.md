# Personalized Trip Planner - ADK Multi-Agent System

A sophisticated AI-powered trip planning application built with Google's Agent Development Kit (ADK) and Vertex AI. This multi-agent system provides personalized travel recommendations, itinerary planning, and comprehensive trip management through natural language interactions.

## 🏗️ Architecture

This application implements a multi-agent architecture with the following components:

### Core Agents
- **Orchestrator Agent** - Main coordinator managing the entire workflow
- **User Intent Agent** - Natural language processing for trip requirements
- **Place Finder Agent** - POI discovery and AI-enhanced recommendations
- **Weather Agent** - Weather analysis and activity filtering
- **Itinerary Planner Agent** - Comprehensive trip planning with optimization

### Tools & APIs
- **Maps API Tool** - Google Places API integration
- **Weather API Tool** - OpenWeatherMap integration
- **BigQuery Tool** - Data caching and analytics
- **Firestore Tool** - Session and trip data persistence
- **Payment Tool** - Stripe payment processing

### Data Models
- Comprehensive Pydantic schemas for type safety
- Trip requests, POIs, itineraries, booking baskets
- Weather information and transport options

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Google Cloud Project with enabled APIs:
  - Vertex AI API
  - BigQuery API
  - Firestore API
  - Maps API
- API Keys:
  - Google Maps API Key
  - OpenWeatherMap API Key
  - Stripe API Key (optional)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd PersonalisedTripPlanner2
   ```

2. **Set up Python environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

4. **Set up Google Cloud authentication**
   ```bash
   # Option 1: Service Account Key
   export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account.json"
   
   # Option 2: Application Default Credentials
   gcloud auth application-default login
   ```

5. **Initialize BigQuery dataset (optional)**
   ```bash
   # The application will create tables automatically
   # But you can pre-create the dataset:
   bq mk --dataset your-project:trip_planner
   ```

### Running the Application

#### Local Development with ADK
```bash
# Install ADK CLI if not already installed
pip install google-adk

# Run the ADK application locally
adk web

# The application will be available at http://localhost:8080
```

#### Direct Python Execution
```bash
python app.py
```

#### Testing the Core Functionality
```bash
# Run the built-in test scenarios
python -m pytest tests/
```

## 🎯 Usage Examples

### Basic Trip Planning
```
User: "I want to plan a 4-day trip to Tokyo for 2 adults, budget around $3000, interested in culture and food"

System Response:
✅ Your 4-day trip to Tokyo is ready! We've planned 16 amazing activities with an estimated total cost of $2,847.50.

📍 Destination: Tokyo, Japan
📅 Duration: 4 days
💰 Total Estimated Cost: $2,847.50
🎯 Activities: 16

📋 Daily Itinerary:
Day 1 (4 activities, $712.50)
  • Senso-ji Temple (09:00 - 11:00)
  • Tokyo National Museum (11:30 - 14:00)
  • Tsukiji Outer Market Food Tour (15:00 - 17:00)
  • ... and 1 more activity

✨ Trip Highlights:
  • Authentic cultural experiences at historic temples
  • World-class food scene exploration
  • Perfect balance of traditional and modern Tokyo

🔗 Session ID: `abc123-def456` (save this to modify your trip later)
```

### Trip Refinement
```
User: "Can you make it cheaper and add more museums?"

System Response:
✅ I've updated your Tokyo itinerary with budget optimizations and additional museums!

💰 New Total Cost: $2,234.75 (saved $612.75)
🏛️ Added 3 more museums including Tokyo Metropolitan Museum
📅 Redistributed activities across 4 days for better pacing
```

### Weather-Based Adjustments
```
User: "What if it rains during my trip?"

System Response:
✅ I've analyzed the weather forecast and prepared backup indoor activities!

🌧️ Weather Analysis: Light rain expected on Days 2-3
🏢 Indoor Alternatives: Art galleries, shopping districts, covered food halls
📱 Real-time Notifications: Weather alerts and activity suggestions
```

## 🔧 Configuration

### Environment Variables

Required configuration in your `.env` file:

```bash
# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
VERTEX_AI_MODEL=gemini-1.5-pro

# API Keys
GOOGLE_MAPS_API_KEY=your-google-maps-api-key
OPENWEATHER_API_KEY=your-openweather-api-key
STRIPE_API_KEY=your-stripe-api-key

# Database Configuration
BIGQUERY_DATASET_ID=trip_planner
FIRESTORE_DATABASE=(default)

# Application Settings
LOG_LEVEL=INFO
PORT=8080
DEBUG=false
```

### Google Cloud Setup

1. **Create a Google Cloud Project**
   ```bash
   gcloud projects create your-project-id
   gcloud config set project your-project-id
   ```

2. **Enable Required APIs**
   ```bash
   gcloud services enable aiplatform.googleapis.com
   gcloud services enable bigquery.googleapis.com
   gcloud services enable firestore.googleapis.com
   gcloud services enable places.googleapis.com
   ```

3. **Create Service Account**
   ```bash
   gcloud iam service-accounts create trip-planner-service
   gcloud projects add-iam-policy-binding your-project-id \
     --member="serviceAccount:trip-planner-service@your-project-id.iam.gserviceaccount.com" \
     --role="roles/aiplatform.user"
   gcloud projects add-iam-policy-binding your-project-id \
     --member="serviceAccount:trip-planner-service@your-project-id.iam.gserviceaccount.com" \
     --role="roles/bigquery.admin"
   gcloud projects add-iam-policy-binding your-project-id \
     --member="serviceAccount:trip-planner-service@your-project-id.iam.gserviceaccount.com" \
     --role="roles/datastore.user"
   ```

## 🧪 Testing

### Unit Tests
```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/test_agents.py
pytest tests/test_tools.py
pytest tests/test_schemas.py

# Run with coverage
pytest --cov=./ --cov-report=html
```

### Integration Tests
```bash
# Test with mock APIs (no real API calls)
pytest tests/integration/ --mock-apis

# Test with real APIs (requires valid API keys)
pytest tests/integration/ --real-apis
```

### Local Development Testing
```bash
# Run the built-in test scenarios
python app.py
```

## 🚀 Deployment

### Cloud Run Deployment

1. **Build and Deploy**
   ```bash
   # Build container
   gcloud builds submit --tag gcr.io/your-project-id/trip-planner

   # Deploy to Cloud Run
   gcloud run deploy trip-planner \
     --image gcr.io/your-project-id/trip-planner \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars GOOGLE_CLOUD_PROJECT=your-project-id
   ```

2. **Set Environment Variables**
   ```bash
   gcloud run services update trip-planner \
     --set-env-vars GOOGLE_MAPS_API_KEY=your-key,OPENWEATHER_API_KEY=your-key
   ```

### Vertex AI Agent Engine Deployment

1. **Package Application**
   ```bash
   # Create deployment package
   adk package --output trip-planner.tar.gz
   ```

2. **Deploy to Vertex AI**
   ```bash
   # Upload to Vertex AI Agent Engine
   adk deploy --package trip-planner.tar.gz --project your-project-id
   ```

## 📊 Monitoring and Analytics

### Application Metrics
- **Trip Planning Success Rate**: Percentage of completed trip plans
- **User Satisfaction**: Based on refinement requests and feedback
- **API Response Times**: Performance monitoring for external APIs
- **Cost Optimization**: Budget adherence and cost savings

### BigQuery Analytics
```sql
-- Popular destinations
SELECT destination, COUNT(*) as trip_count
FROM `your-project.trip_planner.trips`
GROUP BY destination
ORDER BY trip_count DESC;

-- Average trip costs by destination
SELECT destination, AVG(total_cost) as avg_cost
FROM `your-project.trip_planner.trips`
WHERE total_cost > 0
GROUP BY destination;
```

### Logging and Debugging
- Structured logging with correlation IDs
- Error tracking and alerting
- Performance monitoring
- User interaction analytics

## 🔒 Security Considerations

### API Key Management
- Store API keys in Google Secret Manager
- Use IAM roles and service accounts
- Rotate keys regularly
- Monitor API usage and quotas

### Data Privacy
- PII data encryption at rest
- Session data cleanup
- GDPR compliance for EU users
- User consent management

### Access Control
- Authentication required for production
- Rate limiting and abuse prevention
- Input validation and sanitization
- Secure communication (HTTPS only)

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Install development dependencies: `pip install -r requirements-dev.txt`
4. Run tests: `pytest`
5. Submit a pull request

### Code Standards
- Python 3.9+ with type hints
- Black for code formatting
- Flake8 for linting
- Pydantic for data validation
- Comprehensive test coverage

### Adding New Agents
1. Create agent class in `agents/` directory
2. Inherit from `LlmAgent` base class
3. Implement required methods
4. Add comprehensive tests
5. Update documentation

## 📖 API Reference

### Core Classes

#### TripRequest
```python
class TripRequest(BaseModel):
    destination: str
    start_date: datetime
    duration_days: int
    number_of_travelers: int
    budget_range: BudgetRange
    group_type: GroupType
    interests: List[InterestCategory]
```

#### Itinerary
```python
class Itinerary(BaseModel):
    id: str
    trip_request: TripRequest
    days: List[DayPlan]
    total_cost: Decimal
    created_at: datetime
    version: int
```

### Agent Methods

#### OrchestratorAgent.plan_trip()
```python
async def plan_trip(
    user_input: str,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    tools: Optional[Dict[str, Any]] = None
) -> AgentResponse
```

## 🐛 Troubleshooting

### Common Issues

**Import Errors**
```
ImportError: No module named 'adk'
```
Solution: Install Google ADK - `pip install google-adk`

**Authentication Errors**
```
google.auth.exceptions.DefaultCredentialsError
```
Solution: Set up Google Cloud authentication - `gcloud auth application-default login`

**API Quota Exceeded**
```
Error: Maps API quota exceeded
```
Solution: Check API quotas in Google Cloud Console and increase limits

**Missing Environment Variables**
```
KeyError: 'GOOGLE_MAPS_API_KEY'
```
Solution: Copy `.env.example` to `.env` and configure your API keys

### Debug Mode
Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
python app.py
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Google Cloud Platform for Vertex AI and ADK
- OpenWeatherMap for weather data
- Google Maps Platform for location services
- Stripe for payment processing
- The open-source community for various libraries and tools

## 📞 Support

For support and questions:
- 📧 Email: [support@tripplanner.ai](mailto:support@tripplanner.ai)
- 📖 Documentation: [https://docs.tripplanner.ai](https://docs.tripplanner.ai)
- 🐛 Issues: [GitHub Issues](https://github.com/your-repo/issues)
- 💬 Community: [Discord Server](https://discord.gg/tripplanner)