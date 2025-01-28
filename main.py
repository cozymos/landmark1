import streamlit as st
import folium
from streamlit_folium import st_folium
from google_places import GooglePlacesHandler
from map_utils import create_base_map, draw_distance_circle, add_landmarks_to_map
from cache_manager import get_cached_landmarks
import time
from urllib.parse import quote, unquote
import json
from journey_tracker import JourneyTracker
import hashlib
import os
from recommender import LandmarkRecommender

# Page config
st.set_page_config(
    page_title="Local Landmarks Explorer",
    page_icon="🗺️",
    layout="wide"
)

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
if 'journey_tracker' not in st.session_state:
    st.session_state.journey_tracker = JourneyTracker()
if 'recommender' not in st.session_state:
    st.session_state.recommender = LandmarkRecommender()

# CSS styling for recommendations
st.markdown("""
<style>
    .recommended-image {
        width: 100%;
        height: 200px;
        object-fit: cover;
        border-radius: 10px;
        margin: 10px 0;
    }
    .recommendation-card {
        padding: 10px;
        border-radius: 10px;
        background-color: #f0f2f6;
        margin: 5px;
        height: 100%;
    }
</style>
""", unsafe_allow_html=True)

# Title and description
st.title("🗺️ Local Landmarks Explorer")
st.markdown("""
Explore landmarks in your area with information from Google Places. 
Pan and zoom the map to discover new locations!
""")

# Recommendations section
st.markdown("### 🎯 Recommended Landmarks")
if st.session_state.landmarks:
    recommendations = st.session_state.recommender.get_recommendations(
        st.session_state.landmarks,
        st.session_state.map_center
    )

    if recommendations:
        rec_cols = st.columns(len(recommendations))
        for i, landmark in enumerate(recommendations):
            with rec_cols[i]:
                st.markdown(f"""
                <div class="recommendation-card">
                    <h4>{landmark['title']}</h4>
                    {'<img src="' + landmark['image_url'] + '" class="recommended-image">' if 'image_url' in landmark else ''}
                    <p>Score: {landmark['personalized_score']:.2f}</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button("👍 Favorite", key=f"fav_{i}_{landmark['title']}"):
                    is_favorite = st.session_state.recommender.toggle_favorite(
                        str(landmark['coordinates'])
                    )
                    if is_favorite:
                        st.success("Added to favorites!")
                    else:
                        st.info("Removed from favorites")


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

# Journey Progress
st.sidebar.markdown("---")
st.sidebar.header("🗺️ Journey Progress")

# Get current progress
progress = st.session_state.journey_tracker.get_progress()
total_discovered = progress["total_discovered"]

# Show progress metrics
st.sidebar.metric("Landmarks Discovered", total_discovered)

# Show achievements
if progress["achievements"]:
    st.sidebar.subheader("🏆 Achievements")
    for achievement in progress["achievements"]:
        st.sidebar.markdown(f"{achievement.icon} **{achievement.name}**")
        st.sidebar.caption(achievement.description)

# Show next achievement
if progress["next_achievement"]:
    next_achievement = progress["next_achievement"]
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 Next Achievement")
    st.sidebar.markdown(f"{next_achievement.icon} **{next_achievement.name}**")
    st.sidebar.caption(next_achievement.description)
    st.sidebar.progress(min(total_discovered / next_achievement.requirement, 1.0))

# Main map container
map_col, info_col = st.columns([2, 1])

with map_col:
    try:
        # Create base map with Google Maps tiles
        m = folium.Map(
            location=st.session_state.map_center,
            zoom_start=st.session_state.zoom_level,
            tiles=f"https://mt1.google.com/vt/lyrs=m&x={{x}}&y={{y}}&z={{z}}&key={os.environ['GOOGLE_MAPS_API_KEY']}",
            attr="Google Maps",
            control_scale=True,
            prefer_canvas=True
        )

        # Add landmarks and distance circle only if we have data
        if st.session_state.landmarks:
            add_landmarks_to_map(m, st.session_state.landmarks, show_heatmap)
            if radius_km > 0:
                draw_distance_circle(m, tuple(st.session_state.map_center), radius_km)

        # Display map with minimal returned objects and reduced updates
        map_data = st_folium(
            m,
            width=800,
            height=600,
            key="landmark_explorer",
            returned_objects=["center", "zoom"]
        )

        # Handle map interactions with optimized updates
        if isinstance(map_data, dict) and time.time() - st.session_state.last_update_time > 1.0:  # 1 second debounce
            center_data = map_data.get("center")
            new_zoom = map_data.get("zoom")

            # Batch updates to reduce state changes
            updates_needed = False

            if isinstance(center_data, dict):
                new_lat = float(center_data.get("lat", st.session_state.map_center[0]))
                new_lng = float(center_data.get("lng", st.session_state.map_center[1]))

                # Check if center changed significantly
                if abs(new_lat - st.session_state.map_center[0]) > 0.001 or \
                   abs(new_lng - st.session_state.map_center[1]) > 0.001:
                    st.session_state.map_center = [new_lat, new_lng]
                    updates_needed = True

            # Update zoom if changed
            if new_zoom is not None and new_zoom != st.session_state.zoom_level:
                st.session_state.zoom_level = int(new_zoom)
                updates_needed = True

            # Only fetch new landmarks if significant changes occurred
            if updates_needed:
                # Update URL parameters in batch
                st.query_params.update({
                    'center': f"{st.session_state.map_center[0]},{st.session_state.map_center[1]}",
                    'zoom': str(st.session_state.zoom_level)
                })

                # Calculate bounds only when needed
                zoom_factor = 360 / (2 ** st.session_state.zoom_level)
                new_bounds = (
                    st.session_state.map_center[0] - zoom_factor * 0.3,  # Reduced view area
                    st.session_state.map_center[1] - zoom_factor * 0.4,
                    st.session_state.map_center[0] + zoom_factor * 0.3,
                    st.session_state.map_center[1] + zoom_factor * 0.4
                )

                # Check if bounds changed enough to warrant new data
                if st.session_state.last_bounds is None or \
                   any(abs(a - b) > zoom_factor * 0.1 for a, b in zip(new_bounds, st.session_state.last_bounds)):
                    try:
                        landmarks = get_cached_landmarks(new_bounds, st.session_state.zoom_level)
                        if landmarks:
                            st.session_state.landmarks = landmarks
                            st.session_state.last_bounds = new_bounds
                    except Exception as e:
                        st.error(f"Error fetching landmarks: {str(e)}")

                st.session_state.last_update_time = time.time()

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

    # Display landmarks with discovery tracking
    def process_landmark_discovery(landmark):
        """Process landmark discovery and handle animations"""
        # Create unique ID for landmark
        landmark_id = hashlib.md5(f"{landmark['title']}:{landmark['coordinates']}".encode()).hexdigest()

        # Check if this is a new discovery
        discovery_info = st.session_state.journey_tracker.add_discovery(landmark_id, landmark['title'])

        if discovery_info["is_new"]:
            # Show discovery animation
            st.balloons()

            # Show achievement notifications
            for achievement in discovery_info.get("new_achievements", []):
                st.success(f"🎉 Achievement Unlocked: {achievement.icon} {achievement.name}")
                st.toast(f"New Achievement: {achievement.name}")

    # Display landmarks
    for landmark in filtered_landmarks:
        with st.expander(landmark['title']):
            process_landmark_discovery(landmark)

            # Record interaction with landmark
            st.session_state.recommender.record_interaction(
                str(landmark['coordinates']),
                landmark.get('type', 'landmark')
            )

            # Display the landmark image if available
            if 'image_url' in landmark:
                st.image(landmark['image_url'], caption=landmark['title'], use_container_width=True)

            st.markdown(f"""
            <div style='background-color: #f0f2f6; padding: 1rem; border-radius: 0.5rem;'>
                <h3 style='margin-top: 0;'>{landmark['title']}</h3>
                <p><strong>🎯 Relevance:</strong> {landmark['relevance']:.2f}</p>
                <p><strong>📍 Distance:</strong> {landmark['distance']:.1f}km</p>
                <p>{landmark['summary']}</p>
                <a href='{landmark['url']}' target='_blank'>Read more on Google Places</a>
            </div>
            """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
Data sourced from Google Places. Updates automatically as you explore the map.
* 🔴 Red markers: High relevance landmarks
* 🟠 Orange markers: Medium relevance landmarks
* 🔵 Blue markers: Lower relevance landmarks
""")

def get_cached_landmarks(bounds, zoom_level):
    # Placeholder - Replace with actual caching logic using bounds and zoom level
    try:
        return cache_landmarks(bounds)
    except:
        return []