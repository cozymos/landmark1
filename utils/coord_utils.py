import re
from typing import Tuple, Optional
from dataclasses import dataclass
import math


@dataclass
class Coordinates:
    lat: float
    lon: float


def round_coordinates_by_radius(
    lat: float, lon: float, radius_km: int
) -> Tuple[float, float]:
    """
    Round geo-coordinates (latitude, longitude) to a precision that corresponds
    to the given radius in kilometers.

    Args:
        lat (float): The latitude in decimal degrees
        lon (float): The longitude in decimal degrees
        radius_km (float): The desired radius in kilometers

    Returns:
        tuple: (rounded_latitude, rounded_longitude) in decimal degrees
    """
    # Validate the coordinates are in proper range
    if not validate_coords(lat, lon):
        raise ValueError(f"Invalid coordinates: lat={lat}, lon={lon}")

    # Make sure radius is a positive number
    radius = abs(float(radius_km))
    if radius <= 0:
        radius = 1.0  # Default to 1km if invalid

    # Earth's radius in kilometers
    # EARTH_RADIUS_KM = 6371.0

    # Calculate appropriate decimal precision
    # 1 degree of latitude is approximately 111 km
    # 1 degree of longitude varies with latitude (gets smaller as you move away from equator)

    # For latitude: determine decimal places needed for the given radius
    # The formula approximates the number of decimal places needed
    lat_precision = max(0, math.ceil(-math.log10(radius / 111.0)))

    # For longitude: need to account for the convergence of meridians
    # The distance between longitude lines decreases as you move away from the equator
    # At the equator, 1 degree of longitude is about 111 km
    # At latitude φ, 1 degree of longitude is about 111 * cos(φ) km
    longitude_km_per_degree = 111.0 * math.cos(math.radians(abs(lat)))
    lon_precision = max(
        0, math.ceil(-math.log10(radius / longitude_km_per_degree))
    )

    # Round the coordinates to the calculated precision
    rounded_latitude = round(lat, lat_precision)
    rounded_longitude = round(lon, lon_precision)

    return rounded_latitude, rounded_longitude


def parse_dms(dms: str) -> Optional[float]:
    """Parse a DMS (degrees, minutes, seconds) string into decimal degrees"""
    # Pattern for DMS: optional direction + degrees°minutes′seconds″direction
    # Handles both standard quotes ('/) and prime characters (′/″)
    pattern = r"^([NSEW])?\s*(\d+)\s*°\s*(\d+)\s*[\'′]\s*([\d.]+)\s*[\"″]\s*([NSEW])?$"
    match = re.match(pattern, dms.strip())

    if not match:
        return None

    prefix_dir, degrees, minutes, seconds, suffix_dir = match.groups()
    direction = prefix_dir or suffix_dir  # Use whichever direction was provided

    if not direction:
        return None

    degrees = float(degrees)
    minutes = float(minutes)
    seconds = float(seconds)

    # Convert to decimal degrees
    decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)

    # Make negative for South or West
    if direction in ["S", "W"]:
        decimal = -decimal

    return decimal


def parse_dd(dd: str) -> Optional[float]:
    """Parse a decimal degrees string"""
    try:
        return float(dd.strip())
    except ValueError:
        return None


def parse_coordinates(coord_str: str) -> Optional[Coordinates]:
    """Parse coordinates in either DD or DMS format"""
    # Remove any whitespace
    coord_str = coord_str.strip()

    # Split into lat/lon components
    parts = [p.strip() for p in coord_str.split(",")]
    if len(parts) != 2:
        return None

    lat_str, lon_str = parts

    # Try DMS format first
    if "°" in lat_str and "°" in lon_str:
        lat = parse_dms(lat_str)
        lon = parse_dms(lon_str)
    else:
        # Try DD format
        lat = parse_dd(lat_str)
        lon = parse_dd(lon_str)

    if lat is not None and lon is not None:
        if validate_coords(lat, lon):
            return Coordinates(lat, lon)

    return None


def format_dms(decimal: float, is_latitude: bool) -> str:
    """Convert decimal degrees to DMS format"""
    direction = (
        "N"
        if decimal >= 0 and is_latitude
        else "S"
        if is_latitude
        else "E"
        if decimal >= 0
        else "W"
    )
    decimal = abs(decimal)

    degrees = int(decimal)
    minutes = int((decimal - degrees) * 60)
    seconds = round(((decimal - degrees) * 60 - minutes) * 60, 2)

    return f"{degrees}° {minutes}' {seconds}\"{direction}"


def validate_coords(lat: float, lon: float) -> bool:
    """
    Validate that coordinates are within proper ranges

    Args:
        lat: Latitude value to validate
        lon: Longitude value to validate

    Returns:
        True if coordinates are valid, False otherwise
    """
    try:
        lat_float = float(lat)
        lon_float = float(lon)
        return -90 <= lat_float <= 90 and -180 <= lon_float <= 180
    except (ValueError, TypeError):
        return False


def standardize_coord_dict(coord_dict: dict) -> dict:
    """
    Standardize coordinate dictionary to ensure it uses 'lon' key instead of 'lng'

    Args:
        coord_dict: Dictionary that may contain lat/lng or lat/lon keys

    Returns:
        Standardized dictionary with 'lat' and 'lon' keys
    """
    if not isinstance(coord_dict, dict):
        raise ValueError(f"Expected dictionary but received {type(coord_dict)}")

    result = coord_dict.copy()

    # Ensure we have the latitude value (case-insensitive)
    if "lat" not in result:
        # Check for various forms of latitude keys
        for key in result.keys():
            if isinstance(key, str) and key.lower() in ["latitude", "lat"]:
                result["lat"] = result[key]
                break

    # Handle longitude - standardize to 'lon' (case-insensitive)
    if "lon" not in result:
        # Check for various forms of longitude keys
        for key in result.keys():
            if isinstance(key, str) and key.lower() in [
                "longitude",
                "lng",
                "long",
            ]:
                result["lon"] = result[key]
                # Remove the original key to avoid duplicates if not 'lon'
                if key != "lon":
                    del result[key]
                break

    # Ensure coordinates are numeric
    if "lat" in result and "lon" in result:
        try:
            result["lat"] = float(result["lat"])
            result["lon"] = float(result["lon"])
        except (ValueError, TypeError):
            raise ValueError(
                f"Coordinates must be numeric: lat={result.get('lat')}, lon={result.get('lon')}"
            )

        # Validate coordinates are in valid ranges
        if not validate_coords(result["lat"], result["lon"]):
            raise ValueError(
                f"Invalid coordinate ranges: lat={result['lat']}, lon={result['lon']}"
            )
    else:
        missing = []
        if "lat" not in result:
            missing.append("lat")
        if "lon" not in result:
            missing.append("lon")
        raise ValueError(
            f"Standardized coordinates missing required keys: {', '.join(missing)}"
        )

    return result


def list_to_coord_dict(coord_list: list) -> dict:
    """
    Convert a coordinate list [lat, lon] to a standardized dictionary

    Args:
        coord_list: List containing [latitude, longitude]

    Returns:
        Standardized dictionary with 'lat' and 'lon' keys
    """
    if not isinstance(coord_list, list) or len(coord_list) < 2:
        raise ValueError(f"Invalid coordinate list: {coord_list}")

    try:
        # Convert to float for consistency
        lat, lon = float(coord_list[0]), float(coord_list[1])
    except (ValueError, TypeError):
        raise ValueError(f"Coordinates must be numeric: {coord_list}")

    # Validate coordinates
    if not validate_coords(lat, lon):
        raise ValueError(f"Invalid coordinates in list: lat={lat}, lon={lon}")

    return {"lat": lat, "lon": lon}


def ensure_coord_format(coords) -> list:
    """
    Ensure coordinates are in standard [lat, lon] list format

    Args:
        coords: Coordinates in various formats (list, dict, Coordinates object)

    Returns:
        Standardized [lat, lon] list
    """
    if isinstance(coords, list) and len(coords) >= 2:
        # Already a list, ensure it's valid
        if validate_coords(coords[0], coords[1]):
            return [float(coords[0]), float(coords[1])]
    elif isinstance(coords, dict):
        # Convert from dictionary format
        std_dict = standardize_coord_dict(coords)
        if "lat" in std_dict and "lon" in std_dict:
            return [float(std_dict["lat"]), float(std_dict["lon"])]
    elif isinstance(coords, Coordinates):
        # Convert from Coordinates object
        return [float(coords.lat), float(coords.lon)]
    elif isinstance(coords, tuple) and len(coords) >= 2:
        # Convert from tuple format
        if validate_coords(coords[0], coords[1]):
            return [float(coords[0]), float(coords[1])]

    raise ValueError(
        f"Could not convert to standard coordinate format: {coords}"
    )
