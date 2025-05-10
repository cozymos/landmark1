import json
import os
import time
import requests
import hashlib
from typing import Tuple, Dict, List, Any, Optional, Union
import logging
import streamlit as st

# Set up logger
logger = logging.getLogger("cache")


# Use Streamlit's caching to ensure singleton pattern
@st.cache_resource
def get_cache_manager_instance():
    """
    Creates a singleton instance of CacheManager using Streamlit's caching
    This ensures it's only initialized once per session
    """
    logger.debug("Creating new CacheManager instance")
    return CacheManager()


class CacheManager:
    def __init__(self):
        # Initialize cache directories with absolute paths
        self.cache_dir = os.environ.get('CACHE_DIR', os.path.abspath("cache"))

        # Cache file paths
        self.landmarks_cache_path = os.path.join(
            self.cache_dir, "landmarks_cache.json"
        )
        self.landmarks_dir = os.path.abspath(
            os.path.join(self.cache_dir, "landmarks")
        )
        self.images_dir = os.path.abspath(
            os.path.join(self.cache_dir, "images")
        )

        # Create cache directories if they don't exist
        for directory in [self.cache_dir, self.landmarks_dir, self.images_dir]:
            try:
                if not os.path.exists(directory):
                    os.makedirs(directory, exist_ok=True)
                    logger.info(f"Created directory: {directory}")
            except Exception as e:
                logger.error(
                    f"Failed to create directory {directory}: {str(e)}"
                )

        logger.info("CacheManager initialized successfully")

    def _cache_image(self, image_url: str) -> str:
        """Download and cache an image, return absolute filename if successful"""
        try:
            # Generate filename from URL using MD5 hash
            safe_hash = hashlib.md5(image_url.encode()).hexdigest()
            filename = os.path.abspath(
                os.path.join(self.images_dir, f"{safe_hash}.jpg")
            )

            logger.info(f"Processing image URL: {image_url}")
            logger.debug(f"Target cache path: {filename}")

            # Check if file exists and is readable
            if os.path.exists(filename):
                try:
                    # Verify file is readable
                    with open(filename, "rb") as f:
                        f.read(1)
                    logger.info(f"Using existing cached image file: {filename}")
                    return filename
                except Exception as e:
                    logger.error(f"Error reading existing image file: {str(e)}")

            # Download and save new image
            try:
                response = requests.get(image_url, timeout=10)
                if response.status_code == 200:
                    with open(filename, "wb") as f:
                        f.write(response.content)
                    logger.info(f"Successfully cached new image: {filename}")
                    # Verify the file was written successfully
                    if os.path.exists(filename):
                        return filename
                    else:
                        logger.error(
                            f"Failed to download image: HTTP {response.status_code}"
                        )
            except requests.RequestException as e:
                logger.error(f"Request failed for {image_url}: {str(e)}")

            return ""

        except Exception as e:
            logger.error(f"Error in _cache_image: {str(e)}")
            return ""

    def cache_landmarks(
        self, landmarks: List[Dict], center_coords: Tuple[float, float], radius_km: float
    ):
        """
        Cache landmark data and associated images for offline use
        
        Args:
            landmarks: List of landmark dictionaries to cache
            center_coords: (lat, lon) tuple for the center point
            radius_km: Radius in kilometers from the center
        """
        try:
            cache_path = os.path.abspath(
                os.path.join(self.landmarks_dir, "landmarks.json")
            )

            logger.info(f"Caching landmarks to: {cache_path}")

            cached_landmarks = []
            for landmark in landmarks:
                try:
                    cached_landmark = landmark.copy()

                    if "image_url" in landmark and landmark["image_url"]:
                        logger.info(
                            f"Processing image for landmark: {landmark['title']}"
                        )
                        cached_path = self._cache_image(landmark["image_url"])
                        if cached_path:
                            cached_landmark["image_url"] = cached_path
                            logger.debug(
                                f"Cached image path set to: {cached_path}"
                            )

                    cached_landmarks.append(cached_landmark)
                except Exception as e:
                    logger.error(
                        f"Error processing landmark {landmark.get('title', 'unknown')}: {str(e)}"
                    )

            # Save to cache file
            try:
                with open(cache_path, "w") as f:
                    json.dump(
                        {
                            "landmarks": cached_landmarks,
                            "timestamp": time.time(),
                            "center": {"lat": center_coords[0], "lon": center_coords[1]},
                            "radius_km": radius_km,
                        },
                        f,
                        indent=2,
                    )
            except Exception as e:
                logger.error(
                    f"Failed to write cache file {cache_path}: {str(e)}"
                )
                raise

            logger.info(
                f"Successfully cached {len(cached_landmarks)} landmarks"
            )

        except Exception as e:
            logger.error(f"Error in cache_landmarks: {str(e)}")
            raise

    def get_cached_landmarks(
        self, center_coords: Tuple[float, float], radius_km: float
    ) -> List[Dict]:
        """
        Retrieve cached landmarks
        
        Args:
            center_coords: (lat, lon) tuple for the center point
            radius_km: Radius in kilometers from the center
            
        Returns:
            List of cached landmark dictionaries
        """
        try:
            cache_path = os.path.join(self.landmarks_dir, "landmarks.json")
            with open(cache_path, "r") as f:
                logger.info(
                    f"Using existing cached landmark file: {cache_path}"
                )
                cache_data = json.load(f)
                landmarks = cache_data["landmarks"]
                return landmarks

        except Exception as e:
            logger.error(f"Error in get_cached_landmarks: {str(e)}")
            return []
