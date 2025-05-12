import streamlit as st
from typing import Tuple, List, Dict
from components.map_viewer import render_map
from utils.coord_utils import parse_coordinates
from utils.config_utils import is_test_mode_enabled, enable_test_mode
from components.cache_manager import cache_manager
import logging

logger = logging.getLogger("main")
logger.debug("*** RERUN ***")

st.set_page_config(
    page_title="Landmarks Locator",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Update CSS for width and margins only
st.markdown(
    """
<style>
    .block-container {
        padding-top: 3rem;
        padding-bottom: 0;
        max-width: 100%;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Initialize session state with URL parameters if available
if "map_center" not in st.session_state:
    center_str = st.query_params.get("center", "37.7749,-122.4194")
    lat, lon = map(float, center_str.split(","))
    st.session_state.map_center = [lat, lon]
if "new_center" not in st.session_state:
    st.session_state.new_center = st.session_state.map_center

if "zoom_level" not in st.session_state:
    st.session_state.zoom_level = int(st.query_params.get("zoom", "12"))
if "new_zoom" not in st.session_state:
    st.session_state.new_zoom = st.session_state.zoom_level

# Initialize radius in session state if not present
if "radius" not in st.session_state:
    st.session_state.radius = 5  # Default 5km radius
if "landmarks" not in st.session_state:
    st.session_state.landmarks = []
if "last_data_source" not in st.session_state:
    st.session_state.last_data_source = "Test Mode"  # Default to Test Mode


def get_landmarks(
    center_coords: Tuple[float, float],
    radius_km: float,
    zoom_level: int,
    data_source: str = "Google Places",
) -> List[Dict]:
    """
    Fetch and cache landmarks near the specified center within the given radius

    Args:
        center_coords: (lat, lon) tuple for the center point
        radius_km: Radius in kilometers to search within
        zoom_level: Current map zoom level (used for caching decisions)
        data_source: Source of landmark data ("Google Places" or "Test Mode")

    Returns:
        List of landmark dictionaries
    """
    try:
        # Check cache first
        landmarks = cache_manager.get_cached_landmarks(center_coords, radius_km)
        if landmarks:
            return landmarks

        # If test mode is selected as data source, don't make API calls
        if data_source == "Test Mode":
            # Force enable test mode for this request
            from utils.config_utils import enable_test_mode

            enable_test_mode()

        # Use Google Places API
        from components.google_places import GooglePlacesHandler

        places_handler = GooglePlacesHandler()
        landmarks = places_handler.get_landmarks(center_coords, radius_km)

        # Cache the landmarks for offline use
        if landmarks:
            cache_manager.cache_landmarks(landmarks, center_coords, radius_km)

        return landmarks

    except Exception as e:
        st.error(f"Error fetching landmarks: {str(e)}")
        return []


def update_landmarks():
    """Update landmarks for the current map view."""
    st.session_state.map_center = st.session_state.new_center
    st.session_state.zoom_level = st.session_state.new_zoom

    # Get radius from UI or calculate based on zoom
    radius_km = (
        st.session_state.radius
        if st.session_state.radius > 0
        else max(1, 20 - st.session_state.zoom_level)
    )

    try:
        with st.spinner("Fetching landmarks..."):
            landmarks = get_landmarks(
                center_coords=st.session_state.map_center,
                radius_km=radius_km,
                zoom_level=st.session_state.zoom_level,
                data_source=st.session_state.last_data_source,
            )
            if landmarks:
                st.session_state.landmarks = landmarks

        # Update URL parameters
        new_lat = st.session_state.new_center[0]
        new_lng = st.session_state.new_center[1]
        st.query_params["center"] = f"{new_lat},{new_lng}"
        st.query_params["zoom"] = str(st.session_state.new_zoom)
    except Exception as e:
        st.error(f"Error fetching landmarks: {str(e)}")


# Show circle control
st.session_state.radius = st.sidebar.number_input(
    "Show distance circle (km)",
    min_value=0,
    max_value=20,
    value=st.session_state.get("radius", 0),
    step=1,
)

coord_input = st.sidebar.text_input(
    "Custom Location",
    help="Enter coordinates in either format:\n"
    + "• Decimal Degrees (DD): 37.3349, -122.0090\n"
    + "• DMS: 37°20'5.64\"N, 122°0'32.40\"W",
    label_visibility="collapsed",
    placeholder="Custom location (DD/DMS)",
    key="coord_input",
)

if coord_input:
    coords = parse_coordinates(coord_input)
    if coords:
        if st.sidebar.button("Go to Location"):
            st.session_state.map_center = [coords.lat, coords.lon]
            st.session_state.zoom_level = 12
            # Update URL parameters
            st.query_params["center"] = f"{coords.lat},{coords.lon}"
            st.query_params["zoom"] = str(st.session_state.zoom_level)
            st.rerun()
    else:
        st.sidebar.error(
            "Invalid coordinate format. Please use DD or DMS format."
        )

try:
    map_data = render_map(
        center=st.session_state.map_center, zoom=st.session_state.zoom_level
    )
    # Handle map interactions
    if map_data and isinstance(map_data, dict):
        # Update center and zoom
        center_data = map_data.get("center")
        new_zoom = map_data.get("zoom")

        if isinstance(center_data, dict):
            new_lat = float(
                center_data.get("lat", st.session_state.map_center[0])
            )
            new_lng = float(
                center_data.get("lng", st.session_state.map_center[1])
            )
            st.session_state.new_center = [new_lat, new_lng]

        # Handle zoom changes without forcing refresh
        if new_zoom is not None:
            new_zoom = int(
                float(new_zoom)
            )  # Convert to float first to handle any decimal values
            if new_zoom != st.session_state.zoom_level:
                st.session_state.new_zoom = new_zoom

    if st.sidebar.button("🔍 Search Landmarks", type="primary"):
        update_landmarks()
        st.rerun()

except Exception as e:
    st.error(f"Error rendering map: {str(e)}")

# Display landmarks
landmarks_expander = st.sidebar.expander(
    f"View {len(st.session_state.landmarks)} Landmarks", expanded=False
)
with landmarks_expander:
    for landmark in st.session_state.landmarks:
        with st.container():
            # Display the landmark image if available
            if "image_url" in landmark:
                st.image(
                    landmark["image_url"],
                    caption=f"[{landmark['title']}]({landmark['url']})",
                    use_container_width=True,
                )

# Update data source handling
data_source = st.sidebar.radio(
    "Choose Data Source",
    options=["Test Mode", "Google Places"],
    help="Select where to fetch landmark information from. Test Mode uses sample data without API calls.",
    key="data_source",
    index=0,  # Default to Test Mode
)

# Store the selected data source
st.session_state.last_data_source = data_source
