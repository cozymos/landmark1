import streamlit as st
from typing import List, Tuple, Any

def initialize_session_state():
    """Initialize all session state variables with default values"""
    defaults = {
        'map_center': [37.7749, -122.4194],  # Default to San Francisco
        'zoom_level': 12,
        'current_bounds': None,
        'last_bounds': None,
        'landmarks': [],
        'show_circle': False,
        'ai_landmarks': False,
        'offline_mode': False,
        'last_data_source': "Wikipedia",
        'show_markers': True,
        'cache_stats': {
            'landmarks_cached': 0,
            'images_cached': 0,
            'last_update': None
        }
    }
    
    # Initialize from URL parameters if available
    try:
        center_str = st.query_params.get('center', '37.7749,-122.4194')
        lat, lon = map(float, center_str.split(','))
        defaults['map_center'] = [lat, lon]
    except:
        pass

    try:
        defaults['zoom_level'] = int(st.query_params.get('zoom', '12'))
    except:
        pass

    # Set default values for any missing session state variables
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def update_url_params(center: List[float], zoom: int):
    """Update URL parameters with current map state"""
    st.query_params['center'] = f"{center[0]},{center[1]}"
    st.query_params['zoom'] = str(zoom)

def get_map_state() -> Tuple[List[float], int, Any]:
    """Get current map state"""
    return (
        st.session_state.map_center,
        st.session_state.zoom_level,
        st.session_state.current_bounds
    )

def update_map_state(center: List[float], zoom: int, bounds: Any):
    """Update map state in session"""
    st.session_state.map_center = center
    st.session_state.zoom_level = zoom
    st.session_state.current_bounds = bounds
    update_url_params(center, zoom)
