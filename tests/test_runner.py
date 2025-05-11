#!/usr/bin/env python3
import os
import sys
import json
import logging
import argparse
from typing import Dict, List, Tuple, Any
import time

# Disable Streamlit warnings and debug messages completely before any streamlit-related imports
logging.getLogger('streamlit').setLevel(logging.ERROR)
logging.getLogger('watchdog').setLevel(logging.INFO)
logging.getLogger('urllib3').setLevel(logging.INFO)
logging.getLogger('PIL').setLevel(logging.INFO)

# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(name)s:%(levelname)s: %(message)s")
logger = logging.getLogger("test_runner")

# Add root directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Parse command line arguments
parser = argparse.ArgumentParser(description="Landmark Locator Test Runner")
parser.add_argument('--test', choices=['all', 'coords', 'places', 'cache'], 
                    default='all', help='Specific test to run')
parser.add_argument('--verbose', '-v', action='store_true', 
                    help='Enable verbose output')
parser.add_argument('--json', action='store_true', 
                    help='Output results in JSON format')
args = parser.parse_args()

# Import config utils and enable test mode
from utils.config_utils import enable_test_mode, load_config, get_test_landmarks, get_test_center
enable_test_mode()

# Import app components
from utils.coord_utils import parse_coordinates, validate_coords
from components.cache_manager import get_cache_manager_instance
from components.google_places import GooglePlacesHandler

# Set up cache directories to use the top-level ones
os.environ['CACHE_DIR'] = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'cache')

def run_test():
    """Run tests based on command line arguments"""
    print("=== Running Landmark Locator Tests ===")
    
    # Track overall test success
    all_passed = True
    test_results = {
        "coords": {"passed": 0, "failed": 0, "status": None},
        "places": {"passed": 0, "failed": 0, "status": None},
        "cache": {"passed": 0, "failed": 0, "status": None}
    }
    
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
    import math
    south = center_coords[0] - (radius_km / 111.0)  # Approx 1 degree = 111km
    north = center_coords[0] + (radius_km / 111.0)
    # Longitude degrees vary based on latitude
    lng_degree_dist = 111.0 * abs(math.cos(math.radians(center_coords[0])))
    west = center_coords[1] - (radius_km / lng_degree_dist)
    east = center_coords[1] + (radius_km / lng_degree_dist)
    
    test_bounds = (south, west, north, east)
    
    # Run coordinate utilities tests if requested
    if args.test in ['all', 'coords']:
        print("\n1. Testing Coordinate Utilities...")
        
        # Test coordinate parsing
        coords = parse_coordinates(f"{center_coords[0]}, {center_coords[1]}")
        if coords and coords.lat == center_coords[0] and coords.lon == center_coords[1]:
            print("  ✅ PASS: Parse decimal coordinates")
            test_results["coords"]["passed"] += 1
        else:
            print("  ❌ FAIL: Parse decimal coordinates")
            test_results["coords"]["failed"] += 1
            all_passed = False
        
        # Test validation
        if validate_coords(center_coords[0], center_coords[1]):
            print("  ✅ PASS: Validate coordinates")
            test_results["coords"]["passed"] += 1
        else:
            print("  ❌ FAIL: Validate coordinates")
            test_results["coords"]["failed"] += 1
            all_passed = False
            
        test_results["coords"]["status"] = "passed" if test_results["coords"]["failed"] == 0 else "failed"
    
    # Get landmarks for other tests
    landmarks = []
    
    # Run Google Places tests if requested
    if args.test in ['all', 'places']:
        print("\n2. Testing GooglePlacesHandler...")
        try:
            places_handler = GooglePlacesHandler()
            landmarks = places_handler.get_landmarks(center_coords, radius_km)
            
            if landmarks and len(landmarks) > 0:
                print(f"  ✅ PASS: Retrieved {len(landmarks)} landmarks")
                test_results["places"]["passed"] += 1
                # Print the first landmark as a sample
                if landmarks and args.verbose:
                    print(f"  Sample landmark: {landmarks[0]['title']}")
                    if 'image_url' in landmarks[0]:
                        print(f"  Image URL: {landmarks[0]['image_url']}")
            else:
                print("  ❌ FAIL: No landmarks retrieved")
                test_results["places"]["failed"] += 1
                all_passed = False
        except Exception as e:
            print(f"  ❌ ERROR: {str(e)}")
            test_results["places"]["failed"] += 1
            all_passed = False
            
        test_results["places"]["status"] = "passed" if test_results["places"]["failed"] == 0 else "failed"
    
    # Run cache manager tests if requested
    if args.test in ['all', 'cache'] and landmarks:
        print("\n3. Testing CacheManager...")
        try:
            cache_manager = get_cache_manager_instance()
            
            # Cache landmarks
            print("  Caching landmarks...")
            start = time.time()
            cache_manager.cache_landmarks(landmarks, center_coords, radius_km)
            end = time.time()
            print(f"  ✅ PASS: Cached landmarks in {end-start:.2f}s")
            test_results["cache"]["passed"] += 1
            
            # Retrieve from cache
            print("  Retrieving cached landmarks...")
            start = time.time()
            cached = cache_manager.get_cached_landmarks(center_coords, radius_km)
            end = time.time()
            
            if cached and len(cached) > 0:
                print(f"  ✅ PASS: Retrieved {len(cached)} cached landmarks in {end-start:.2f}s")
                test_results["cache"]["passed"] += 1
            else:
                print("  ❌ FAIL: No cached landmarks retrieved")
                test_results["cache"]["failed"] += 1
                all_passed = False
                
        except Exception as e:
            print(f"  ❌ ERROR: {str(e)}")
            test_results["cache"]["failed"] += 1
            all_passed = False
            
        test_results["cache"]["status"] = "passed" if test_results["cache"]["failed"] == 0 else "failed"
    
    # Output results
    print("\n=== Test Results Summary ===")
    
    if args.test in ['all', 'coords']:
        print(f"Coordinate Tests: {test_results['coords']['passed']} passed, {test_results['coords']['failed']} failed")
        
    if args.test in ['all', 'places']:
        print(f"Google Places Tests: {test_results['places']['passed']} passed, {test_results['places']['failed']} failed")
        
    if args.test in ['all', 'cache']:
        print(f"Cache Manager Tests: {test_results['cache']['passed']} passed, {test_results['cache']['failed']} failed")
    
    # Output JSON if requested
    if args.json:
        json_output = {
            "summary": {
                "all_passed": all_passed,
                "total_passed": sum(r["passed"] for r in test_results.values()),
                "total_failed": sum(r["failed"] for r in test_results.values()),
            },
            "tests": test_results
        }
        
        with open('test_results.json', 'w') as f:
            json.dump(json_output, f, indent=2)
        print("Results saved to test_results.json")
    
    if all_passed:
        print("\n✅ All requested tests passed!")
    else:
        print("\n❌ Some tests failed. See summary above.")
        
    return all_passed

if __name__ == "__main__":
    try:
        import math
        success = run_test()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        sys.exit(1)