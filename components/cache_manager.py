import streamlit as st
from typing import Tuple, List, Dict
import json
import os
import time
import requests
import hashlib
import logging


class CacheManager:

    def __init__(self):
        self.logger = logging.getLogger("cache")

        # Initialize cache directories with absolute paths
        self.cache_dir = os.path.abspath(".cache")
        self.landmarks_dir = os.path.abspath(
            os.path.join(self.cache_dir, "landmarks"))
        self.images_dir = os.path.abspath(
            os.path.join(self.cache_dir, "images"))

        # Create cache directories if they don't exist
        for directory in [
                self.cache_dir, self.landmarks_dir, self.images_dir
        ]:
            try:
                if not os.path.exists(directory):
                    os.makedirs(directory, exist_ok=True)
                    self.logger.info(f"Created directory: {directory}")
            except Exception as e:
                self.logger.error(
                    f"Failed to create directory {directory}: {str(e)}")
                st.error(f"Cache directory creation failed: {str(e)}")

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
                    self.logger.info(f"Using existing cached image file: {filename}")
                    return filename
                except Exception as e:
                    self.logger.error(f"Error reading existing image file: {str(e)}")

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
            cache_path = os.path.abspath(
                os.path.join(self.landmarks_dir,
                             f"landmarks_{st.session_state.last_data_source}.json"))

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
                        }, f, indent=2)
            except Exception as e:
                self.logger.error(
                    f"Failed to write cache file {cache_path}: {str(e)}")
                raise

            self.logger.info(
                f"Successfully cached {len(cached_landmarks)} landmarks")

        except Exception as e:
            self.logger.error(f"Error in cache_landmarks: {str(e)}")
            raise

    def get_cached_landmarks(self,
                             bounds: Tuple[float, float, float, float]) -> List[Dict]:
        """Retrieve cached landmarks with smart bounds matching"""
        try:
            cache_path = os.path.join(self.landmarks_dir,
					f"landmarks_{st.session_state.last_data_source}.json")
            with open(cache_path, 'r') as f:
                self.logger.info(f"Using existing cached landmark file: {cache_path}")
                cache_data = json.load(f)
                landmarks = cache_data['landmarks']
                return landmarks

        except Exception as e:
            self.logger.error(f"Error in get_cached_landmarks: {str(e)}")
            st.warning(f"Failed to retrieve cached landmarks: {str(e)}")
            return []
