import argparse
import requests
import sys

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


def geocode_city(city: str):
    """
    Look up geographic coordinates for a given city name using Open-Meteo's geocoding API.

    Parameters
    ----------
    city : str
        Name of the city to geocode.

    Returns
    -------
    tuple
        A tuple containing (latitude, longitude, resolved_city_name, country).

    Raises
    ------
    SystemExit
        If the city cannot be found or the API request fails.
    """
    try:
        response = requests.get(GEOCODE_URL, params={"name": city, "count": 1})
        response.raise_for_status()
        data = response.json()

        if "results" not in data or not data["results"]:
            print(f"❌ Location not found: {city}")
            sys.exit(1)

        result = data["results"][0]
        return result["latitude"], result["longitude"], result["name"], result["country"]

    except Exception as e:
        print(f"❌ Geocoding error: {e}")
        sys.exit(1)


def fetch_weather(lat: float, lon: float):
    """
    Fetch current weather data for given geographic coordinates using Open-Meteo.

    Parameters
    ----------
    lat : float
        Latitude of the location.
    lon : float
        Longitude of the location.

    Returns
    -------
    dict
        Parsed JSON response containing weather data.

    Raises
    ------
    SystemExit
        If the API request fails.
    """
    try:
        response = requests.get(
            WEATHER_URL, params={"latitude": lat, "longitude": lon, "current_weather": True}
        )
        response.raise_for_status()
        return response.json()

    except Exception as e:
        print(f"❌ Weather API error: {e}")
        sys.exit(1)


def main():
    """
    Entry point for the weather CLI tool.

    This function parses command-line arguments, resolves the location
    (either via city name or direct coordinates), fetches weather data,
    and prints a formatted summary to the console.
    """
    parser = argparse.ArgumentParser(description="Simple weather CLI using Open-Meteo")
    parser.add_argument("--city", type=str, help="City name")
    parser.add_argument("--lat", type=float, help="Latitude")
    parser.add_argument("--lon", type=float, help="Longitude")

    args = parser.parse_args()

    # Determine location
    if args.city:
        lat, lon, name, country = geocode_city(args.city)
        print(f"📍 Location: {name}, {country} ({lat}, {lon})")
    elif args.lat and args.lon:
        lat, lon = args.lat, args.lon
        print(f"📍 Location: {lat}, {lon}")
    else:
        print("❌ Provide --city or both --lat and --lon")
        sys.exit(1)

    # Fetch weather
    data = fetch_weather(lat, lon)

    if "current_weather" not in data:
        print("❌ No weather data available")
        sys.exit(1)

    w = data["current_weather"]

    # Output
    print("\n🌤️  Current Weather:")
    print(f"   🌡️  Temperature: {w['temperature']}°C")
    print(f"   💨  Wind Speed: {w['windspeed']} km/h")
    print(f"   🧭  Wind Direction: {w['winddirection']}°")
    print(f"   ⏱️  Observation Time: {w['time']}")


if __name__ == "__main__":
    main()
