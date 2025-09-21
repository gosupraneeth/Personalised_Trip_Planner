"""
Streamlit UI for the Personalized AI Travel Itinerary System.
"""
import streamlit as st
import asyncio
import json
import sys
import re
import requests
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime, timedelta, date

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add current directory to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Try to import the ADK app
try:
    from app import TripPlannerApp
    from streamlit_wrapper import SimpleTripPlannerWrapper
    ADK_AVAILABLE = True
except ImportError as e:
    ADK_AVAILABLE = False

# Page configuration
st.set_page_config(
    page_title="EasyTrip AI - Travel Planner",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': 'https://github.com/gosupraneeth/Travel_Itinerary',
        'Report a bug': 'https://github.com/gosupraneeth/Travel_Itinerary/issues',
        'About': "# EasyTrip AI\nEaseMyTrip-style travel planner powered by AI agents"
    }
)

# EaseMyTrip-inspired CSS styling
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Reset and base styles */
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    
    .main {
        background: #f8f9fa;
        font-family: 'Inter', sans-serif;
        padding: 0;
    }
    
    /* Add spacing to main container - left, right, and bottom only */
    .stMainBlockContainer {
        padding: 0rem 1rem 1rem 1rem !important;
        margin: 0rem !important;
    }
    
    /* Header Navigation */
    .header-nav {
        background: #fff;
        padding: 1rem 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        position: sticky;
        top: 0;
        z-index: 1000;
        margin-bottom: 0.5rem;
    }
    
    .nav-container {
        max-width: 1200px;
        margin: 0 auto;
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0 2rem;
        position: relative;
    }
    
    .logo {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        order: -1; /* Ensures logo stays on the left */
    }
    
    .logo-text {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1e40af;
    }
    
    .nav-menu {
        display: flex;
        gap: 2rem;
        list-style: none;
        margin: 0 auto; /* Center the navigation items */
    }
    
    .nav-item {
        color: #4b5563;
        font-weight: 500;
        text-decoration: none;
        padding: 0.5rem 1rem;
        border-radius: 6px;
        transition: all 0.3s ease;
    }
    
    .nav-item:hover {
        background: #eff6ff;
        color: #1e40af;
    }
    
    /* Hamburger Menu Styles */
    .hamburger {
        display: none;
        flex-direction: column;
        cursor: pointer;
        padding: 0.5rem;
        z-index: 1001;
    }
    
    .hamburger span {
        width: 25px;
        height: 3px;
        background: #1e40af;
        margin: 3px 0;
        transition: 0.3s;
        border-radius: 2px;
    }
    
    .hamburger.active span:nth-child(1) {
        transform: rotate(-45deg) translate(-5px, 6px);
    }
    
    .hamburger.active span:nth-child(2) {
        opacity: 0;
    }
    
    .hamburger.active span:nth-child(3) {
        transform: rotate(45deg) translate(-5px, -6px);
    }
    
    /* Mobile Navigation */
    .nav-menu.mobile {
        position: fixed;
        top: 70px;
        left: -100%;
        width: 100%;
        height: calc(100vh - 70px);
        background: white;
        flex-direction: column;
        justify-content: flex-start;
        align-items: center;
        padding-top: 2rem;
        transition: left 0.3s ease;
        z-index: 1000;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    
    .nav-menu.mobile.active {
        left: 0;
    }
    
    .nav-menu.mobile .nav-item {
        padding: 1rem 2rem;
        width: 80%;
        text-align: center;
        border-bottom: 1px solid #e5e7eb;
        margin: 0.5rem 0;
    }
    
    /* Hero Section */
    .hero-section {
        background: linear-gradient(135deg, #1e40af 0%, #3b82f6 50%, #60a5fa 100%);
        color: white;
        padding: 3rem 0;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .hero-title {
        font-size: 3rem;
        font-weight: 700;
        margin-bottom: 1rem;
    }
    
    .hero-subtitle {
        font-size: 1.2rem;
        opacity: 0.9;
        margin-bottom: 2rem;
    }
    
    /* Search Widget Tabs */
    .search-tabs {
        background: white;
        border-radius: 15px;
        padding: 2rem;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        margin: 2rem auto;
        max-width: 1000px;
    }
    
    .tab-header {
        display: flex;
        border-bottom: 2px solid #e5e7eb;
        margin-bottom: 2rem;
    }
    
    .tab-button {
        padding: 1rem 2rem;
        background: none;
        border: none;
        font-weight: 600;
        color: #6b7280;
        cursor: pointer;
        border-bottom: 3px solid transparent;
        transition: all 0.3s ease;
    }
    
    .tab-button.active {
        color: #1e40af;
        border-bottom-color: #1e40af;
    }
    
    /* Form container */
    .form-container {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        margin-bottom: 2rem;
        border: 1px solid #e0e0e0;
    }
    
    /* Section headers */
    .section-header {
        color: #1f2937;
        font-size: 1.4rem;
        font-weight: 600;
        margin-bottom: 1.5rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e2e8f0;
        text-align: center;
    }
    
    .form-label {
        font-weight: 600;
        color: #374151;
        margin-bottom: 0.5rem;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Input styling */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select,
    .stDateInput > div > div > input,
    .stNumberInput > div > div > input,
    .stTextArea > div > div > textarea {
        border: 2px solid #e5e7eb;
        border-radius: 8px;
        padding: 0.75rem;
        font-size: 1rem;
        transition: all 0.3s ease;
        font-family: 'Inter', sans-serif;
    }
    
    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus,
    .stDateInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(45deg, #1e40af, #3b82f6) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 1rem 2rem !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        cursor: pointer !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(30, 64, 175, 0.3) !important;
    }
    
    /* Quick Actions */
    .quick-actions {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1rem;
        margin: 2rem 0;
    }
    
    .quick-btn {
        background: linear-gradient(45deg, #06b6d4, #0891b2);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
        border: none;
        font-weight: 500;
    }
    
    .quick-btn:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 20px rgba(6, 182, 212, 0.3);
    }
    
    /* Text Input Alternative */
    .text-input-section {
        background: #f0f9ff;
        padding: 2rem;
        border-radius: 15px;
        margin: 2rem 0;
        border-left: 4px solid #0284c7;
    }
    
    /* Result container */
    .result-container {
        background: #f8fafc;
        padding: 2rem;
        border-radius: 15px;
        border: 1px solid #e2e8f0;
        margin-top: 2rem;
    }
    
    /* Success message */
    .success-banner {
        background: linear-gradient(90deg, #10b981, #059669);
        color: white;
        padding: 1rem 2rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        text-align: center;
        font-weight: 600;
    }
    
    /* Vertical Timeline Styles */
    .timeline-container {
        position: relative;
        max-width: 800px;
        margin: 2rem auto;
        padding: 2rem 0;
    }
    
    /* Main vertical line connecting all items */
    .timeline-container::before {
        content: '';
        position: absolute;
        left: 50%;
        top: 0;
        bottom: 0;
        width: 2px;
        background: linear-gradient(180deg, #cbd5e0 0%, #667eea 20%, #764ba2 50%, #667eea 80%, #cbd5e0 100%);
        border-radius: 2px;
        transform: translateX(-50%);
        z-index: 0;
    }
    
    /* Plain text styles for first and last items - attached to line */
    .plain-item {
        background: #f8fafc;
        border: 2px solid #667eea;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 2rem auto;
        max-width: 400px;
        text-align: center;
        color: #4a5568;
        font-size: 1rem;
        line-height: 1.6;
        position: relative;
        z-index: 2;
        /* Attach to the vertical line */
        border-left: 4px solid #667eea;
    }
    
    .plain-item-title {
        font-size: 1.3rem;
        font-weight: 600;
        color: #667eea;
        margin-bottom: 0.8rem;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
    }
    
    .timeline {
        position: relative;
        padding: 2rem 0;
    }
    
    .timeline::before {
        content: '';
        position: absolute;
        left: 50%;
        top: 0;
        bottom: 0;
        width: 3px;
        background: linear-gradient(180deg, #667eea 0%, #764ba2 50%, #667eea 100%);
        border-radius: 2px;
        transform: translateX(-50%);
        z-index: 1;
    }
    
    .timeline-item {
        position: relative;
        margin: 3rem 0;
        width: 100%;
    }
    
    /* Centered items (Day 1) - attached to line */
    .timeline-item.center .timeline-content {
        margin: 0 auto;
        text-align: center;
        max-width: 400px;
        /* Attach to the vertical line */
        border-left: 4px solid #667eea;
    }
    
    /* Left-aligned items */
    .timeline-item.left .timeline-content {
        margin-left: 0;
        margin-right: 52%;
        padding-right: 2rem;
        text-align: left;
    }
    
    /* Right-aligned items */
    .timeline-item.right .timeline-content {
        margin-left: 52%;
        margin-right: 0;
        padding-left: 2rem;
        text-align: left;
    }
    
    .timeline-content {
        background: white;
        border-radius: 12px;
        padding: 1.2rem;
        box-shadow: 0 6px 20px rgba(0,0,0,0.08);
        position: relative;
        border: 2px solid #f1f5f9;
        transition: all 0.3s ease;
        max-width: 350px;
    }
    
    .timeline-content:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 28px rgba(0,0,0,0.12);
        border-color: #667eea;
    }
    
    /* Remove circle markers for centered items, keep for left/right items */
    .timeline-item.left .timeline-marker,
    .timeline-item.right .timeline-marker {
        position: absolute;
        left: 50%;
        top: 50%;
        width: 18px;
        height: 18px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: 3px solid white;
        border-radius: 50%;
        transform: translate(-50%, -50%);
        z-index: 2;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2);
    }
    
    /* Hide marker for centered items */
    .timeline-item.center .timeline-marker {
        display: none;
    }
    
    .timeline-day {
        font-size: 1.3rem;
        font-weight: 700;
        color: #667eea;
        margin-bottom: 0.6rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* Center the day label for centered items */
    .timeline-item.center .timeline-day {
        justify-content: center;
    }
    
    .timeline-activities {
        color: #4a5568;
        line-height: 1.5;
        font-size: 0.9rem;
    }
    
    .timeline-activities ul {
        margin: 0.5rem 0;
        padding-left: 1.2rem;
    }
    
    .timeline-activities li {
        margin: 0.25rem 0;
        color: #2d3748;
    }
    
    /* Payment Section Styles */
    .payment-section {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 20px;
        margin: 2rem 0;
        color: white;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    
    .payment-title {
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 1rem;
        color: white;
    }
    
    .payment-subtitle {
        font-size: 1.1rem;
        margin-bottom: 2rem;
        opacity: 0.9;
    }
    
    .payment-button {
        background: white;
        color: #667eea;
        padding: 1rem 2rem;
        border-radius: 50px;
        font-weight: 600;
        font-size: 1.1rem;
        text-decoration: none;
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        transition: all 0.3s ease;
        border: none;
        cursor: pointer;
        box-shadow: 0 4px 15px rgba(255,255,255,0.3);
    }
    
    .payment-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(255,255,255,0.4);
        color: #5a67d8;
    }
    
    /* Mobile Responsive Timeline */
    @media (max-width: 768px) {
        .timeline::before {
            left: 20px;
        }
        
        .timeline-container::before {
            left: 20px;
        }
        
        .timeline-item.left .timeline-content,
        .timeline-item.right .timeline-content {
            margin-left: 60px;
            margin-right: 0;
            padding-left: 1rem;
            padding-right: 1rem;
            text-align: left;
            max-width: calc(100vw - 120px);
        }
        
        .timeline-item.center .timeline-content {
            margin-left: 60px;
            margin-right: 0;
            padding-left: 1rem;
            padding-right: 1rem;
            text-align: left;
            max-width: calc(100vw - 120px);
            border-left: 4px solid #667eea;
        }
        
        .timeline-item.left .timeline-marker,
        .timeline-item.right .timeline-marker {
            left: 20px;
        }
        
        .timeline-container {
            padding: 1rem 0;
            max-width: 100%;
        }
        
        .plain-item {
            margin: 1rem;
            max-width: calc(100vw - 2rem);
            border-left: 4px solid #667eea;
        }
    }
        }
        
        .timeline {
            padding: 0 1rem;
        }
    }
    
    /* Horizontal Flashcard styles */
    .flashcard-container {
        display: flex;
        flex-direction: column;
        gap: 1rem;
        margin: 2rem 0;
    }
    
    .day-flashcard {
        background: white;
        border-radius: 15px;
        border-left: 6px solid #667eea;
        padding: 1.5rem;
        width: 100%;
        min-height: 120px;
        color: #2d3748;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
        cursor: pointer;
        position: relative;
        overflow: hidden;
        display: flex;
        align-items: center;
        gap: 2rem;
    }
    
    .day-flashcard:hover {
        transform: translateX(5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        border-left-width: 8px;
    }
    
    .day-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 12px;
        text-align: center;
        min-width: 140px;
        flex-shrink: 0;
    }
    
    .day-number {
        font-size: 1.8rem;
        font-weight: 800;
        margin-bottom: 0.3rem;
    }
    
    .day-title {
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 0.3rem;
        color: white;
        opacity: 0.9;
    }
    
    .day-content {
        flex-grow: 1;
        color: #4a5568;
    }
    
    .day-activities {
        font-size: 0.9rem;
        line-height: 1.6;
        color: #4a5568;
        margin: 0;
        max-height: none;
        overflow: visible;
    }
    
    .attractions-section {
        margin: 1.5rem 0;
        padding: 1.5rem;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .attractions-title {
        color: #2d3748;
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 1.5rem;
        text-align: center;
    }
    
    .attraction-card {
        background: white;
        border-radius: 15px;
        overflow: hidden;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
        position: relative;
        margin-bottom: 1rem;
        height: 320px;
        display: flex;
        flex-direction: column;
    }
    
    .attraction-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 30px rgba(0,0,0,0.15);
    }
    
    .attraction-image {
        width: 100%;
        height: 180px;
        object-fit: cover;
        border-radius: 0;
        flex-shrink: 0;
    }
    
    .attraction-content {
        padding: 1rem;
        flex-grow: 1;
        display: flex;
        flex-direction: column;
    }
    
    .attraction-name {
        font-size: 1.1rem;
        font-weight: 600;
        color: #2d3748;
        margin-bottom: 0.5rem;
        line-height: 1.3;
    }
    
    .attraction-rating {
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .rating-badge {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.2rem 0.6rem;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: 600;
        min-width: 35px;
        text-align: center;
    }
    
    .attraction-type {
        color: #718096;
        font-size: 0.8rem;
        background: #edf2f7;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        display: inline-block;
        margin-bottom: 0.5rem;
        width: fit-content;
    }
    
    .attraction-description {
        color: #718096;
        font-size: 0.85rem;
        line-height: 1.4;
        margin-top: auto;
        flex-grow: 1;
    }
    
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {visibility: hidden;}
    
    /* Responsive design */
    @media (max-width: 768px) {
        .hero-title {
            font-size: 2rem;
        }
        
        .nav-container {
            padding: 0 1rem;
        }
        
        .hamburger {
            display: flex;
        }
        
        .nav-menu:not(.mobile) {
            display: none;
        }
        
        .nav-container > div:last-child {
            display: none; /* Hide "AI-Powered Travel Planning" text on mobile */
        }
        
        .search-tabs {
            margin: 1rem;
            padding: 1rem;
        }
        
        .logo-text {
            font-size: 1.5rem;
        }
    }
    
    @media (max-width: 480px) {
        .nav-container {
            padding: 0 0.5rem;
        }
        
        .logo-text {
            font-size: 1.3rem;
        }
    }
</style>
""", unsafe_allow_html=True)

def create_header():
    """Create EaseMyTrip-style header navigation with quick access links"""
    st.markdown("""
    <div class="header-nav">
        <div class="nav-container">
            <div class="logo">
                <span style="font-size: 2rem;">✈️</span>
                <span class="logo-text">EasyTrip AI</span>
            </div>
            <div class="nav-menu">
                <a href="https://www.easemytrip.com/hotels/" target="_blank" class="nav-item"> 🏩 Hotels</a>
                <a href="https://www.easemytrip.com/flights/" target="_blank" class="nav-item">✈️ Flights</a>
                <a href="https://www.easemytrip.com/holidays/" target="_blank" class="nav-item">🏖️ Holidays</a>
                <a href="https://www.easemytrip.com/bus/" target="_blank" class="nav-item">🚌 Bus</a>
                <a href="https://www.easemytrip.com/cabs/" target="_blank" class="nav-item">🚗 Cabs</a>
            </div>
            <div style="color: #6b7280; font-weight: 500;">AI-Powered Travel Planning</div>
        </div>
    </div>
    """, unsafe_allow_html=True)



def create_hero_section():
    """Create hero section with main title"""
    st.markdown("""
    <div class="hero-section">
        <h1 class="hero-subtitle">AI-Powered Multi-Agent Travel Planning </h1>
    </div>
    """, unsafe_allow_html=True)

def parse_voice_text_to_form_data(text: str) -> Dict:
    """Parse voice/text input and extract structured travel information"""
    if not text:
        return {}
    
    text_lower = text.lower()
    parsed_data = {}
    
    # Extract destination using enhanced patterns
    destination_patterns = [
        r'(?:go to|visit|travel to|trip to|vacation to|holiday to|planning.*?to)\s+([^,.\n!?]+?)(?:[,.\n!?]|for|in|during|with|and|starting|from|$)',
        r'(?:destination is|going to|flying to|heading to|want to go to)\s+([^,.\n!?]+?)(?:[,.\n!?]|for|in|during|with|and|$)',
        r'(?:want to see|explore|discover|planning.*?in)\s+([^,.\n!?]+?)(?:[,.\n!?]|for|in|during|with|and|$)',
        r'(?:visiting|touring)\s+([^,.\n!?]+?)(?:[,.\n!?]|for|in|during|with|and|$)',
    ]
    
    for pattern in destination_patterns:
        match = re.search(pattern, text_lower)
        if match:
            destination = match.group(1).strip()
            # Clean up common words and improve formatting
            destination = re.sub(r'\b(the|in|at|to|for|a|an)\b', '', destination).strip()
            destination = re.sub(r'\s+', ' ', destination)  # Remove extra spaces
            if len(destination) > 2:
                # Capitalize properly (each word)
                parsed_data['destination'] = ' '.join(word.capitalize() for word in destination.split())
                break
    
    # Extract duration with more patterns
    duration_patterns = [
        r'(\d+)\s*(?:days?|day)\s*(?:trip|vacation|holiday|tour)?',
        r'for\s*(\d+)\s*(?:days?|day)',
        r'(\d+)(?:-|\s*)day\s*(?:trip|vacation|holiday)',
        r'stay(?:ing)?\s*(?:for\s*)?(\d+)\s*(?:days?|day)',
        r'(\d+)\s*(?:weeks?|week)',  # Handle weeks
        r'a\s*week' # Handle "a week"
    ]
    
    for pattern in duration_patterns:
        match = re.search(pattern, text_lower)
        if match:
            if 'week' in pattern:
                if 'a week' in text_lower or 'one week' in text_lower:
                    days = 7
                else:
                    days = int(match.group(1)) * 7  # Convert weeks to days
            else:
                days = int(match.group(1))
            
            if 1 <= days <= 365:  # Reasonable range
                parsed_data['num_days'] = days
                break
                start_date = parsed_data.get('start_date')
                if start_date:
                    try:
                        start = datetime.strptime(start_date, "%Y-%m-%d")
                        end = start + timedelta(days=days)
                        parsed_data['end_date'] = end.strftime("%Y-%m-%d")
                    except:
                        pass
                break
    
    # Extract number of travelers with enhanced patterns
    traveler_patterns = [
        r'(\d+)\s*(?:people|persons?|travelers?|travellers?|guests?|adults?)',
        r'(?:group of|party of|team of|with)\s*(\d+)',
        r'(\d+)\s*(?:of us|in our group|in the group)',
        r'(?:we are|there are|there will be)\s*(\d+)',
        r'for\s*(\d+)\s*(?:people|persons?|travelers?|adults?)',
        r'me and (\d+) others?',  # "me and 2 others" = 3 people
    ]
    
    for pattern in traveler_patterns:
        match = re.search(pattern, text_lower)
        if match:
            num = int(match.group(1))
            # Handle "me and X others" case
            if 'me and' in pattern and 'others' in pattern:
                num += 1  # Add 1 for "me"
            if 1 <= num <= 50:  # Reasonable range
                parsed_data['num_travelers'] = num
                break
    
    # Extract travel type with enhanced detection
    if any(word in text_lower for word in ['solo', 'alone', 'myself', 'by myself', 'single traveler', 'just me']):
        parsed_data['travel_type'] = 'solo'
        parsed_data['num_travelers'] = 1
    elif any(word in text_lower for word in ['couple', 'partner', 'boyfriend', 'girlfriend', 'husband', 'wife', 'spouse', 'my partner', 'with my']):
        parsed_data['travel_type'] = 'couple'
        if 'num_travelers' not in parsed_data:
            parsed_data['num_travelers'] = 2
    elif any(word in text_lower for word in ['family', 'kids', 'children', 'parents', 'family trip', 'with family']):
        parsed_data['travel_type'] = 'family'
    elif any(word in text_lower for word in ['friends', 'buddies', 'mates', 'group', 'with friends']):
        parsed_data['travel_type'] = 'friends'
    elif any(word in text_lower for word in ['business', 'work', 'conference', 'meeting', 'business trip']):
        parsed_data['travel_type'] = 'business'
    
    # Extract budget with enhanced patterns and rupee amounts
    budget_keywords = {
        'low': ['cheap', 'budget', 'affordable', 'low cost', 'economical', 'inexpensive', 'tight budget'],
        'medium': ['medium', 'moderate', 'mid-range', 'reasonable', 'average', 'middle'],
        'high': ['luxury', 'premium', 'expensive', 'high-end', 'upscale', 'lavish', 'fancy', 'splurge']
    }
    
    # Check for specific rupee amounts
    rupee_patterns = [
        r'₹?(\d+(?:,\d{3})*)\s*(?:per day|daily|each day|a day)',
        r'budget\s*of\s*₹?(\d+(?:,\d{3})*)',
        r'₹?(\d+(?:,\d{3})*)\s*budget',
        r'around\s*₹?(\d+(?:,\d{3})*)',
        r'about\s*₹?(\d+(?:,\d{3})*)',
    ]
    
    for pattern in rupee_patterns:
        match = re.search(pattern, text_lower)
        if match:
            amount = int(match.group(1).replace(',', ''))
            if amount < 6200:  # Less than ₹6,200 (approx $75)
                parsed_data['budget_range'] = 'low'
            elif amount < 16600:  # Less than ₹16,600 (approx $200)
                parsed_data['budget_range'] = 'medium'
            else:
                parsed_data['budget_range'] = 'high'
            break
    else:
        # Fall back to keyword detection
        for budget_type, keywords in budget_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                parsed_data['budget_range'] = budget_type
                break
    
    # Extract preferences/interests
    interest_keywords = {
        'cultural': ['culture', 'cultural', 'heritage', 'tradition', 'traditional'],
        'food': ['food', 'cuisine', 'eating', 'restaurants', 'dining', 'culinary'],
        'temples': ['temple', 'temples', 'shrine', 'shrines', 'religious'],
        'photography': ['photography', 'photos', 'pictures', 'instagram', 'camera'],
        'museums': ['museum', 'museums', 'gallery', 'galleries', 'exhibitions'],
        'nightlife': ['nightlife', 'bars', 'clubs', 'evening', 'night'],
        'nature': ['nature', 'outdoors', 'hiking', 'mountains', 'forests', 'parks'],
        'shopping': ['shopping', 'shops', 'markets', 'boutiques', 'souvenirs'],
        'adventure': ['adventure', 'activities', 'sports', 'extreme', 'adrenaline'],
        'relaxation': ['relax', 'relaxation', 'spa', 'wellness', 'peaceful', 'calm'],
        'history': ['history', 'historical', 'historic', 'ancient', 'old'],
        'art': ['art', 'artistic', 'paintings', 'sculptures', 'artists'],
        'architecture': ['architecture', 'buildings', 'churches', 'castles'],
        'local experiences': ['local', 'authentic', 'real', 'genuine', 'native']
    }
    
    preferences = []
    for interest, keywords in interest_keywords.items():
        if any(keyword in text_lower for keyword in keywords):
            preferences.append(interest)
    
    if preferences:
        parsed_data['preferences'] = preferences
    
    # Extract dates with enhanced patterns
    from datetime import datetime, timedelta
    import calendar
    
    month_names = ['january', 'february', 'march', 'april', 'may', 'june',
                   'july', 'august', 'september', 'october', 'november', 'december']
    month_abbr = ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
                  'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
    
    # Date patterns to look for
    date_patterns = [
        # Month Day, Year or Month Day Year
        r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})(?:st|nd|rd|th)?,?\s*(\d{4})?',
        # Month Year (without day)
        r'in\s+(january|february|march|april|may|june|july|august|september|october|november|december)\s*(\d{4})?',
        # Abbreviated months
        r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+(\d{1,2}),?\s*(\d{4})?',
        # Departure/return patterns
        r'(?:depart|departing|leaving|start).*?(?:on\s+)?(?:in\s+)?(january|february|march|april|may|june|july|august|september|october|november|december)\s*(\d{1,2})?,?\s*(\d{4})?',
        r'(?:return|returning|coming back|end).*?(?:on\s+)?(?:in\s+)?(january|february|march|april|may|june|july|august|september|october|november|december)\s*(\d{1,2})?,?\s*(\d{4})?',
    ]
    
    current_year = datetime.now().year
    
    for pattern in date_patterns:
        matches = re.finditer(pattern, text_lower)
        for match in matches:
            groups = match.groups()
            month_str = groups[0].lower()
            
            # Get month number
            month_num = None
            if month_str in month_names:
                month_num = month_names.index(month_str) + 1
            elif month_str in month_abbr:
                month_num = month_abbr.index(month_str) + 1
            
            if month_num:
                # Get day (default to 15 if not specified)
                day = 15
                if len(groups) > 1 and groups[1]:
                    try:
                        day = int(groups[1])
                    except:
                        pass
                
                # Get year (default to current or next year)
                year = current_year
                if len(groups) > 2 and groups[2]:
                    try:
                        year = int(groups[2])
                    except:
                        pass
                
                # If the date would be in the past, assume next year
                try:
                    test_date = datetime(year, month_num, day)
                    if test_date < datetime.now():
                        year += 1
                    
                    start_date = datetime(year, month_num, day)
                    parsed_data['start_date'] = start_date.strftime("%Y-%m-%d")
                    
                    # Calculate end date if we have duration
                    if 'num_days' in parsed_data:
                        end_date = start_date + timedelta(days=parsed_data['num_days'])
                        parsed_data['end_date'] = end_date.strftime("%Y-%m-%d")
                    
                    break  # Stop after finding first valid date
                except ValueError:
                    continue  # Invalid date, try next pattern
    
    return parsed_data

def show_features():
    """Display key features of the system"""
    st.markdown("""
    ### 🚀 Why Choose EasyTrip AI?
    
    **🤖 Multi-Agent AI System**  
    6 specialized AI agents working in parallel and sequential phases
    
    **🌤️ Weather-Aware Planning**  
    Real-time weather analysis for optimal activity recommendations
    
    **💰 Budget Optimization**  
    Smart cost analysis to maximize value within your budget
    
    **⭐ Review Integration**  
    Curated recommendations based on reviews and popularity data
    
    **🗺️ Route Optimization**  
    Efficient multi-day route planning and transportation
    
    **⚡ Parallel Processing**  
    Faster planning with simultaneous information gathering
    
    **📝 Flexible Input**  
    Choose between detailed forms or natural language text
    """)

# Helper functions for bidirectional sync
def form_data_to_text(form_data):
    """Convert form data to natural language text"""
    if not form_data.get('destination'):
        return ""
    
    text_parts = []
    
    # Basic trip info
    if form_data.get('destination'):
        duration_text = ""
        if form_data.get('num_days', 0) > 0:
            duration_text = f" for {form_data['num_days']} days"
        text_parts.append(f"I want to visit {form_data['destination']}{duration_text}")
    
    # Travelers and type
    if form_data.get('num_travelers', 0) > 0:
        traveler_text = f"with {form_data['num_travelers']} travelers"
        if form_data.get('travel_type'):
            traveler_text += f" ({form_data['travel_type']} trip)"
        text_parts.append(traveler_text)
    
    # Dates
    if form_data.get('start_date') and form_data.get('end_date'):
        text_parts.append(f"from {form_data['start_date']} to {form_data['end_date']}")
    
    # Budget
    if form_data.get('budget_range'):
        budget_text = f"Budget: {form_data['budget_range']}"
        if isinstance(form_data['budget_range'], int):
            budget_text = f"Budget: ₹{form_data['budget_range']} per day per person"
        text_parts.append(budget_text)
    
    # Preferences
    if form_data.get('preferences'):
        text_parts.append(f"I'm interested in {', '.join(form_data['preferences'])}")
    
    # Special requirements
    if form_data.get('special_requirements'):
        reqs = form_data['special_requirements']
        if isinstance(reqs, list):
            reqs = ', '.join(reqs)
        if reqs.strip():
            text_parts.append(f"Special requirements: {reqs}")
    
    return ". ".join(text_parts) + "."

def text_to_form_data(text):
    """Extract form data from natural language text using smart parsing"""
    if not text or len(text.strip()) < 10:
        return {}
    
    import re
    from datetime import datetime, timedelta
    
    text_lower = text.lower()
    form_data = {}
    
    # Extract destination (look for "to X" or "visit X" patterns)
    destination_patterns = [
        r'(?:visit|to|in|going to)\s+([A-Z][a-zA-Z\s,]+?)(?:\s+for|\s+from|\s+with|\s+during|[.!?]|$)',
        r'trip to\s+([A-Z][a-zA-Z\s,]+?)(?:\s+for|\s+from|\s+with|\s+during|[.!?]|$)',
        r'([A-Z][a-zA-Z\s]+,\s*[A-Z][a-zA-Z\s]+)(?:\s+for|\s+from|\s+with|\s+during|[.!?]|$)'
    ]
    
    for pattern in destination_patterns:
        match = re.search(pattern, text)
        if match:
            destination = match.group(1).strip()
            # Clean up common artifacts
            destination = re.sub(r'\s+(?:for|from|with|during).*$', '', destination)
            if len(destination) > 3 and not destination.lower() in ['and', 'the', 'with']:
                form_data['destination'] = destination
                break
    
    # Extract duration
    duration_patterns = [
        r'(\d+)\s*(?:days?|day)',
        r'for\s+(\d+)\s*(?:days?|day)',
        r'(\d+)[-\s]*day'
    ]
    
    for pattern in duration_patterns:
        match = re.search(pattern, text_lower)
        if match:
            days = int(match.group(1))
            if 1 <= days <= 365:
                form_data['num_days'] = days
                break
    
    # Extract number of travelers
    traveler_patterns = [
        r'(\d+)\s+(?:people|travelers?|persons?)',
        r'with\s+(\d+)\s+(?:people|travelers?|persons?|friends?|family)',
        r'group of\s+(\d+)',
        r'(\d+)\s+of us'
    ]
    
    for pattern in traveler_patterns:
        match = re.search(pattern, text_lower)
        if match:
            travelers = int(match.group(1))
            if 1 <= travelers <= 20:
                form_data['num_travelers'] = travelers
                break
    
    # If no explicit travelers mentioned, infer from travel type
    if 'num_travelers' not in form_data:
        if any(word in text_lower for word in ['solo', 'alone', 'by myself']):
            form_data['num_travelers'] = 1
        elif any(word in text_lower for word in ['couple', 'partner', 'boyfriend', 'girlfriend', 'husband', 'wife']):
            form_data['num_travelers'] = 2
        elif any(word in text_lower for word in ['family', 'kids', 'children']):
            form_data['num_travelers'] = 4
        elif any(word in text_lower for word in ['friends', 'group']):
            form_data['num_travelers'] = 3
        else:
            form_data['num_travelers'] = 2  # Default
    
    # Extract travel type
    if any(word in text_lower for word in ['solo', 'alone', 'by myself']):
        form_data['travel_type'] = 'solo'
    elif any(word in text_lower for word in ['couple', 'romantic', 'honeymoon', 'partner', 'boyfriend', 'girlfriend', 'husband', 'wife']):
        form_data['travel_type'] = 'couple'
    elif any(word in text_lower for word in ['family', 'kids', 'children', 'parents']):
        form_data['travel_type'] = 'family'
    elif any(word in text_lower for word in ['friends', 'group', 'buddies']):
        form_data['travel_type'] = 'friends'
    elif any(word in text_lower for word in ['business', 'work', 'conference', 'meeting']):
        form_data['travel_type'] = 'business'
    else:
        form_data['travel_type'] = 'couple'  # Default
    
    # Extract budget
    budget_patterns = [
        r'\$(\d+)(?:\s*per\s*day|\s*daily|\s*each|\s*pp)',
        r'budget.*?\$(\d+)',
        r'(\d+)\s*dollars?\s*(?:per\s*day|daily)',
    ]
    
    for pattern in budget_patterns:
        match = re.search(pattern, text_lower)
        if match:
            budget = int(match.group(1))
            if 20 <= budget <= 2000:
                form_data['budget_range'] = budget
                break
    
    # If no specific budget, categorize by keywords
    if 'budget_range' not in form_data:
        if any(word in text_lower for word in ['cheap', 'budget', 'low cost', 'affordable', 'backpack']):
            form_data['budget_range'] = 'low'
        elif any(word in text_lower for word in ['luxury', 'expensive', 'high end', 'premium', 'splurge']):
            form_data['budget_range'] = 'high'
        else:
            form_data['budget_range'] = 'medium'
    
    # Extract preferences/interests
    preference_mapping = {
        'food': ['food', 'cuisine', 'restaurant', 'dining', 'eat', 'culinary'],
        'cultural': ['culture', 'cultural', 'tradition', 'heritage', 'local'],
        'temples': ['temple', 'shrine', 'religious', 'spiritual', 'church'],
        'photography': ['photo', 'picture', 'instagram', 'scenic', 'views'],
        'museums': ['museum', 'gallery', 'art', 'exhibit'],
        'nightlife': ['nightlife', 'bar', 'club', 'party', 'drinks'],
        'nature': ['nature', 'hiking', 'outdoor', 'wildlife', 'park'],
        'shopping': ['shopping', 'market', 'souvenirs', 'retail'],
        'adventure': ['adventure', 'extreme', 'thrill', 'adrenaline'],
        'relaxation': ['relax', 'spa', 'wellness', 'peaceful', 'calm'],
        'history': ['history', 'historical', 'ancient', 'historic'],
        'architecture': ['architecture', 'building', 'design'],
        'local experiences': ['local', 'authentic', 'traditional', 'immersive']
    }
    
    preferences = []
    for pref, keywords in preference_mapping.items():
        if any(keyword in text_lower for keyword in keywords):
            preferences.append(pref)
    
    if not preferences:  # Default preferences
        preferences = ['cultural', 'food']
    
    form_data['preferences'] = preferences
    
    # Extract dates (basic pattern matching)
    import re
    date_patterns = [
        r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})',
        r'(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
        r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})',
        r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+(\d{1,2})'
    ]
    
    # For now, set default dates if duration is known
    if form_data.get('num_days'):
        from datetime import date, timedelta
        start_date = date.today() + timedelta(days=30)
        end_date = start_date + timedelta(days=form_data['num_days'])
        form_data['start_date'] = start_date.strftime("%Y-%m-%d")
        form_data['end_date'] = end_date.strftime("%Y-%m-%d")
    
    return form_data

def get_travel_preferences_form():
    """Collect travel preferences using EaseMyTrip-style form"""
    st.markdown('<p class="section-header">🗺️ Plan Your Perfect Trip</p>', unsafe_allow_html=True)
    
    # Text input option
    st.markdown("### 💬 Quick Trip Description (Optional)")
    st.markdown("*Describe your trip in your own words, or use the detailed form below*")
    
    user_text_input = st.text_area(
        "",
        placeholder='e.g., "I want to visit Tokyo, Japan for 5 days in November with my partner. We love food and temples. Budget is medium."',
        help="Describe your trip preferences in natural language",
        key="quick_text_input",
        label_visibility="collapsed",
        height=100
    )
    
    if user_text_input and user_text_input.strip():
        if st.button("🚀 Generate Trip from Description", type="primary", use_container_width=True):
            with st.spinner("🤖 Understanding your request and generating itinerary..."):
                # Parse the text input and generate itinerary
                text_data = parse_text_input_to_preferences(user_text_input)
                st.session_state.travel_data = text_data
                st.session_state.input_method = "text"
                result = generate_itinerary_with_adk_text(user_text_input)
                st.session_state.itinerary_result = result
                st.rerun()
    
    st.markdown("---")
    st.markdown("### � Detailed Trip Form")
    st.markdown("*Or fill out the detailed form below for structured planning*")
    
    # Initialize session state for sync
    if 'form_data' not in st.session_state:
        st.session_state.form_data = {}
    if 'text_description' not in st.session_state:
        st.session_state.text_description = ""
    if 'last_update_source' not in st.session_state:
        st.session_state.last_update_source = None
    

    # Get default values 
    def get_default_value(key, default):
        return default
    
    # Destination and dates in one row
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('<div class="form-label">🏛️ DESTINATION</div>', unsafe_allow_html=True)
        destination = st.text_input(
            "",
            value=get_default_value('destination', ''),
            placeholder="e.g., Tokyo, Japan or Paris, France",
            help="Enter your dream destination - city and country",
            key="form_destination",
            label_visibility="collapsed"
        )
    
    with col2:
        st.markdown('<div class="form-label">📅 START DATE</div>', unsafe_allow_html=True)
        default_start = get_default_value('start_date', '')
        start_date_value = date.today() + timedelta(days=30)
        if default_start:
            try:
                start_date_value = datetime.strptime(default_start, "%Y-%m-%d").date()
            except:
                pass
        
        start_date = st.date_input(
            "",
            value=start_date_value,
            min_value=date.today(),
            help="When do you want to start your trip?",
            key="form_start_date",
            label_visibility="collapsed"
        )
    
    with col3:
        st.markdown('<div class="form-label">📅 END DATE</div>', unsafe_allow_html=True)
        default_end = get_default_value('end_date', '')
        end_date_value = date.today() + timedelta(days=35)
        if default_end:
            try:
                end_date_value = datetime.strptime(default_end, "%Y-%m-%d").date()
            except:
                pass
        elif get_default_value('num_days', 0):
            end_date_value = start_date + timedelta(days=get_default_value('num_days', 5))
        
        end_date = st.date_input(
            "",
            value=end_date_value,
            min_value=start_date,
            help="When will your trip end?",
            key="form_end_date",
            label_visibility="collapsed"
        )
    
    # Calculate trip duration
    num_days = 0
    if start_date and end_date:
        num_days = (end_date - start_date).days
        if num_days > 0:
            st.info(f"🗓️ Trip Duration: **{num_days} days**")
        else:
            st.warning("End date must be after start date")
    
    # Travel details in one row
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('<div class="form-label">👥 TRAVELERS</div>', unsafe_allow_html=True)
        num_travelers = st.number_input(
            "",
            min_value=1,
            max_value=20,
            value=get_default_value('num_travelers', 2),
            help="How many people will be traveling?",
            key="form_travelers",
            label_visibility="collapsed"
        )
    
    with col2:
        st.markdown('<div class="form-label">🎯 TRAVEL TYPE</div>', unsafe_allow_html=True)
        travel_types = ["solo", "couple", "family", "friends", "business"]
        default_type = get_default_value('travel_type', 'couple')
        default_index = travel_types.index(default_type) if default_type in travel_types else 1
        
        travel_type = st.selectbox(
            "",
            travel_types,
            index=default_index,
            help="What type of trip is this?",
            key="form_travel_type",
            label_visibility="collapsed"
        )
    
    with col3:
        st.markdown('<div class="form-label">💰 BUDGET RANGE</div>', unsafe_allow_html=True)
        budget_types = ["low", "medium", "high", "custom"]
        default_budget = get_default_value('budget_range', 'medium')
        default_budget_index = budget_types.index(default_budget) if default_budget in budget_types else 1
        
        budget_type = st.selectbox(
            "",
            budget_types,
            index=default_budget_index,
            help="Select your budget category",
            key="form_budget_type",
            label_visibility="collapsed"
        )
    
    # Custom budget input if selected
    if budget_type == "custom":
        st.markdown('<div class="form-label">💵 DAILY BUDGET PER PERSON (₹)</div>', unsafe_allow_html=True)
        custom_budget = st.number_input(
            "",
            min_value=1650,  # Approx ₹1,650 (was $20)
            max_value=166000,  # Approx ₹1,66,000 (was $2000)
            value=8300,  # Approx ₹8,300 (was $100)
            step=830,  # Approx ₹830 (was $10)
            help="Enter your daily budget per person",
            key="form_custom_budget",
            label_visibility="collapsed"
        )
        budget_range = custom_budget
    else:
        budget_range = budget_type
        budget_info = {
            "low": "₹4,150-8,300 per day",      # $50-100 converted to rupees
            "medium": "₹8,300-16,600 per day",  # $100-200 converted to rupees
            "high": "₹16,600+ per day"          # $200+ converted to rupees
        }
        st.info(f"💡 {budget_info.get(budget_type, '')}")
    
    # Preferences
    st.markdown('<div class="form-label">🎯 INTERESTS & PREFERENCES</div>', unsafe_allow_html=True)
    all_preferences = [
        "cultural", "food", "temples", "photography", "museums", 
        "nightlife", "nature", "shopping", "adventure", "relaxation",
        "history", "art", "architecture", "local experiences"
    ]
    default_preferences = get_default_value('preferences', ["cultural", "food"])
    
    preferences = st.multiselect(
        "",
        all_preferences,
        default=default_preferences,
        help="Select all that interest you",
        key="form_preferences",
        label_visibility="collapsed"
    )
    
    # Special Requirements
    st.markdown('<div class="form-label">📝 SPECIAL REQUIREMENTS (OPTIONAL)</div>', unsafe_allow_html=True)
    special_requirements = st.text_area(
        "",
        placeholder="e.g., wheelchair accessible, vegetarian food, family-friendly activities...",
        help="Any special needs or requirements for your trip",
        key="form_special_requirements",
        label_visibility="collapsed"
    )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    return {
        "destination": destination,
        "start_date": start_date.strftime("%Y-%m-%d") if start_date else "",
        "end_date": end_date.strftime("%Y-%m-%d") if end_date else "",
        "num_days": num_days,
        "num_travelers": int(num_travelers),
        "travel_type": travel_type,
        "budget_range": budget_range,
        "preferences": preferences,
        "special_requirements": [req.strip() for req in special_requirements.split(",") if req.strip()] if special_requirements else []
    }

def show_example_buttons():
    """Display example travel scenarios"""
    st.markdown('<p class="section-header">🧪 Quick Start Examples</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🗾 Tokyo Adventure\n5-day cultural trip", use_container_width=True, key="example_tokyo"):
            return {
                "destination": "Tokyo, Japan",
                "start_date": "2025-10-15",
                "end_date": "2025-10-20",
                "num_days": 5,
                "num_travelers": 2,
                "travel_type": "couple",
                "budget_range": "medium",
                "preferences": ["cultural", "food", "temples", "photography"],
                "special_requirements": []
            }
    
    with col2:
        if st.button("🗼 Paris Romance\n4-day romantic getaway", use_container_width=True, key="example_paris"):
            return {
                "destination": "Paris, France",
                "start_date": "2025-11-01",
                "end_date": "2025-11-05",
                "num_days": 4,
                "num_travelers": 2,
                "travel_type": "couple",
                "budget_range": "high",
                "preferences": ["cultural", "food", "art", "museums"],
                "special_requirements": []
            }
    
    with col3:
        if st.button("🏖️ Bali Relaxation\n7-day wellness retreat", use_container_width=True, key="example_bali"):
            return {
                "destination": "Bali, Indonesia",
                "start_date": "2025-12-01",
                "end_date": "2025-12-08",
                "num_days": 7,
                "num_travelers": 1,
                "travel_type": "solo",
                "budget_range": "medium",
                "preferences": ["relaxation", "nature", "local experiences", "photography"],
                "special_requirements": []
            }
    
    return None

# Initialize wrapper with caching
@st.cache_resource
def initialize_trip_planner():
    """Initialize the trip planner with caching"""
    if not ADK_AVAILABLE:
        return None
    try:
        from streamlit_wrapper import SimpleTripPlannerWrapper
        wrapper = SimpleTripPlannerWrapper()
        return wrapper
    except Exception as e:
        st.error(f"Failed to initialize trip planner: {e}")
        return None

def generate_itinerary_with_adk(travel_input):
    """Generate itinerary using the ADK system"""
    # Add debug information
    st.write("🔍 **Debug Information:**")
    st.write(f"- ADK_AVAILABLE: {ADK_AVAILABLE}")
    
    trip_planner = initialize_trip_planner()
    st.write(f"- Trip planner initialized: {trip_planner is not None}")
    
    if not trip_planner:
        st.warning("⚠️ ADK not available, using demo mode")
        return create_demo_itinerary(travel_input)
    
    try:
        # Convert travel input to the format expected by ADK
        user_query = f"""
        Plan a {travel_input['num_days']}-day trip to {travel_input['destination']} 
        for {travel_input['num_travelers']} {travel_input['travel_type']} travelers.
        Budget: {travel_input['budget_range']}
        Interests: {', '.join(travel_input['preferences'])}
        Dates: {travel_input['start_date']} to {travel_input['end_date']}
        Special requirements: {', '.join(travel_input.get('special_requirements', []))}
        """
        
        st.write(f"- Sending query to ADK agents...")
        st.write(f"- Query preview: {user_query[:150]}...")
        
        # Show that we're actually calling the agents
        with st.spinner("🤖 Calling ADK agents..."):
            result = trip_planner.process_message(user_query)
        
        st.write(f"- ADK result received: {result is not None}")
        if result:
            st.write(f"- Success status: {result.get('success')}")
            st.write(f"- Response length: {len(result.get('response', ''))}")
        
        if result and result.get("success"):
            st.success("✅ ADK agents responded successfully!")
            return {
                "success": True,
                "itinerary": result["response"],
                "method": "ADK AI System"
            }
        else:
            st.warning("⚠️ ADK returned unsuccessful result, using demo mode")
            return create_demo_itinerary(travel_input)
            
    except Exception as e:
        st.error(f"❌ ADK system error: {e}")
        st.exception(e)  # Show full stack trace
        return create_demo_itinerary(travel_input)

def generate_itinerary_with_adk_text(user_text):
    """Generate itinerary from natural language text using ADK"""
    # Add debug information
    st.write("🔍 **Debug Information (Text Input):**")
    st.write(f"- ADK_AVAILABLE: {ADK_AVAILABLE}")
    
    trip_planner = initialize_trip_planner()
    st.write(f"- Trip planner initialized: {trip_planner is not None}")
    
    if not trip_planner:
        st.warning("⚠️ ADK not available, using demo mode")
        return generate_demo_itinerary_from_text(user_text)
    
    try:
        st.write(f"- Sending text to ADK agents...")
        st.write(f"- User text: {user_text[:150]}...")
        
        # Use the text directly as the user query
        with st.spinner("🤖 ADK agents processing natural language..."):
            result = trip_planner.process_message(user_text)
        
        st.write(f"- ADK result received: {result is not None}")
        if result:
            st.write(f"- Success status: {result.get('success')}")
            st.write(f"- Response length: {len(result.get('response', ''))}")
        
        if result and result.get("success"):
            st.success("✅ ADK agents understood your text and responded!")
            return {
                "success": True,
                "itinerary": result["response"],
                "method": "ADK AI System (Natural Language)"
            }
        else:
            st.warning("⚠️ ADK returned unsuccessful result, using demo mode")
            return generate_demo_itinerary_from_text(user_text)
            
    except Exception as e:
        st.error(f"❌ ADK system error: {e}")
        st.exception(e)  # Show full stack trace
        return generate_demo_itinerary_from_text(user_text)

def generate_demo_itinerary_from_text(user_text):
    """Create a demo itinerary from natural language text"""
    demo_itinerary = f"""
# 🌍 Your AI-Generated Travel Itinerary

## 🎯 Based on Your Request
*"{user_text}"*

## 📍 Suggested Itinerary

### 🏁 Getting Started
Our AI agents are working to understand your travel preferences from your description. 

### 🤖 What Our AI Found:
- **Natural Language Processing**: Understanding your travel style and preferences
- **Destination Analysis**: Identifying the best locations based on your interests  
- **Activity Matching**: Finding experiences that match what you described
- **Weather Considerations**: Optimal timing for your activities

---

## 📅 Your Personalized Itinerary

### Day 1: Arrival & Orientation
**Morning**
- Arrival and settling in
- Orientation to the area
- Light exploration of immediate surroundings

**Afternoon** 
- Visit main attractions based on your interests
- Local dining experience
- Cultural immersion activities

**Evening**
- Relaxation time
- Optional evening entertainment
- Planning for tomorrow

### Day 2: Core Experiences
**Full Day**
- Main activity experiences aligned with your preferences
- Guided tours or self-exploration based on your style
- Local cuisine and cultural experiences
- Photo opportunities and memory making

### Day 3: Hidden Gems & Departure
**Morning**
- Off-the-beaten-path experiences
- Local markets or unique attractions
- Last-minute shopping or activities

**Afternoon**
- Departure preparation
- Final memorable experiences
- Travel back home

---

## 💡 AI Agent Insights

Our multi-agent system would normally:
- **Analyze** your text for destinations, preferences, and constraints
- **Research** the best options matching your travel style
- **Optimize** routes and timing for maximum enjoyment
- **Personalize** recommendations based on your unique interests

---

## 🚀 Next Steps
To get a fully personalized itinerary, our AI agents need to process your request with real-time data including:
- Weather forecasts
- Current attraction availability  
- Real-time pricing
- Local events and festivals

*This is a demo version. Connect with our full ADK system for comprehensive planning!*
"""
    
    return {
        "success": True,
        "itinerary": demo_itinerary,
        "method": "Demo Mode (Natural Language)"
    }

def create_demo_itinerary(travel_data):
    """Create a demo itinerary when backend is not available"""
    destination = travel_data.get("destination", "Your Destination")
    num_days = travel_data.get("num_days", 3)
    
    demo_itinerary = f"""
# 🌍 Your Personalized {num_days}-Day Itinerary for {destination}

## 🎯 Trip Overview
- **Destination**: {destination}
- **Duration**: {num_days} days
- **Travelers**: {travel_data.get("num_travelers", 1)} people
- **Trip Type**: {travel_data.get("travel_type", "solo").title()}
- **Budget**: {travel_data.get("budget_range", "medium").title()}
- **Interests**: {", ".join(travel_data.get("preferences", []))}

---

## 📅 Daily Itinerary

### Day 1: Arrival & City Exploration
**Morning (9:00 AM - 12:00 PM)**
- ✈️ Arrival and hotel check-in
- 🏛️ Visit main cultural district
- ☕ Welcome coffee at local café

**Afternoon (12:00 PM - 5:00 PM)**
- 🍽️ Lunch at traditional restaurant
- 🏛️ Explore historic landmarks
- 📸 Photography tour of iconic spots

**Evening (5:00 PM - 9:00 PM)**
- 🌅 Sunset viewing point
- 🍽️ Dinner at recommended restaurant
- 🚶 Evening stroll through local markets

---

### Day 2: Cultural Deep Dive
**Morning (9:00 AM - 12:00 PM)**
- 🏛️ Visit major museums
- 🎨 Art gallery exploration
- 📚 Cultural history tour

**Afternoon (12:00 PM - 5:00 PM)**
- 🍜 Local cuisine experience
- 🏯 Temple/religious site visits
- 🛍️ Artisan craft shopping

**Evening (5:00 PM - 9:00 PM)**
- 🎭 Cultural performance or show
- 🍽️ Traditional dinner experience
- 🌃 Night photography session

---

## 💰 Budget Breakdown
- **Accommodation**: ₹6,640-9,960/night   
- **Meals**: ₹3,320-4,980/day per person
- **Activities**: ₹2,490-4,150/day per person
- **Transportation**: ₹1,245-2,075/day
- **Shopping**: ₹1,660-3,320/day

## 🌤️ Weather & Packing Tips
- Check local weather forecast
- Pack comfortable walking shoes
- Bring weather-appropriate clothing
- Don't forget camera and power bank!

## 🚨 Important Notes
- This is a demo itinerary format
- Real ADK system provides detailed recommendations
- Weather-aware recommendations included in full version

---

*Generated by AI Travel Planner - ADK Multi-Agent System*
"""
    
    return {
        "success": True,
        "itinerary": demo_itinerary,
        "method": "Demo Mode",
        "is_demo": True
    }

def extract_places_from_itinerary(itinerary_text: str) -> List[str]:
    """Extract place names from the itinerary text"""
    places = []
    
    # Simple extraction patterns
    patterns = [
        r'Visit\s+([A-Z][^,.\n]*(?:Museum|Gallery|Temple|Shrine|Park|Palace|Garden|Market|Cathedral|Church|Center|Plaza|Square|Tower|Bridge|Castle))',
        r'visit\s+([A-Z][^,.\n]*(?:Museum|Gallery|Temple|Shrine|Park|Palace|Garden|Market|Cathedral|Church|Center|Plaza|Square|Tower|Bridge|Castle))',
        r'Explore\s+([A-Z][^,.\n]*(?:Museum|Gallery|Temple|Shrine|Park|Palace|Garden|Market|Cathedral|Church|Center|Plaza|Square|Tower|Bridge|Castle))',
        r'explore\s+([A-Z][^,.\n]*(?:Museum|Gallery|Temple|Shrine|Park|Palace|Garden|Market|Cathedral|Church|Center|Plaza|Square|Tower|Bridge|Castle))',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, itinerary_text)
        for match in matches:
            place = match.strip()
            if place and len(place) > 3 and place not in places:
                places.append(place)
    
    return places[:6]  # Return top 6 places

def display_place_gallery(places: List[str], destination: str):
    """Display interactive image gallery for places"""
    if not places:
        return
    
    st.markdown("### 📸 Explore Places in Your Itinerary")
    st.markdown("*Discover the amazing places you'll visit!*")
    
    # Create grid layout for images
    cols = st.columns(min(len(places), 3))
    
    for i, place in enumerate(places):
        col_idx = i % 3
        with cols[col_idx]:
            # Create placeholder for place with gradient
            st.markdown(f"""
            <div style="width: 100%; height: 200px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        display: flex; align-items: center; justify-content: center; border-radius: 10px; 
                        color: white; font-weight: bold; margin-bottom: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                📍 {place}
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"ℹ️ Learn More", key=f"place_{i}", use_container_width=True):
                st.success(f"🏛️ **{place}**\n\nThis is a fascinating destination in {destination}. In the full version, you'll see detailed information, photos, opening hours, and visitor tips!")

def parse_itinerary_into_days(itinerary_text: str) -> List[Dict[str, str]]:
    """Parse markdown itinerary text into structured day-by-day format"""
    days = []
    if not itinerary_text:
        return days
    
    lines = itinerary_text.split('\n')
    current_day = None
    current_content = []
    
    for line in lines:
        line = line.strip()
        
        # Check if line contains day indicator
        if any(keyword in line.lower() for keyword in ['day ', 'jour ', 'día ', 'tag ']):
            # Save previous day if exists
            if current_day is not None and current_content:
                days.append({
                    'day': current_day,
                    'title': f'Day {len(days) + 1}',
                    'activities': '\n'.join(current_content).strip()
                })
            
            # Start new day
            current_day = line
            current_content = []
        elif line and current_day is not None:
            # Add content to current day
            current_content.append(line)
    
    # Add the last day
    if current_day is not None and current_content:
        days.append({
            'day': current_day,
            'title': f'Day {len(days) + 1}',
            'activities': '\n'.join(current_content).strip()
        })
    
    return days

def get_nearby_attractions(destination: str) -> List[Dict[str, Any]]:
    """Get nearby attractions for a destination using simplified Google Places search"""
    try:
        # Simple mock implementation for nearby attractions
        # In a real implementation, you would use the actual Maps API
        destination_lower = destination.lower()
        
        # Mock data based on common destinations
        mock_attractions = {}
        
        if 'tokyo' in destination_lower or 'japan' in destination_lower:
            mock_attractions = [
                {
                    "name": "Senso-ji Temple", 
                    "rating": 4.5, 
                    "type": "temple", 
                    "description": "Ancient Buddhist temple in Asakusa district",
                    "image": "https://images.unsplash.com/photo-1545569341-9eb8b30979d9?w=400&h=300&fit=crop"
                },
                {
                    "name": "Tokyo Skytree", 
                    "rating": 4.6, 
                    "type": "landmark", 
                    "description": "Iconic broadcasting tower with city views",
                    "image": "https://images.unsplash.com/photo-1513407030348-c983a97b98d8?w=400&h=300&fit=crop"
                },
                {
                    "name": "Meiji Shrine", 
                    "rating": 4.4, 
                    "type": "shrine", 
                    "description": "Peaceful shrine dedicated to Emperor Meiji",
                    "image": "https://images.unsplash.com/photo-1528360983277-13d401cdc186?w=400&h=300&fit=crop"
                },
                {
                    "name": "Tsukiji Outer Market", 
                    "rating": 4.3, 
                    "type": "market", 
                    "description": "Famous fish market with fresh seafood",
                    "image": "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=400&h=300&fit=crop"
                },
                {
                    "name": "Shibuya Crossing", 
                    "rating": 4.2, 
                    "type": "landmark", 
                    "description": "World's busiest pedestrian crosswalk",
                    "image": "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=400&h=300&fit=crop"
                },
                {
                    "name": "Ueno Park", 
                    "rating": 4.3, 
                    "type": "park", 
                    "description": "Cherry blossom viewing spot with museums",
                    "image": "https://images.unsplash.com/photo-1522664267911-20df8b78de3c?w=400&h=300&fit=crop"
                }
            ]
        elif 'paris' in destination_lower or 'france' in destination_lower:
            mock_attractions = [
                {
                    "name": "Eiffel Tower", 
                    "rating": 4.6, 
                    "type": "landmark", 
                    "description": "Iconic iron lattice tower and symbol of Paris",
                    "image": "https://images.unsplash.com/photo-1511739001486-6bfe10ce785f?w=400&h=300&fit=crop"
                },
                {
                    "name": "Louvre Museum", 
                    "rating": 4.5, 
                    "type": "museum", 
                    "description": "World's largest art museum with Mona Lisa",
                    "image": "https://images.unsplash.com/photo-1566139447513-d5c6c18293e8?w=400&h=300&fit=crop"
                },
                {
                    "name": "Notre-Dame Cathedral", 
                    "rating": 4.4, 
                    "type": "cathedral", 
                    "description": "Medieval Catholic cathedral masterpiece",
                    "image": "https://images.unsplash.com/photo-1502602898536-47ad22581b52?w=400&h=300&fit=crop"
                },
                {
                    "name": "Arc de Triomphe", 
                    "rating": 4.5, 
                    "type": "monument", 
                    "description": "Triumphal arch at Champs-Élysées",
                    "image": "https://images.unsplash.com/photo-1461913407906-95b734c26ee1?w=400&h=300&fit=crop"
                },
                {
                    "name": "Sacré-Cœur Basilica", 
                    "rating": 4.4, 
                    "type": "basilica", 
                    "description": "Beautiful white basilica in Montmartre",
                    "image": "https://images.unsplash.com/photo-1549144511-f099e773c147?w=400&h=300&fit=crop"
                },
                {
                    "name": "Champs-Élysées", 
                    "rating": 4.2, 
                    "type": "avenue", 
                    "description": "Famous shopping street and avenue",
                    "image": "https://images.unsplash.com/photo-1522093007474-d86e2dcda94e?w=400&h=300&fit=crop"
                }
            ]
        elif 'bali' in destination_lower or 'indonesia' in destination_lower:
            mock_attractions = [
                {
                    "name": "Tanah Lot Temple", 
                    "rating": 4.4, 
                    "type": "temple", 
                    "description": "Sea temple on dramatic rock formation",
                    "image": "https://images.unsplash.com/photo-1537953773345-d172ccf13cf1?w=400&h=300&fit=crop"
                },
                {
                    "name": "Uluwatu Temple", 
                    "rating": 4.5, 
                    "type": "temple", 
                    "description": "Clifftop temple with stunning ocean views",
                    "image": "https://images.unsplash.com/photo-1572873480235-0cf5f8b26dc8?w=400&h=300&fit=crop"
                },
                {
                    "name": "Tegallalang Rice Terraces", 
                    "rating": 4.3, 
                    "type": "nature", 
                    "description": "Beautiful emerald rice paddies in Ubud",
                    "image": "https://images.unsplash.com/photo-1552733407-5d5c46c3bb3b?w=400&h=300&fit=crop"
                },
                {
                    "name": "Sacred Monkey Forest", 
                    "rating": 4.2, 
                    "type": "nature", 
                    "description": "Monkey sanctuary in the heart of Ubud",
                    "image": "https://images.unsplash.com/photo-1578593077593-3ba292d0e1d1?w=400&h=300&fit=crop"
                },
                {
                    "name": "Mount Batur", 
                    "rating": 4.6, 
                    "type": "volcano", 
                    "description": "Active volcano perfect for sunrise trekking",
                    "image": "https://images.unsplash.com/photo-1537953773345-d172ccf13cf1?w=400&h=300&fit=crop"
                },
                {
                    "name": "Sekumpul Falls", 
                    "rating": 4.5, 
                    "type": "waterfall", 
                    "description": "Magnificent seven-tiered waterfall",
                    "image": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400&h=300&fit=crop"
                }
            ]
        else:
            # Generic attractions for unknown destinations
            mock_attractions = [
                {
                    "name": "City Center", 
                    "rating": 4.3, 
                    "type": "landmark", 
                    "description": "Main city area with shopping and dining",
                    "image": "https://images.unsplash.com/photo-1514924013411-cbf25faa35bb?w=400&h=300&fit=crop"
                },
                {
                    "name": "Local Museum", 
                    "rating": 4.2, 
                    "type": "museum", 
                    "description": "Regional history and cultural artifacts",
                    "image": "https://images.unsplash.com/photo-1574375927938-d5a98e8ffe85?w=400&h=300&fit=crop"
                },
                {
                    "name": "Central Park", 
                    "rating": 4.4, 
                    "type": "park", 
                    "description": "Green space perfect for relaxation",
                    "image": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400&h=300&fit=crop"
                },
                {
                    "name": "Historic District", 
                    "rating": 4.3, 
                    "type": "district", 
                    "description": "Charming old town with architecture",
                    "image": "https://images.unsplash.com/photo-1513475382585-d06e58bcb0e0?w=400&h=300&fit=crop"
                },
                {
                    "name": "Shopping District", 
                    "rating": 4.1, 
                    "type": "shopping", 
                    "description": "Main shopping area with local stores",
                    "image": "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=400&h=300&fit=crop"
                },
                {
                    "name": "Waterfront Promenade", 
                    "rating": 4.4, 
                    "type": "waterfront", 
                    "description": "Scenic walkway with beautiful water views",
                    "image": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400&h=300&fit=crop"
                }
            ]
        
        # Sort by rating (highest first) and return top 6
        sorted_attractions = sorted(mock_attractions, key=lambda x: x.get('rating', 0), reverse=True)
        return sorted_attractions[:6]
        
    except Exception as e:
        logger.error(f"Error getting nearby attractions: {e}")
        return []

def display_timeline_itinerary(days_data: List[Dict[str, str]]):
    """Display itinerary as a vertical timeline with plain first/last items and alternating middle items"""
    if not days_data:
        return
    
    st.markdown('<div class="timeline-container">', unsafe_allow_html=True)
    
    total_days = len(days_data)
    timeline_item_counter = 0  # Counter for alternating left/right positioning
    
    for i, day_info in enumerate(days_data):
        activities = day_info.get('activities', 'No activities planned')
        
        # Convert activities to a more structured format
        formatted_activities = format_activities_for_timeline(activities)
        
        # Determine the day label and layout based on position
        if total_days <= 2:
            # For 1-2 days, treat normally with timeline
            day_label = f"📅 Day {i + 1}"
            is_plain_item = False
        elif i == 0:
            # First item - show as plain text (arrival/travel info)
            day_label = "🛫 Arrival & Travel"
            is_plain_item = True
        elif i == total_days - 1:
            # Last item - show as plain text (departure/travel info)
            day_label = "🛬 Departure & Travel"
            is_plain_item = True
        else:
            # Middle items - start numbering from Day 1 and use timeline
            day_number = timeline_item_counter + 1
            day_label = f"📅 Day {day_number}"
            is_plain_item = False
            timeline_item_counter += 1
        
        if is_plain_item:
            # Display as plain item (first and last)
            st.markdown(f"""
            <div class="plain-item">
                <div class="plain-item-title">
                    {day_label}
                </div>
                <div>
                    {formatted_activities}
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Display as timeline item (middle items)
            if i == 1 or (total_days < 2 and i == 0):
                # Start timeline for first actual day
                st.markdown('<div class="timeline">', unsafe_allow_html=True)
            
            # Determine positioning: Day 1 centered, then alternating left/right

            side_class = "center"  # Day 1 is centered
          
            st.markdown(f"""
            <div class="timeline-item {side_class}">
                <div class="timeline-marker"></div>
                <div class="timeline-content">
                    <div class="timeline-day">
                        {day_label}
                    </div>
                    <div class="timeline-activities">
                        {formatted_activities}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Close timeline after last timeline item
            if (i == total_days - 2 and total_days > 2) or (total_days <= 2 and i == total_days - 1):
                st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def format_activities_for_timeline(activities_text: str) -> str:
    """Format activities text for better timeline display"""
    if not activities_text or activities_text.strip() == "":
        return "<p>No activities planned for this day.</p>"
    
    # Split by common delimiters and create a structured list
    lines = activities_text.split('\n')
    formatted_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Remove markdown formatting and bullets
        line = line.replace('*', '').replace('-', '').replace('•', '').strip()
        
        if line:
            # Add time indicators if not present
            if not any(time_word in line.lower() for time_word in ['morning', 'afternoon', 'evening', 'night', ':', 'am', 'pm']):
                formatted_lines.append(f"<li>{line}</li>")
            else:
                formatted_lines.append(f"<li><strong>{line}</strong></li>")
    
    if formatted_lines:
        return f"<ul>{''.join(formatted_lines)}</ul>"
    else:
        return f"<p>{activities_text}</p>"

def display_payment_section(destination: str, travel_data: Dict):
    """Display payment and booking section with EMT navigation"""
    st.markdown('<div class="payment-section">', unsafe_allow_html=True)
    
    # Calculate estimated cost based on travel data
    num_days = travel_data.get('num_days', 5)
    num_travelers = travel_data.get('num_travelers', 2)
    budget_range = travel_data.get('budget_range', 'medium')
    
    # Simple cost estimation
    daily_cost_map = {
        'low': 6640,      # ₹6,640 (approx $80)
        'medium': 12450,  # ₹12,450 (approx $150)
        'high': 24900     # ₹24,900 (approx $300)
    }
    
    if isinstance(budget_range, (int, float)):
        daily_cost = budget_range
    else:
        daily_cost = daily_cost_map.get(budget_range, 12450)  # Default to medium range
    
    estimated_cost = daily_cost * num_days * num_travelers
    
    st.markdown(f"""
    <div class="payment-title">✈️ Ready to Book Your {destination} Trip?</div>
    <div class="payment-subtitle">
        Estimated Cost: ₹{estimated_cost:,} for {num_travelers} travelers × {num_days} days<br>
        Complete your booking with our trusted partner EaseMyTrip
    </div>
    """, unsafe_allow_html=True)
    
    # Single button for EMT payment navigation
    if st.button("💳 Navigate to EMT for Payment", use_container_width=True, type="primary"):
        st.success("🔄 Redirecting to EaseMyTrip for Payment...")
        st.balloons()
        # Use JavaScript to open EMT main page in new tab
        st.components.v1.html("""
            <script>
                window.open('https://www.easemytrip.com/', '_blank');
            </script>
            <p style="text-align: center; margin-top: 10px;">
                <strong>💳 Opening EaseMyTrip for Payment...</strong><br>
                <small>If the page doesn't open automatically, 
                <a href="https://www.easemytrip.com/" target="_blank">click here</a></small>
            </p>
        """, height=80)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Additional booking info
    st.info("💡 **Booking Benefits**: EMT Price Match Guarantee | 24/7 Support | Instant Confirmation | Zero Cancellation Fee")

def display_flashcard_itinerary(days_data: List[Dict[str, str]]):
    """Display itinerary as horizontal cards with colored headers"""
    if not days_data:
        return
    
    st.markdown('<div class="flashcard-container">', unsafe_allow_html=True)
    
    total_days = len(days_data)
    
    for i, day_info in enumerate(days_data):
        # Create different gradient colors for each day header
        gradients = [
            "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
            "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
            "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
            "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)",
            "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
            "linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)",
            "linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)"
        ]
        
        gradient = gradients[i % len(gradients)]
        
        # Determine the day label and title based on position
        if total_days <= 2:
            # For 1-2 days, treat normally
            day_number = f"Day {i + 1}"
            day_title = day_info.get('day', f'Day {i + 1}').replace('Day', '').strip()
        elif i == 0:
            # First item - show as plain text (arrival/travel info)
            day_number = "🛫 Arrival"
            day_title = "Travel & Check-in"
        elif i == total_days - 1:
            # Last item - show as plain text (departure/travel info)
            day_number = "🛬 Departure"
            day_title = "Check-out & Travel"
        else:
            # Middle items - start numbering from Day 1 (i-1 because we skip first item)
            day_number_value = i - 1 + 1  # i-1 to skip first, +1 to start from Day 1
            day_number = f"Day {day_number_value}"
            day_title = day_info.get('day', f'Day {day_number_value}').replace('Day', '').strip()
        
        st.markdown(f"""
        <div class="day-flashcard">
            <div class="day-header" style="background: {gradient};">
                <div class="day-number">{day_number}</div>
                <div class="day-title">{day_title}</div>
            </div>
            <div class="day-content">
                <div class="day-activities">{day_info.get('activities', 'No activities planned')}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def display_nearby_attractions(destination: str):
    """Display nearby attractions for the destination with images and highest ratings first"""
    attractions = get_nearby_attractions(destination)
    
    if not attractions:
        return
    
    st.markdown('<div class="attractions-section">', unsafe_allow_html=True)
    st.markdown(f'<h2 class="attractions-title">🎯 Top-Rated Attractions Near {destination}</h2>', unsafe_allow_html=True)
    
    # Create columns for better layout with reduced spacing
    cols = st.columns(3, gap="small")
    
    for i, attraction in enumerate(attractions):
        col_idx = i % 3
        with cols[col_idx]:
            rating_stars = "⭐" * int(attraction.get('rating', 4))
            rating_value = attraction.get('rating', 4.0)
            image_url = attraction.get('image', 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400&h=300&fit=crop')
            
            st.markdown(f"""
            <div class="attraction-card">
                <img src="{image_url}" alt="{attraction.get('name', 'Attraction')}" class="attraction-image" />
                <div class="attraction-content">
                    <div class="attraction-name">{attraction.get('name', 'Unknown')}</div>
                    <div class="attraction-rating">
                        <span>{rating_stars}</span>
                        <span class="rating-badge">{rating_value}</span>
                    </div>
                    <div class="attraction-type">{attraction.get('type', 'attraction').title()}</div>
                    <div class="attraction-description">
                        {attraction.get('description', 'Popular local attraction')}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def display_itinerary(result):
    """Display the generated itinerary with timeline format and payment options"""
    if result and result.get("success"):
        st.markdown('<div class="success-banner">✅ Your personalized itinerary is ready!</div>', unsafe_allow_html=True)
        
        # Show generation method
        method = result.get("method", "Unknown")
        if "Demo" in method:
            st.info("💡 **Demo Mode**: This itinerary was generated using our demo system. For full AI-powered personalization, the ADK system will provide real-time recommendations!")
        elif "ADK" in method:
            st.success("🤖 **ADK AI Generated**: This itinerary was created using our advanced multi-agent AI system!")
        
        # Get destination and travel data for context
        destination = st.session_state.get('travel_data', {}).get('destination', '')
        travel_data = st.session_state.get('travel_data', {})
        
        # Display nearby attractions first
        if destination:
            display_nearby_attractions(destination)
            st.markdown("---")
        
        # Parse itinerary into days for timeline display
        itinerary_text = result.get("itinerary", "")
        days_data = parse_itinerary_into_days(itinerary_text)
        
        if days_data:
          
            
            # Add view toggle option at the top
            view_option = st.radio(
                "Choose your preferred view:",
                ["📅 Timeline View", "🎴 Card View", "📄 Full Text"],
                horizontal=True,
                index=0,
                key="itinerary_view_mode"
            )
            
            if view_option == "📅 Timeline View":
                st.markdown("*Follow your journey day by day with our interactive timeline*")
                display_timeline_itinerary(days_data)
            elif view_option == "🎴 Card View":
                st.markdown("*Explore your itinerary with beautiful day cards*")
                display_flashcard_itinerary(days_data)
            elif view_option == "📄 Full Text":
                st.markdown("*Complete itinerary in traditional text format*")
                st.markdown('<div class="result-container">', unsafe_allow_html=True)
                st.markdown(itinerary_text)
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            # Fallback to original markdown display if parsing fails
            st.markdown("## 📋 Your Complete Itinerary")
            st.markdown('<div class="result-container">', unsafe_allow_html=True)
            st.markdown(itinerary_text)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Extract places from itinerary (existing functionality)
        places = extract_places_from_itinerary(result["itinerary"])
        
        # Display place gallery if places found (existing functionality)
        if places:
            st.markdown("---")
            display_place_gallery(places, destination)
        
        # Add payment and booking section
        st.markdown("---")
        display_payment_section(destination, travel_data)
        
        # Action buttons
        st.markdown("### 📋 Itinerary Actions")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.download_button(
                label="📥 Download Itinerary",
                data=result["itinerary"],
                file_name=f"travel_itinerary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown",
                help="Download your itinerary as a Markdown file",
                use_container_width=True
            )
        
        with col2:
            if st.button("🔄 Generate Another", use_container_width=True):
                st.session_state.itinerary_result = None
                st.session_state.travel_data = None
                st.rerun()
        
        with col3:
            if st.button("✏️ Modify Preferences", use_container_width=True):
                st.session_state.itinerary_result = None
                st.rerun()
    
    else:
        st.error(f"❌ Failed to generate itinerary: {result.get('error', 'Unknown error') if result else 'No result available'}")
        
        # Show troubleshooting tips
        with st.expander("🔧 Troubleshooting Tips"):
            st.markdown("""
            **If you're seeing this error:**
            1. Check that all required fields are filled correctly
            2. Ensure dates are in the correct format
            3. Try a different destination format (e.g., "Paris, France")
            4. Refresh the page and try again
            
            **For the full experience:**
            - The ADK multi-agent system provides real-time recommendations
            - Weather-aware activity suggestions
            - Budget optimization and route planning
            - Review-based place recommendations
            """)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Try Again", use_container_width=True):
                st.session_state.itinerary_result = None
                st.rerun()
        with col2:
            if st.button("🏠 Start Over", use_container_width=True):
                st.session_state.itinerary_result = None
                st.session_state.travel_data = None
                st.rerun()

def parse_text_input_to_preferences(user_input):
    """Parse natural language input into structured travel preferences"""
    if not user_input or user_input.strip() == "":
        return None
    
    # This is a simple parser - in a real system you'd use NLP
    # For now, we'll return the text as-is for the AI to process
    return {
        "text_input": user_input.strip(),
        "input_type": "natural_language"
    }

def main():
    """Main EasyTrip AI Streamlit application"""
    
    # Initialize session state
    if 'itinerary_result' not in st.session_state:
        st.session_state.itinerary_result = None
    if 'travel_data' not in st.session_state:
        st.session_state.travel_data = None
    if 'input_method' not in st.session_state:
        st.session_state.input_method = "form"
    
    # Header Navigation
    create_header()
    
    # Hero Section
    create_hero_section()
    
 
    # Quick examples
    example_data = show_example_buttons()
    if example_data:
        st.session_state.travel_data = example_data
        st.session_state.input_method = "form"
        with st.spinner("🤖 Generating your personalized itinerary..."):
            result = generate_itinerary_with_adk(example_data)
            st.session_state.itinerary_result = result
        st.rerun()
    
    # Form-based input
    travel_data = get_travel_preferences_form()
    
    # Generate button for form
    if st.button("🚀 Generate My Itinerary", type="primary", use_container_width=True, key="form_generate"):
        if not travel_data["destination"]:
            st.error("Please enter a destination!")
        elif travel_data["num_days"] <= 0:
            st.error("Please select valid travel dates!")
        else:
            with st.spinner("🤖 Generating your personalized itinerary..."):
                st.session_state.travel_data = travel_data
                st.session_state.input_method = "form"
                result = generate_itinerary_with_adk(travel_data)
                st.session_state.itinerary_result = result
                st.rerun()

    # Display results immediately after generation
    if st.session_state.itinerary_result:
        st.markdown("---")
        display_itinerary(st.session_state.itinerary_result)

    # Sidebar with features and system info
    with st.sidebar:
        st.markdown("## 🚀 EasyTrip AI Features")
        show_features()
        
        st.markdown("---")
        st.markdown("## 📊 System Status")
        
        # Check system status
        env_file = Path(".env")
        if env_file.exists():
            st.success("✅ Environment configured")
        else:
            st.warning("⚠️ Environment needs setup")
        
        if ADK_AVAILABLE:
            st.success("✅ ADK system ready")
        else:
            st.warning("⚠️ ADK in demo mode")
        
        st.markdown("---")
        st.markdown("## ℹ️ How it Works")
        st.markdown("""
        **Multi-Agent AI System:**
        1. **Parallel Phase**: Destination + Weather agents work simultaneously
        2. **Sequential Phase**: Review → Budget → Route optimization
        3. **Coordination**: Master agent synthesizes everything
        4. **Result**: Comprehensive, optimized itinerary
        """)
        
        # Show current trip stats
        if st.session_state.travel_data:
            st.markdown("---")
            st.markdown("## 🎯 Current Trip")
            data = st.session_state.travel_data
            
            if st.session_state.input_method == "form":
                st.metric("Destination", data.get('destination', 'Not set'))
                st.metric("Duration", f"{data.get('num_days', 0)} days")
                st.metric("Travelers", f"{data.get('num_travelers', 0)} people")
                st.metric("Budget", data.get('budget_range', 'Not set').title())
            else:
                st.info("✨ Natural language input received")
                if st.button("🔄 Start New Trip", use_container_width=True):
                    st.session_state.travel_data = None
                    st.session_state.itinerary_result = None
                    st.rerun()
    
    # System Architecture Information (collapsible)
    with st.expander("🤖 Multi-Agent System Architecture - How It Works", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🎯 Specialized Agents Working in Parallel")
            agents_info = """
            **🔄 Phase 1: PARALLEL Information Gathering**
            
            **1. Destination Discovery Agent**
            - Finds attractions, restaurants, activities
            - Discovers hidden gems and unique spots
            - Works simultaneously with Weather Agent
            
            **2. Weather Analysis Agent** 
            - Provides weather forecasts and suitability
            - Weather-appropriate activity recommendations
            - Runs parallel with Destination Discovery
            
            **➡️ Phase 2: SEQUENTIAL Analysis & Optimization**
            
            **3. Review & Popularity Agent**
            - Analyzes reviews and ratings from gathered destinations
            - Ranks places by popularity and quality
            
            **4. Budget Optimization Agent**
            - Filters selections within budget constraints
            - Cost estimation and optimization
            
            **5. Route Optimization Agent**
            - Plans efficient routes between selected places
            - Multi-day route planning and transportation
            
            **🎯 Phase 3: Final Coordination**
            
            **6. Master Coordinator Agent**
            - Synthesizes all agent outputs
            - Creates final structured itinerary
            - Ensures weather, budget, and route integration
            """
            st.markdown(agents_info)
        
        with col2:
            st.markdown("#### 🛠️ Multi-Agent Coordination")
            coordination_info = """
            **Parallel Processing Benefits:**
            - Faster information gathering
            - Simultaneous destination + weather analysis
            - Reduced total processing time
            
            **Sequential Optimization:**
            - Logical flow: Reviews → Budget → Routes
            - Each agent builds on previous results
            - Ensures coherent final recommendations
            
            **Unified Tool Integration:**
            - All agents use comprehensive travel planner
            - Specialized queries per agent role
            - Coordinated data flow between phases
            
            **Real-time Coordination:**
            - Destination Discovery finds places
            - Weather Agent checks activity suitability  
            - Review Agent ranks by quality
            - Budget Agent filters by cost
            - Route Agent optimizes travel
            - Coordinator synthesizes everything
            
            **Result: Comprehensive, multi-perspective 
            travel planning with parallel efficiency 
            and sequential optimization.**
            """
            st.markdown(coordination_info)
        
        st.info("💡 **How it works**: The multi-agent system coordinates 6 specialized agents working in parallel and sequential phases. Parallel processing gathers information quickly, while sequential optimization ensures logical flow and integration of all perspectives into a comprehensive itinerary.")
        
        # Show current system status
        st.markdown("#### 📊 System Metrics")
        status_col1, status_col2, status_col3 = st.columns(3)
        
        with status_col1:
            st.metric("🤖 Active Agents", "6", help="Specialized agents working on your itinerary")
        with status_col2:
            st.metric("🛠️ Available Tools", "5+", help="Maps, Weather, Firestore, and more")
        with status_col3:
            st.metric("🌍 Backend", "Vertex AI", help="Powered by Google Cloud Vertex AI")
    
    

if __name__ == "__main__":
    main()