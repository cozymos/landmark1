import streamlit as st
import folium
from streamlit_folium import st_folium
from wiki_handler import WikiLandmarkFetcher
from map_utils import create_base_map, draw_distance_circle, add_landmarks_to_map
from cache_manager import cache_landmarks #Presume this is still needed for fallback or other uses.
import time
from urllib.parse import quote, unquote
import json

# Page config
st.set_page_config(
    page_title="Local Landmarks Explorer",
    page_icon="🗺️",
    layout="wide"
)

# Initialize session state with URL parameters if available
if 'map_center' not in st.session_state:
    try:
        center_str = st.query_params.get('center', '37.7749,-122.4194')
        lat, lon = map(float, center_str.split(','))
        st.session_state.map_center = [lat, lon]
    except:
        st.session_state.map_center = [37.7749, -122.4194]  # Default to San Francisco

if 'zoom_level' not in st.session_state:
    try:
        st.session_state.zoom_level = int(st.query_params.get('zoom', '12'))
    except:
        st.session_state.zoom_level = 12

if 'last_bounds' not in st.session_state:
    st.session_state.last_bounds = None
if 'landmarks' not in st.session_state:
    st.session_state.landmarks = []
if 'selected_landmark' not in st.session_state:
    st.session_state.selected_landmark = None
if 'show_heatmap' not in st.session_state:
    st.session_state.show_heatmap = False

# Title and description
st.title("🗺️ Local Landmarks Explorer")
st.markdown("""
Explore landmarks in your area with information from Wikipedia. 
Pan and zoom the map to discover new locations!
""")

# Sidebar controls
st.sidebar.header("Map Controls")

# Layer toggles
show_heatmap = st.sidebar.checkbox("Show Heatmap", value=st.session_state.show_heatmap)
st.session_state.show_heatmap = show_heatmap

# Filters
st.sidebar.header("Filters")
search_term = st.sidebar.text_input("Search landmarks", "")
min_rating = st.sidebar.slider("Minimum relevance score", 0.0, 1.0, 0.3)
radius_km = st.sidebar.number_input("Show distance circle (km)", min_value=0.0, max_value=50.0, value=0.0, step=0.5)

# Custom location
st.sidebar.header("Custom Location")
custom_lat = st.sidebar.number_input("Latitude", value=st.session_state.map_center[0], format="%.4f")
custom_lon = st.sidebar.number_input("Longitude", value=st.session_state.map_center[1], format="%.4f")

if st.sidebar.button("Go to Location"):
    st.session_state.map_center = [custom_lat, custom_lon]
    st.session_state.zoom_level = 12
    # Update URL parameters
    st.query_params['center'] = f"{custom_lat},{custom_lon}"
    st.query_params['zoom'] = str(st.session_state.zoom_level)

# Main map container
map_col, info_col = st.columns([2, 1])

with map_col:
    try:
        # Create base map
        m = create_base_map()

        # Add landmarks to map
        if st.session_state.landmarks:
            add_landmarks_to_map(m, st.session_state.landmarks, show_heatmap)

        # Add distance circle if radius is set
        if radius_km > 0:
            draw_distance_circle(m, tuple(st.session_state.map_center), radius_km)

        # Display map with stable key and include center in returned objects
        map_data = st_folium(
            m,
            width=800,
            height=600,
            key="landmark_explorer",
            returned_objects=["bounds", "center", "zoom"]
        )

        # Map data handling functions
        def safe_float(value, default=0.0):
            """Safely convert value to float with fallback"""
            try:
                if value is not None:
                    return float(value)
                return default
            except (ValueError, TypeError):
                return default

        # Handle map state updates
        if isinstance(map_data, dict):
            # Update center if changed
            center_data = map_data.get("center")
            if isinstance(center_data, dict):
                lat = safe_float(center_data.get("lat"), st.session_state.map_center[0])
                lng = safe_float(center_data.get("lng"), st.session_state.map_center[1])
                st.session_state.map_center = [lat, lng]
                # Update URL parameters
                st.query_params['center'] = f"{lat},{lng}"
                st.query_params['zoom'] = str(st.session_state.zoom_level)

            # Update zoom level if changed
            zoom = map_data.get("zoom")
            if zoom is not None:
                st.session_state.zoom_level = int(zoom)
                # Update URL parameters
                st.query_params['center'] = f"{st.session_state.map_center[0]},{st.session_state.map_center[1]}"
                st.query_params['zoom'] = str(zoom)

            # Handle bounds updates if available
            bounds = map_data.get("bounds")
            if isinstance(bounds, dict):
                sw = bounds.get("_southWest", {})
                ne = bounds.get("_northEast", {})

                if (isinstance(sw, dict) and isinstance(ne, dict)):
                    new_bounds = (
                        safe_float(sw.get("lat")),
                        safe_float(sw.get("lng")),
                        safe_float(ne.get("lat")),
                        safe_float(ne.get("lng"))
                    )

                    # Only update if we have valid bounds
                    if all(isinstance(x, float) for x in new_bounds):
                        # Update landmarks if bounds changed significantly
                        if (st.session_state.last_bounds is None or
                            new_bounds != st.session_state.last_bounds):
                            try:
                                from cache_manager import get_cached_landmarks
                                landmarks = get_cached_landmarks(new_bounds, st.session_state.zoom_level)
                                if landmarks:
                                    st.session_state.landmarks = landmarks
                                    st.session_state.last_bounds = new_bounds
                            except Exception as e:
                                st.error(f"Error fetching landmarks: {str(e)}")

    except Exception as e:
        st.error(f"Error rendering map: {str(e)}")

with info_col:
    # Filter landmarks based on search and rating
    filtered_landmarks = [
        l for l in st.session_state.landmarks
        if (search_term.lower() in l['title'].lower() or not search_term)
        and l['relevance'] >= min_rating
    ]

    st.subheader(f"Found {len(filtered_landmarks)} Landmarks")

    # Display landmarks
    for landmark in filtered_landmarks:
        with st.expander(landmark['title']):
            st.markdown(f"""
            <div style='background-color: #f0f2f6; padding: 1rem; border-radius: 0.5rem;'>
                <h3 style='margin-top: 0;'>{landmark['title']}</h3>
                <p><strong>🎯 Relevance:</strong> {landmark['relevance']:.2f}</p>
                <p><strong>📍 Distance:</strong> {landmark['distance']:.1f}km</p>
                <p>{landmark['summary']}</p>
                <a href='{landmark['url']}' target='_blank'>Read more on Wikipedia</a>
            </div>
            """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
Data sourced from Wikipedia. Updates automatically as you explore the map.
* 🔴 Red markers: High relevance landmarks
* 🟠 Orange markers: Medium relevance landmarks
* 🔵 Blue markers: Lower relevance landmarks
""")

def get_cached_landmarks(bounds, zoom_level):
    # Placeholder - Replace with actual caching logic using bounds and zoom level
    try:
        return cache_landmarks(bounds) #Fallback to original if new caching fails.
    except:
        return []