# Initialize UI and session state
from ui_config import setup_ui
from session_manager import initialize_session_state
from map_manager import MapManager
from sidebar_manager import SidebarManager
from location_handler import LocationHandler
from settings_manager import SettingsManager
from cache_manager import OfflineCacheManager
from ai_handler import LandmarkAIHandler

import streamlit as st
from typing import List, Dict

def get_landmarks(bounds: tuple, zoom_level: int, data_source: str = 'Wikipedia') -> List[Dict]:
    """Fetch landmarks based on current view and settings"""
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

            # Enhance landmarks with AI if enabled
            if landmarks and st.session_state.ai_landmarks and not st.session_state.offline_mode:
                landmarks = [
                    ai_handler.enhance_landmark_description(landmark)
                    for landmark in landmarks
                ]

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

def update_landmarks():
    """Update landmarks for the current map view"""
    if not st.session_state.current_bounds:
        return

    bounds = st.session_state.current_bounds
    try:
        with st.spinner('Fetching landmarks...'):
            landmarks = get_landmarks(
                bounds,
                st.session_state.zoom_level,
                data_source=st.session_state.last_data_source
            )
            if landmarks:
                st.session_state.landmarks = landmarks
                st.session_state.last_bounds = bounds
    except Exception as e:
        st.error(f"Error fetching landmarks: {str(e)}")

def main():
    # Initialize components
    setup_ui()
    initialize_session_state()

    # Initialize managers
    cache_manager = OfflineCacheManager()
    ai_handler = LandmarkAIHandler()
    map_manager = MapManager(cache_manager)
    sidebar_manager = SidebarManager(cache_manager)
    location_handler = LocationHandler()
    settings_manager = SettingsManager()

    # Render sidebar
    sidebar_manager.render_header()
    show_markers, show_circle = sidebar_manager.render_map_controls()
    sidebar_manager.render_ai_toggle()

    # Handle map rendering
    try:
        radius_km = 1 if show_circle else 0
        map_data = map_manager.create_map(
            st.session_state.map_center,
            st.session_state.zoom_level,
            st.session_state.landmarks,
            show_markers,
            show_circle,
            radius_km
        )

        # Process map interactions
        center, zoom, bounds = map_manager.parse_map_data(map_data)
        if center and zoom:
            st.session_state.map_center = center
            st.session_state.zoom_level = zoom
            st.query_params['center'] = f"{center[0]},{center[1]}"
            st.query_params['zoom'] = str(zoom)

        if bounds:
            st.session_state.current_bounds = bounds

    except Exception as e:
        st.error(f"Error rendering map: {str(e)}")

    # Handle location inputs
    lat_input, lon_input = sidebar_manager.render_location_inputs()
    if st.sidebar.button("Go to Location"):
        success, error = location_handler.process_location_update(lat_input, lon_input)
        if not success:
            st.sidebar.error(error)

    # Handle offline mode and cache management
    offline_mode = sidebar_manager.render_offline_mode_toggle()
    if offline_mode != st.session_state.offline_mode:
        settings_manager.toggle_offline_mode(offline_mode)

    update_cache, clear_cache = sidebar_manager.render_cache_management()
    if update_cache and st.session_state.last_bounds:
        update_landmarks()
    elif clear_cache:
        cache_manager.clear_old_cache()

    # Handle data source selection
    data_source = sidebar_manager.render_data_source_selector()
    if settings_manager.switch_data_source(data_source):
        if st.session_state.last_bounds:
            update_landmarks()
            st.rerun()

    # Render landmarks list
    sidebar_manager.render_landmarks_list(st.session_state.landmarks)

    # Search area button
    if st.sidebar.button("🔍 Search This Area", type="primary"):
        update_landmarks()

if __name__ == "__main__":
    main()