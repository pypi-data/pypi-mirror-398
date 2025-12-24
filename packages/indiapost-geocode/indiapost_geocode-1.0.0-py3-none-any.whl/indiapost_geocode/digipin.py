"""Core DIGIPIN encoding and decoding functions"""

DIGIPIN_GRID = [
    ['F', 'C', '9', '8'],
    ['J', '3', '2', '7'],
    ['K', '4', '5', '6'],
    ['L', 'M', 'P', 'T']
]

BOUNDS = {
    'min_lat': 2.5,
    'max_lat': 38.5,
    'min_lon': 63.5,
    'max_lon': 99.5
}


def get_digipin(lat, lon):
    """
    Encode latitude and longitude to DIGIPIN.
    
    Args:
        lat (float): Latitude in decimal degrees
        lon (float): Longitude in decimal degrees
        
    Returns:
        str: 10-character DIGIPIN code (format: XXX-XXX-XXXX)
        
    Raises:
        ValueError: If coordinates are out of bounds
    """
    if lat < BOUNDS['min_lat'] or lat > BOUNDS['max_lat']:
        raise ValueError(f'Latitude must be between {BOUNDS["min_lat"]} and {BOUNDS["max_lat"]}')
    if lon < BOUNDS['min_lon'] or lon > BOUNDS['max_lon']:
        raise ValueError(f'Longitude must be between {BOUNDS["min_lon"]} and {BOUNDS["max_lon"]}')
    
    min_lat, max_lat = BOUNDS['min_lat'], BOUNDS['max_lat']
    min_lon, max_lon = BOUNDS['min_lon'], BOUNDS['max_lon']
    
    digipin = ''
    
    for level in range(1, 11):
        lat_div = (max_lat - min_lat) / 4
        lon_div = (max_lon - min_lon) / 4
        
        # Reversed row logic to match original
        row = 3 - int((lat - min_lat) / lat_div)
        col = int((lon - min_lon) / lon_div)
        
        row = max(0, min(row, 3))
        col = max(0, min(col, 3))
        
        digipin += DIGIPIN_GRID[row][col]
        
        if level == 3 or level == 6:
            digipin += '-'
        
        # Update bounds (reverse logic for row)
        max_lat = min_lat + lat_div * (4 - row)
        min_lat = min_lat + lat_div * (3 - row)
        
        min_lon = min_lon + lon_div * col
        max_lon = min_lon + lon_div
    
    return digipin


def get_lat_lng_from_digipin(digipin):
    """
    Decode DIGIPIN to latitude and longitude.
    
    Args:
        digipin (str): DIGIPIN code (with or without hyphens)
        
    Returns:
        dict: Dictionary with 'latitude' and 'longitude' keys
        
    Raises:
        ValueError: If DIGIPIN is invalid
    """
    pin = digipin.replace('-', '')
    if len(pin) != 10:
        raise ValueError('DIGIPIN must be exactly 10 characters (excluding hyphens)')
    
    min_lat, max_lat = BOUNDS['min_lat'], BOUNDS['max_lat']
    min_lon, max_lon = BOUNDS['min_lon'], BOUNDS['max_lon']
    
    for i, char in enumerate(pin):
        found = False
        ri, ci = -1, -1
        
        # Locate character in DIGIPIN grid
        for r in range(4):
            for c in range(4):
                if DIGIPIN_GRID[r][c] == char:
                    ri, ci = r, c
                    found = True
                    break
            if found:
                break
        
        if not found:
            raise ValueError(f'Invalid character "{char}" at position {i+1} in DIGIPIN')
        
        lat_div = (max_lat - min_lat) / 4
        lon_div = (max_lon - min_lon) / 4
        
        lat1 = max_lat - lat_div * (ri + 1)
        lat2 = max_lat - lat_div * ri
        lon1 = min_lon + lon_div * ci
        lon2 = min_lon + lon_div * (ci + 1)
        
        # Update bounding box for next level
        min_lat, max_lat = lat1, lat2
        min_lon, max_lon = lon1, lon2
    
    center_lat = (min_lat + max_lat) / 2
    center_lon = (min_lon + max_lon) / 2
    
    return {
        'latitude': round(center_lat, 6),
        'longitude': round(center_lon, 6)
    }