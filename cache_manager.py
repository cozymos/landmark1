import streamlit as st
from typing import Tuple, List, Dict
import json
import os
import time
from datetime import datetime
import requests
import hashlib
import logging


class OfflineCacheManager:

    def __init__(self):
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Initialize cache directories with absolute paths
        self.cache_dir = os.path.abspath(".cache")
        self.tiles_dir = os.path.abspath(
            os.path.join(self.cache_dir, "map_tiles"))
        self.landmarks_dir = os.path.abspath(
            os.path.join(self.cache_dir, "landmarks"))
        self.images_dir = os.path.abspath(
            os.path.join(self.cache_dir, "images"))

        # Create cache directories if they don't exist
        for directory in [
                self.cache_dir, self.tiles_dir, self.landmarks_dir,
                self.images_dir
        ]:
            try:
                if not os.path.exists(directory):
                    os.makedirs(directory, exist_ok=True)
                    self.logger.info(f"Created directory: {directory}")
            except Exception as e:
                self.logger.error(
                    f"Failed to create directory {directory}: {str(e)}")
                st.error(f"Cache directory creation failed: {str(e)}")

        # Initialize cache stats in session state
        if 'cache_stats' not in st.session_state:
            st.session_state.cache_stats = {
                'landmarks_cached': 0,
                'images_cached': 0,
                'last_update': None
            }

    def _cache_image(self, image_url: str) -> str:
        """Download and cache an image, return absolute filename if successful"""
        try:
            # Generate filename from URL using MD5 hash
            safe_hash = hashlib.md5(image_url.encode()).hexdigest()
            filename = os.path.abspath(
                os.path.join(self.images_dir, f"{safe_hash}.jpg"))

            self.logger.info(f"Processing image URL: {image_url}")
            self.logger.debug(f"Target cache path: {filename}")

            # Check if file exists and is readable
            if os.path.exists(filename):
                try:
                    # Verify file is readable
                    with open(filename, 'rb') as f:
                        f.read(1)
                    self.logger.info(f"Using existing cached file: {filename}")
                    return filename
                except Exception as e:
                    self.logger.error(f"Error reading existing file: {str(e)}")

            # Download and save new image
            try:
                response = requests.get(image_url, timeout=10)
                if response.status_code == 200:
                    with open(filename, 'wb') as f:
                        f.write(response.content)
                    self.logger.info(
                        f"Successfully cached new image: {filename}")
                    # Verify the file was written successfully
                    if os.path.exists(filename):
                        return filename
                    else:
                        self.logger.error(
                            f"Failed to download image: HTTP {response.status_code}"
                        )
            except requests.RequestException as e:
                self.logger.error(f"Request failed for {image_url}: {str(e)}")

            return ""

        except Exception as e:
            self.logger.error(f"Error in _cache_image: {str(e)}")
            return ""

    def cache_landmarks(self, landmarks: List[Dict],
                        bounds: Tuple[float, float, float, float]):
        """Cache landmark data and associated images for offline use"""
        try:
            # bounds_key = "_".join(str(round(b, 3)) for b in bounds)
            # use single cache file for now
            bounds_key = "_1"
            cache_path = os.path.abspath(
                os.path.join(self.landmarks_dir,
                             f"landmarks_{bounds_key}.json"))

            self.logger.info(f"Caching landmarks to: {cache_path}")

            cached_landmarks = []
            for landmark in landmarks:
                try:
                    cached_landmark = landmark.copy()

                    if 'image_url' in landmark and landmark['image_url']:
                        self.logger.info(
                            f"Processing image for landmark: {landmark['title']}"
                        )
                        cached_path = self._cache_image(landmark['image_url'])
                        if cached_path:
                            cached_landmark['image_url'] = cached_path
                            self.logger.debug(
                                f"Cached image path set to: {cached_path}")

                    cached_landmarks.append(cached_landmark)
                except Exception as e:
                    self.logger.error(
                        f"Error processing landmark {landmark.get('title', 'unknown')}: {str(e)}"
                    )

            # Save to cache file
            try:
                with open(cache_path, 'w') as f:
                    json.dump(
                        {
                            'landmarks': cached_landmarks,
                            'timestamp': time.time(),
                            'bounds': bounds
                        }, f)
            except Exception as e:
                self.logger.error(
                    f"Failed to write cache file {cache_path}: {str(e)}")
                raise

            # Update cache stats
            try:
                st.session_state.cache_stats['landmarks_cached'] = len(
                    os.listdir(self.landmarks_dir))
                st.session_state.cache_stats['images_cached'] = len(
                    os.listdir(self.images_dir))
                st.session_state.cache_stats['last_update'] = datetime.now(
                ).strftime("%Y-%m-%d %H:%M:%S")
            except Exception as e:
                self.logger.error(f"Failed to update cache stats: {str(e)}")

            self.logger.info(
                f"Successfully cached {len(cached_landmarks)} landmarks")

        except Exception as e:
            self.logger.error(f"Error in cache_landmarks: {str(e)}")
            raise

    def get_tile_url(self) -> str:
        """Get appropriate tile URL based on mode"""
        if st.session_state.offline_mode:
            # Use OpenStreetMap tiles when offline (they support offline caching)
            return "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        else:
            # Use Google Maps tiles when online
            api_key = os.environ['GOOGLE_MAPS_API_KEY']
            return f"https://mt1.google.com/vt/lyrs=m&x={{x}}&y={{y}}&z={{z}}&key={api_key}"

    def get_cached_landmarks(self,
                             bounds: Tuple[float, float, float, float],
                             max_age_hours: int = 24) -> List[Dict]:
        """Retrieve cached landmarks with smart bounds matching"""
        try:
            # Find the closest cached bounds
            # closest_cache = None
            # use single cache file for now
            closest_cache = "landmarks_1.json"
            '''
            min_distance = float('inf')

            for cache_file in os.listdir(self.landmarks_dir):
                if cache_file.startswith('landmarks_'):
                    cached_bounds = [float(x) for x in cache_file[10:-5].split('_')]
                    distance = sum((a - b) ** 2 for a, b in zip(bounds, cached_bounds))

                    if distance < min_distance:
                        min_distance = distance
                        closest_cache = cache_file
            '''
            if closest_cache:
                cache_path = os.path.join(self.landmarks_dir, closest_cache)
                with open(cache_path, 'r') as f:
                    cache_data = json.load(f)

            # Check if cache is still valid
            # age_hours = (time.time() - cache_data['timestamp']) / 3600
            # disable cache expiration for now
            age_hours = 0
            if age_hours <= max_age_hours:
                # Process cached landmarks
                landmarks = cache_data['landmarks']
                for landmark in landmarks:
                    # Always use cached image if available
                    if 'cached_image' in landmark:
                        landmark['image_url'] = landmark['cached_image']
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
                if os.path.getmtime(
                        cache_path) < current_time - (max_age_hours * 3600):
                    os.remove(cache_path)
                    cleared_count += 1

            # Clear old image cache
            for image_file in os.listdir(self.images_dir):
                image_path = os.path.join(self.images_dir, image_file)
                if os.path.getmtime(
                        image_path) < current_time - (max_age_hours * 3600):
                    os.remove(image_path)
                    cleared_count += 1

            if cleared_count > 0:
                st.success(f"Cleared {cleared_count} old cache files")

        except Exception as e:
            st.warning(f"Failed to clear old cache: {str(e)}")

    def get_cache_stats(self) -> Dict:
        """Get current cache statistics"""
        return st.session_state.cache_stats
