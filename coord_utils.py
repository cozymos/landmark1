import re
from typing import Tuple, Optional
from dataclasses import dataclass

@dataclass
class Coordinates:
    lat: float
    lon: float

def parse_dms(dms: str) -> Optional[float]:
    """Parse a DMS (degrees, minutes, seconds) string into decimal degrees"""
    # Pattern for DMS: degrees°minutes'seconds"direction
    pattern = r'(\d+)°(\d+)\'([\d.]+)"([NSEW])'
    match = re.match(pattern, dms.strip())
    
    if not match:
        return None
        
    degrees = float(match.group(1))
    minutes = float(match.group(2))
    seconds = float(match.group(3))
    direction = match.group(4)
    
    # Convert to decimal degrees
    decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
    
    # Make negative for South or West
    if direction in ['S', 'W']:
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
    parts = [p.strip() for p in coord_str.split(',')]
    if len(parts) != 2:
        return None
        
    lat_str, lon_str = parts
    
    # Try DMS format first
    if '°' in lat_str and '°' in lon_str:
        lat = parse_dms(lat_str)
        lon = parse_dms(lon_str)
    else:
        # Try DD format
        lat = parse_dd(lat_str)
        lon = parse_dd(lon_str)
        
    if lat is not None and lon is not None:
        # Validate coordinates
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            return Coordinates(lat, lon)
            
    return None

def format_dms(decimal: float, is_latitude: bool) -> str:
    """Convert decimal degrees to DMS format"""
    direction = 'N' if decimal >= 0 and is_latitude else 'S' if is_latitude else 'E' if decimal >= 0 else 'W'
    decimal = abs(decimal)
    
    degrees = int(decimal)
    minutes = int((decimal - degrees) * 60)
    seconds = round(((decimal - degrees) * 60 - minutes) * 60, 2)
    
    return f"{degrees}°{minutes}'{seconds}\"{direction}"
