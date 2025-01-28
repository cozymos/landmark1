import folium
from typing import Tuple

def create_base_map() -> folium.Map:
    """Create the base Folium map"""
    return folium.Map(
        location=[37.7749, -122.4194],  # Default to San Francisco
        zoom_start=12,
        tiles='OpenStreetMap',
        control_scale=True
    )

def get_map_bounds(m: folium.Map) -> Tuple[float, float, float, float]:
    """Get the current map bounds"""
    # Get the southwest and northeast bounds
    sw = m.get_bounds()[0]
    ne = m.get_bounds()[1]

    return (
        sw[0],  # south
        sw[1],  # west
        ne[0],  # north
        ne[1]   # east
    )

def add_landmarks_to_map(m: folium.Map, landmarks: list) -> None:
    """Add landmark markers to the map"""
    for landmark in landmarks:
        folium.Marker(
            location=landmark['coordinates'],
            popup=landmark['title'],
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(m)