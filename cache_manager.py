import streamlit as st
from typing import Tuple, List, Dict
from functools import partial

@st.cache_data(ttl=3600, show_spinner=False)  # Cache for 1 hour
def cache_landmarks(
    bounds: Tuple[float, float, float, float],
    min_zoom: int = 8,
    cache_radius: float = 0.1  # Degree radius for cache tolerance
) -> List[Dict]:
    """
    Cache landmark data for the given bounds with smart caching strategy.
    Args:
        bounds: (south, west, north, east)
        min_zoom: Minimum zoom level to fetch landmarks
        cache_radius: Degree radius for cache tolerance to prevent redundant fetches
    """
    # Round bounds to reduce cache fragmentation
    rounded_bounds = tuple(round(b, 3) for b in bounds)

    from wiki_handler import WikiLandmarkFetcher
    wiki_fetcher = WikiLandmarkFetcher()
    return wiki_fetcher.get_landmarks(rounded_bounds)

def get_cached_landmarks(
    bounds: Tuple[float, float, float, float],
    zoom_level: int
) -> List[Dict]:
    """
    Smart wrapper for landmark caching with zoom-level awareness
    """
    try:
        # Only fetch new landmarks if zoom level is appropriate
        if zoom_level >= 8:  # Prevent fetching at very low zoom levels
            return cache_landmarks(bounds)
        return []
    except Exception as e:
        st.error(f"Error fetching landmarks: {str(e)}")
        return []