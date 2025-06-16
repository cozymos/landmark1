import streamlit as st
from typing import Tuple, List, Dict
from components.map_viewer import render_map
from utils.coord_utils import parse_coordinates
from utils.config_utils import is_test_mode_enabled, enable_test_mode
from components.cache_manager import cache_manager
from components.debug_panel import render_debug_panel, update_cache_stats, update_api_stats
import logging
import time
import math

logger = logging.getLogger("main")
logger.debug("*** RERUN ***")

st.set_page_config(
    page_title="Landmarks Locator",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Update CSS for width and margins only
st.markdown(
    """
<style>
    .block-container {
        padding-top: 3rem;
        padding-bottom: 0;
        max-width: 100%;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Initialize session state with URL parameters if available
if "map_center" not in st.session_state:
    center_str = st.query_params.get("center", "37.7749,-122.4194")
    lat, lon = map(float, center_str.split(","))
    st.session_state.map_center = [lat, lon]
if "new_center" not in st.session_state:
    st.session_state.new_center = st.session_state.map_center

if "zoom_level" not in st.session_state:
    st.session_state.zoom_level = int(st.query_params.get("zoom", "12"))
if "new_zoom" not in st.session_state:
    st.session_state.new_zoom = st.session_state.zoom_level

# Initialize radius in session state if not present
if "radius" not in st.session_state:
    st.session_state.radius = 5  # Default 5km radius
if "landmarks" not in st.session_state:
    st.session_state.landmarks = []
if "last_data_source" not in st.session_state:
    st.session_state.last_data_source = "Test Mode"  # Default to Test Mode


def track_zoom_radius_performance(zoom_level: int, radius_km: float, landmark_count: int, from_cache: bool):
    """
    Track zoom-to-radius performance data for optimization analysis.
    
    Args:
        zoom_level: Current map zoom level
        radius_km: Search radius in kilometers
        landmark_count: Number of landmarks found
        from_cache: Whether data came from cache
    """
    if "zoom_radius_analytics" not in st.session_state:
        st.session_state.zoom_radius_analytics = []
    
    # Calculate efficiency metrics
    density = landmark_count / (math.pi * radius_km ** 2) if radius_km > 0 else 0
    efficiency_score = landmark_count / radius_km if radius_km > 0 else 0
    
    performance_data = {
        "timestamp": time.strftime("%H:%M:%S"),
        "zoom_level": zoom_level,
        "radius_km": radius_km,
        "landmark_count": landmark_count,
        "from_cache": from_cache,
        "density_per_km2": round(density, 4),
        "efficiency_score": round(efficiency_score, 2),
        "zoom_radius_ratio": round(zoom_level / radius_km, 2) if radius_km > 0 else 0
    }
    
    st.session_state.zoom_radius_analytics.append(performance_data)
    
    # Keep only last 100 entries
    if len(st.session_state.zoom_radius_analytics) > 100:
        st.session_state.zoom_radius_analytics = st.session_state.zoom_radius_analytics[-100:]


def calculate_optimal_radius(zoom_level: int) -> float:
    """
    Calculate optimal search radius based on zoom level and historical performance.
    
    Args:
        zoom_level: Current map zoom level
        
    Returns:
        Recommended radius in kilometers
    """
    # Base formula: higher zoom = smaller optimal radius
    base_radius = max(1, 25 - zoom_level * 1.5)
    
    # Adjust based on historical performance data if available
    analytics = st.session_state.get("zoom_radius_analytics", [])
    if len(analytics) >= 5:
        # Find similar zoom levels in history
        similar_zooms = [data for data in analytics if abs(data["zoom_level"] - zoom_level) <= 2]
        
        if similar_zooms:
            # Find the radius that gave best efficiency scores
            best_efficiency = max(similar_zooms, key=lambda x: x["efficiency_score"])
            optimal_radius = best_efficiency["radius_km"]
            
            # Blend with base calculation for stability
            return round((base_radius + optimal_radius) / 2, 1)
    
    return round(base_radius, 1)


def get_landmarks(
    center_coords: Tuple[float, float],
    radius_km: float,
    zoom_level: int,
    data_source: str = "Google Places",
) -> List[Dict]:
    """
    Fetch and cache landmarks near the specified center within the given radius

    Args:
        center_coords: (lat, lon) tuple for the center point
        radius_km: Radius in kilometers to search within
        zoom_level: Current map zoom level (used for caching decisions)
        data_source: Source of landmark data ("Google Places" or "Test Mode")

    Returns:
        List of landmark dictionaries
    """
    start_time = time.time()
    
    try:
        # Update API stats - loading state
        update_api_stats(data_source, "loading", 0, 0)
        
        # Check cache first
        landmarks = cache_manager.get_cached_landmarks(center_coords, radius_km)
        if landmarks:
            # Cache hit
            update_cache_stats(hits=1, misses=0, total_cached=len(landmarks))
            response_time = int((time.time() - start_time) * 1000)
            update_api_stats(data_source, "success", response_time, len(landmarks))
            
            # Track zoom-to-radius optimization data
            track_zoom_radius_performance(zoom_level, radius_km, len(landmarks), True)
            return landmarks

        # Cache miss
        update_cache_stats(hits=0, misses=1, total_cached=0)

        # If test mode is selected as data source, don't make API calls
        if data_source == "Test Mode":
            # Force enable test mode for this request
            from utils.config_utils import enable_test_mode
            enable_test_mode()

        # Use Google Places API
        from components.google_places import GooglePlacesHandler

        places_handler = GooglePlacesHandler()
        landmarks = places_handler.get_landmarks(center_coords, radius_km)

        # Cache the landmarks for offline use
        if landmarks:
            cache_manager.cache_landmarks(landmarks, center_coords, radius_km)
            update_cache_stats(hits=0, misses=0, total_cached=len(landmarks))

        # Update API stats with success
        response_time = int((time.time() - start_time) * 1000)
        update_api_stats(data_source, "success", response_time, len(landmarks))
        
        # Track zoom-to-radius optimization data
        track_zoom_radius_performance(zoom_level, radius_km, len(landmarks), False)
        
        return landmarks

    except Exception as e:
        # Update API stats with error
        response_time = int((time.time() - start_time) * 1000)
        update_api_stats(data_source, "error", response_time, 0)
        st.error(f"Error fetching landmarks: {str(e)}")
        return []


def update_landmarks():
    """Update landmarks for the current map view."""
    st.session_state.map_center = st.session_state.new_center
    st.session_state.zoom_level = st.session_state.new_zoom

    # Get radius from UI or calculate based on zoom
    radius_km = (
        st.session_state.radius
        if st.session_state.radius > 0
        else max(1, 20 - st.session_state.zoom_level)
    )

    try:
        with st.spinner("Fetching landmarks..."):
            landmarks = get_landmarks(
                center_coords=st.session_state.map_center,
                radius_km=radius_km,
                zoom_level=st.session_state.zoom_level,
                data_source=st.session_state.last_data_source,
            )
            if landmarks:
                st.session_state.landmarks = landmarks

        # Update URL parameters
        new_lat = st.session_state.new_center[0]
        new_lng = st.session_state.new_center[1]
        st.query_params["center"] = f"{new_lat},{new_lng}"
        st.query_params["zoom"] = str(st.session_state.new_zoom)
    except Exception as e:
        st.error(f"Error fetching landmarks: {str(e)}")


# Optimization controls
st.sidebar.markdown("### 🎯 Optimization Controls")

# Show optimal radius suggestion
current_zoom = st.session_state.get("zoom_level", 12)
optimal_radius = calculate_optimal_radius(current_zoom)

col1, col2 = st.sidebar.columns([2, 1])
with col1:
    st.session_state.radius = st.number_input(
        "Search radius (km)",
        min_value=0,
        max_value=20,
        value=st.session_state.get("radius", 5),
        step=1,
        help=f"Optimal radius for zoom {current_zoom}: {optimal_radius} km"
    )

with col2:
    if st.button("✨ Use Optimal", help="Apply AI-optimized radius"):
        st.session_state.radius = optimal_radius
        st.rerun()

# Show optimization metrics
analytics = st.session_state.get("zoom_radius_analytics", [])
if analytics:
    latest = analytics[-1]
    efficiency = latest.get("efficiency_score", 0)
    density = latest.get("density_per_km2", 0)
    
    st.sidebar.markdown(f"""
    **Current Performance:**
    - Efficiency Score: {efficiency}
    - Density: {density:.3f}/km²
    - From Cache: {'✅' if latest.get('from_cache') else '❌'}
    """)

    # Performance comparison
    if len(analytics) >= 2:
        previous = analytics[-2]
        efficiency_change = latest.get("efficiency_score", 0) - previous.get("efficiency_score", 0)
        trend = "📈" if efficiency_change > 0 else "📉" if efficiency_change < 0 else "➡️"
        st.sidebar.markdown(f"Trend: {trend} {efficiency_change:+.2f}")

coord_input = st.sidebar.text_input(
    "Custom Location",
    help="Enter coordinates in either format:\n"
    + "• Decimal Degrees (DD): 37.3349, -122.0090\n"
    + "• DMS: 37°20'5.64\"N, 122°0'32.40\"W",
    label_visibility="collapsed",
    placeholder="Custom location (DD/DMS)",
    key="coord_input",
)

if coord_input:
    coords = parse_coordinates(coord_input)
    if coords:
        if st.sidebar.button("Go to Location"):
            st.session_state.map_center = [coords.lat, coords.lon]
            st.session_state.zoom_level = 12
            # Update URL parameters
            st.query_params["center"] = f"{coords.lat},{coords.lon}"
            st.query_params["zoom"] = str(st.session_state.zoom_level)
            st.rerun()
    else:
        st.sidebar.error(
            "Invalid coordinate format. Please use DD or DMS format."
        )

try:
    map_data = render_map(
        center=st.session_state.map_center, zoom=st.session_state.zoom_level
    )
    # Handle map interactions
    if map_data and isinstance(map_data, dict):
        # Update center and zoom
        center_data = map_data.get("center")
        new_zoom = map_data.get("zoom")

        if isinstance(center_data, dict):
            new_lat = float(
                center_data.get("lat", st.session_state.map_center[0])
            )
            new_lng = float(
                center_data.get("lng", st.session_state.map_center[1])
            )
            st.session_state.new_center = [new_lat, new_lng]

        # Handle zoom changes without forcing refresh
        if new_zoom is not None:
            new_zoom = int(
                float(new_zoom)
            )  # Convert to float first to handle any decimal values
            if new_zoom != st.session_state.zoom_level:
                st.session_state.new_zoom = new_zoom

    if st.sidebar.button("🔍 Search Landmarks", type="primary"):
        update_landmarks()
        st.rerun()

except Exception as e:
    st.error(f"Error rendering map: {str(e)}")

# Display landmarks
landmarks_expander = st.sidebar.expander(
    f"View {len(st.session_state.landmarks)} Landmarks", expanded=False
)
with landmarks_expander:
    for landmark in st.session_state.landmarks:
        with st.container():
            # Display the landmark image if available
            if "image_url" in landmark:
                st.image(
                    landmark["image_url"],
                    caption=f"[{landmark['title']}]({landmark['url']})",
                    use_container_width=True,
                )

# Update data source handling
data_source = st.sidebar.radio(
    "Choose Data Source",
    options=["Test Mode", "Google Places"],
    help="Select where to fetch landmark information from. Test Mode uses sample data without API calls.",
    key="data_source",
    index=0,  # Default to Test Mode
)

# Store the selected data source
st.session_state.last_data_source = data_source

# Render the comprehensive debug panel
render_debug_panel()

# Add optimization analytics view
st.markdown("---")
st.markdown("### 📊 Zoom-to-Radius Analytics Dashboard")

analytics = st.session_state.get("zoom_radius_analytics", [])
if analytics:
    # Create tabs for different analytics views
    tab1, tab2, tab3 = st.tabs(["Performance Trends", "Optimization Table", "Best Practices"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Efficiency Scores Over Time**")
            chart_data = []
            for i, data in enumerate(analytics[-20:]):  # Last 20 searches
                chart_data.append({
                    "Search": i + 1,
                    "Efficiency Score": data["efficiency_score"],
                    "Zoom Level": data["zoom_level"],
                    "Radius": data["radius_km"]
                })
            if chart_data:
                st.line_chart(chart_data, x="Search", y="Efficiency Score")
        
        with col2:
            st.markdown("**Density Distribution**")
            density_data = []
            for i, data in enumerate(analytics[-20:]):
                density_data.append({
                    "Search": i + 1,
                    "Density": data["density_per_km2"],
                    "Cache Hit": "Yes" if data["from_cache"] else "No"
                })
            if density_data:
                st.scatter_chart(density_data, x="Search", y="Density")
    
    with tab2:
        st.markdown("**Recent Search Performance**")
        table_data = []
        for data in analytics[-10:]:  # Last 10 searches
            table_data.append({
                "Time": data["timestamp"],
                "Zoom": data["zoom_level"],
                "Radius (km)": data["radius_km"],
                "Landmarks": data["landmark_count"],
                "Efficiency": f"{data['efficiency_score']:.2f}",
                "Density": f"{data['density_per_km2']:.4f}",
                "Cached": "✅" if data["from_cache"] else "❌"
            })
        
        if table_data:
            st.dataframe(table_data, use_container_width=True)
        else:
            st.info("No analytics data available yet. Perform some searches to see optimization insights.")
    
    with tab3:
        st.markdown("**AI-Powered Recommendations**")
        
        if len(analytics) >= 5:
            # Calculate best performing zoom-radius combinations
            best_efficiency = max(analytics, key=lambda x: x["efficiency_score"])
            best_density = max(analytics, key=lambda x: x["density_per_km2"])
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.success(f"""
                **Best Efficiency Configuration:**
                - Zoom Level: {best_efficiency['zoom_level']}
                - Radius: {best_efficiency['radius_km']} km
                - Score: {best_efficiency['efficiency_score']:.2f}
                - Landmarks Found: {best_efficiency['landmark_count']}
                """)
            
            with col2:
                st.info(f"""
                **Best Density Configuration:**
                - Zoom Level: {best_density['zoom_level']}
                - Radius: {best_density['radius_km']} km
                - Density: {best_density['density_per_km2']:.4f}/km²
                - Landmarks Found: {best_density['landmark_count']}
                """)
            
            # Performance insights
            st.markdown("**Optimization Insights:**")
            
            avg_efficiency = sum(d["efficiency_score"] for d in analytics) / len(analytics)
            cache_hit_rate = sum(1 for d in analytics if d["from_cache"]) / len(analytics) * 100
            
            insights = []
            if avg_efficiency > 2.0:
                insights.append("✅ Your search parameters are well-optimized!")
            elif avg_efficiency < 1.0:
                insights.append("💡 Try smaller radius values for better efficiency")
            
            if cache_hit_rate > 50:
                insights.append(f"✅ Good cache utilization: {cache_hit_rate:.1f}% hit rate")
            else:
                insights.append(f"💡 Low cache hits: {cache_hit_rate:.1f}% - consider repeated searches in similar areas")
            
            # Zoom-specific recommendations
            zoom_groups = {}
            for data in analytics:
                zoom = data["zoom_level"]
                if zoom not in zoom_groups:
                    zoom_groups[zoom] = []
                zoom_groups[zoom].append(data["efficiency_score"])
            
            for zoom, scores in zoom_groups.items():
                avg_score = sum(scores) / len(scores)
                if len(scores) >= 3:  # Only show if we have enough data
                    optimal_radius = calculate_optimal_radius(zoom)
                    insights.append(f"📊 Zoom {zoom}: Avg efficiency {avg_score:.2f}, optimal radius ~{optimal_radius} km")
            
            for insight in insights:
                st.markdown(f"- {insight}")
                
        else:
            st.warning("Perform at least 5 searches to see AI-powered recommendations and insights.")
            
            # Show getting started tips
            st.markdown("""
            **Getting Started with Optimization:**
            1. Try different zoom levels (10-18) with various radius settings
            2. Search in both urban and rural areas to gather diverse data
            3. Use the "Use Optimal" button to apply AI suggestions
            4. Monitor the efficiency trends in the Performance tab
            5. Check cache utilization to optimize repeated searches
            """)

else:
    st.info("No optimization data available yet. Start searching to build your analytics dashboard!")
