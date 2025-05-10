import json
import os
import logging
from typing import Dict, List, Tuple, Any, Optional

def enable_test_mode():
    """Enable test mode by setting environment variable"""
    os.environ["TEST_MODE"] = "1"

def is_test_mode_enabled():
    """Check if app is running in test mode"""
    return os.environ.get("TEST_MODE") == "1"

def load_config():
    """Load configuration from config.json"""
    try:
        with open("config.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.warning(f"Failed to load config.json: {str(e)}")
        # Return empty config if file not found or invalid
        return {}

def get_test_landmarks():
    """Get test landmark data"""
    config = load_config()
    return config.get("test_landmarks", {})

def get_test_center(name="san_francisco") -> Optional[Dict]:
    """
    Get test center data with radius
    
    Returns:
        Dict with lat, lon, and radius_km or None if not found
    """
    config = load_config()
    centers = config.get("test_centers", {})
    return centers.get(name)