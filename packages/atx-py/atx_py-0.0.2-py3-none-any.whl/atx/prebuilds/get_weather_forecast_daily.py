"""
atx build --tool-name get_weather_forecast_daily --tool-version 1 atx/prebuilds/get_weather_forecast_daily.py

./dist/get_weather_forecast_daily/1/tool --arguments '{"query": "25.07169091030504, 121.57707965767086", "duration": 5, "location_name": "Neihu District, Taipei City"}'
"""  # noqa: E501

import json
import logging
import os
from datetime import datetime
from textwrap import dedent
from typing import Any, Dict, Optional, Text, Union, cast

import requests

from atx import AielloToolx

logger = logging.getLogger(__name__)


AZURE_WEATHER_FORECAST_DAILY_URL = (
    "https://atlas.microsoft.com/weather/forecast/daily/json"
)
AZURE_WEATHER_FORECAST_DAILY_API_VERSION = "1.1"

AZURE_MAPS_API_KEY_NAME = "AZURE_MAPS_API_KEY"


class GetWeatherForecastDaily(AielloToolx):
    def name(self) -> str:
        return "get_weather_forecast_daily"

    def description(self, context: Optional[str] = None) -> str:
        return dedent(
            """
            The Get Daily Forecast API retrieves detailed daily weather forecasts for locations worldwide.
            The API requires geographic coordinates (latitude/longitude) and provides comprehensive weather data including temperature, wind conditions, precipitation, air quality, and UV index.
            Forecasts are available for 1, 5, or 10 days ahead.
            This API supports weather lookups for:
            - Land-based locations
            - Inland water bodies
            - Coastal areas (up to ~50 nautical miles offshore)
            You must first use the Geocoding API to convert the location name into precise latitude/longitude coordinates.
            """  # noqa: E501
        ).strip()

    def parameters(self, context: Optional[str] = None) -> dict[str, Any]:
        return {
            "properties": {
                "query": {
                    "description": "Geographic coordinates specified as a comma-separated string of latitude and longitude values (e.g., '47.641268,-122.125679').",  # noqa: E501
                    "title": "Query",
                    "type": "string",
                },
                "location_name": {
                    "anyOf": [{"type": "string"}, {"type": "null"}],
                    "default": None,
                    "description": "Optional human-readable name for the location (e.g., 'Seattle, WA' or 'Central Park, NYC'). This field is for reference only and does not affect the weather data retrieval.",  # noqa: E501
                    "title": "Location Name",
                },
                "duration": {
                    "default": 1,
                    "description": "Number of days for which to return forecast data:\n- 1: Next day forecast (default)\n- 5: Five-day forecast\n- 10: Ten-day forecast",  # noqa: E501
                    "enum": [1, 5, 10],
                    "title": "Duration",
                    "type": "integer",
                },
            },
            "required": ["query"],
            "type": "object",
        }

    def run(
        self, arguments: Optional[str] = None, context: Optional[str] = None
    ) -> str:
        AZURE_MAPS_API_KEY = os.getenv(AZURE_MAPS_API_KEY_NAME)
        if not AZURE_MAPS_API_KEY:
            raise ValueError(f"{AZURE_MAPS_API_KEY_NAME} is not set")

        if not arguments:
            raise ValueError("Arguments are required")

        args = json.loads(arguments)

        query: Optional[Text] = args.get("query")
        if not query:
            raise ValueError("Query is required")
        query_parts = query.split(",")
        if len(query_parts) != 2:
            raise ValueError("Query must be in the format 'latitude,longitude'")
        latitude: Text = query_parts[0].strip()
        longitude: Text = query_parts[1].strip()
        if not latitude or not longitude:
            raise ValueError("Latitude and longitude are required")

        location_name: Optional[Text] = args.get("location_name")
        if location_name:
            location_name = location_name.strip()

        duration: Optional[Union[int, float, str]] = args.get("duration")
        if not duration:
            duration = 1
        try:
            duration = int(duration)
        except (ValueError, TypeError):
            raise ValueError("Duration must be an integer")
        if duration not in [1, 5, 10]:
            raise ValueError(f"Duration must be an integer [1, 5, 10], got {duration}")

        url = AZURE_WEATHER_FORECAST_DAILY_URL
        params = {}
        params["api-version"] = AZURE_WEATHER_FORECAST_DAILY_API_VERSION
        params["subscription-key"] = AZURE_MAPS_API_KEY
        params["query"] = f"{latitude},{longitude}"
        params["duration"] = duration
        response = requests.get(url, params=params)

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logger.exception(e)
            raise ValueError(f"HTTP error: {e.response.status_code} {e.response.text}")

        weather_data = response.json()

        article_parts = []

        top_heading = "## Weather Forecast Daily"
        if location_name and location_name.strip():
            top_heading = f"{top_heading} ({location_name})"
        article_parts.append(top_heading + "\n")

        # Handle summary if exists
        if "summary" in weather_data:
            summary = weather_data["summary"]
            start_date_str = summary.get("startDate") or None
            end_date_str = summary.get("endDate") or None
            start_date_display: Optional[Text] = None
            end_date_display: Optional[Text] = None
            if start_date_str:
                start_date_display = datetime.fromisoformat(
                    summary.get("startDate", "")
                ).strftime("%B %d")
            if end_date_str:
                end_date_display = datetime.fromisoformat(
                    summary.get("endDate", "")
                ).strftime("%B %d")
            if start_date_display and end_date_display:
                article_parts.append(
                    f"Weather Summary ({start_date_display} - {end_date_display}):"
                )
            elif start_date_display:
                article_parts.append(f"Weather Summary ({start_date_display})")
            else:
                article_parts.append("Weather Summary:")
            article_parts.append(f"{summary.get('phrase', '')}")

        # Process each forecast
        for forecast in weather_data.get("forecasts", []):
            forecast = cast(Dict[Text, Any], forecast)
            try:
                # Parse date
                date_str = forecast.get("date")
                if date_str:
                    date = datetime.fromisoformat(date_str)
                    date_formatted = date.strftime("%A, %B %d, %Y")
                    article_parts.append(f"\n### {date_formatted}")

                # Temperature and Real Feel
                temp = forecast.get("temperature", {})
                real_feel = forecast.get("realFeelTemperature", {})
                min_temp = get_safe_value(temp, "minimum", "value")
                max_temp = get_safe_value(temp, "maximum", "value")
                real_min = get_safe_value(real_feel, "minimum", "value")
                real_max = get_safe_value(real_feel, "maximum", "value")

                if min_temp is not None and max_temp is not None:
                    article_parts.append(f"Temperature: {min_temp}°C to {max_temp}°C")
                    if real_min is not None and real_max is not None:
                        article_parts.append(
                            f"Feels like: {real_min}°C to {real_max}°C"
                        )

                # Sun and UV information
                hours_of_sun = forecast.get("hoursOfSun")
                if hours_of_sun is not None:
                    article_parts.append(f"Hours of Sun: {hours_of_sun} hours")

                # Air Quality and UV Index
                air_pollen = forecast.get("airAndPollen", [])
                for item in air_pollen:
                    if item.get("name") == "UVIndex":
                        article_parts.append(
                            f"UV Index: {item.get('value')} ({item.get('category', '')})"  # noqa: E501
                        )
                    elif item.get("name") == "AirQuality":
                        article_parts.append(f"Air Quality: {item.get('category', '')}")

                # Day forecast
                day = forecast.get("day", {})
                if day:
                    article_parts.append("\nDaytime:")
                    article_parts.append(f"- Conditions: {day.get('longPhrase', '')}")

                    # Precipitation details
                    precip_prob = day.get("precipitationProbability")
                    if precip_prob is not None:
                        article_parts.append(f"- Precipitation: {precip_prob}% chance")
                        if day.get("hasPrecipitation"):
                            rain = day.get("rain", {}).get("value")
                            if rain:
                                article_parts.append(f"- Expected rainfall: {rain}mm")

                    # Wind details
                    wind = day.get("wind", {})
                    wind_gust = day.get("windGust", {})
                    if wind:
                        direction = get_safe_value(
                            wind, "direction", "localizedDescription"
                        )
                        speed = get_safe_value(wind, "speed", "value", default=0)
                        gust_speed = get_safe_value(
                            wind_gust, "speed", "value", default=0
                        )
                        if direction and speed:
                            article_parts.append(f"- Wind: {direction} at {speed}km/h")
                            if gust_speed:
                                article_parts.append(
                                    f"- Wind gusts up to {gust_speed}km/h"
                                )

                # Night forecast
                night = forecast.get("night", {})
                if night:
                    article_parts.append("\nNighttime:")
                    article_parts.append(f"- Conditions: {night.get('longPhrase', '')}")

                    # Precipitation details
                    precip_prob = night.get("precipitationProbability")
                    if precip_prob is not None:
                        article_parts.append(f"- Precipitation: {precip_prob}% chance")
                        if night.get("hasPrecipitation"):
                            rain = night.get("rain", {}).get("value")
                            if rain:
                                article_parts.append(f"- Expected rainfall: {rain}mm")

                    # Cloud cover
                    cloud_cover = night.get("cloudCover")
                    if cloud_cover is not None:
                        article_parts.append(f"- Cloud cover: {cloud_cover}%")

            except Exception as e:
                logger.exception(e)
                continue  # Skip problematic forecasts

        out = "\n".join(article_parts).strip()

        return (
            out
            + "\n\nPlease present the forecast in clear, plain language with a natural, conversational tone, avoiding the use of any markdown formatting."  # noqa: E501
        )


def get_safe_value(obj: Dict, *keys: Text, default: Any = None) -> Any:
    """Safely get nested dictionary values"""

    try:
        result = obj
        for key in keys:
            result = result[key]
        return result
    except (KeyError, TypeError, IndexError):
        return default
