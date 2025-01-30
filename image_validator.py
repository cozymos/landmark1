import os
import requests
from PIL import Image
from io import BytesIO
import streamlit as st
from typing import Optional, Tuple
import logging
import hashlib

class ImageValidator:
    def __init__(self):
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Define valid image formats
        self.valid_formats = {'JPEG', 'PNG', 'JPG', 'GIF'}

        # Define minimum image dimensions
        self.min_width = 200
        self.min_height = 200

        # Define maximum file size (5MB)
        self.max_file_size = 5 * 1024 * 1024

        # Fallback image URLs in order of preference
        self.fallback_images = {
            'tourist_attraction': 'https://via.placeholder.com/300x200?text=Tourist+Attraction',
            'landmark': 'https://via.placeholder.com/300x200?text=Landmark',
            'museum': 'https://via.placeholder.com/300x200?text=Museum',
            'park': 'https://via.placeholder.com/300x200?text=Park',
            'default': 'https://via.placeholder.com/300x200?text=No+Image'
        }

    def validate_image_file(self, file_path: str) -> Tuple[bool, str]:
        """
        Validate a local image file
        Returns: (is_valid, error_message)
        """
        try:
            if not os.path.exists(file_path):
                self.logger.warning(f"File does not exist: {file_path}")
                return False, "File does not exist"

            # Check file size
            try:
                file_size = os.path.getsize(file_path)
                if file_size > self.max_file_size:
                    self.logger.warning(f"File size too large: {file_size} bytes")
                    return False, "File size too large"
            except OSError as e:
                self.logger.error(f"Error checking file size: {str(e)}")
                return False, f"File size check failed: {str(e)}"

            # Try to open and verify the image
            try:
                with Image.open(file_path) as img:
                    # Verify image format
                    if img.format not in self.valid_formats:
                        self.logger.warning(f"Invalid format: {img.format}")
                        return False, f"Invalid format: {img.format}"

                    # Check dimensions
                    width, height = img.size
                    if width < self.min_width or height < self.min_height:
                        self.logger.warning(f"Image too small: {width}x{height}")
                        return False, f"Image too small: {width}x{height}"

                    # Try to load the image data to verify it's not corrupted
                    try:
                        img.load()
                        return True, "Valid image"
                    except Exception as e:
                        self.logger.error(f"Failed to load image data: {str(e)}")
                        return False, f"Corrupted image data: {str(e)}"

            except Exception as e:
                self.logger.error(f"Error opening image file: {str(e)}")
                return False, f"Invalid image file: {str(e)}"

        except Exception as e:
            self.logger.error(f"Error validating image {file_path}: {str(e)}")
            return False, f"Validation error: {str(e)}"

    def validate_image_url(self, image_url: str) -> Tuple[bool, str]:
        """
        Validate an image from URL
        Returns: (is_valid, error_message)
        """
        try:
            self.logger.info(f"Validating image URL: {image_url}")
            response = requests.get(image_url, timeout=10)
            if response.status_code != 200:
                self.logger.warning(f"Failed to fetch image: HTTP {response.status_code}")
                return False, f"Failed to fetch image: {response.status_code}"

            # Check content type
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                self.logger.warning(f"Invalid content type: {content_type}")
                return False, f"Invalid content type: {content_type}"

            # Check file size
            content_length = len(response.content)
            if content_length > self.max_file_size:
                self.logger.warning(f"File size too large: {content_length} bytes")
                return False, "File size too large"

            # Validate image data
            try:
                img = Image.open(BytesIO(response.content))
                if img.format not in self.valid_formats:
                    self.logger.warning(f"Invalid format: {img.format}")
                    return False, f"Invalid format: {img.format}"

                width, height = img.size
                if width < self.min_width or height < self.min_height:
                    self.logger.warning(f"Image too small: {width}x{height}")
                    return False, f"Image too small: {width}x{height}"

                return True, "Valid image"

            except Exception as e:
                self.logger.error(f"Error processing image data: {str(e)}")
                return False, f"Invalid image data: {str(e)}"

        except requests.RequestException as e:
            self.logger.error(f"Request failed for {image_url}: {str(e)}")
            return False, f"Request failed: {str(e)}"
        except Exception as e:
            self.logger.error(f"Error validating image URL {image_url}: {str(e)}")
            return False, f"Validation error: {str(e)}"

    def get_fallback_image(self, landmark_type: Optional[str] = None) -> str:
        """Get appropriate fallback image URL based on landmark type"""
        fallback_url = self.fallback_images.get(landmark_type, self.fallback_images['default'])
        self.logger.info(f"Using fallback image for type {landmark_type}: {fallback_url}")
        return fallback_url

    def process_image(self, image_source: str, landmark_type: Optional[str] = None) -> str:
        """
        Process and validate image from either URL or file path
        Returns: validated image source or appropriate fallback
        """
        try:
            self.logger.info(f"Processing image source: {image_source}")
            is_valid = False
            error_msg = ""

            # Check if it's a URL or file path
            if image_source.startswith(('http://', 'https://')):
                is_valid, error_msg = self.validate_image_url(image_source)
            else:
                is_valid, error_msg = self.validate_image_file(image_source)

            if not is_valid:
                self.logger.warning(f"Image validation failed: {error_msg}")
                return self.get_fallback_image(landmark_type)

            return image_source

        except Exception as e:
            self.logger.error(f"Error processing image: {str(e)}")
            return self.get_fallback_image(landmark_type)

# Initialize global validator
image_validator = ImageValidator()