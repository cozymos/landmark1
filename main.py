import streamlit as st
import folium
from streamlit_folium import st_folium
from wiki_handler import WikiLandmarkFetcher
from map_utils import create_base_map, draw_distance_circle, add_landmarks_to_map
from cache_manager import cache_landmarks
import time

# Page config
st.set_page_config(
    page_title="Local Landmarks Explorer",
    page_icon="🗺️",
    layout="wide"
)

# Initialize session state
if 'last_bounds' not in st.session_state:
    st.session_state.last_bounds = None
if 'landmarks' not in st.session_state:
    st.session_state.landmarks = []
if 'selected_landmark' not in st.session_state:
    st.session_state.selected_landmark = None
if 'show_heatmap' not in st.session_state:
    st.session_state.show_heatmap = False
if 'map_center' not in st.session_state:
    st.session_state.map_center = [37.7749, -122.4194]

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
if show_heatmap != st.session_state.show_heatmap:
    st.session_state.show_heatmap = show_heatmap
    st.rerun()

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
    st.rerun()

# Main map container
map_col, info_col = st.columns([2, 1])

with map_col:
    # Create base map
    m = folium.Map(
        location=st.session_state.map_center,
        zoom_start=12,
        tiles='OpenStreetMap',
        control_scale=True
    )

    # Add current landmarks to map if available
    if st.session_state.landmarks:
        add_landmarks_to_map(m, st.session_state.landmarks, st.session_state.show_heatmap)

    # Display map using st_folium
    map_data = st_folium(
        m,
        width=800,
        height=600,
        returned_objects=["bounds", "last_clicked"]
    )

    # Process map bounds
    if (map_data and 
        isinstance(map_data, dict) and 
        "bounds" in map_data and 
        map_data["bounds"]):

        bounds_data = map_data["bounds"]
        if (isinstance(bounds_data, dict) and 
            "_southWest" in bounds_data and 
            "_northEast" in bounds_data):

            sw = bounds_data["_southWest"]
            ne = bounds_data["_northEast"]

            if (sw and ne and 
                isinstance(sw, dict) and isinstance(ne, dict) and
                all(key in sw for key in ["lat", "lng"]) and 
                all(key in ne for key in ["lat", "lng"])):

                bounds = (
                    float(sw["lat"]),
                    float(sw["lng"]),
                    float(ne["lat"]),
                    float(ne["lng"])
                )

                # Only fetch new landmarks if bounds changed
                if bounds != st.session_state.last_bounds:
                    with st.spinner("Fetching landmarks..."):
                        landmarks = cache_landmarks(bounds)
                        st.session_state.landmarks = landmarks
                        st.session_state.last_bounds = bounds
                        st.rerun()

    # Handle clicked location
    if (map_data and 
        isinstance(map_data, dict) and 
        "last_clicked" in map_data and 
        map_data["last_clicked"]):

        clicked_data = map_data["last_clicked"]
        if (isinstance(clicked_data, dict) and 
            "lat" in clicked_data and 
            "lng" in clicked_data):

            clicked_lat = clicked_data["lat"]
            clicked_lon = clicked_data["lng"]

            if radius_km > 0:
                draw_distance_circle(m, (clicked_lat, clicked_lon), radius_km)

with info_col:
    # Filter landmarks based on search and rating
    filtered_landmarks = [
        l for l in st.session_state.landmarks
        if (search_term.lower() in l['title'].lower() or not search_term) 
        and l['relevance'] >= min_rating
    ]

    st.subheader(f"Found {len(filtered_landmarks)} Landmarks")

    # Display landmarks with enhanced cards
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

            # Add buttons for interaction
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"Show Distance Circle ({landmark['title']})", key=f"circle_{landmark['title']}"):
                    draw_distance_circle(m, landmark['coordinates'], radius_km if radius_km > 0 else 1.0)
            with col2:
                if st.button(f"Center Map ({landmark['title']})", key=f"center_{landmark['title']}"):
                    st.session_state.map_center = list(landmark['coordinates'])
                    st.rerun()

# Footer
st.markdown("---")
st.markdown("""
Data sourced from Wikipedia. Updates automatically as you explore the map.
* 🔴 Red markers: High relevance landmarks
* 🟠 Orange markers: Medium relevance landmarks
* 🔵 Blue markers: Lower relevance landmarks
""")