import os
import googlemaps
from typing import Dict, List, Tuple
import time
import math
import geopy.distance
import logging
from utils.config_utils import is_test_mode_enabled, get_test_landmarks

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

    def get_landmarks(self, center_coords: Tuple[float, float], radius_km: float) -> List[Dict]:
        """
        Fetch landmarks near the specified center within the given radius
        
        Args:
            center_coords: (lat, lon) tuple for the center point
            radius_km: radius in kilometers to search within
            
        Returns:
            List of landmark dictionaries
        """
        # If in test mode, return test landmarks
        if is_test_mode_enabled():
            logging.debug("Using test landmarks from config")
            test_landmarks = get_test_landmarks()
            
            center_lat, center_lon = center_coords
            
            landmarks = []
            for name, landmark in test_landmarks.items():
                # Calculate distance from center (only in non-test mode)
                if not is_test_mode_enabled():
                    distance = geopy.distance.distance(
                        center_coords,
                        (landmark['lat'], landmark['lon'])
                    ).km
                    
                    # Only include landmarks within the radius
                    if distance > radius_km:
                        continue
                        
                    relevance = max(0.1, 1.0 - (distance / radius_km if radius_km > 0 else 0))
                else:
                    distance = 0.0
                    relevance = 1.0
                
                landmarks.append({
                    'title': landmark['title'],
                    'summary': f"Test summary for {landmark['title']}",
                    'url': landmark.get('url', ''),
                    'image_url': landmark['image_url'],
                    'distance': round(distance, 2),
                    'relevance': round(relevance, 2),
                    'coordinates': (landmark['lat'], landmark['lon'])
                })
            
            return landmarks
            
        # Normal API mode
        self._rate_limit()

        center_lat, center_lon = center_coords

        try:
            # Convert radius to meters for the API (max 50km)
            radius_meters = min(50000, int(radius_km * 1000))
            
            # Location string for the API
            location = f"{center_lat},{center_lon}"
            
            # Call the Places API
            places_result = self.client.places_nearby(
                location=location,
                radius=radius_meters,
                type=['tourist_attraction', 'landmark', 'museum', 'park']
            )

            landmarks = []
            
            for place in places_result.get('results', []):
                place_lat = place['geometry']['location']['lat']
                place_lng = place['geometry']['location']['lng']
                
                # Calculate distance from center
                distance = geopy.distance.distance(
                    (center_lat, center_lon),
                    (place_lat, place_lng)
                ).km
                
                # Only include places within the specified radius
                if distance <= radius_km:
                    # Get place details for additional information
                    place_details = self.client.place(place['place_id'], fields=[
                        'name', 'formatted_address', 'photo', 'rating', 'url'
                    ])['result']
                    
                    # Calculate relevance score based on distance and rating
                    base_relevance = 1.0 - (distance / radius_km if radius_km > 0 else 0)
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