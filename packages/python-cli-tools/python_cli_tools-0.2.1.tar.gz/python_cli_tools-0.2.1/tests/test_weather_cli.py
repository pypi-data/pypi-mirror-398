"""
Comprehensive test suite for the Weather CLI application.

This module tests:
- Geocoding logic (success, not found, API errors)
- Weather fetching logic (success, API errors)
- CLI behavior (city mode, lat/lon mode, missing arguments)
- Output formatting and error handling

All external API calls are mocked to ensure deterministic behavior.
"""

import argparse
import pytest
import requests
from unittest.mock import patch, MagicMock

import weather_cli.weather_cli as weather_cli


# ============================================================
# Geocoding tests
# ============================================================


def test_geocode_city_success():
    """Test successful geocoding response with valid city data."""
    mock_response = {
        "results": [
            {
                "latitude": 52.52,
                "longitude": 13.41,
                "name": "Berlin",
                "country": "Germany",
            }
        ]
    }

    with patch("requests.get") as mock_get:
        mock_get.return_value = MagicMock(json=lambda: mock_response, raise_for_status=lambda: None)

        lat, lon, name, country = weather_cli.geocode_city("Berlin")

        assert lat == 52.52
        assert lon == 13.41
        assert name == "Berlin"
        assert country == "Germany"


def test_geocode_city_not_found():
    """Test geocoding when API returns no results."""
    mock_response = {"results": []}

    with patch("requests.get") as mock_get, pytest.raises(SystemExit):
        mock_get.return_value = MagicMock(json=lambda: mock_response, raise_for_status=lambda: None)
        weather_cli.geocode_city("Atlantis")


def test_geocode_city_api_error():
    """Test geocoding when the API request fails."""
    with patch("requests.get") as mock_get, pytest.raises(SystemExit):
        mock_get.side_effect = requests.exceptions.RequestException("API error")
        weather_cli.geocode_city("Berlin")


# ============================================================
# Weather fetch tests
# ============================================================


def test_fetch_weather_success():
    """Test successful weather data retrieval."""
    mock_response = {
        "current_weather": {
            "temperature": 10.5,
            "windspeed": 5.2,
            "winddirection": 180,
            "time": "2025-12-21T12:00",
        }
    }

    with patch("requests.get") as mock_get:
        mock_get.return_value = MagicMock(json=lambda: mock_response, raise_for_status=lambda: None)

        data = weather_cli.fetch_weather(52.52, 13.41)

        assert "current_weather" in data
        assert data["current_weather"]["temperature"] == 10.5


def test_fetch_weather_api_error():
    """Test weather fetch when API request fails."""
    with patch("requests.get") as mock_get, pytest.raises(SystemExit):
        mock_get.side_effect = requests.exceptions.RequestException("API error")
        weather_cli.fetch_weather(52.52, 13.41)


# ============================================================
# CLI tests
# ============================================================


def test_cli_city_success(capsys):
    """Simulate running the CLI with --city and verify output formatting."""
    geocode_mock = (52.52, 13.41, "Berlin", "Germany")
    weather_mock = {
        "current_weather": {
            "temperature": 10,
            "windspeed": 5,
            "winddirection": 200,
            "time": "2025-12-21T12:00",
        }
    }

    with (
        patch("weather_cli.weather_cli.geocode_city", return_value=geocode_mock),
        patch("weather_cli.weather_cli.fetch_weather", return_value=weather_mock),
        patch(
            "argparse.ArgumentParser.parse_args",
            return_value=argparse.Namespace(city="Berlin", lat=None, lon=None),
        ),
    ):
        weather_cli.main()
        captured = capsys.readouterr()

        assert "Berlin" in captured.out
        assert "Temperature" in captured.out
        assert "Wind Speed" in captured.out


def test_cli_lat_lon_success(capsys):
    """Simulate running the CLI with --lat and --lon."""
    weather_mock = {
        "current_weather": {
            "temperature": 15,
            "windspeed": 7,
            "winddirection": 150,
            "time": "2025-12-21T12:00",
        }
    }

    with (
        patch("weather_cli.weather_cli.fetch_weather", return_value=weather_mock),
        patch(
            "argparse.ArgumentParser.parse_args",
            return_value=argparse.Namespace(city=None, lat=52.52, lon=13.41),
        ),
    ):
        weather_cli.main()
        captured = capsys.readouterr()

        assert "52.52" in captured.out
        assert "13.41" in captured.out
        assert "Temperature" in captured.out


def test_cli_missing_arguments(capsys):
    """Test CLI behavior when neither city nor coordinates are provided."""
    with (
        patch(
            "argparse.ArgumentParser.parse_args",
            return_value=argparse.Namespace(city=None, lat=None, lon=None),
        ),
        pytest.raises(SystemExit),
    ):
        weather_cli.main()

    captured = capsys.readouterr()
    assert "Provide --city" in captured.out


def test_cli_missing_weather_data(capsys):
    """Test CLI behavior when API returns no current_weather field."""
    with (
        patch(
            "weather_cli.weather_cli.geocode_city",
            return_value=(52.52, 13.41, "Berlin", "Germany"),
        ),
        patch("weather_cli.weather_cli.fetch_weather", return_value={}),
        patch(
            "argparse.ArgumentParser.parse_args",
            return_value=argparse.Namespace(city="Berlin", lat=None, lon=None),
        ),
        pytest.raises(SystemExit),
    ):
        weather_cli.main()

    captured = capsys.readouterr()
    assert "No weather data available" in captured.out
