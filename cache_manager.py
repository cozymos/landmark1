import streamlit as st
from typing import Tuple, List, Dict
import json
import os
import time
from datetime import datetime, timedelta
import base64
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

        # Create cache directories if they don't exist
        for directory in [self.cache_dir, self.tiles_dir, self.landmarks_dir]:
            os.makedirs(directory, exist_ok=True)

        # Initialize cache in session state
        if 'offline_mode' not in st.session_state:
            st.session_state.offline_mode = False

    def cache_map_tile(self, url: str, zoom: int, x: int, y: int) -> str:
        """Cache a map tile locally"""
        tile_path = os.path.join(self.tiles_dir, f"tile_{zoom}_{x}_{y}.png")

        if not os.path.exists(tile_path):
            try:
                response = requests.get(url)
                response.raise_for_status()

                # Save tile image
                img = Image.open(BytesIO(response.content))
                img.save(tile_path)
            except Exception as e:
                st.warning(f"Failed to cache tile: {str(e)}")
                return url

        return f"file://{tile_path}"

    def cache_landmarks(self, landmarks: List[Dict], bounds: Tuple[float, float, float, float]):
        """Cache landmark data for offline use"""
        bounds_key = "_".join(str(round(b, 3)) for b in bounds)
        cache_path = os.path.join(self.landmarks_dir, f"landmarks_{bounds_key}.json")

        try:
            # Cache landmark data
            with open(cache_path, 'w') as f:
                json.dump({
                    'landmarks': landmarks,
                    'timestamp': time.time(),
                    'bounds': bounds
                }, f)
        except Exception as e:
            st.warning(f"Failed to cache landmarks: {str(e)}")

    def get_cached_landmarks(self, bounds: Tuple[float, float, float, float], max_age_hours: int = 24) -> List[Dict]:
        """Retrieve cached landmarks"""
        try:
            # Find the closest cached bounds
            closest_cache = None
            min_distance = float('inf')

            for cache_file in os.listdir(self.landmarks_dir):
                if cache_file.startswith('landmarks_'):
                    cached_bounds = [float(x) for x in cache_file[10:-5].split('_')]
                    distance = sum((a - b) ** 2 for a, b in zip(bounds, cached_bounds))

                    if distance < min_distance:
                        min_distance = distance
                        closest_cache = cache_file

            if closest_cache:
                cache_path = os.path.join(self.landmarks_dir, closest_cache)
                with open(cache_path, 'r') as f:
                    cache_data = json.load(f)

                # Check if cache is still valid
                age_hours = (time.time() - cache_data['timestamp']) / 3600
                if age_hours <= max_age_hours:
                    return cache_data['landmarks']

            return []

        except Exception as e:
            st.warning(f"Failed to retrieve cached landmarks: {str(e)}")
            return []

    def clear_old_cache(self, max_age_hours: int = 24):
        """Clear cache files older than specified hours"""
        try:
            current_time = time.time()

            # Clear old landmark cache
            for cache_file in os.listdir(self.landmarks_dir):
                cache_path = os.path.join(self.landmarks_dir, cache_file)
                if os.path.getmtime(cache_path) < current_time - (max_age_hours * 3600):
                    os.remove(cache_path)

            # Clear old tile cache
            for cache_file in os.listdir(self.tiles_dir):
                cache_path = os.path.join(self.tiles_dir, cache_file)
                if os.path.getmtime(cache_path) < current_time - (max_age_hours * 3600):
                    os.remove(cache_path)

        except Exception as e:
            st.warning(f"Failed to clear old cache: {str(e)}")

# Initialize cache manager
cache_manager = OfflineCacheManager()

@st.cache_data(ttl=3600, show_spinner=False)
def get_cached_landmarks(
    bounds: Tuple[float, float, float, float],
    zoom_level: int,
    offline_mode: bool = False
) -> List[Dict]:
    """
    Smart wrapper for landmark caching with offline support
    """
    try:
        if offline_mode:
            return cache_manager.get_cached_landmarks(bounds)

        # Only fetch new landmarks if zoom level is appropriate
        if zoom_level >= 8:  # Prevent fetching at very low zoom levels
            from google_places import GooglePlacesHandler
            places_handler = GooglePlacesHandler()
            landmarks = places_handler.get_landmarks(bounds)

            # Cache the landmarks for offline use
            if landmarks:
                cache_manager.cache_landmarks(landmarks, bounds)

            return landmarks
        return []

    except Exception as e:
        st.error(f"Error fetching landmarks: {str(e)}")
        if offline_mode:
            return cache_manager.get_cached_landmarks(bounds)
        return []