from typing import Tuple, Optional
import streamlit as st
from coord_utils import parse_coordinates

class LocationHandler:
    def __init__(self):
        pass

    def validate_coordinates(self, lat: float, lon: float) -> bool:
        """Validate if coordinates are within valid ranges"""
        return -90 <= lat <= 90 and -180 <= lon <= 180

    def process_location_update(self, lat: float, lon: float) -> Tuple[bool, Optional[str]]:
        """Process and validate location update request"""
        if self.validate_coordinates(lat, lon):
            st.session_state.map_center = [lat, lon]
            st.session_state.zoom_level = 12
            # Update URL parameters
            st.query_params['center'] = f"{lat},{lon}"
            st.query_params['zoom'] = str(st.session_state.zoom_level)
            return True, None
        else:
            return False, "Invalid coordinates. Latitude must be between -90 and 90, longitude between -180 and 180."

    def parse_location_input(self, input_text: str) -> Tuple[Optional[float], Optional[float]]:
        """Parse location input in various formats"""
        if not input_text:
            return None, None
            
        coords = parse_coordinates(input_text)
        if coords:
            return coords.lat, coords.lon
        return None, None
