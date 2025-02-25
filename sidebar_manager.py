import streamlit as st
from typing import Tuple, Dict
from coord_utils import parse_coordinates, format_dms

class SidebarManager:
    def __init__(self, cache_manager):
        self.cache_manager = cache_manager

    def render_header(self):
        """Render the sidebar header"""
        st.sidebar.header("🗺️ Landmarks Locator")

    def render_map_controls(self) -> Tuple[bool, bool]:
        """Render map control toggles"""
        show_markers = st.sidebar.checkbox(
            "Show Markers", 
            value=st.session_state.show_markers
        )
        show_circle = st.sidebar.checkbox(
            "Show Location",
            value=st.session_state.show_circle
        )
        st.session_state.show_markers = show_markers
        st.session_state.show_circle = show_circle
        
        return show_markers, show_circle

    def render_ai_toggle(self) -> bool:
        """Render AI landmarks toggle"""
        ai_landmarks = st.sidebar.checkbox(
            "AI landmarks",
            value=st.session_state.ai_landmarks
        )
        st.session_state.ai_landmarks = ai_landmarks
        return ai_landmarks

    def render_location_inputs(self) -> Tuple[float, float]:
        """Render location input fields"""
        st.sidebar.markdown("---")
        
        # Combined coordinates input
        combined_coords = st.sidebar.text_input(
            "Custom Location",
            help="Enter coordinates in either format:\n" +
            "• Decimal Degrees (DD): 37.3349, -122.0090\n" +
            "• DMS: 37°20'5.64\"N, 122°0'32.40\"W",
            placeholder="Enter coordinates (DD or DMS)",
            key="combined_coords"
        )

        # Parse combined coordinates if provided
        custom_lat = None
        custom_lon = None
        if combined_coords:
            coords = parse_coordinates(combined_coords)
            if coords:
                custom_lat = coords.lat
                custom_lon = coords.lon
                st.sidebar.success(f"""
                ✅ Valid coordinates:
                • DD: {custom_lat:.4f}, {custom_lon:.4f}
                • DMS: {format_dms(custom_lat, True)}, {format_dms(custom_lon, False)}
                """)
            else:
                st.sidebar.error("Invalid coordinate format. Please use DD or DMS format.")

        # Separate lat/lon inputs
        lat_input = st.sidebar.number_input(
            "Latitude",
            value=float(custom_lat if custom_lat is not None else st.session_state.map_center[0]),
            format="%.4f",
            help="Decimal degrees (e.g., 37.3349)"
        )

        lon_input = st.sidebar.number_input(
            "Longitude",
            value=float(custom_lon if custom_lon is not None else st.session_state.map_center[1]),
            format="%.4f",
            help="Decimal degrees (e.g., -122.0090)"
        )

        return lat_input, lon_input

    def render_offline_mode_toggle(self) -> bool:
        """Render offline mode toggle and cache management"""
        st.sidebar.header("Map Controls")
        
        offline_mode = st.sidebar.checkbox(
            "📱 Offline Mode",
            value=st.session_state.offline_mode
        )
        
        if offline_mode != st.session_state.offline_mode:
            st.session_state.offline_mode = offline_mode
            if offline_mode:
                st.sidebar.info("🔄 Offline mode enabled. Using cached map data.")
            else:
                st.sidebar.info("🌐 Online mode enabled. Fetching live data.")
        
        return offline_mode

    def render_cache_management(self):
        """Render cache management controls"""
        if st.session_state.offline_mode:
            st.sidebar.header("📦 Cache Management")
            
            # Display cache statistics
            cache_stats = self.cache_manager.get_cache_stats()
            st.sidebar.markdown(f"""
            **Cache Statistics:**
            - 📍 Landmarks: {cache_stats['landmarks_cached']}
            - 🖼️ Images: {cache_stats['images_cached']}
            - 🕒 Last Update: {cache_stats['last_update'] or 'Never'}
            """)
            
            # Cache management buttons
            col1, col2 = st.sidebar.columns(2)
            return col1.button("🔄 Update Cache"), col2.button("🗑️ Clear Old Cache")
        return False, False

    def render_data_source_selector(self) -> str:
        """Render data source selection radio buttons"""
        return st.sidebar.radio(
            "Choose Landmarks Data Source",
            options=["Wikipedia", "Google Places"],
            help="Select where to fetch landmark information from",
            key="data_source"
        )

    def render_landmarks_list(self, landmarks: list):
        """Render the list of landmarks in the sidebar"""
        landmarks_expander = st.sidebar.expander(
            f"View {len(landmarks)} Landmarks",
            expanded=False
        )
        
        with landmarks_expander:
            for landmark in landmarks:
                with st.container():
                    if st.session_state.ai_landmarks:
                        st.subheader(landmark['title'])
                        if 'enhanced_description' in landmark:
                            st.write(landmark['enhanced_description'])
                        if 'historical_significance' in landmark:
                            st.write("**Historical Significance:**")
                            st.write(landmark['historical_significance'])
                        if 'best_times' in landmark:
                            st.write("**Best Times to Visit:**")
                            st.write(landmark['best_times'])
                        if 'interesting_facts' in landmark:
                            st.write("**Interesting Facts:**")
                            for fact in landmark['interesting_facts']:
                                st.markdown(f"• {fact}")
                        st.divider()
                    if 'image_url' in landmark:
                        st.image(
                            landmark['image_url'],
                            caption=f"[{landmark['title']}]({landmark['url']})",
                            use_container_width=True
                        )
