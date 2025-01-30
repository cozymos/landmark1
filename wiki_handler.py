import wikipediaapi
import geopy.distance
from typing import Dict, List, Tuple
import time
import math
import streamlit as st

class WikiLandmarkFetcher:
    def __init__(self):
        # Initialize language in session state if not present
        if 'wiki_language' not in st.session_state:
            st.session_state.wiki_language = 'en'

        self.supported_languages = {
            'en': 'English',
            'es': 'Español',
            'fr': 'Français',
            'de': 'Deutsch',
            'it': 'Italiano',
            'ja': '日本語',
            'zh': '中文'
        }

        # Create Wikipedia API instance with current language
        self._init_wiki_instance()

        self.last_request = 0
        self.min_delay = 1  # Minimum delay between requests in seconds

        # Pre-defined landmarks for testing
        self.test_landmarks = {
            'San Francisco': {
                'title': 'Golden Gate Bridge',
                'lat': 37.8199,
                'lon': -122.4783,
                'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/0c/GoldenGateBridge-001.jpg/1200px-GoldenGateBridge-001.jpg'
            },
            'Alcatraz': {
                'title': 'Alcatraz Island',
                'lat': 37.8267,
                'lon': -122.4233,
                'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/0a/Alcatraz_Island_photo_D_Ramey_Logan.jpg/1200px-Alcatraz_Island_photo_D_Ramey_Logan.jpg'
            },
            'Pier39': {
                'title': 'Pier 39',
                'lat': 37.8087,
                'lon': -122.4098,
                'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/b/b8/Pier_39_-_San_Francisco%2C_CA_-_USA_-_panoramio.jpg/1200px-Pier_39_-_San_Francisco%2C_CA_-_USA_-_panoramio.jpg'
            },
            'Lombard': {
                'title': 'Lombard Street',
                'lat': 37.8021,
                'lon': -122.4187,
                'image_url': 'https://upload.wikimedia.org/wikipedia/commons/thumb/1/13/Lombard_Street_San_Francisco.jpg/1200px-Lombard_Street_San_Francisco.jpg'
            }
        }

    def _init_wiki_instance(self):
        """Initialize or reinitialize Wikipedia API instance with current language"""
        self.wiki = wikipediaapi.Wikipedia(
            'LandmarkExplorer/1.0',
            st.session_state.wiki_language,
            extract_format=wikipediaapi.ExtractFormat.WIKI
        )

    def set_language(self, language_code: str) -> bool:
        """Set the Wikipedia language and reinitialize the API instance"""
        if language_code in self.supported_languages:
            st.session_state.wiki_language = language_code
            self._init_wiki_instance()
            return True
        return False

    def get_supported_languages(self) -> Dict[str, str]:
        """Return dictionary of supported languages"""
        return self.supported_languages

    def _rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        time_passed = current_time - self.last_request
        if time_passed < self.min_delay:
            time.sleep(self.min_delay - time_passed)
        self.last_request = time.time()

    def get_landmarks(self, bounds: Tuple[float, float, float, float]) -> List[Dict]:
        """
        Fetch landmarks within the given bounds with content in current language
        bounds: (south, west, north, east)
        """
        self._rate_limit()

        center_lat = (bounds[0] + bounds[2]) / 2
        center_lon = (bounds[1] + bounds[3]) / 2

        try:
            landmarks = []

            # Calculate the visible area in square kilometers
            width = geopy.distance.distance(
                (center_lat, bounds[1]), 
                (center_lat, bounds[3])
            ).km
            height = geopy.distance.distance(
                (bounds[0], center_lon),
                (bounds[2], center_lon)
            ).km
            visible_area = width * height

            # Only show landmarks within the visible bounds
            for landmark in self.test_landmarks.values():
                if (bounds[0] <= landmark['lat'] <= bounds[2] and
                    bounds[1] <= landmark['lon'] <= bounds[3]):

                    # Calculate distance from center
                    distance = geopy.distance.distance(
                        (center_lat, center_lon),
                        (landmark['lat'], landmark['lon'])
                    ).km

                    # Calculate relevance score based on distance and visible area
                    max_distance = math.sqrt(width**2 + height**2) / 2
                    relevance = 1.0 - (distance / max_distance if max_distance > 0 else 0)
                    relevance = max(0.1, min(1.0, relevance))

                    # Get language-specific title based on test data
                    # In a real implementation, this would use the Wikipedia API's language links
                    page = self.wiki.page(landmark['title'])
                    if page.exists():
                        landmarks.append({
                            'title': page.title,
                            'summary': page.summary[:200] + "..." if len(page.summary) > 200 else page.summary,
                            'url': page.fullurl,
                            'image_url': landmark['image_url'],
                            'distance': round(distance, 2),
                            'relevance': round(relevance, 2),
                            'coordinates': (landmark['lat'], landmark['lon']),
                            'language': st.session_state.wiki_language
                        })

            return landmarks

        except Exception as e:
            raise Exception(f"Failed to fetch landmarks: {str(e)}")