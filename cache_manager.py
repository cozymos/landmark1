import streamlit as st
from typing import Tuple, List, Dict

@st.cache_data(ttl=3600)  # Cache for 1 hour
def cache_landmarks(
    bounds: Tuple[float, float, float, float]
) -> List[Dict]:
    """
    Cache landmark data for the given bounds.
    The wiki_fetcher is moved outside the cache key.
    """
    from wiki_handler import WikiLandmarkFetcher
    wiki_fetcher = WikiLandmarkFetcher()
    return wiki_fetcher.get_landmarks(bounds)