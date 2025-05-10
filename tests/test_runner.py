#!/usr/bin/env python3
import os
import sys
import json
import logging
from typing import Dict, List, Tuple, Any
import time

# Add root directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(name)s:%(levelname)s: %(message)s")
logger = logging.getLogger("test_runner")

# Import config utils and enable test mode
from config_utils import enable_test_mode, load_config, get_test_landmarks, get_test_center
enable_test_mode()

# Import app components
from utils.coord_utils import parse_coordinates, validate_coords
from components.cache_manager import get_cache_manager_instance
from utils.google_places import GooglePlacesHandler

def run_test():
    """Run a sequential test of the application flow"""
    print("=== Running Landmark Locator Tests ===")
    
    # Load test fixtures
    config = load_config()
    print(f"Loaded test fixtures with {len(config.get('test_landmarks', {}))} landmarks")
    
    # Get test center
    test_center = get_test_center()
    if not test_center:
        print("❌ ERROR: No test center defined in config.json")
        return False
    
    center_coords = (test_center["lat"], test_center["lon"])
    radius_km = test_center["radius_km"]
    print(f"Using test center: {center_coords} with radius {radius_km}km")
    
    # Convert center coordinates to bounds for testing
    south = center_coords[0] - (radius_km / 111.0)  # Approx 1 degree = 111km
    north = center_coords[0] + (radius_km / 111.0)
    # Longitude degrees vary based on latitude
    lng_degree_dist = 111.0 * abs(math.cos(math.radians(center_coords[0])))
    west = center_coords[1] - (radius_km / lng_degree_dist)
    east = center_coords[1] + (radius_km / lng_degree_dist)
    
    test_bounds = (south, west, north, east)
    
    # Test coordinate utils
    print("\n1. Testing Coordinate Utilities...")
    
    # Test coordinate parsing
    coords = parse_coordinates(f"{center_coords[0]}, {center_coords[1]}")
    if coords and coords.lat == center_coords[0] and coords.lon == center_coords[1]:
        print("  ✅ PASS: Parse decimal coordinates")
    else:
        print("  ❌ FAIL: Parse decimal coordinates")
        return False
    
    # Test validation
    if validate_coords(center_coords[0], center_coords[1]):
        print("  ✅ PASS: Validate coordinates")
    else:
        print("  ❌ FAIL: Validate coordinates")
        return False
    
    # Test Google Places for landmarks
    print("\n2. Testing GooglePlacesHandler...")
    try:
        places_handler = GooglePlacesHandler()
        landmarks = places_handler.get_landmarks(test_bounds)
        
        if landmarks and len(landmarks) > 0:
            print(f"  ✅ PASS: Retrieved {len(landmarks)} landmarks")
            # Print the first landmark as a sample
            if landmarks:
                print(f"  Sample landmark: {landmarks[0]['title']}")
        else:
            print("  ❌ FAIL: No landmarks retrieved")
            return False
    except Exception as e:
        print(f"  ❌ ERROR: {str(e)}")
        return False
    
    # Test cache manager
    print("\n3. Testing CacheManager...")
    try:
        cache_manager = get_cache_manager_instance()
        
        # Cache landmarks
        print("  Caching landmarks...")
        start = time.time()
        cache_manager.cache_landmarks(landmarks, test_bounds)
        end = time.time()
        print(f"  ✅ PASS: Cached landmarks in {end-start:.2f}s")
        
        # Retrieve from cache
        print("  Retrieving cached landmarks...")
        start = time.time()
        cached = cache_manager.get_cached_landmarks(test_bounds)
        end = time.time()
        
        if cached and len(cached) > 0:
            print(f"  ✅ PASS: Retrieved {len(cached)} cached landmarks in {end-start:.2f}s")
        else:
            print("  ❌ FAIL: No cached landmarks retrieved")
            return False
            
    except Exception as e:
        print(f"  ❌ ERROR: {str(e)}")
        return False
    
    # Test complete
    print("\n=== Test Results ===")
    print("✅ All tests passed!")
    return True

if __name__ == "__main__":
    try:
        import math
        success = run_test()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        sys.exit(1)