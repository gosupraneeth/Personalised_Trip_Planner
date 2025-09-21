#!/bin/bash

# Trip Planner Development Environment Setup Script
# This script activates the virtual environment and sets up the development environment

echo "🚀 Activating Trip Planner Development Environment"
echo "=" * 50

# Activate virtual environment
source venv/bin/activate

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp .env.example .env
    echo "✅ Created .env file from template"
    echo "📝 Please edit .env with your API keys and configuration"
else
    echo "✅ .env file found"
fi

# Check Python environment
echo "🐍 Python environment: $(which python)"
echo "📦 Python version: $(python --version)"

# Show installed packages summary
echo "📚 Key installed packages:"
pip list | grep -E "(google|pydantic|fastapi|stripe|pytest)" | head -10

echo ""
echo "🎯 Environment ready! You can now:"
echo "   • Run the app: python app.py"
echo "   • Run tests: pytest"
echo "   • Start development server: uvicorn app:app --reload"
echo ""
echo "📖 Configuration needed in .env:"
echo "   • GOOGLE_CLOUD_PROJECT"
echo "   • GOOGLE_MAPS_API_KEY"
echo "   • OPENWEATHER_API_KEY"
echo "   • STRIPE_API_KEY (optional)"
echo ""