import streamlit as st
import folium
from folium import plugins
from streamlit_folium import st_folium
from typing import List, Dict, Any, Optional
from utils.coord_utils import validate_coords, ensure_coord_format
import os
import logging

logger = logging.getLogger("map")


# cache by a global-var if more blank map (missing map-data) occurred
@st.cache_data(ttl=600, show_spinner=False)
def create_base_map(center: List[float], zoom: int) -> folium.Map:
    """
    Create a base folium map with multiple tile layers and performance optimizations

    Args:
        center: [latitude, longitude] for map center
        zoom: Initial zoom level

    Returns:
        folium map instance (reuse for map rendering and interactions, panning and zooming)
    """
    logger.debug(f"Creating base map at {center} with zoom {zoom}")

    # Configure map with tile caching if provided
    m = folium.Map(
        location=center,
        zoom_start=zoom,
        tiles=None,  # No default tile layer, we'll add our own below
        attr=None,
        control_scale=True,
        prefer_canvas=True,  # Use canvas for better performance
        zoom_control=True,  # Enable default zoom control
    )

    # Add Google Maps tile layer - faster and smoother
    folium.TileLayer(
        tiles="https://{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
        attr="Google",
        name="Google Maps",
        max_zoom=20,
        subdomains=["mt0", "mt1", "mt2", "mt3"],
        overlay=False,
        control=True,
        show=True,  # Default visible layer
    ).add_to(m)

    # Add Google Satellite tile layer
    folium.TileLayer(
        tiles="https://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
        attr="Google",
        name="Google Satellite",
        max_zoom=20,
        subdomains=["mt0", "mt1", "mt2", "mt3"],
        overlay=False,
        control=True,
        show=False,
    ).add_to(m)

    # Add Streets with labels - hybrid view
    folium.TileLayer(
        tiles="https://{s}.google.com/vt/lyrs=s,h&x={x}&y={y}&z={z}",
        attr="Google",
        name="Satellite with Labels",
        max_zoom=20,
        subdomains=["mt0", "mt1", "mt2", "mt3"],
        overlay=False,
        control=True,
        show=False,
    ).add_to(m)

    # Add Google Terrain/Earth view layer
    folium.TileLayer(
        tiles="https://{s}.google.com/vt/lyrs=p&x={x}&y={y}&z={z}",
        attr="Google",
        name="Google Terrain",
        max_zoom=20,
        subdomains=["mt0", "mt1", "mt2", "mt3"],
        overlay=False,
        control=True,
        show=False,
    ).add_to(m)

    # Add Hillshade/3D terrain layer (gives some 3D-like effect)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Shaded_Relief/MapServer/tile/{z}/{y}/{x}",
        attr="ESRI",
        name="3D Terrain View",
        overlay=False,
        control=True,
        show=False,
    ).add_to(m)

    # Add OpenStreetMap tile layer
    folium.TileLayer(
        tiles="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        attr="OpenStreetMap",
        name="OpenStreetMap",
        max_zoom=19,
        overlay=False,
        control=True,
        show=False,
    ).add_to(m)

    import time

    # add more sleep if more blank map (missing map-data) occurred
    time.sleep(0.3)  # Small delay to ensure map is ready
    return m


def render_map(center: List[float], zoom: int) -> Optional[Dict[str, Any]]:
    """
    Render an interactive folium map with optimized interaction handling.

    Args:
        center: [latitude, longitude] for map center
        zoom: Initial zoom level

    Returns:
        Dictionary with map interaction data or None if error
    """
    try:
        # Validate coordinates using our standardized function
        if len(center) != 2 or not validate_coords(center[0], center[1]):
            logger.error(f"Invalid map center coordinates: {center}")
            return None

        m = create_base_map(center, zoom)

        if "landmarks" in st.session_state and st.session_state.landmarks:
            add_landmarks_to_map(m, center, st.session_state.landmarks)

        if (search_radius := st.session_state.get("radius", 5)) > 0:
            draw_distance_circle(m, center, search_radius)

        # Add layer control with better positioning
        folium.LayerControl(position="topright").add_to(m)

        # Get viewport height from URL parameters using st.query_params
        optimal_height = 600  # Default height
        if "vh" in st.query_params:
            optimal_height = int(st.query_params["vh"])

        # Display the map with calculated height
        map_data = st_folium(
            m,
            width="100%",
            height=optimal_height,
            returned_objects=["center", "zoom"],
            key="interactive_map",
            use_container_width=True,  # Use full width of container
        )

        return map_data

    except Exception as e:
        logger.error(f"Error rendering map: {str(e)}")
        return None


def local_file_to_url(file_path):
    """
    Convert a file path to a data URL with base64 encoding to work cross-platform
    """
    if not file_path or file_path == "":
        return ""

    # Check if it's already a web URL
    if file_path.startswith("http://") or file_path.startswith("https://"):
        return file_path

    # Strip any existing file:// prefix if present
    if file_path.startswith("file://"):
        file_path = file_path[7:]  # Remove 'file://'

    try:
        abs_path = os.path.abspath(file_path)
        # Convert the file to a data URL using base64 encoding
        # This works across all platforms and browsers
        with open(abs_path, "rb") as img_file:
            import base64

            img_data = base64.b64encode(img_file.read()).decode("utf-8")
            return f"data:image/jpeg;base64,{img_data}"
    except Exception as e:
        logger.error(f"Error reading image file {file_path}: {str(e)}")
        # If we fail to read the file, log the error and return an empty string
        # This will show a broken image in the UI
        return ""

    return file_path


def add_landmarks_to_map(m: folium.Map, center, landmarks: List[Dict]) -> None:
    """
    Add landmark markers to the map with clustering

    Args:
        m: Folium map instance
        landmarks: List of landmark dictionaries, each containing at least 'name', 'lat', 'lon'
    """
    if not landmarks or len(landmarks) == 0:
        return

    logger.debug(f"Marking {len(landmarks)} landmarks near {center}")

    # Create a marker cluster for better performance with many points
    marker_cluster = plugins.MarkerCluster(
        name="Landmarks",
        overlay=True,
        control=True,
        options={"maxClusterRadius": 100, "disableClusteringAtZoom": 12},
    ).add_to(m)
    # landmark_group = folium.FeatureGroup(name="Landmarks").add_to(m)  # saved don't delete

    for landmark in landmarks:
        # Ensure landmark has required coordinates
        if "coordinates" not in landmark:
            logger.warning(
                f"Landmark missing coordinates: {landmark.get('name', 'unknown')}"
            )
            continue

        try:
            coords = landmark["coordinates"]
            local_url = local_file_to_url(landmark.get("image_url", ""))

            # Create custom popup HTML
            popup_html = f"""
            <div style="width:200px">
                <h5>{landmark["title"]}</h5>
                <img src="{local_url}" width="200px">
                <p>{landmark["summary"][:100]}…</p>
                <p><small>{coords[0]:.5f}, {coords[1]:.5f}</small></p>
            </div>
            """

            marker = folium.Marker(
                location=coords,
                popup=folium.Popup(popup_html, max_width=300),
                icon=folium.Icon(
                    color="blue" if (coords == center) else "lightgray"
                ),
                tooltip=landmark.get("name", "Landmark"),
            )
            marker.add_to(marker_cluster)
            # marker.add_to(landmark_group)  # saved don't delete
        except (ValueError, TypeError) as e:
            logger.error(
                f"Error marking landmark: {landmark.get('name', 'unknown')}: {str(e)}"
            )


def draw_distance_circle(m: folium.Map, center, radius_km: float):
    """
    Draw a circle with given radius around a point

    Args:
        m: Folium map instance
        center: Coordinates (lat, lon) in any supported format
        radius_km: Radius in kilometers
    """
    location = ensure_coord_format(center)

    folium.Circle(
        location=location,
        radius=radius_km * 1000,  # Convert km to meters
        color="green",
        fill=True,
        fill_opacity=0.1,
        popup=f"{radius_km}km radius",
    ).add_to(m)
