import folium
from streamlit_folium import st_folium
import streamlit as st
from typing import Dict, List, Tuple, Optional
from map_utils import draw_distance_circle, add_landmarks_to_map

class MapManager:
    def __init__(self, cache_manager):
        self.cache_manager = cache_manager

    def create_map(self, center: List[float], zoom: int, 
                  landmarks: List[Dict], show_markers: bool,
                  show_circle: bool, radius_km: float = 1) -> Dict:
        """Create and render the map with all components"""
        try:
            # Create base map
            m = folium.Map(
                location=center,
                zoom_start=zoom,
                tiles=self.cache_manager.get_tile_url(),
                attr="OpenStreetMap" if st.session_state.offline_mode else "Google Maps",
                control_scale=True,
                prefer_canvas=True
            )

            # Add landmarks if available and enabled
            if landmarks and show_markers:
                add_landmarks_to_map(m, landmarks, False)

            # Add distance circle if enabled
            if show_circle and radius_km > 0:
                draw_distance_circle(m, (float(center[0]), float(center[1])), radius_km)

            # Render map
            map_data = st_folium(
                m,
                width="100%",
                height=700,  # Initial height, adjusted by JavaScript
                key="landmark_locator",
                returned_objects=["center", "zoom", "bounds"]
            )

            return map_data

        except Exception as e:
            st.error(f"Error rendering map: {str(e)}")
            return {}

    def parse_map_data(self, map_data: Dict) -> Tuple[Optional[List[float]], Optional[int], Optional[Tuple]]:
        """Parse and extract data from map interaction"""
        if not isinstance(map_data, dict):
            return None, None, None

        # Extract center
        center = None
        center_data = map_data.get("center")
        if isinstance(center_data, dict):
            try:
                lat = float(center_data.get("lat"))
                lng = float(center_data.get("lng"))
                center = [lat, lng]
            except:
                pass

        # Extract zoom
        zoom = None
        try:
            zoom_data = map_data.get("zoom")
            if zoom_data is not None:
                zoom = int(float(zoom_data))
        except:
            pass

        # Extract bounds
        bounds = None
        bounds_data = map_data.get("bounds")
        if bounds_data:
            try:
                bounds = (
                    bounds_data['_southWest']['lat'],
                    bounds_data['_southWest']['lng'],
                    bounds_data['_northEast']['lat'],
                    bounds_data['_northEast']['lng']
                )
            except:
                pass

        return center, zoom, bounds
