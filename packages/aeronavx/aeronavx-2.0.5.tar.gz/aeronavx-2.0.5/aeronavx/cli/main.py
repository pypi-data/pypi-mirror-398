import argparse
import sys

from ..core.airports import get
from ..core.distance import distance
from ..core.search import nearest_airports, search_airports_by_name
from ..core.emissions import estimate_co2_kg_by_codes
from ..core.routing import estimate_flight_time_hours, route_distance_by_codes
from ..exceptions import AeroNavXError


def cmd_distance(args):
    try:
        from_airport = get(args.from_code, code_type="auto")
        to_airport = get(args.to_code, code_type="auto")

        if from_airport is None:
            print(f"Error: Airport not found: {args.from_code}", file=sys.stderr)
            return 1

        if to_airport is None:
            print(f"Error: Airport not found: {args.to_code}", file=sys.stderr)
            return 1

        dist = distance(
            from_airport.latitude_deg,
            from_airport.longitude_deg,
            to_airport.latitude_deg,
            to_airport.longitude_deg,
            model=args.model,
            unit=args.unit
        )

        print(f"{from_airport.name} ({args.from_code}) to {to_airport.name} ({args.to_code})")
        print(f"Distance: {dist:.2f} {args.unit}")

        return 0

    except AeroNavXError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_nearest(args):
    try:
        airports = nearest_airports(args.lat, args.lon, n=args.n)

        if not airports:
            print("No airports found")
            return 0

        print(f"Nearest {len(airports)} airport(s) to ({args.lat}, {args.lon}):\n")

        for i, airport in enumerate(airports, 1):
            codes = []
            if airport.iata_code:
                codes.append(f"IATA: {airport.iata_code}")
            if airport.gps_code:
                codes.append(f"ICAO: {airport.gps_code}")

            code_str = f" ({', '.join(codes)})" if codes else ""

            dist_km = distance(
                args.lat, args.lon,
                airport.latitude_deg, airport.longitude_deg,
                unit="km"
            )

            print(f"{i}. {airport.name}{code_str}")
            print(f"   Distance: {dist_km:.2f} km")
            print(f"   Location: {airport.municipality}, {airport.iso_country}")
            print()

        return 0

    except AeroNavXError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_search(args):
    try:
        airports = search_airports_by_name(args.name, limit=args.limit)

        if not airports:
            print(f"No airports found matching '{args.name}'")
            return 0

        print(f"Found {len(airports)} airport(s) matching '{args.name}':\n")

        for i, airport in enumerate(airports, 1):
            codes = []
            if airport.iata_code:
                codes.append(f"IATA: {airport.iata_code}")
            if airport.gps_code:
                codes.append(f"ICAO: {airport.gps_code}")

            code_str = f" ({', '.join(codes)})" if codes else ""

            print(f"{i}. {airport.name}{code_str}")
            print(f"   Type: {airport.type}")
            print(f"   Location: {airport.municipality}, {airport.iso_country}")
            print()

        return 0

    except AeroNavXError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_emissions(args):
    try:
        co2_kg = estimate_co2_kg_by_codes(
            args.from_code,
            args.to_code,
            code_type="auto",
            model=args.model
        )

        from_airport = get(args.from_code, code_type="auto")
        to_airport = get(args.to_code, code_type="auto")

        print(f"{from_airport.name} ({args.from_code}) to {to_airport.name} ({args.to_code})")
        print(f"Estimated CO2 emissions: {co2_kg:.2f} kg per passenger")

        return 0

    except AeroNavXError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_flight_time(args):
    try:
        from_airport = get(args.from_code, code_type="auto")
        to_airport = get(args.to_code, code_type="auto")

        if from_airport is None:
            print(f"Error: Airport not found: {args.from_code}", file=sys.stderr)
            return 1

        if to_airport is None:
            print(f"Error: Airport not found: {args.to_code}", file=sys.stderr)
            return 1

        time_hours = estimate_flight_time_hours(
            from_airport,
            to_airport,
            speed_kts=args.speed_kts
        )

        hours = int(time_hours)
        minutes = int((time_hours - hours) * 60)

        print(f"{from_airport.name} ({args.from_code}) to {to_airport.name} ({args.to_code})")
        print(f"Estimated flight time: {hours}h {minutes}m (at {args.speed_kts} knots)")

        return 0

    except AeroNavXError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def main():
    parser = argparse.ArgumentParser(
        prog="aeronavx",
        description="AeroNavX - Airport and flight geometry utilities"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    distance_parser = subparsers.add_parser("distance", help="Calculate distance between airports")
    distance_parser.add_argument("--from", dest="from_code", required=True, help="Origin airport code")
    distance_parser.add_argument("--to", dest="to_code", required=True, help="Destination airport code")
    distance_parser.add_argument("--unit", choices=["km", "mi", "nmi"], default="km", help="Distance unit")
    distance_parser.add_argument("--model", choices=["haversine", "slc", "vincenty"], default="haversine", help="Distance model")

    nearest_parser = subparsers.add_parser("nearest", help="Find nearest airports to coordinates")
    nearest_parser.add_argument("--lat", type=float, required=True, help="Latitude")
    nearest_parser.add_argument("--lon", type=float, required=True, help="Longitude")
    nearest_parser.add_argument("--n", type=int, default=5, help="Number of airports to return")

    search_parser = subparsers.add_parser("search", help="Search airports by name")
    search_parser.add_argument("--name", required=True, help="Search query")
    search_parser.add_argument("--limit", type=int, default=10, help="Maximum results")

    emissions_parser = subparsers.add_parser("emissions", help="Estimate CO2 emissions")
    emissions_parser.add_argument("--from", dest="from_code", required=True, help="Origin airport code")
    emissions_parser.add_argument("--to", dest="to_code", required=True, help="Destination airport code")
    emissions_parser.add_argument("--model", choices=["haversine", "slc", "vincenty"], default="haversine", help="Distance model")

    time_parser = subparsers.add_parser("flight-time", help="Estimate flight time")
    time_parser.add_argument("--from", dest="from_code", required=True, help="Origin airport code")
    time_parser.add_argument("--to", dest="to_code", required=True, help="Destination airport code")
    time_parser.add_argument("--speed-kts", type=float, default=450.0, help="Cruise speed in knots")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    if args.command == "distance":
        return cmd_distance(args)
    elif args.command == "nearest":
        return cmd_nearest(args)
    elif args.command == "search":
        return cmd_search(args)
    elif args.command == "emissions":
        return cmd_emissions(args)
    elif args.command == "flight-time":
        return cmd_flight_time(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
