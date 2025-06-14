"""
Debug Panel Component for Landmark Locator

Provides a collapsible debug interface with real-time metrics,
cache status, and API call monitoring.
"""

import streamlit as st
import time
from typing import Dict, Any, Optional
import json


def render_debug_panel():
    """
    Render the main debug panel underneath the map.
    Collapsible by default with grid layout inside.
    """
    # Debug view selector in sidebar
    debug_view = st.sidebar.selectbox(
        "Debug View",
        ["Overview", "Cache Details", "API Calls", "Session State"],
        index=0,
        help="Select which debug information to display"
    )
    
    # Main debug container - collapsible by default
    with st.expander("🐛 Debug Panel", expanded=False):
        
        if debug_view == "Overview":
            _render_overview()
        elif debug_view == "Cache Details":
            _render_cache_details()
        elif debug_view == "API Calls":
            _render_api_calls()
        elif debug_view == "Session State":
            _render_session_state()


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
    if cache_stats["hits"] + cache_stats["misses"] > 0:
        hit_rate = cache_stats["hits"] / (cache_stats["hits"] + cache_stats["misses"]) * 100
    
    status_color = "🟢" if hit_rate > 50 else "🟡" if hit_rate > 20 else "🔴"
    
    st.markdown(f"""
    <div style="font-size: 12px; line-height: 1.4;">
    {status_color} <strong>Hit Rate:</strong> {hit_rate:.1f}%<br>
    ✅ <strong>Hits:</strong> {cache_stats["hits"]}<br>
    ❌ <strong>Misses:</strong> {cache_stats["misses"]}<br>
    💾 <strong>Cached:</strong> {cache_stats["total_cached"]} items
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
    }.get(api_stats["last_call_status"], "⚪")
    
    last_call = api_stats["last_call_time"]
    time_since = ""
    if last_call:
        time_since = f" ({int(time.time() - last_call)}s ago)"
    
    st.markdown(f"""
    <div style="font-size: 12px; line-height: 1.4;">
    {status_icon} <strong>Status:</strong> {api_stats["last_call_status"]}{time_since}<br>
    🔄 <strong>Calls Made:</strong> {api_stats["google_places_calls"]}<br>
    ⏱️ <strong>Rate Limit:</strong> {api_stats["rate_limit_remaining"]}<br>
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
        if key.startswith("_"):  # Skip private streamlit keys
            continue
        if isinstance(value, (list, dict)) and len(str(value)) > 1000:
            filtered_state[key] = f"<Large object: {type(value).__name__} with {len(value) if hasattr(value, '__len__') else '?'} items>"
        else:
            filtered_state[key] = value
    
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