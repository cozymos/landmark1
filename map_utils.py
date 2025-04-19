import streamlit as st
import folium
from folium import plugins
from streamlit_folium import st_folium
import logging
from typing import Tuple, List, Dict, Any, Optional
import os

logger = logging.getLogger("map")


# cache by a global-var if more blank map (missing map-data) occurred
@st.cache_data(ttl=600, show_spinner=False)
def create_base_map(center: List[float], zoom: int) -> folium.Map:
    logger.debug(f"Creating base map at {center} with zoom {zoom}")

    # Create base map
    m = folium.Map(
        location=st.session_state.map_center,
        zoom_start=st.session_state.zoom_level,
        tiles=get_tile_url(),
        attr=(
            "OpenStreetMap" if st.session_state.offline_mode else "Google Maps"
        ),
        control_scale=True,
        prefer_canvas=True,  # Use canvas for better performance
        zoom_control=True,  # Enable default zoom control
    )

    import time

    # add more sleep if more blank map (missing map-data) occurred
    time.sleep(0.3)  # Small delay to ensure map is ready
    return m


def get_tile_url() -> str:
    """Get appropriate tile URL based on mode"""
    if st.session_state.offline_mode:
        # Use OpenStreetMap tiles when offline (they support offline caching)
        return "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
    else:
        # Use Google Maps tiles when online
        api_key = os.environ['GOOGLE_MAPS_API_KEY']
        return f"https://mt1.google.com/vt/lyrs=m&x={{x}}&y={{y}}&z={{z}}&key={api_key}"


def render_map(center: List[float], zoom: int) -> Optional[Dict[str, Any]]:
    try:
        m = create_base_map(center, zoom)

        # Add landmarks and distance circle if we have data
        if st.session_state.landmarks and st.session_state.show_markers:
            add_landmarks_to_map(m, st.session_state.landmarks, False)

        radius_km = 10 if st.session_state.show_circle else 0
        if radius_km > 0:
            center = (
                float(st.session_state.map_center[0]),
                float(st.session_state.map_center[1]),
            )
            draw_distance_circle(m, center, radius_km)

        # Display map with dynamic height
        map_data = st_folium(
            m,
            width="100%",
            height=st.session_state.current_page_height,
            key="landmark_locator",
            returned_objects=["center", "zoom", "bounds"],
            use_container_width=True,  # Use full width of container
        )

        return map_data

    except Exception as e:
        logger.error(f"Error rendering map: {str(e)}")
        return None


def get_relevance_color(relevance: float) -> str:
    """Get marker color based on relevance score"""
    if relevance >= 0.8:
        return 'red'
    elif relevance >= 0.5:
        return 'orange'
    else:
        return 'blue'

from urllib.parse import quote

# Function to convert local file path to a URL
def local_file_to_url(file_path):
    # Convert to absolute path and normalize
    abs_path = os.path.abspath(file_path)
    # Convert backslashes to forward slashes
    path_with_forward_slashes = abs_path.replace('\\', '/')
    # URL encode the path
    encoded_path = quote(path_with_forward_slashes)
    # Create proper file URI
    return f"file:///{encoded_path}"

def add_landmarks_to_map(m: folium.Map,
                         landmarks: List[Dict],
                         show_heatmap: bool = False) -> None:
    """Add landmark markers to the map with clustering and optional heatmap"""
    if not landmarks or len(landmarks) == 0:
        return

    try:
        landmark_group = folium.FeatureGroup(name="Landmarks").add_to(m)

        # Prepare heatmap data
        heat_data = []

        for landmark in landmarks:
            # Get color based on relevance
            color = get_relevance_color(landmark['relevance'])
            coords = landmark['coordinates']

            # local_url = local_file_to_url(landmark['image_url'])
            # logger.info(f"Cached local_url: {local_url}")
            # <img src="{local_url}" width="150px">

            # Create custom popup HTML
            popup_html = f"""
            <div style="width:200px">
                <h5>{landmark['title']}</h5>
                <p>{landmark['summary'][:100]}…</p>
                <p><small>{coords[0]:.5f}, {coords[1]:.5f}</small></p>
            </div>
            """

            # Create marker
            marker = folium.Marker(
                location=coords,
                popup=folium.Popup(popup_html, max_width=300),
                icon=folium.Icon(color=color, icon='info-sign'),
            )
            marker.add_to(landmark_group)

            # Add to heatmap data
            heat_data.append([
                coords[0], coords[1],
                landmark['relevance'] * 100  # Scale weight for visibility
            ])

        # Add heatmap if there's data and it's enabled
        if heat_data and show_heatmap:
            plugins.HeatMap(data=heat_data,
                            name='Heatmap',
                            min_opacity=0.3,
                            max_zoom=18,
                            radius=25,
                            blur=15,
                            overlay=True,
                            control=True,
                            show=show_heatmap).add_to(m)

        # Add layer control
        folium.LayerControl().add_to(m)
    except Exception as e:
        logger.error(f"Error adding landmarks to map: {str(e)}")


def draw_distance_circle(m: folium.Map, center: Tuple[float, float],
                         radius_km: float):
    """Draw a circle with given radius around a point"""
    folium.Circle(
        location=center,
        radius=radius_km * 1000,  # Convert km to meters
        color='green',
        fill=True,
        fill_opacity=0.1,
        popup=f'{radius_km}km radius').add_to(m)
