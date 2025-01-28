import folium
from typing import Tuple

def create_base_map() -> folium.Map:
    """Create the base Folium map"""
    return folium.Map(
        location=[0, 0],  # Default to null island
        zoom_start=2,
        tiles='OpenStreetMap',
        control_scale=True
    )

def get_map_bounds(m: folium.Map) -> Tuple[float, float, float, float]:
    """Get the current map bounds"""
    bounds = m.get_bounds()
    return (
        bounds['_southWest']['lat'],
        bounds['_southWest']['lng'],
        bounds['_northEast']['lat'],
        bounds['_northEast']['lng']
    )

def add_landmarks_to_map(m: folium.Map, landmarks: list) -> None:
    """Add landmark markers to the map"""
    for landmark in landmarks:
        folium.Marker(
            location=landmark['coordinates'],
            popup=landmark['title'],
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(m)
