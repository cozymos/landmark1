import streamlit as st
from typing import Tuple, List, Dict

@st.cache_data(ttl=3600)  # Cache for 1 hour
def cache_landmarks(
    bounds: Tuple[float, float, float, float],
    wiki_fetcher
) -> List[Dict]:
    """
    Cache landmark data for the given bounds
    """
    return wiki_fetcher.get_landmarks(bounds)
