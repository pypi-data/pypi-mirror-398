# AeroNavX

**Advanced Aviation Analytics Library for Python**

A production-grade Python library for airport data, flight geometry, network intelligence, emissions analysis, and passenger experience optimization.

[![PyPI version](https://badge.fury.io/py/aeronavx.svg)](https://pypi.org/project/aeronavx/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Latest Release: v2.0.5** - Production-grade fixes: great_circle_path TypeError fixed, Airport model normalized, all imports verified

---

## Features

### Core Features
- **Airport Database**: 84,000+ global airports from [OurAirports](https://ourairports.com) (MIT License)
- **Distance Calculations**: Haversine, Vincenty, and Spherical Law of Cosines
- **Geodesy**: Bearings, midpoints, great circle paths
- **Search**: Fuzzy name search, nearest neighbor queries, radius search
- **Routing**: Multi-segment routes, flight time estimation, shortest paths
- **Emissions**: CO2 emissions estimation per passenger
- **Weather**: METAR and TAF data fetching (requires `requests`)
- **Timezone Support**: Automatic timezone detection and local time conversion

### NEW in v2.0.0+
- **Network Intelligence**: Hub scoring, connectivity analysis, global/regional network metrics
- **Synthetic Route Engine**: Generate realistic flight routes with waypoints and flight profiles
- **Advanced Emissions Calculator**: Detailed emissions analysis with aircraft types and SAF comparisons
- **Geo-Spatial Advanced**: Route comparison, optimal altitude calculation, polar route detection
- **Passenger Experience**: Jet lag analysis, fatigue assessment, optimal departure time recommendations

---

## Installation

```bash
pip install aeronavx
```

**With optional dependencies:**
```bash
# Full features (pandas, scipy, timezonefinder, rapidfuzz, requests)
pip install aeronavx[full]

# API server support
pip install aeronavx[api]

# Everything
pip install aeronavx[all]
```

**From source:**
```bash
git clone https://github.com/teyfikoz/AeroNavX.git
cd AeroNavX
pip install -e .
```

---

## Quick Start

### Basic Usage

```python
import aeronavx

# Get airports
ist = aeronavx.get_airport("IST")
jfk = aeronavx.get_airport("JFK")

print(f"{ist.name} ({ist.iata_code})")  # Istanbul Airport (IST)
print(f"{jfk.name} ({jfk.iata_code})")  # John F Kennedy International Airport (JFK)

# Calculate distance
dist_km = ist.distance_to(jfk)
print(f"Distance: {dist_km:.2f} km")  # Distance: 8031.54 km

# Find nearest airports
nearest = aeronavx.nearest_airports(41.0, 29.0, n=5)
for airport in nearest:
    iata = airport.iata_code if airport.iata_code else "---"
    print(f"  {iata}: {airport.name}")

# Estimate CO2 emissions
co2 = aeronavx.estimate_co2_kg_for_segment("IST", "JFK")
print(f"CO2 emissions: {co2:.2f} kg per passenger")
```

### NEW v2.0.0+ Features

#### 1. Passenger Experience & Jet Lag Analysis

```python
from aeronavx import calculate_jet_lag, get_airport

ist = get_airport("IST")
jfk = get_airport("JFK")

# Calculate jet lag for IST → JFK flight
jet_lag = calculate_jet_lag(ist, jfk, age=35)

print(f"Timezone difference: {jet_lag.timezone_difference_hours:.1f} hours")
print(f"Direction: {jet_lag.direction.value}")  # westward/eastward
print(f"Severity: {jet_lag.severity.value}")    # mild/moderate/severe
print(f"Recovery time: {jet_lag.estimated_recovery_days:.1f} days")
```

#### 2. Network Intelligence & Hub Analysis

```python
from aeronavx import identify_global_hubs, NetworkIntelligence

# Identify major aviation hubs
hubs = identify_global_hubs(top_n=10)

for hub in hubs:
    print(f"{hub.airport.iata_code}: {hub.airport.name}")
    print(f"  Hub Score: {hub.hub_score:.2f}")
    print(f"  Connectivity: {hub.connectivity_score:.2f}")
```

#### 3. Synthetic Route Generation

```python
from aeronavx import generate_route

# Generate realistic flight route with waypoints
route = generate_route("IST", "JFK")

print(f"Total distance: {route.total_distance_km:.2f} km")
print(f"Estimated flight time: {route.total_time_hours:.2f} hours")
print(f"Number of waypoints: {len(route.waypoints)}")

# Access individual waypoints
for waypoint in route.waypoints[:3]:
    print(f"  {waypoint.name}: ({waypoint.latitude:.2f}, {waypoint.longitude:.2f})")
```

#### 4. Advanced Emissions Analysis

```python
from aeronavx import calculate_flight_emissions, AircraftType, FuelType

# Detailed emissions calculation
emissions = calculate_flight_emissions(
    "IST", "JFK",
    aircraft_type=AircraftType.WIDE_BODY,
    fuel_type=FuelType.JET_A1,
    load_factor=0.85
)

print(f"Total CO2: {emissions.total_co2_kg:.2f} kg")
print(f"Per passenger: {emissions.co2_per_passenger_kg:.2f} kg")
print(f"Fuel consumption: {emissions.fuel_kg:.2f} kg")

# Compare with Sustainable Aviation Fuel (SAF)
from aeronavx import compare_saf_savings
savings = compare_saf_savings("IST", "JFK", saf_percentage=50)
print(f"CO2 savings with 50% SAF: {savings.co2_reduction_kg:.2f} kg ({savings.reduction_percentage:.1f}%)")
```

#### 5. Geo-Spatial Analysis

```python
from aeronavx import compare_routes, check_polar_route

# Compare different route types
comparison = compare_routes("IST", "JFK")
print(f"Great Circle: {comparison.great_circle_km:.2f} km")
print(f"Rhumb Line: {comparison.rhumb_line_km:.2f} km")
print(f"Difference: {comparison.difference_km:.2f} km")

# Check if polar route is beneficial
polar_check = check_polar_route("JFK", "NRT")  # New York to Tokyo
if polar_check.is_polar_beneficial:
    print(f"Polar route saves {polar_check.distance_savings_km:.2f} km")
```

---

## Advanced Usage

### Filtering Airports

```python
from aeronavx.core import loader

# Load only major airports (large + medium with scheduled service)
major_airports = loader.load_airports(
    include_types=['large_airport', 'medium_airport'],
    scheduled_service_only=True
)
print(f"Major airports: {len(major_airports):,}")  # ~3,200

# Load specific countries
us_airports = loader.load_airports(countries=['US'])
print(f"US airports: {len(us_airports):,}")  # ~20,000

# Load airports with IATA codes only
iata_airports = loader.load_airports(has_iata_only=True)
print(f"IATA airports: {len(iata_airports):,}")  # ~9,000
```

### Working with Runways

```python
from aeronavx.models import Runway, Airport

# Access airport runway information
ist = aeronavx.get_airport("IST")

# Runway model is available for custom data
runway = Runway(
    id=1,
    airport_ref=ist.id,
    airport_ident="LTFM",
    length_ft=12467,
    width_ft=197,
    surface="ASPH",
    le_ident="16L",
    he_ident="34R"
)

print(f"Runway: {runway.designation}")  # 16L/34R
print(f"Length: {runway.length_ft:.0f} ft")
print(f"Paved: {runway.is_paved}")
```

---

## CLI Usage

```bash
# Calculate distance
aeronavx distance --from IST --to JFK --unit nmi

# Find nearest airports
aeronavx nearest --lat 41.0 --lon 29.0 --n 5

# Search by name
aeronavx search --name "Heathrow"

# Estimate emissions
aeronavx emissions --from IST --to LHR

# Flight time
aeronavx flight-time --from IST --to JFK
```

---

## API Server

Start the REST API server:

```bash
python -m aeronavx.api.server
```

Then access:
- `http://localhost:8000/health` - Health check
- `http://localhost:8000/airport/IST` - Get airport details
- `http://localhost:8000/distance?from=IST&to=JFK` - Calculate distance
- `http://localhost:8000/nearest?lat=41.0&lon=29.0&n=5` - Find nearest airports

---

## What's Fixed in v2.0.3

**All import errors resolved:**
- ✅ `Runway` class now properly importable from `aeronavx.models`
- ✅ `get_timezone_offset()` function added to `aeronavx.core.timezone`
- ✅ `PassengerExperience` module fully functional
- ✅ `NetworkIntelligence` module working correctly
- ✅ Removed references to non-existent modules (`runways.py`, `statistics.py`)

**Verified working:**
```python
# All these imports now work without errors
from aeronavx.models import Runway, Airport
from aeronavx.core.timezone import get_timezone_offset
from aeronavx.core.passenger_experience import calculate_jet_lag
from aeronavx.core.network_intelligence import NetworkIntelligence
```

---

## Known Limitations & Workarounds

### Timezone Calculations
If `timezonefinder` is not installed, timezone offsets fall back to longitude-based approximation (accurate to ±1 hour in most cases).

**Workaround:**
```bash
pip install timezonefinder
```

### Weather Data
METAR/TAF fetching requires internet connection and `requests` library.

**Workaround:**
```bash
pip install aeronavx[full]
```

### Performance with Large Datasets
For optimal performance with 80k+ airports, install scipy:

**Workaround:**
```bash
pip install scipy
```

---

## Data Attribution

Airport data from [OurAirports](https://ourairports.com) (David Megginson et al.) - Licensed under [MIT License](https://github.com/davidmegginson/ourairports-data)

**Includes:**
- ✅ **84,000+ airports** worldwide
- ✅ **Global Coverage**: Airports, heliports, seaplane bases
- ✅ **MIT License**: Free for commercial use
- ✅ **Regular Updates**: Community-maintained
- ✅ **Comprehensive Data**: IATA/ICAO codes, coordinates, elevation, types

---

## Examples

See `examples/` directory for comprehensive examples:
- `basic_distance.py` - Distance calculations
- `nearest_airports.py` - Finding nearby airports
- `routing_example.py` - Multi-segment routes
- `emissions_example.py` - CO2 estimation
- `jet_lag_example.py` - NEW: Passenger experience analysis
- `network_analysis.py` - NEW: Hub identification
- `synthetic_routes.py` - NEW: Route generation

---

## Testing

Run the test suite:

```bash
pytest
```

With coverage:

```bash
pytest --cov=aeronavx --cov-report=html
```

---

## Dependencies

**Required:**
- Python >= 3.10

**Optional (install with `pip install aeronavx[full]`):**
- `pandas` - DataFrame support for bulk operations
- `scipy` - Faster spatial indexing (KDTree)
- `rapidfuzz` - Enhanced fuzzy name search
- `timezonefinder` - Accurate timezone detection
- `requests` - Weather data (METAR/TAF)

**API Server (install with `pip install aeronavx[api]`):**
- `fastapi` - Web framework
- `uvicorn` - ASGI server

---

## Roadmap

### Future Enhancements (v3.0)
- Region-aware filtering (EU, ASIA, US regions)
- Built-in KDTree/BallTree proximity engine
- DataFrame-first API design
- Enhanced hub intelligence algorithms
- Airport attribute consistency improvements
- Performance optimizations for large-scale queries

**Contributions welcome!** Open an issue or pull request on [GitHub](https://github.com/teyfikoz/AeroNavX).

---

## License

MIT License - See [LICENSE](LICENSE) file for details.

---

## Support

- **Issues**: [GitHub Issues](https://github.com/teyfikoz/AeroNavX/issues)
- **Discussions**: [GitHub Discussions](https://github.com/teyfikoz/AeroNavX/discussions)
- **PyPI**: [https://pypi.org/project/aeronavx/](https://pypi.org/project/aeronavx/)

---

## Changelog

### v2.0.5 (Latest)
- **CRITICAL FIX**: Fixed `TypeError: great_circle_path() got an unexpected keyword argument 'fraction'`
- **Fixed**: SyntheticRouteEngine now uses `intermediate_point()` correctly
- **Enhanced**: Airport model with backward-compatible alias properties (latitude, longitude, country_code, icao_code)
- **Added**: Distance conversion methods (`distance_to_km()`, `distance_to_nmi()`, `distance_to_miles()`)
- **Added**: Comprehensive regression tests for route generation
- **Status**: Production-ready, all critical bugs fixed

### v2.0.4
- **Enhanced**: Comprehensive README with all v2.0.0+ features documented
- **Added**: Complete usage examples for jet lag analysis, network intelligence, and synthetic routes
- **Improved**: PyPI project description for better discoverability
- **Updated**: Documentation with known limitations and workarounds
- **Status**: Production-ready with complete documentation

### v2.0.3
- **Fixed**: Runway class import error
- **Fixed**: get_timezone_offset function missing
- **Fixed**: PassengerExperience module import issues
- **Removed**: References to non-existent modules
- **Status**: Production-ready, all imports verified

### v2.0.0
- **NEW**: Network Intelligence & Hub Analysis
- **NEW**: Synthetic Route Generation Engine
- **NEW**: Advanced Emissions Calculator v2
- **NEW**: Geo-Spatial Advanced Analysis
- **NEW**: Passenger Experience & Jet Lag Analysis

### v0.2.0
- Initial public release with 84k+ airports

---

**Made with ❤️ for the aviation and data science community**
