from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

from ..core.airports import get
from ..core.distance import distance
from ..core.search import nearest_airports, search_airports_by_name
from ..core.routing import estimate_flight_time_hours
from ..core.emissions import estimate_co2_kg_by_codes
from ..exceptions import AeroNavXError


app = FastAPI(
    title="AeroNavX API",
    description="Airport and flight geometry utilities",
    version="0.1.0"
)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "AeroNavX API"}


@app.get("/airport/{code}")
async def get_airport(
    code: str,
    code_type: str = Query("auto", regex="^(iata|icao|auto)$")
):
    try:
        airport = get(code, code_type=code_type)

        if airport is None:
            raise HTTPException(status_code=404, detail=f"Airport not found: {code}")

        return airport.as_dict()

    except AeroNavXError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/distance")
async def calculate_distance(
    from_code: str = Query(..., alias="from"),
    to_code: str = Query(..., alias="to"),
    code_type: str = Query("auto", regex="^(iata|icao|auto)$"),
    model: str = Query("haversine", regex="^(haversine|slc|vincenty)$"),
    unit: str = Query("km", regex="^(km|mi|nmi)$")
):
    try:
        from_airport = get(from_code, code_type=code_type)
        to_airport = get(to_code, code_type=code_type)

        if from_airport is None:
            raise HTTPException(status_code=404, detail=f"Origin airport not found: {from_code}")

        if to_airport is None:
            raise HTTPException(status_code=404, detail=f"Destination airport not found: {to_code}")

        dist = distance(
            from_airport.latitude_deg,
            from_airport.longitude_deg,
            to_airport.latitude_deg,
            to_airport.longitude_deg,
            model=model,
            unit=unit
        )

        return {
            "from": from_airport.as_dict(),
            "to": to_airport.as_dict(),
            "distance": dist,
            "unit": unit,
            "model": model
        }

    except AeroNavXError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/nearest")
async def find_nearest(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    n: int = Query(5, ge=1, le=100)
):
    try:
        airports = nearest_airports(lat, lon, n=n)

        return {
            "query": {"lat": lat, "lon": lon},
            "count": len(airports),
            "airports": [a.as_dict() for a in airports]
        }

    except AeroNavXError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/search")
async def search(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100)
):
    try:
        airports = search_airports_by_name(q, limit=limit)

        return {
            "query": q,
            "count": len(airports),
            "airports": [a.as_dict() for a in airports]
        }

    except AeroNavXError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/flight-time")
async def flight_time(
    from_code: str = Query(..., alias="from"),
    to_code: str = Query(..., alias="to"),
    speed_kts: float = Query(450.0, ge=100, le=1000)
):
    try:
        from_airport = get(from_code, code_type="auto")
        to_airport = get(to_code, code_type="auto")

        if from_airport is None:
            raise HTTPException(status_code=404, detail=f"Origin airport not found: {from_code}")

        if to_airport is None:
            raise HTTPException(status_code=404, detail=f"Destination airport not found: {to_code}")

        time_hours = estimate_flight_time_hours(from_airport, to_airport, speed_kts=speed_kts)

        hours = int(time_hours)
        minutes = int((time_hours - hours) * 60)

        return {
            "from": from_airport.as_dict(),
            "to": to_airport.as_dict(),
            "speed_kts": speed_kts,
            "time_hours": time_hours,
            "time_formatted": f"{hours}h {minutes}m"
        }

    except AeroNavXError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/emissions")
async def emissions(
    from_code: str = Query(..., alias="from"),
    to_code: str = Query(..., alias="to"),
    model: str = Query("haversine", regex="^(haversine|slc|vincenty)$")
):
    try:
        co2_kg = estimate_co2_kg_by_codes(from_code, to_code, code_type="auto", model=model)

        from_airport = get(from_code, code_type="auto")
        to_airport = get(to_code, code_type="auto")

        return {
            "from": from_airport.as_dict(),
            "to": to_airport.as_dict(),
            "co2_kg_per_passenger": co2_kg,
            "model": model
        }

    except AeroNavXError as e:
        raise HTTPException(status_code=400, detail=str(e))


def run_server(host: str = "0.0.0.0", port: int = 8000):
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
