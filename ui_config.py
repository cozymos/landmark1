import streamlit as st

def configure_page():
    """Configure initial page settings"""
    st.set_page_config(
        page_title="Landmarks Locator",
        page_icon="🗺️",
        layout="wide",
        initial_sidebar_state="expanded"
    )

def apply_custom_css():
    """Apply custom CSS styling"""
    st.markdown("""
    <style>
        .block-container {
            padding-top: 1rem;
            padding-bottom: 0;
            max-width: 100%;
        }

        .sidebar .element-container {
            margin-bottom: 0.5rem;
        }

        footer {
            display: none;
        }
    </style>
    """, unsafe_allow_html=True)

def add_map_resize_script():
    """Add JavaScript for dynamic map height calculation"""
    st.markdown("""
    <script>
        function updateMapHeight() {
            const headerHeight = 60;  // Streamlit header
            const topPadding = 16;    // Container padding
            const bottomBuffer = 10;   // Bottom buffer
            const availableHeight = window.innerHeight - headerHeight - topPadding - bottomBuffer;
            const mapContainer = document.querySelector('.stfolium-container');
            if (mapContainer) {
                mapContainer.style.height = availableHeight + 'px';
            }
        }

        window.addEventListener('load', updateMapHeight);
        window.addEventListener('resize', updateMapHeight);
    </script>
    """, unsafe_allow_html=True)

def setup_ui():
    """Initialize all UI configurations"""
    configure_page()
    apply_custom_css()
    add_map_resize_script()
