# Requirements Management

This project uses multiple requirements files to manage dependencies effectively:

## Core Requirements (`requirements.txt`)
Contains all the essential dependencies needed to run the Trip Planner application:
- **Google ADK and AI Platform**: Core framework and AI capabilities
- **Google Cloud Services**: BigQuery, Firestore, Storage integrations  
- **Web Framework**: FastAPI, Uvicorn for web server functionality
- **Data Validation**: Pydantic for schema validation
- **External APIs**: Google Maps, Stripe payments, HTTP clients
- **Testing**: Core testing framework

## Development Requirements (`requirements-dev.txt`)
Optional development tools for enhanced development experience:
- **Code Quality**: Black, Flake8, MyPy for formatting and linting
- **Documentation**: MkDocs for documentation generation  
- **Enhanced Testing**: Coverage reports, additional test utilities
- **Data Analysis**: Pandas, visualization tools (optional)
- **Jupyter**: Notebook support for development and analysis

## Installation

### Basic Installation
```bash
# Install core dependencies
pip install -r requirements.txt
```

### Development Installation  
```bash
# Install core + development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Using Virtual Environment (Recommended)
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On macOS/Linux
# venv\Scripts\activate    # On Windows

# Install dependencies
pip install -r requirements.txt
```

## Python Version Compatibility

- **Minimum**: Python 3.9 (current)
- **Recommended**: Python 3.10+ (for full MCP support)
- **Optimal**: Python 3.11+ (best performance)

## Version Pinning Strategy

The requirements use **exact version pinning** to ensure:
- ✅ Reproducible builds across environments
- ✅ Consistent behavior in production
- ✅ Avoiding unexpected breaking changes
- ✅ Easier debugging of version-specific issues

## Key Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| google-adk | 1.14.1 | Core Agent Development Kit framework |
| google-cloud-aiplatform | 1.115.0 | Vertex AI integration |
| fastapi | 0.117.1 | Web framework for API endpoints |
| pydantic | 2.11.9 | Data validation and settings |
| googlemaps | 4.10.0 | Google Maps API integration |
| stripe | 12.5.1 | Payment processing |

## Updating Dependencies

To update dependencies safely:

1. **Check for updates**:
   ```bash
   pip list --outdated
   ```

2. **Test updates in isolation**:
   ```bash
   pip install package-name==new-version
   # Test your application thoroughly
   ```

3. **Update requirements.txt**:
   ```bash
   # After successful testing
   pip freeze > requirements-new.txt
   # Review changes and update requirements.txt manually
   ```

4. **Verify compatibility**:
   ```bash
   pip check
   python -m pytest  # Run your test suite
   ```

## Platform Notes

- **macOS**: May see SSL warnings with LibreSSL (harmless)
- **Windows**: Ensure Windows Subsystem for Linux for best compatibility
- **Linux**: Should work without issues

## Troubleshooting

### Common Issues

1. **grpcio not supported warning**: 
   - Expected on some platforms, doesn't affect functionality

2. **MCP requires Python 3.10+ warning**:
   - Upgrade Python for full feature support
   - Basic functionality works with Python 3.9

3. **SSL warnings**:
   - Update Python or use virtual environment with newer SSL

### Getting Help

- Check the main [README.md](./README.md) for setup instructions
- Verify environment variables in `.env.example`
- Ensure all Google Cloud APIs are enabled
- Check that API keys are properly configured