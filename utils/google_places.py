import os
import googlemaps
from typing import Dict, List, Tuple
import time
import math
import geopy.distance
import logging
from config_utils import is_test_mode_enabled, get_test_landmarks

class GooglePlacesHandler:
    def __init__(self):
        # In test mode, we don't need a real API client
        if not is_test_mode_enabled():
            try:
                self.client = googlemaps.Client(key=os.environ['GOOGLE_MAPS_API_KEY'])
            except KeyError:
                logging.warning("GOOGLE_MAPS_API_KEY environment variable not set")
                self.client = None
        else:
            self.client = None
        
        self.last_request = 0
        self.min_delay = 0.1  # Minimum delay between requests in seconds

    def _rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        time_passed = current_time - self.last_request
        if time_passed < self.min_delay:
            time.sleep(self.min_delay - time_passed)
        self.last_request = time.time()

    def get_landmarks(self, bounds: Tuple[float, float, float, float]) -> List[Dict]:
        """
        Fetch landmarks within the given bounds using Google Places API
        bounds: (south, west, north, east)
        """
        # If in test mode, return test landmarks
        if is_test_mode_enabled():
            logging.debug("Using test landmarks from config")
            test_landmarks = get_test_landmarks()
            
            center_lat = (bounds[0] + bounds[2]) / 2
            center_lon = (bounds[1] + bounds[3]) / 2
            
            landmarks = []
            for name, landmark in test_landmarks.items():
                landmarks.append({
                    'title': landmark['title'],
                    'summary': f"Test summary for {landmark['title']}",
                    'url': landmark.get('url', ''),
                    'image_url': landmark['image_url'],
                    'distance': 0.0,
                    'relevance': 1.0,
                    'coordinates': (landmark['lat'], landmark['lon'])
                })
            
            return landmarks
            
        # Normal API mode
        self._rate_limit()

        center_lat = (bounds[0] + bounds[2]) / 2
        center_lon = (bounds[1] + bounds[3]) / 2

        try:
            # Calculate the visible area
            width = geopy.distance.distance(
                (center_lat, bounds[1]),
                (center_lat, bounds[3])
            ).km
            height = geopy.distance.distance(
                (bounds[0], center_lon),
                (bounds[2], center_lon)
            ).km

            # Search for places in the area
            location = f"{center_lat},{center_lon}"
            radius = min(50000, int(math.sqrt(width**2 + height**2) * 500))  # Max 50km radius
            
            places_result = self.client.places_nearby(
                location=location,
                radius=radius,
                type=['tourist_attraction', 'landmark', 'museum', 'park']
            )

            landmarks = []
            
            for place in places_result.get('results', []):
                place_lat = place['geometry']['location']['lat']
                place_lng = place['geometry']['location']['lng']
                
                # Only include places within bounds
                if (bounds[0] <= place_lat <= bounds[2] and
                    bounds[1] <= place_lng <= bounds[3]):
                    
                    # Get place details for additional information
                    place_details = self.client.place(place['place_id'], fields=[
                        'name', 'formatted_address', 'photo', 'rating', 'url'
                    ])['result']
                    
                    # Calculate distance from center
                    distance = geopy.distance.distance(
                        (center_lat, center_lon),
                        (place_lat, place_lng)
                    ).km
                    
                    # Calculate relevance score
                    max_distance = math.sqrt(width**2 + height**2) / 2
                    base_relevance = 1.0 - (distance / max_distance if max_distance > 0 else 0)
                    rating_factor = place.get('rating', 3.0) / 5.0  # Normalize rating to 0-1
                    relevance = (base_relevance * 0.6) + (rating_factor * 0.4)  # Weighted average
                    relevance = max(0.1, min(1.0, relevance))

                    # Get photo if available
                    image_url = None
                    if 'photos' in place_details:
                        photo_reference = place_details['photos'][0]['photo_reference']
                        image_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photo_reference={photo_reference}&key={os.environ['GOOGLE_MAPS_API_KEY']}"

                    landmarks.append({
                        'title': place['name'],
                        'summary': place.get('vicinity', ''),
                        'url': place_details.get('url', ''),
                        'image_url': image_url,
                        'distance': round(distance, 2),
                        'relevance': round(relevance, 2),
                        'coordinates': (place_lat, place_lng)
                    })

            return landmarks

        except Exception as e:
            raise Exception(f"Failed to fetch landmarks: {str(e)}")
