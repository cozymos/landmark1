import wikipediaapi
import geopy.distance
from typing import Dict, List, Tuple
import time

class WikiLandmarkFetcher:
    def __init__(self):
        self.wiki = wikipediaapi.Wikipedia(
            'LandmarkExplorer/1.0',
            'en'
        )
        self.last_request = 0
        self.min_delay = 1  # Minimum delay between requests in seconds

    def _rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        time_passed = current_time - self.last_request
        if time_passed < self.min_delay:
            time.sleep(self.min_delay - time_passed)
        self.last_request = time.time()

    def get_landmarks(self, bounds: Tuple[float, float, float, float]) -> List[Dict]:
        """
        Fetch landmarks within the given bounds
        bounds: (south, west, north, east)
        """
        self._rate_limit()
        
        center_lat = (bounds[0] + bounds[2]) / 2
        center_lon = (bounds[1] + bounds[3]) / 2
        
        try:
            # Use geosearch to find nearby pages
            landmarks = []
            
            # Simulate geosearch (in real implementation, would use MediaWiki API)
            # This is a simplified version for demonstration
            sample_landmarks = [
                {'title': 'Sample Landmark 1', 'lat': center_lat + 0.01, 'lon': center_lon + 0.01},
                {'title': 'Sample Landmark 2', 'lat': center_lat - 0.01, 'lon': center_lon - 0.01},
            ]
            
            for landmark in sample_landmarks:
                page = self.wiki.page(landmark['title'])
                if page.exists():
                    # Calculate distance from center
                    distance = geopy.distance.distance(
                        (center_lat, center_lon),
                        (landmark['lat'], landmark['lon'])
                    ).km
                    
                    # Calculate relevance score (simplified)
                    relevance = 1.0 - (distance / 10)  # Decrease relevance with distance
                    relevance = max(0.0, min(1.0, relevance))
                    
                    landmarks.append({
                        'title': page.title,
                        'summary': page.summary[:200] + "...",
                        'url': page.fullurl,
                        'distance': distance,
                        'relevance': relevance,
                        'coordinates': (landmark['lat'], landmark['lon'])
                    })
            
            return landmarks
        
        except Exception as e:
            raise Exception(f"Failed to fetch landmarks: {str(e)}")
