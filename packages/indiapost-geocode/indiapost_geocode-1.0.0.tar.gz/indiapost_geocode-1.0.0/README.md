# indiapost-geocode

DIGIPIN encoder/decoder for India Post geocoding system.

## Installation
```bash
pip install indiapost-geocode
```

## Usage
```python
from indiapost_geocode import get_digipin, get_lat_lng_from_digipin

# Encode coordinates to DIGIPIN
pin = get_digipin(28.6139, 77.2090)
print(pin)  # Output: FFF-3MF-34F8

# Decode DIGIPIN to coordinates
coords = get_lat_lng_from_digipin('FFF-3MF-34F8')
print(coords)  # Output: {'latitude': 28.613900, 'longitude': 77.209000}
```

## License

MIT