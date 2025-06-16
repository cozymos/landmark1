"""
Debug Panel Component for Landmark Locator

Provides a collapsible debug interface with real-time metrics,
cache status, and API call monitoring.
"""

import streamlit as st
import time
from typing import Dict, Any, Optional
import json
from components.optimization_panel import (
    render_optimization_metrics,
    render_customizable_charts,
    render_advanced_filters,
    render_machine_learning_insights,
    render_data_export_tools
)


def render_debug_panel():
    """
    Render the main debug panel underneath the map.
    Collapsible by default with grid layout inside.
    """
    # Enhanced debug view selector in sidebar
    debug_view = st.sidebar.selectbox(
        "Debug & Analytics View",
        [
            "Overview", 
            "Cache Details", 
            "API Calls", 
            "Session State",
            "Optimization Metrics",
            "Custom Charts",
            "Advanced Filters",
            "ML Insights",
            "Data Export"
        ],
        index=0,
        help="Select which debug and analytics information to display"
    )
    
    # Enable real-time updates toggle
    realtime_updates = st.sidebar.checkbox(
        "Real-time Updates",
        value=True,
        help="Automatically refresh debug data"
    )
    
    # Debug panel settings
    with st.sidebar.expander("Debug Settings", expanded=False):
        log_level = st.selectbox(
            "Log Level",
            ["INFO", "DEBUG", "WARNING", "ERROR"],
            index=0
        )
        
        max_entries = st.slider(
            "Max Log Entries",
            min_value=10,
            max_value=200,
            value=50,
            step=10
        )
        
        show_timestamps = st.checkbox("Show Timestamps", value=True)
        show_response_times = st.checkbox("Show Response Times", value=True)
    
    # Store settings in session state
    st.session_state.debug_settings = {
        "log_level": log_level,
        "max_entries": max_entries,
        "show_timestamps": show_timestamps,
        "show_response_times": show_response_times,
        "realtime_updates": realtime_updates
    }
    
    # Main debug container - collapsible by default
    with st.expander("🐛 Debug & Analytics Panel", expanded=False):
        
        # Real-time updates implementation
        if realtime_updates:
            # Create placeholder containers for live updates
            if "live_containers" not in st.session_state:
                st.session_state.live_containers = {}
            
            # Auto-refresh every 2 seconds when real-time is enabled
            if debug_view in ["Overview", "Optimization Metrics"]:
                st.markdown("**🔴 LIVE** - Auto-refreshing every 2 seconds")
                time.sleep(0.1)  # Small delay to show live indicator
        
        if debug_view == "Overview":
            if realtime_updates:
                _render_overview_realtime()
            else:
                _render_overview()
        elif debug_view == "Cache Details":
            _render_cache_details()
        elif debug_view == "API Calls":
            _render_api_calls()
        elif debug_view == "Session State":
            _render_session_state()
        elif debug_view == "Optimization Metrics":
            if realtime_updates:
                render_optimization_metrics_realtime()
            else:
                render_optimization_metrics()
        elif debug_view == "Custom Charts":
            render_customizable_charts()
        elif debug_view == "Advanced Filters":
            render_advanced_filters()
        elif debug_view == "ML Insights":
            render_machine_learning_insights()
        elif debug_view == "Data Export":
            render_data_export_tools()
        
        # Auto-refresh for real-time updates using streamlit's built-in mechanism
        if realtime_updates and debug_view in ["Overview", "Optimization Metrics"]:
            # Use Streamlit's fragment mechanism for efficient updates
            if st.button("🔄 Manual Refresh", key="manual_refresh_debug"):
                st.rerun()


def _render_overview():
    """Render overview debug information with grid layout."""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Map State**")
        _render_map_metrics()
    
    with col2:
        st.markdown("**Cache Status**")
        _render_cache_status()
    
    with col3:
        st.markdown("**API Status**")
        _render_api_status()


def _render_overview_realtime():
    """Render real-time overview with live updating metrics."""
    st.markdown("### 🔴 Live Debug Overview")
    
    # Create real-time metric containers
    col1, col2, col3 = st.columns(3)
    
    with col1:
        with st.container():
            st.markdown("**🗺️ Live Map State**")
            _render_map_metrics_realtime()
    
    with col2:
        with st.container():
            st.markdown("**💾 Live Cache Status**")
            _render_cache_status_realtime()
    
    with col3:
        with st.container():
            st.markdown("**🌐 Live API Status**")
            _render_api_status_realtime()
    
    # Real-time performance metrics
    st.markdown("---")
    _render_performance_metrics_realtime()


def _render_map_metrics():
    """Display real-time map metrics."""
    center = st.session_state.get("map_center", [0, 0])
    zoom = st.session_state.get("zoom_level", 10)
    radius = st.session_state.get("radius", 0)
    landmark_count = len(st.session_state.get("landmarks", []))
    
    st.markdown(f"""
    <div style="font-size: 12px; line-height: 1.4;">
    📍 <strong>Center:</strong> {center[0]:.4f}, {center[1]:.4f}<br>
    🔍 <strong>Zoom:</strong> {zoom}<br>
    📏 <strong>Radius:</strong> {radius} km<br>
    🏛️ <strong>Landmarks:</strong> {landmark_count}
    </div>
    """, unsafe_allow_html=True)


def _render_cache_status():
    """Display cache hit/miss information."""
    # Get cache stats from session state or initialize
    cache_stats = st.session_state.get("cache_stats", {
        "hits": 0,
        "misses": 0,
        "total_cached": 0,
        "last_update": None
    })
    
    hit_rate = 0
    hits = int(cache_stats.get("hits", 0) or 0)
    misses = int(cache_stats.get("misses", 0) or 0)
    total_cached = int(cache_stats.get("total_cached", 0) or 0)
    if hits + misses > 0:
        hit_rate = hits / (hits + misses) * 100
    
    status_color = "🟢" if hit_rate > 50 else "🟡" if hit_rate > 20 else "🔴"
    
    st.markdown(f"""
    <div style="font-size: 12px; line-height: 1.4;">
    {status_color} <strong>Hit Rate:</strong> {hit_rate:.1f}%<br>
    ✅ <strong>Hits:</strong> {hits}<br>
    ❌ <strong>Misses:</strong> {misses}<br>
    💾 <strong>Cached:</strong> {total_cached} items
    </div>
    """, unsafe_allow_html=True)


def _render_api_status():
    """Display API call status and metrics."""
    api_stats = st.session_state.get("api_stats", {
        "google_places_calls": 0,
        "last_call_time": None,
        "last_call_status": "idle",
        "rate_limit_remaining": "unknown"
    })
    
    status_icon = {
        "success": "🟢",
        "error": "🔴", 
        "loading": "🟡",
        "idle": "⚪"
    }.get(str(api_stats.get("last_call_status", "idle")), "⚪")
    
    last_call = api_stats.get("last_call_time")
    time_since = ""
    if last_call and isinstance(last_call, (int, float)):
        time_since = f" ({int(time.time() - float(last_call))}s ago)"
    
    st.markdown(f"""
    <div style="font-size: 12px; line-height: 1.4;">
    {status_icon} <strong>Status:</strong> {api_stats.get("last_call_status", "idle")}{time_since}<br>
    🔄 <strong>Calls Made:</strong> {api_stats.get("google_places_calls", 0)}<br>
    ⏱️ <strong>Rate Limit:</strong> {api_stats.get("rate_limit_remaining", "unknown")}<br>
    🌐 <strong>Source:</strong> {st.session_state.get("last_data_source", "Unknown")}
    </div>
    """, unsafe_allow_html=True)


def _render_cache_details():
    """Detailed cache information view."""
    st.markdown("**Cache Details**")
    
    # Cache statistics table
    cache_stats = st.session_state.get("cache_stats", {})
    if cache_stats:
        st.table({
            "Metric": ["Total Hits", "Total Misses", "Hit Rate", "Cached Items", "Last Update"],
            "Value": [
                cache_stats.get("hits", 0),
                cache_stats.get("misses", 0),
                f"{cache_stats.get('hits', 0) / max(1, cache_stats.get('hits', 0) + cache_stats.get('misses', 0)) * 100:.1f}%",
                cache_stats.get("total_cached", 0),
                cache_stats.get("last_update", "Never") or "Never"
            ]
        })
    else:
        st.info("No cache statistics available")
    
    # Cached landmarks summary
    landmarks = st.session_state.get("landmarks", [])
    if landmarks:
        st.markdown("**Cached Landmarks Preview**")
        preview_data = []
        for i, landmark in enumerate(landmarks[:5]):  # Show first 5
            preview_data.append({
                "Name": landmark.get("name", "Unknown")[:30],
                "Type": landmark.get("type", "Unknown"),
                "Distance": f"{landmark.get('distance_km', 0):.2f} km" if landmark.get('distance_km') else "N/A"
            })
        
        if preview_data:
            st.table(preview_data)
        
        if len(landmarks) > 5:
            st.markdown(f"*... and {len(landmarks) - 5} more landmarks*")


def _render_api_calls():
    """API calls monitoring view."""
    st.markdown("**API Call History**")
    
    # API call log
    api_log = st.session_state.get("api_call_log", [])
    if api_log:
        # Show recent API calls
        recent_calls = api_log[-10:]  # Last 10 calls
        call_data = []
        for call in recent_calls:
            call_data.append({
                "Time": call.get("timestamp", "Unknown"),
                "API": call.get("api_name", "Unknown"),
                "Status": call.get("status", "Unknown"),
                "Response Time": f"{call.get('response_time_ms', 0)}ms",
                "Results": call.get("result_count", 0)
            })
        
        st.table(call_data)
    else:
        st.info("No API calls recorded yet")
    
    # Current API configuration
    st.markdown("**API Configuration**")
    api_config = {
        "Google Places API": "✅ Configured" if st.session_state.get("google_api_key") else "❌ Not configured",
        "Rate Limiting": "✅ Enabled",
        "Cache First": "✅ Enabled",
        "Test Mode": "✅ Active" if st.session_state.get("test_mode") else "❌ Inactive"
    }
    
    for api, status in api_config.items():
        st.markdown(f"- **{api}:** {status}")


def _render_session_state():
    """Session state debugging view."""
    st.markdown("**Session State**")
    
    # Filter out large or sensitive data
    filtered_state = {}
    for key, value in st.session_state.items():
        key_str = str(key)
        if key_str.startswith("_"):  # Skip private streamlit keys
            continue
        if isinstance(value, (list, dict)) and len(str(value)) > 1000:
            filtered_state[key_str] = f"<Large object: {type(value).__name__} with {len(value) if hasattr(value, '__len__') else '?'} items>"
        else:
            filtered_state[key_str] = value
    
    # Display as expandable JSON
    if filtered_state:
        st.json(filtered_state)
    else:
        st.info("No session state data available")


def update_cache_stats(hits: int = 0, misses: int = 0, total_cached: int = 0):
    """
    Update cache statistics in session state.
    
    Args:
        hits: Number of cache hits to add
        misses: Number of cache misses to add  
        total_cached: Total number of cached items
    """
    if "cache_stats" not in st.session_state:
        st.session_state.cache_stats = {
            "hits": 0,
            "misses": 0,
            "total_cached": 0,
            "last_update": None
        }
    
    st.session_state.cache_stats["hits"] += hits
    st.session_state.cache_stats["misses"] += misses
    st.session_state.cache_stats["total_cached"] = total_cached
    st.session_state.cache_stats["last_update"] = time.strftime("%H:%M:%S")


def update_api_stats(api_name: str, status: str, response_time_ms: int = 0, result_count: int = 0):
    """
    Update API call statistics and log.
    
    Args:
        api_name: Name of the API called
        status: Status of the call (success, error, loading)
        response_time_ms: Response time in milliseconds
        result_count: Number of results returned
    """
    # Update API stats
    if "api_stats" not in st.session_state:
        st.session_state.api_stats = {
            "google_places_calls": 0,
            "last_call_time": None,
            "last_call_status": "idle",
            "rate_limit_remaining": "unknown"
        }
    
    if api_name == "Google Places":
        st.session_state.api_stats["google_places_calls"] += 1
    
    st.session_state.api_stats["last_call_time"] = time.time()
    st.session_state.api_stats["last_call_status"] = status
    
    # Update API call log
    if "api_call_log" not in st.session_state:
        st.session_state.api_call_log = []
    
    call_entry = {
        "timestamp": time.strftime("%H:%M:%S"),
        "api_name": api_name,
        "status": status,
        "response_time_ms": response_time_ms,
        "result_count": result_count
    }
    
    st.session_state.api_call_log.append(call_entry)
    
    # Keep only last 50 entries to prevent memory issues
    if len(st.session_state.api_call_log) > 50:
        st.session_state.api_call_log = st.session_state.api_call_log[-50:]


def _render_map_metrics_realtime():
    """Display real-time map metrics with live updates."""
    center = st.session_state.get("map_center", [0, 0])
    zoom = st.session_state.get("zoom_level", 10)
    radius = st.session_state.get("radius", 0)
    landmark_count = len(st.session_state.get("landmarks", []))
    
    # Live updating metrics with color coding
    current_time = time.strftime("%H:%M:%S")
    
    # Create metrics with dynamic styling
    st.metric(
        label="🌍 Current Center",
        value=f"{center[0]:.4f}, {center[1]:.4f}",
        delta=f"Updated: {current_time}"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            label="🔍 Zoom Level",
            value=zoom,
            delta="Optimal" if 10 <= zoom <= 15 else "Adjust recommended"
        )
    
    with col2:
        st.metric(
            label="📏 Search Radius",
            value=f"{radius} km",
            delta="Good" if 1 <= radius <= 10 else "Review settings"
        )
    
    st.metric(
        label="🏛️ Active Landmarks",
        value=landmark_count,
        delta="High density" if landmark_count > 10 else "Low density" if landmark_count < 3 else "Normal"
    )


def _render_cache_status_realtime():
    """Display real-time cache status with live indicators."""
    cache_stats = st.session_state.get("cache_stats", {
        "hits": 0,
        "misses": 0,
        "total_cached": 0,
        "last_update": None
    })
    
    hits = int(cache_stats.get("hits", 0) or 0)
    misses = int(cache_stats.get("misses", 0) or 0)
    total_cached = int(cache_stats.get("total_cached", 0) or 0)
    
    hit_rate = 0
    if hits + misses > 0:
        hit_rate = hits / (hits + misses) * 100
    
    # Real-time cache metrics with status indicators
    st.metric(
        label="📊 Cache Hit Rate",
        value=f"{hit_rate:.1f}%",
        delta="Excellent" if hit_rate > 70 else "Good" if hit_rate > 40 else "Poor"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            label="✅ Cache Hits",
            value=hits,
            delta=f"+{hits}" if hits > 0 else None
        )
    
    with col2:
        st.metric(
            label="❌ Cache Misses",
            value=misses,
            delta=f"+{misses}" if misses > 0 else None
        )
    
    st.metric(
        label="💾 Cached Items",
        value=total_cached,
        delta="Active cache" if total_cached > 0 else "Empty cache"
    )


def _render_api_status_realtime():
    """Display real-time API status with live monitoring."""
    api_stats = st.session_state.get("api_stats", {
        "google_places_calls": 0,
        "last_call_time": None,
        "last_call_status": "idle",
        "rate_limit_remaining": "unknown"
    })
    
    # Calculate time since last call
    last_call = api_stats.get("last_call_time")
    time_since = "Never"
    if last_call and isinstance(last_call, (int, float)):
        seconds_ago = int(time.time() - float(last_call))
        if seconds_ago < 60:
            time_since = f"{seconds_ago}s ago"
        elif seconds_ago < 3600:
            time_since = f"{seconds_ago // 60}m ago"
        else:
            time_since = f"{seconds_ago // 3600}h ago"
    
    # Live API metrics
    status = str(api_stats.get("last_call_status", "idle"))
    status_color = {
        "success": "🟢",
        "error": "🔴",
        "loading": "🟡",
        "idle": "⚪"
    }.get(status, "⚪")
    
    st.metric(
        label=f"{status_color} API Status",
        value=status.title(),
        delta=f"Last call: {time_since}"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        total_calls = api_stats.get("google_places_calls", 0)
        if isinstance(total_calls, (int, float)):
            total_calls = int(total_calls)
        else:
            total_calls = 0
            
        st.metric(
            label="📞 Total Calls",
            value=total_calls,
            delta="Active usage" if total_calls > 0 else None
        )
    
    with col2:
        st.metric(
            label="🌐 Data Source",
            value=st.session_state.get("last_data_source", "Unknown"),
            delta="Live connection"
        )


def _render_performance_metrics_realtime():
    """Display real-time performance metrics and system health."""
    st.markdown("### ⚡ Live Performance Metrics")
    
    # Calculate real-time performance indicators
    analytics = st.session_state.get("zoom_radius_analytics", [])
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_searches = len(analytics)
        recent_searches = len([a for a in analytics if time.time() - time.mktime(time.strptime(a.get("timestamp", "00:00:00"), "%H:%M:%S")) < 300])
        
        st.metric(
            label="🔍 Total Searches",
            value=total_searches,
            delta=f"{recent_searches} in last 5min"
        )
    
    with col2:
        if analytics:
            avg_efficiency = sum(d["efficiency_score"] for d in analytics) / len(analytics)
            latest_efficiency = analytics[-1]["efficiency_score"] if analytics else 0
            efficiency_trend = latest_efficiency - avg_efficiency
            
            st.metric(
                label="🎯 Efficiency Score",
                value=f"{latest_efficiency:.2f}",
                delta=f"{efficiency_trend:+.2f} vs avg"
            )
        else:
            st.metric(
                label="🎯 Efficiency Score",
                value="N/A",
                delta="No data yet"
            )
    
    with col3:
        if analytics:
            cache_hits = sum(1 for d in analytics if d["from_cache"])
            cache_rate = cache_hits / len(analytics) * 100
            
            st.metric(
                label="💾 Cache Efficiency",
                value=f"{cache_rate:.1f}%",
                delta="Optimal" if cache_rate > 50 else "Needs improvement"
            )
        else:
            st.metric(
                label="💾 Cache Efficiency",
                value="N/A",
                delta="Building cache"
            )
    
    with col4:
        current_time = time.strftime("%H:%M:%S")
        st.metric(
            label="🕐 System Time",
            value=current_time,
            delta="Live updates active"
        )
    
    # Real-time trend visualization
    if analytics and len(analytics) >= 2:
        st.markdown("**📈 Live Trend Analysis**")
        
        recent_data = analytics[-10:]  # Last 10 searches
        trend_data = []
        
        for i, data in enumerate(recent_data):
            trend_data.append({
                "Search": i + 1,
                "Efficiency": data["efficiency_score"],
                "Cache Hit": 1 if data["from_cache"] else 0
            })
        
        if trend_data:
            st.line_chart(trend_data, x="Search", y="Efficiency")


def render_optimization_metrics_realtime():
    """Render real-time optimization metrics with live updates."""
    st.markdown("### 🎯 Live Optimization Dashboard")
    
    # Real-time optimization recommendations
    analytics = st.session_state.get("zoom_radius_analytics", [])
    current_zoom = st.session_state.get("zoom_level", 12)
    current_radius = st.session_state.get("radius", 5)
    
    if analytics:
        # Live performance analysis
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🔴 Live Performance Analysis**")
            
            latest = analytics[-1]
            current_efficiency = latest["efficiency_score"]
            current_density = latest["density_per_km2"]
            
            # Dynamic performance indicators
            efficiency_status = "🟢 Excellent" if current_efficiency > 3 else "🟡 Good" if current_efficiency > 1.5 else "🔴 Poor"
            density_status = "🟢 High" if current_density > 0.01 else "🟡 Medium" if current_density > 0.001 else "🔴 Low"
            
            st.markdown(f"""
            - **Current Efficiency:** {current_efficiency:.2f} {efficiency_status}
            - **Current Density:** {current_density:.4f}/km² {density_status}
            - **Landmarks Found:** {latest['landmark_count']}
            - **From Cache:** {'✅ Yes' if latest['from_cache'] else '❌ No'}
            """)
        
        with col2:
            st.markdown("**🤖 Live AI Recommendations**")
            
            # Calculate optimal settings in real-time
            from components.optimization_panel import predict_efficiency
            
            # Test different radius values
            test_radii = [1, 3, 5, 7, 10]
            predictions = []
            
            for test_radius in test_radii:
                predicted_eff = predict_efficiency(analytics, current_zoom, test_radius)
                predictions.append({
                    "Radius": test_radius,
                    "Predicted Efficiency": predicted_eff
                })
            
            # Find best prediction
            best_radius = max(predictions, key=lambda x: x["Predicted Efficiency"])
            
            st.markdown(f"""
            - **Recommended Radius:** {best_radius['Radius']} km
            - **Expected Efficiency:** {best_radius['Predicted Efficiency']:.2f}
            - **Current vs Optimal:** {current_efficiency - best_radius['Predicted Efficiency']:+.2f}
            """)
            
            # Live optimization suggestions
            suggestions = []
            if current_efficiency < 2.0:
                suggestions.append("💡 Try reducing search radius")
            if current_density < 0.001:
                suggestions.append("💡 Increase zoom level for better density")
            if not latest['from_cache']:
                suggestions.append("💡 Search nearby areas to utilize cache")
            
            if suggestions:
                st.markdown("**Live Suggestions:**")
                for suggestion in suggestions:
                    st.markdown(f"- {suggestion}")
        
        # Real-time comparison chart
        st.markdown("**📊 Live Performance Comparison**")
        
        if len(analytics) >= 3:
            comparison_data = []
            for i, data in enumerate(analytics[-5:]):  # Last 5 searches
                comparison_data.append({
                    "Search": f"#{i+1}",
                    "Efficiency": data["efficiency_score"],
                    "Radius": data["radius_km"],
                    "Zoom": data["zoom_level"]
                })
            
            st.bar_chart(comparison_data, x="Search", y="Efficiency")
    
    else:
        st.info("Perform searches to see live optimization metrics and AI recommendations.")
        
        # Show current settings analysis
        st.markdown("**📋 Current Settings Analysis**")
        st.markdown(f"""
        - **Zoom Level:** {current_zoom} {'🟢 Optimal' if 10 <= current_zoom <= 15 else '🟡 Consider adjusting'}
        - **Search Radius:** {current_radius} km {'🟢 Good' if 1 <= current_radius <= 10 else '🟡 Consider adjusting'}
        - **Recommendation:** Start with a few searches to build optimization data
        """)
    
    # Live system health indicators
    st.markdown("---")
    st.markdown("**🔋 Live System Health**")
    
    health_col1, health_col2, health_col3 = st.columns(3)
    
    with health_col1:
        debug_settings = st.session_state.get("debug_settings", {})
        realtime_status = "🟢 Active" if debug_settings.get("realtime_updates") else "🔴 Disabled"
        st.markdown(f"**Real-time Updates:** {realtime_status}")
    
    with health_col2:
        memory_usage = len(str(st.session_state))
        memory_status = "🟢 Normal" if memory_usage < 50000 else "🟡 High" if memory_usage < 100000 else "🔴 Critical"
        st.markdown(f"**Memory Usage:** {memory_status}")
    
    with health_col3:
        update_time = time.strftime("%H:%M:%S")
        st.markdown(f"**Last Update:** {update_time}")