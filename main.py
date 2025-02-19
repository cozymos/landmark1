# Page config must come first
import streamlit as st

st.set_page_config(page_title="Landmarks Locator",
                   page_icon="🗺️",
                   layout="wide")

import folium
from streamlit_folium import st_folium
from map_utils import draw_distance_circle, add_landmarks_to_map
from cache_manager import OfflineCacheManager
import time
import math
from urllib.parse import quote, unquote
from coord_utils import parse_coordinates, format_dms
from typing import Tuple, List, Dict

# Update CSS for basic styling only
st.markdown("""
<style>
    /* Make the map container take up more space */
    .stfolium-container {
        width: 100% !important;
        margin-bottom: 24px;
    }
    /* Compact sidebar content */
    .sidebar .element-container {
        margin-bottom: 0.5rem;
    }
</style>
""",
            unsafe_allow_html=True)

# Add debounce time to session state
if 'last_update_time' not in st.session_state:
    st.session_state.last_update_time = 0

# Initialize session state with URL parameters if available
if 'map_center' not in st.session_state:
    try:
        center_str = st.query_params.get('center', '37.7749,-122.4194')
        lat, lon = map(float, center_str.split(','))
        st.session_state.map_center = [lat, lon]
    except:
        st.session_state.map_center = [37.7749,
                                       -122.4194]  # Default to San Francisco

if 'zoom_level' not in st.session_state:
    try:
        st.session_state.zoom_level = int(st.query_params.get('zoom', '12'))
    except:
        st.session_state.zoom_level = 12

if 'last_bounds' not in st.session_state:
    st.session_state.last_bounds = None
if 'landmarks' not in st.session_state:
    st.session_state.landmarks = []
if 'show_circle' not in st.session_state:
    st.session_state.show_circle = False
if 'offline_mode' not in st.session_state:
    st.session_state.offline_mode = False
if 'last_data_source' not in st.session_state:
    st.session_state.last_data_source = "Wikipedia"  # Changed default to Wikipedia

# Initialize cache manager
cache_manager = OfflineCacheManager()

# Initialize velocity tracking in session state if not present
if 'last_position' not in st.session_state:
    st.session_state.last_position = st.session_state.map_center
if 'last_velocity' not in st.session_state:
    st.session_state.last_velocity = 0


def get_landmarks(bounds: Tuple[float, float, float, float],
                  zoom_level: int,
                  data_source: str = 'Wikipedia') -> List[Dict]:
    """
    Fetch and cache landmarks for the given area
    """
    try:
        # If we're offline, try to get cached data
        if st.session_state.offline_mode:
            return cache_manager.get_cached_landmarks(bounds)

        # Only fetch new landmarks if zoom level is appropriate
        if zoom_level >= 8:  # Prevent fetching at very low zoom levels
            landmarks = []

            if data_source == "Wikipedia":
                from wiki_handler import WikiLandmarkFetcher
                wiki_fetcher = WikiLandmarkFetcher()
                landmarks = wiki_fetcher.get_landmarks(bounds)
            else:  # Google Places
                from google_places import GooglePlacesHandler
                places_handler = GooglePlacesHandler()
                landmarks = places_handler.get_landmarks(bounds)

            # Cache the landmarks for offline use
            if landmarks:
                cache_manager.cache_landmarks(landmarks, bounds)

            return landmarks
        else:
            return cache_manager.get_cached_landmarks(bounds)

    except Exception as e:
        st.error(f"Error fetching landmarks: {str(e)}")
        if st.session_state.offline_mode:
            return cache_manager.get_cached_landmarks(bounds)
        return []


st.sidebar.header("🗺️ Landmarks Locator")
st.session_state.show_circle = st.sidebar.checkbox(
    "Show Location", value=st.session_state.show_circle)
radius_km = 1 if st.session_state.show_circle else 0
try:
    # Create base map
    m = folium.Map(location=st.session_state.map_center,
                   zoom_start=st.session_state.zoom_level,
                   tiles=cache_manager.get_tile_url(),
                   attr="OpenStreetMap"
                   if st.session_state.offline_mode else "Google Maps",
                   control_scale=True,
                   prefer_canvas=True)

    # Add landmarks and distance circle if we have data
    if st.session_state.landmarks:
        add_landmarks_to_map(m, st.session_state.landmarks, False)
        if radius_km > 0:
            # Ensure center is passed as a proper tuple of two floats
            center = (float(st.session_state.map_center[0]),
                      float(st.session_state.map_center[1]))
            draw_distance_circle(m, center, radius_km)

    # Display map with minimal returned objects
    map_data = st_folium(
        m,
        width=None,  # Let it take full width
        height=600,
        key="landmark_locator",
        returned_objects=["center", "zoom"])

    # Handle map interactions with optimized updates
    if isinstance(map_data, dict):
        center_data = map_data.get("center")
        new_zoom = map_data.get("zoom")
        current_time = time.time()
        time_delta = current_time - st.session_state.last_update_time

        # Batch updates to reduce state changes
        updates_needed = False

        if isinstance(center_data, dict):
            new_lat = float(
                center_data.get("lat", st.session_state.map_center[0]))
            new_lng = float(
                center_data.get("lng", st.session_state.map_center[1]))

            # Calculate movement velocity
            if time_delta > 0:
                distance = math.sqrt(
                    (new_lat - st.session_state.last_position[0])**2 +
                    (new_lng - st.session_state.last_position[1])**2)
                current_velocity = distance / time_delta
                # Smooth velocity using exponential moving average
                st.session_state.last_velocity = (
                    0.7 * st.session_state.last_velocity +
                    0.3 * current_velocity)

            # Adjust debounce time based on velocity
            min_debounce = 0.2  # Minimum debounce time in seconds
            max_debounce = 2.0  # Maximum debounce time in seconds
            velocity_factor = 1.0 / (1 + st.session_state.last_velocity * 10
                                     )  # Adjust multiplier as needed
            debounce_time = min_debounce + (max_debounce -
                                            min_debounce) * velocity_factor

            # Check if enough time has passed since last update
            if time_delta >= debounce_time:
                # Check if center changed significantly
                if abs(new_lat - st.session_state.map_center[0]) > 0.001 or \
                   abs(new_lng - st.session_state.map_center[1]) > 0.001:
                    st.session_state.map_center = [new_lat, new_lng]
                    st.session_state.last_position = [new_lat, new_lng]
                    updates_needed = True

        # Update zoom if changed
        if new_zoom is not None and new_zoom != st.session_state.zoom_level:
            st.session_state.zoom_level = int(new_zoom)
            updates_needed = True

        # Only fetch new landmarks if significant changes occurred
        if updates_needed:
            # Update URL parameters in batch
            st.query_params.update({
                'center':
                f"{st.session_state.map_center[0]},{st.session_state.map_center[1]}",
                'zoom': str(st.session_state.zoom_level)
            })

            # Calculate bounds only when needed
            zoom_factor = 360 / (2**st.session_state.zoom_level)
            new_bounds = (
                st.session_state.map_center[0] -
                zoom_factor * 0.3,  # Reduced view area
                st.session_state.map_center[1] - zoom_factor * 0.4,
                st.session_state.map_center[0] + zoom_factor * 0.3,
                st.session_state.map_center[1] + zoom_factor * 0.4)

            # Check if bounds changed enough to warrant new data
            if st.session_state.last_bounds is None or \
               any(abs(a - b) > zoom_factor * 0.1 for a, b in zip(new_bounds, st.session_state.last_bounds)):
                try:
                    landmarks = get_landmarks(
                        new_bounds,
                        st.session_state.zoom_level,
                        data_source=st.session_state.last_data_source)
                    if landmarks:
                        st.session_state.landmarks = landmarks
                        st.session_state.last_bounds = new_bounds
                except Exception as e:
                    st.error(f"Error fetching landmarks: {str(e)}")

            st.session_state.last_update_time = current_time

except Exception as e:
    st.error(f"Error rendering map: {str(e)}")

# Display landmarks
landmarks_expander = st.sidebar.expander(
    f"View {len(st.session_state.landmarks)} Landmarks", expanded=False)
with landmarks_expander:
    for landmark in st.session_state.landmarks:
        with st.container():
            # Display the landmark image if available
            if 'image_url' in landmark:
                st.image(landmark['image_url'],
                         caption=f"[{landmark['title']}]({landmark['url']})",
                         use_container_width=True)

# Custom location
st.sidebar.markdown("---")

# Add combined coordinates input
combined_coords = st.sidebar.text_input(
    "Custom Location",
    help="Enter coordinates in either format:\n" +
    "• Decimal Degrees (DD): 37.3349, -122.0090\n" +
    "• DMS: 37°20'5.64\"N, 122°0'32.40\"W",
    placeholder="Enter coordinates (DD or DMS)",
    key="combined_coords")

# Initialize coordinate values
custom_lat = None
custom_lon = None
coords_valid = False

if combined_coords:
    coords = parse_coordinates(combined_coords)
    if coords:
        custom_lat = coords.lat
        custom_lon = coords.lon
        coords_valid = True
        st.sidebar.success(f"""
        ✅ Valid coordinates:
        • DD: {custom_lat:.4f}, {custom_lon:.4f}
        • DMS: {format_dms(custom_lat, True)}, {format_dms(custom_lon, False)}
        """)
    else:
        st.sidebar.error(
            "Invalid coordinate format. Please use DD or DMS format.")

# Separate lat/lon inputs with synced values
lat_input = st.sidebar.number_input(
    "Latitude",
    value=float(custom_lat if custom_lat is not None else st.session_state.
                map_center[0]),
    format="%.4f",
    help="Decimal degrees (e.g., 37.3349)",
    key="lat_input")

lon_input = st.sidebar.number_input(
    "Longitude",
    value=float(custom_lon if custom_lon is not None else st.session_state.
                map_center[1]),
    format="%.4f",
    help="Decimal degrees (e.g., -122.0090)",
    key="lon_input")

# Update values from separate inputs if combined input is empty
if not combined_coords:
    custom_lat = lat_input
    custom_lon = lon_input
    # Show both formats for separate input values
    if -90 <= lat_input <= 90 and -180 <= lon_input <= 180:
        st.sidebar.success(f"""
        ✅ Current coordinates:
        • DD: {custom_lat:.4f}, {custom_lon:.4f}
        • DMS: {format_dms(custom_lat, True)}, {format_dms(custom_lon, False)}
        """)

if st.sidebar.button("Go to Location"):
    if custom_lat is not None and custom_lon is not None and -90 <= custom_lat <= 90 and -180 <= custom_lon <= 180:
        st.session_state.map_center = [custom_lat, custom_lon]
        st.session_state.zoom_level = 12
        # Update URL parameters
        st.query_params['center'] = f"{custom_lat},{custom_lon}"
        st.query_params['zoom'] = str(st.session_state.zoom_level)
    else:
        st.sidebar.error(
            "Invalid coordinates. Latitude must be between -90 and 90, longitude between -180 and 180."
        )

st.sidebar.header("Map Controls")

# Offline Mode Toggle
offline_mode = st.sidebar.checkbox("📱 Offline Mode",
                                   value=st.session_state.offline_mode)
if offline_mode != st.session_state.offline_mode:
    st.session_state.offline_mode = offline_mode
    if offline_mode:
        st.sidebar.info("🔄 Offline mode enabled. Using cached map data.")
    else:
        st.sidebar.info("🌐 Online mode enabled. Fetching live data.")

# Add cache management controls
if st.session_state.offline_mode:
    st.sidebar.header("📦 Cache Management")

    # Display cache statistics
    cache_stats = cache_manager.get_cache_stats()
    st.sidebar.markdown(f"""
    **Cache Statistics:**
    - 📍 Landmarks: {cache_stats['landmarks_cached']}
    - 🖼️ Images: {cache_stats['images_cached']}
    - 🕒 Last Update: {cache_stats['last_update'] or 'Never'}
    """)

    # Cache management buttons
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("🔄 Update Cache"):
            # Force a cache update for current view
            if st.session_state.last_bounds:
                landmarks = get_landmarks(
                    st.session_state.last_bounds,
                    st.session_state.zoom_level,
                    data_source=st.session_state.last_data_source)
                if landmarks:
                    st.session_state.landmarks = landmarks
                    st.success("Cache updated successfully!")
    with col2:
        if st.button("🗑️ Clear Old Cache"):
            cache_manager.clear_old_cache()

# Update data source handling and trigger landmark refresh when changed
data_source = st.sidebar.radio(
    "Choose Landmarks Data Source",
    options=["Wikipedia", "Google Places"],
    help="Select where to fetch landmark information from",
    key="data_source")

if data_source != st.session_state.last_data_source:
    st.session_state.last_data_source = data_source
    # Force refresh of landmarks with new data source
    if st.session_state.last_bounds:
        try:
            landmarks = get_landmarks(st.session_state.last_bounds,
                                      st.session_state.zoom_level,
                                      data_source=data_source)
            if landmarks:
                st.session_state.landmarks = landmarks
            else:
                st.error("No landmarks found with selected data source.")
        except Exception as e:
            st.error(f"Error fetching landmarks: {str(e)}")
    st.rerun()

# Footer
st.markdown("---")
