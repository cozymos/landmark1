import streamlit as st
from typing import Dict, Optional

class SettingsManager:
    def __init__(self):
        self.data_sources = ["Wikipedia", "Google Places"]
    
    def toggle_offline_mode(self, new_state: bool) -> None:
        """Toggle offline mode and update session state"""
        if new_state != st.session_state.offline_mode:
            st.session_state.offline_mode = new_state
            return True
        return False

    def switch_data_source(self, new_source: str) -> bool:
        """Switch data source and return if change occurred"""
        if new_source != st.session_state.last_data_source:
            st.session_state.last_data_source = new_source
            return True
        return False

    def get_current_settings(self) -> Dict:
        """Get current application settings"""
        return {
            'offline_mode': st.session_state.offline_mode,
            'data_source': st.session_state.last_data_source,
            'ai_enabled': st.session_state.ai_landmarks,
            'show_markers': st.session_state.show_markers,
            'show_circle': st.session_state.show_circle
        }

    def update_cache_settings(self, stats: Dict) -> None:
        """Update cache statistics in session state"""
        st.session_state.cache_stats = stats
