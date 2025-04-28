# Page config must come first
import streamlit as st

st.set_page_config(
    page_title="Landmarks Locator",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded",
)

from typing import Tuple, List, Dict
from components.map_viewer import render_map
from utils.coord_utils import parse_coordinates
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(name)s:%(levelname)s: %(message)s"
)
logger = logging.getLogger("main")
logger.debug("*** RERUN ***")

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

# Initialize cache manager as a singleton
from components.cache_manager import get_cache_manager_instance

# Get the singleton instance - will only be created once
cache_manager = get_cache_manager_instance()

# Initialize session state with URL parameters if available
if "map_center" not in st.session_state:
    try:
        center_str = st.query_params.get("center", "37.7749,-122.4194")
        lat, lon = map(float, center_str.split(","))
        st.session_state.map_center = [lat, lon]
    except:
        st.session_state.map_center = [
            37.7749,
            -122.4194,
        ]  # Default to San Francisco
if "new_center" not in st.session_state:
    st.session_state.new_center = st.session_state.map_center

if "zoom_level" not in st.session_state:
    try:
        st.session_state.zoom_level = int(st.query_params.get("zoom", "12"))
    except:
        st.session_state.zoom_level = 12
if "new_zoom" not in st.session_state:
    st.session_state.new_zoom = st.session_state.zoom_level

if "current_bounds" not in st.session_state:
    st.session_state.current_bounds = None
if "last_bounds" not in st.session_state:
    st.session_state.last_bounds = None
if "landmarks" not in st.session_state:
    st.session_state.landmarks = []
if "last_data_source" not in st.session_state:
    st.session_state.last_data_source = "Wikipedia"  # Default to Wikipedia


def get_landmarks(
    bounds: Tuple[float, float, float, float],
    zoom_level: int,
    data_source: str = "Wikipedia",
) -> List[Dict]:
    """
    Fetch and cache landmarks for the given area
    """
    try:
        landmarks = cache_manager.get_cached_landmarks(bounds)
        if landmarks:
            return landmarks

        if data_source == "Wikipedia":
            from utils.wiki_handler import WikiLandmarkFetcher

            wiki_fetcher = WikiLandmarkFetcher()
            landmarks = wiki_fetcher.get_landmarks(bounds)
        else:  # Google Places
            from utils.google_places import GooglePlacesHandler

            places_handler = GooglePlacesHandler()
            landmarks = places_handler.get_landmarks(bounds)

        # Cache the landmarks for offline use
        if landmarks:
            cache_manager.cache_landmarks(landmarks, bounds)

        return landmarks

    except Exception as e:
        st.error(f"Error fetching landmarks: {str(e)}")
        return []


def update_landmarks():
    """Update landmarks for the current map view."""
    if not st.session_state.current_bounds:
        return

    st.session_state.map_center = st.session_state.new_center
    st.session_state.zoom_level = st.session_state.new_zoom
    bounds = st.session_state.current_bounds
    try:
        with st.spinner("Fetching landmarks..."):
            landmarks = get_landmarks(
                bounds,
                st.session_state.zoom_level,
                data_source=st.session_state.last_data_source,
            )
            if landmarks:
                st.session_state.landmarks = landmarks
                st.session_state.last_bounds = bounds

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
        bounds_data = map_data.get("bounds")

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

        # Update current bounds from map
        if bounds_data:
            st.session_state.current_bounds = (
                bounds_data["_southWest"]["lat"],
                bounds_data["_southWest"]["lng"],
                bounds_data["_northEast"]["lat"],
                bounds_data["_northEast"]["lng"],
            )

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

# Update data source handling and trigger landmark refresh when changed
data_source = st.sidebar.radio(
    "Choose Data Source",
    options=["Wikipedia", "Google Places"],
    help="Select where to fetch landmark information from",
    key="data_source",
)

if data_source != st.session_state.last_data_source:
    st.session_state.last_data_source = data_source
