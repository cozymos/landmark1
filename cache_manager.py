import streamlit as st
from typing import Tuple, List, Dict
import json
import os
import time
from datetime import datetime, timedelta
import requests
from functools import partial
import folium
from PIL import Image
from io import BytesIO

class OfflineCacheManager:
    def __init__(self):
        # Initialize cache directories
        self.cache_dir = ".cache"
        self.tiles_dir = os.path.join(self.cache_dir, "map_tiles")
        self.landmarks_dir = os.path.join(self.cache_dir, "landmarks")
        self.images_dir = os.path.join(self.cache_dir, "images")

        # Create cache directories if they don't exist
        for directory in [self.cache_dir, self.tiles_dir, self.landmarks_dir, self.images_dir]:
            os.makedirs(directory, exist_ok=True)

        # Initialize offline mode if not present
        if 'offline_mode' not in st.session_state:
            st.session_state.offline_mode = False

    def get_tile_url(self, api_key: str) -> str:
        """Get appropriate tile URL based on mode"""
        if st.session_state.offline_mode:
            # Use OpenStreetMap tiles when offline (they support offline caching)
            return "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        else:
            # Use Google Maps tiles when online
            return f"https://mt1.google.com/vt/lyrs=m&x={{x}}&y={{y}}&z={{z}}&key={api_key}"

    def cache_landmarks(self, landmarks: List[Dict], bounds: Tuple[float, float, float, float], language: str):
        """Cache landmark data and associated images for offline use"""
        bounds_key = f"{language}_" + "_".join(str(round(b, 3)) for b in bounds)
        cache_path = os.path.join(self.landmarks_dir, f"landmarks_{bounds_key}.json")

        try:
            # Cache landmark data
            cached_landmarks = []
            for landmark in landmarks:
                cached_landmark = landmark.copy()

                # Cache image if available
                if landmark.get('image_url'):
                    image_filename = self._cache_image(landmark['image_url'])
                    if image_filename:
                        cached_landmark['cached_image'] = image_filename

                cached_landmarks.append(cached_landmark)

            with open(cache_path, 'w') as f:
                json.dump({
                    'landmarks': cached_landmarks,
                    'timestamp': time.time(),
                    'bounds': bounds,
                    'language': language
                }, f)

            # Update cache stats
            st.session_state.cache_stats['landmarks_cached'] = len(os.listdir(self.landmarks_dir))
            st.session_state.cache_stats['images_cached'] = len(os.listdir(self.images_dir))
            st.session_state.cache_stats['last_update'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        except Exception as e:
            st.warning(f"Failed to cache landmarks: {str(e)}")

    def _cache_image(self, image_url: str) -> str:
        """Download and cache an image, return filename if successful"""
        try:
            # Generate filename from URL
            filename = os.path.join(self.images_dir, f"{hash(image_url)}.jpg")

            # Skip if already cached
            if os.path.exists(filename):
                return filename

            # Download and save image
            response = requests.get(image_url)
            if response.status_code == 200:
                img = Image.open(BytesIO(response.content))
                img.save(filename, 'JPEG')
                return filename

        except Exception as e:
            st.warning(f"Failed to cache image: {str(e)}")
        return None

    def get_cached_landmarks(self, bounds: Tuple[float, float, float, float], language: str, max_age_hours: int = 24) -> List[Dict]:
        """Retrieve cached landmarks with smart bounds matching"""
        try:
            # Find the closest cached bounds for the specified language
            closest_cache = None
            min_distance = float('inf')

            for cache_file in os.listdir(self.landmarks_dir):
                if cache_file.startswith(f'landmarks_{language}_'):
                    cached_bounds = [float(x) for x in cache_file.split('_')[2:-1]]  # Skip language prefix and .json
                    distance = sum((a - b) ** 2 for a, b in zip(bounds, cached_bounds))

                    if distance < min_distance:
                        min_distance = distance
                        closest_cache = cache_file

            if closest_cache:
                cache_path = os.path.join(self.landmarks_dir, closest_cache)
                with open(cache_path, 'r') as f:
                    cache_data = json.load(f)

                # Check if cache is still valid and matches the requested language
                age_hours = (time.time() - cache_data['timestamp']) / 3600
                if age_hours <= max_age_hours and cache_data.get('language') == language:
                    # Process cached landmarks
                    landmarks = cache_data['landmarks']
                    for landmark in landmarks:
                        if 'cached_image' in landmark:
                            # Use cached image path
                            landmark['image_url'] = f"file://{landmark['cached_image']}"
                    return landmarks

            return []

        except Exception as e:
            st.warning(f"Failed to retrieve cached landmarks: {str(e)}")
            return []

    def clear_old_cache(self, max_age_hours: int = 24):
        """Clear cache files older than specified hours"""
        try:
            current_time = time.time()
            cleared_count = 0

            # Clear old landmark cache
            for cache_file in os.listdir(self.landmarks_dir):
                cache_path = os.path.join(self.landmarks_dir, cache_file)
                if os.path.getmtime(cache_path) < current_time - (max_age_hours * 3600):
                    os.remove(cache_path)
                    cleared_count += 1

            # Clear old image cache
            for image_file in os.listdir(self.images_dir):
                image_path = os.path.join(self.images_dir, image_file)
                if os.path.getmtime(image_path) < current_time - (max_age_hours * 3600):
                    os.remove(image_path)
                    cleared_count += 1

            if cleared_count > 0:
                st.success(f"Cleared {cleared_count} old cache files")

        except Exception as e:
            st.warning(f"Failed to clear old cache: {str(e)}")

    def get_cache_stats(self) -> Dict:
        """Get current cache statistics"""
        return st.session_state.cache_stats

# Initialize cache manager
cache_manager = OfflineCacheManager()

@st.cache_data(ttl=3600)
def get_cached_landmarks(
    bounds: Tuple[float, float, float, float],
    zoom_level: int,
    offline_mode: bool = False,
    language: str = 'en',
    data_source: str = 'Google Places'
) -> List[Dict]:
    """
    Smart wrapper for landmark caching with offline support
    """
    try:
        if offline_mode:
            return cache_manager.get_cached_landmarks(bounds, language)

        # Only fetch new landmarks if zoom level is appropriate
        if zoom_level >= 8:  # Prevent fetching at very low zoom levels
            landmarks = []

            if data_source == "Wikipedia":
                from wiki_handler import WikiLandmarkFetcher
                wiki_fetcher = WikiLandmarkFetcher()
                landmarks = wiki_fetcher.get_landmarks(bounds)  # Language handled in class
            else:  # Google Places
                from google_places import GooglePlacesHandler
                places_handler = GooglePlacesHandler()
                landmarks = places_handler.get_landmarks(bounds)

            # Cache the landmarks for offline use
            if landmarks:
                cache_manager.cache_landmarks(landmarks, bounds, language)

            return landmarks
        return []

    except Exception as e:
        st.error(f"Error fetching landmarks: {str(e)}")
        if offline_mode:
            return cache_manager.get_cached_landmarks(bounds, language)
        return []