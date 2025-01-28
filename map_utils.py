import folium
from folium import plugins
from typing import Tuple, List, Dict
import branca.colormap as cm
import streamlit as st

def create_base_map() -> folium.Map:
    """Create the base Folium map with plugins"""
    # Create map with current session state
    m = folium.Map(
        location=st.session_state.map_center,
        zoom_start=st.session_state.zoom_level,
        tiles='OpenStreetMap',
        control_scale=True,
        prefer_canvas=True  # Use canvas renderer for better performance
    )

    # Add fullscreen button
    plugins.Fullscreen().add_to(m)

    # Add locate control
    plugins.LocateControl().add_to(m)

    return m

def get_relevance_color(relevance: float) -> str:
    """Get marker color based on relevance score"""
    if relevance >= 0.8:
        return 'red'
    elif relevance >= 0.5:
        return 'orange'
    else:
        return 'blue'

def create_marker_cluster() -> plugins.MarkerCluster:
    """Create a marker cluster group"""
    return plugins.MarkerCluster(
        name='Landmarks',
        overlay=True,
        control=True,
        icon_create_function=None,
        options={
            'maxClusterRadius': 50,
            'disableClusteringAtZoom': 16
        }
    )

def add_landmarks_to_map(m: folium.Map, landmarks: List[Dict], show_heatmap: bool = False) -> None:
    """Add landmark markers to the map with clustering and optional heatmap"""
    # Create marker cluster and add to map
    marker_cluster = create_marker_cluster()
    marker_cluster.add_to(m)

    # Prepare heatmap data
    heat_data = []

    for landmark in landmarks:
        # Get color based on relevance
        color = get_relevance_color(landmark['relevance'])

        # Create custom popup HTML
        popup_html = f"""
        <div style="width:200px">
            <h4>{landmark['title']}</h4>
            <p><b>Distance:</b> {landmark['distance']}km</p>
            <p><b>Relevance:</b> {landmark['relevance']}</p>
            <p>{landmark['summary'][:100]}...</p>
            <a href="{landmark['url']}" target="_blank">Read more</a>
        </div>
        """

        # Create marker
        marker = folium.Marker(
            location=landmark['coordinates'],
            popup=folium.Popup(popup_html, max_width=300),
            icon=folium.Icon(color=color, icon='info-sign'),
        )
        marker.add_to(marker_cluster)

        # Add to heatmap data
        heat_data.append([
            landmark['coordinates'][0],
            landmark['coordinates'][1],
            landmark['relevance'] * 100  # Scale weight for visibility
        ])

    # Add heatmap if there's data and it's enabled
    if heat_data and show_heatmap:
        plugins.HeatMap(
            data=heat_data,
            name='Heatmap',
            min_opacity=0.3,
            max_zoom=18,
            radius=25,
            blur=15,
            overlay=True,
            control=True,
            show=show_heatmap
        ).add_to(m)

    # Add layer control
    folium.LayerControl().add_to(m)

def draw_distance_circle(m: folium.Map, center: Tuple[float, float], radius_km: float):
    """Draw a circle with given radius around a point"""
    folium.Circle(
        location=center,
        radius=radius_km * 1000,  # Convert km to meters
        color='green',
        fill=True,
        popup=f'{radius_km}km radius'
    ).add_to(m)