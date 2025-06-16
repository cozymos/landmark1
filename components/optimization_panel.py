"""
Optimization Panel Component for Landmark Locator

Provides advanced analytics and customization for zoom-to-radius optimization.
"""

import streamlit as st
import pandas as pd
import time
from typing import List, Dict, Any
import math


def render_optimization_metrics():
    """
    Render comprehensive optimization metrics and controls.
    """
    st.markdown("### 🎯 Advanced Optimization Metrics")
    
    analytics = st.session_state.get("zoom_radius_analytics", [])
    if not analytics:
        st.info("No optimization data available. Perform searches to generate analytics.")
        return
    
    # Create comprehensive metrics dashboard
    col1, col2, col3, col4 = st.columns(4)
    
    # Calculate key metrics
    total_searches = len(analytics)
    cache_hits = sum(1 for d in analytics if d["from_cache"])
    cache_hit_rate = cache_hits / total_searches * 100
    avg_efficiency = sum(d["efficiency_score"] for d in analytics) / total_searches
    avg_density = sum(d["density_per_km2"] for d in analytics) / total_searches
    
    with col1:
        st.metric(
            "Total Searches",
            total_searches,
            delta=f"+{len(analytics[-5:])}" if len(analytics) >= 5 else None
        )
    
    with col2:
        st.metric(
            "Cache Hit Rate",
            f"{cache_hit_rate:.1f}%",
            delta=f"+{cache_hit_rate - 50:.1f}%" if cache_hit_rate > 50 else f"{cache_hit_rate - 50:.1f}%"
        )
    
    with col3:
        st.metric(
            "Avg Efficiency",
            f"{avg_efficiency:.2f}",
            delta=f"+{avg_efficiency - 2:.2f}" if avg_efficiency > 2 else f"{avg_efficiency - 2:.2f}"
        )
    
    with col4:
        st.metric(
            "Avg Density",
            f"{avg_density:.4f}/km²",
            delta=None
        )


def render_customizable_charts():
    """
    Render customizable analytics charts with user controls.
    """
    st.markdown("### 📊 Customizable Analytics Charts")
    
    analytics = st.session_state.get("zoom_radius_analytics", [])
    if not analytics:
        return
    
    # Chart customization controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        chart_type = st.selectbox(
            "Chart Type",
            ["Line Chart", "Scatter Plot", "Bar Chart", "Area Chart"],
            key="chart_type"
        )
    
    with col2:
        x_axis = st.selectbox(
            "X-Axis",
            ["Search Number", "Zoom Level", "Radius", "Timestamp"],
            key="x_axis"
        )
    
    with col3:
        y_axis = st.selectbox(
            "Y-Axis",
            ["Efficiency Score", "Density", "Landmark Count", "Zoom-Radius Ratio"],
            key="y_axis"
        )
    
    # Prepare chart data
    chart_data = []
    for i, data in enumerate(analytics[-50:]):  # Last 50 searches
        row = {
            "Search Number": i + 1,
            "Zoom Level": data["zoom_level"],
            "Radius": data["radius_km"],
            "Timestamp": data["timestamp"],
            "Efficiency Score": data["efficiency_score"],
            "Density": data["density_per_km2"],
            "Landmark Count": data["landmark_count"],
            "Zoom-Radius Ratio": data["zoom_radius_ratio"]
        }
        chart_data.append(row)
    
    if chart_data:
        df = pd.DataFrame(chart_data)
        
        # Render selected chart type
        if chart_type == "Line Chart":
            st.line_chart(df.set_index(x_axis)[y_axis])
        elif chart_type == "Scatter Plot":
            st.scatter_chart(df, x=x_axis, y=y_axis)
        elif chart_type == "Bar Chart":
            if x_axis in ["Zoom Level", "Radius"]:
                # Group by x_axis and average y_axis
                grouped = df.groupby(x_axis)[y_axis].mean().reset_index()
                st.bar_chart(grouped.set_index(x_axis))
            else:
                st.bar_chart(df.set_index(x_axis)[y_axis])
        elif chart_type == "Area Chart":
            st.area_chart(df.set_index(x_axis)[y_axis])


def render_advanced_filters():
    """
    Render advanced filtering and data analysis tools.
    """
    st.markdown("### 🔍 Advanced Data Filters")
    
    analytics = st.session_state.get("zoom_radius_analytics", [])
    if not analytics:
        return
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        zoom_filter = st.slider(
            "Filter by Zoom Level",
            min_value=min(d["zoom_level"] for d in analytics),
            max_value=max(d["zoom_level"] for d in analytics),
            value=(min(d["zoom_level"] for d in analytics), max(d["zoom_level"] for d in analytics)),
            key="zoom_filter"
        )
    
    with col2:
        radius_filter = st.slider(
            "Filter by Radius (km)",
            min_value=min(d["radius_km"] for d in analytics),
            max_value=max(d["radius_km"] for d in analytics),
            value=(min(d["radius_km"] for d in analytics), max(d["radius_km"] for d in analytics)),
            key="radius_filter"
        )
    
    with col3:
        cache_filter = st.selectbox(
            "Filter by Cache Status",
            ["All", "Cache Hits Only", "Cache Misses Only"],
            key="cache_filter"
        )
    
    # Apply filters
    filtered_data = []
    for data in analytics:
        if (zoom_filter[0] <= data["zoom_level"] <= zoom_filter[1] and
            radius_filter[0] <= data["radius_km"] <= radius_filter[1]):
            
            if cache_filter == "All":
                filtered_data.append(data)
            elif cache_filter == "Cache Hits Only" and data["from_cache"]:
                filtered_data.append(data)
            elif cache_filter == "Cache Misses Only" and not data["from_cache"]:
                filtered_data.append(data)
    
    if filtered_data:
        st.markdown(f"**Filtered Results: {len(filtered_data)} searches**")
        
        # Display filtered statistics
        avg_efficiency = sum(d["efficiency_score"] for d in filtered_data) / len(filtered_data)
        avg_density = sum(d["density_per_km2"] for d in filtered_data) / len(filtered_data)
        avg_landmarks = sum(d["landmark_count"] for d in filtered_data) / len(filtered_data)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Avg Efficiency", f"{avg_efficiency:.2f}")
        with col2:
            st.metric("Avg Density", f"{avg_density:.4f}")
        with col3:
            st.metric("Avg Landmarks", f"{avg_landmarks:.1f}")
        
        # Export filtered data
        if st.button("📤 Export Filtered Data", key="export_btn"):
            df = pd.DataFrame(filtered_data)
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"landmark_analytics_{time.strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    else:
        st.warning("No data matches the current filters.")


def render_machine_learning_insights():
    """
    Render machine learning-powered insights and predictions.
    """
    st.markdown("### 🤖 AI-Powered Insights")
    
    analytics = st.session_state.get("zoom_radius_analytics", [])
    if len(analytics) < 10:
        st.warning("Need at least 10 searches to generate ML insights.")
        return
    
    # Calculate correlations
    zoom_levels = [d["zoom_level"] for d in analytics]
    radii = [d["radius_km"] for d in analytics]
    efficiencies = [d["efficiency_score"] for d in analytics]
    densities = [d["density_per_km2"] for d in analytics]
    
    # Simple correlation calculations
    zoom_efficiency_corr = calculate_correlation(zoom_levels, efficiencies)
    radius_efficiency_corr = calculate_correlation(radii, efficiencies)
    zoom_density_corr = calculate_correlation(zoom_levels, densities)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Correlation Analysis**")
        st.markdown(f"- Zoom vs Efficiency: {zoom_efficiency_corr:.3f}")
        st.markdown(f"- Radius vs Efficiency: {radius_efficiency_corr:.3f}")
        st.markdown(f"- Zoom vs Density: {zoom_density_corr:.3f}")
        
        # Interpretation
        if abs(zoom_efficiency_corr) > 0.5:
            trend = "positively" if zoom_efficiency_corr > 0 else "negatively"
            st.info(f"Zoom level is {trend} correlated with efficiency.")
        
        if abs(radius_efficiency_corr) > 0.5:
            trend = "positively" if radius_efficiency_corr > 0 else "negatively"
            st.info(f"Radius is {trend} correlated with efficiency.")
    
    with col2:
        st.markdown("**Predictive Recommendations**")
        
        # Find optimal patterns
        best_searches = sorted(analytics, key=lambda x: x["efficiency_score"], reverse=True)[:5]
        optimal_zoom = sum(s["zoom_level"] for s in best_searches) / len(best_searches)
        optimal_radius = sum(s["radius_km"] for s in best_searches) / len(best_searches)
        
        st.success(f"""
        **Predicted Optimal Settings:**
        - Zoom Level: {optimal_zoom:.1f}
        - Radius: {optimal_radius:.1f} km
        - Expected Efficiency: {sum(s["efficiency_score"] for s in best_searches) / len(best_searches):.2f}
        """)
        
        # Performance prediction for current settings
        current_zoom = st.session_state.get("zoom_level", 12)
        current_radius = st.session_state.get("radius", 5)
        
        predicted_efficiency = predict_efficiency(analytics, current_zoom, current_radius)
        st.markdown(f"**Current Settings Prediction:** {predicted_efficiency:.2f} efficiency")


def calculate_correlation(x: List[float], y: List[float]) -> float:
    """Calculate Pearson correlation coefficient."""
    if len(x) != len(y) or len(x) < 2:
        return 0.0
    
    n = len(x)
    sum_x = sum(x)
    sum_y = sum(y)
    sum_xy = sum(xi * yi for xi, yi in zip(x, y))
    sum_x2 = sum(xi * xi for xi in x)
    sum_y2 = sum(yi * yi for yi in y)
    
    numerator = n * sum_xy - sum_x * sum_y
    denominator = math.sqrt((n * sum_x2 - sum_x * sum_x) * (n * sum_y2 - sum_y * sum_y))
    
    return numerator / denominator if denominator != 0 else 0.0


def predict_efficiency(analytics: List[Dict], zoom: int, radius: float) -> float:
    """Simple efficiency prediction based on historical data."""
    # Find similar configurations
    similar_searches = []
    for data in analytics:
        zoom_diff = abs(data["zoom_level"] - zoom)
        radius_diff = abs(data["radius_km"] - radius)
        
        if zoom_diff <= 2 and radius_diff <= 2:
            similarity = 1 / (1 + zoom_diff + radius_diff)
            similar_searches.append((data["efficiency_score"], similarity))
    
    if similar_searches:
        # Weighted average based on similarity
        total_weight = sum(weight for _, weight in similar_searches)
        weighted_sum = sum(score * weight for score, weight in similar_searches)
        return weighted_sum / total_weight
    else:
        # Fallback to overall average
        return sum(d["efficiency_score"] for d in analytics) / len(analytics)


def render_data_export_tools():
    """
    Render data export and sharing tools.
    """
    st.markdown("### 📤 Data Export & Sharing")
    
    analytics = st.session_state.get("zoom_radius_analytics", [])
    if not analytics:
        st.info("No data available to export.")
        return
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Export Full Dataset"):
            df = pd.DataFrame(analytics)
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download Full CSV",
                data=csv,
                file_name=f"landmark_full_analytics_{time.strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    with col2:
        if st.button("📈 Export Summary Report"):
            summary = generate_summary_report(analytics)
            st.download_button(
                label="Download Summary",
                data=summary,
                file_name=f"landmark_summary_{time.strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )
    
    with col3:
        if st.button("🔧 Export Configuration"):
            config = generate_optimization_config(analytics)
            st.download_button(
                label="Download Config",
                data=config,
                file_name=f"landmark_config_{time.strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )


def generate_summary_report(analytics: List[Dict]) -> str:
    """Generate a text summary report of analytics data."""
    total_searches = len(analytics)
    cache_hits = sum(1 for d in analytics if d["from_cache"])
    cache_hit_rate = cache_hits / total_searches * 100
    avg_efficiency = sum(d["efficiency_score"] for d in analytics) / total_searches
    best_search = max(analytics, key=lambda x: x["efficiency_score"])
    
    report = f"""
Landmark Locator Analytics Summary Report
Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}

OVERVIEW
========
Total Searches: {total_searches}
Cache Hit Rate: {cache_hit_rate:.1f}%
Average Efficiency: {avg_efficiency:.2f}

BEST PERFORMANCE
===============
Zoom Level: {best_search['zoom_level']}
Radius: {best_search['radius_km']} km
Efficiency Score: {best_search['efficiency_score']:.2f}
Landmarks Found: {best_search['landmark_count']}
Timestamp: {best_search['timestamp']}

RECOMMENDATIONS
==============
- Optimal zoom range: {min(d['zoom_level'] for d in analytics if d['efficiency_score'] > avg_efficiency)}-{max(d['zoom_level'] for d in analytics if d['efficiency_score'] > avg_efficiency)}
- Optimal radius range: {min(d['radius_km'] for d in analytics if d['efficiency_score'] > avg_efficiency):.1f}-{max(d['radius_km'] for d in analytics if d['efficiency_score'] > avg_efficiency):.1f} km
- Cache utilization: {'Good' if cache_hit_rate > 50 else 'Needs improvement'}
"""
    return report


def generate_optimization_config(analytics: List[Dict]) -> str:
    """Generate a JSON configuration file with optimal settings."""
    import json
    
    best_searches = sorted(analytics, key=lambda x: x["efficiency_score"], reverse=True)[:5]
    
    config = {
        "optimization_config": {
            "recommended_zoom": sum(s["zoom_level"] for s in best_searches) / len(best_searches),
            "recommended_radius": sum(s["radius_km"] for s in best_searches) / len(best_searches),
            "expected_efficiency": sum(s["efficiency_score"] for s in best_searches) / len(best_searches),
            "generated_from_searches": len(analytics),
            "cache_hit_rate": sum(1 for d in analytics if d["from_cache"]) / len(analytics) * 100,
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
        },
        "top_configurations": [
            {
                "zoom": s["zoom_level"],
                "radius": s["radius_km"],
                "efficiency": s["efficiency_score"],
                "landmarks": s["landmark_count"]
            }
            for s in best_searches
        ]
    }
    
    return json.dumps(config, indent=2)