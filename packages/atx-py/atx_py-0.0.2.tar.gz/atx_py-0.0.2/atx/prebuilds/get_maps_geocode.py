"""
atx build --tool-name get_maps_geocode --tool-version 1 atx/prebuilds/get_maps_geocode.py

./dist/get_maps_geocode/1/tool --arguments '{"address": "Aiello Inc Taipei", "language": "zh-TW"}'
"""  # noqa: E501

import json
import logging
import os
from textwrap import dedent
from typing import Any, List, NotRequired, Optional, TypedDict

import requests

from atx import AielloToolx

logger = logging.getLogger(__name__)


base_url = "https://maps.googleapis.com/maps/api/geocode/json"
GOOGLE_MAPS_API_KEY_NAME = "GOOGLE_MAPS_API_KEY"


class GetMapsGeocode(AielloToolx):
    def name(self) -> str:
        return "get_maps_geocode"

    def description(self, context: Optional[str] = None) -> str:
        return dedent(
            """
            This function converts a human-readable address into detailed geographical information using Google Maps' Geocoding API.
            It provides comprehensive location data including precise coordinates (latitude/longitude), formatted address, administrative divisions (city, country), place types (e.g., establishment, point of interest), and boundary information.
            The AI should use this function when users need to locate addresses, verify locations, understand geographical contexts, or require coordinate data for mapping purposes.
            It's particularly useful for questions about location validation, distance calculations, or when geographical precision is needed.
            """  # noqa: E501
        ).strip()

    def parameters(self, context: Optional[str] = None) -> dict[str, Any]:
        return {
            "properties": {
                "address": {
                    "anyOf": [{"type": "string"}, {"type": "null"}],
                    "description": "The address to geocode.",
                    "title": "Address",
                },
                "region": {
                    "anyOf": [{"type": "string"}, {"type": "null"}],
                    "default": None,
                    "description": "The region code, specified as a ccTLD ('top-level domain') two-character value.",  # noqa: E501
                    "title": "Region",
                },
                "language": {
                    "anyOf": [{"type": "string"}, {"type": "null"}],
                    "default": None,
                    "description": "The language in which to return results.",
                    "title": "Language",
                },
            },
            "required": ["address"],
            "type": "object",
        }

    def run(
        self, arguments: Optional[str] = None, context: Optional[str] = None
    ) -> str:
        GOOGLE_MAPS_API_KEY = os.getenv(GOOGLE_MAPS_API_KEY_NAME)
        if not GOOGLE_MAPS_API_KEY:
            raise ValueError(f"{GOOGLE_MAPS_API_KEY_NAME} is not set")

        if not arguments:
            raise ValueError("Arguments are required")

        args = json.loads(arguments)

        params = {"key": GOOGLE_MAPS_API_KEY}
        if args.get("address"):
            params["address"] = args["address"]
        if args.get("region"):
            params["region"] = args["region"]
        if args.get("language"):
            params["language"] = args["language"]

        response = requests.get(base_url, params=params)

        try:
            response.raise_for_status()

        except requests.exceptions.HTTPError as e:
            logger.exception(e)
            raise ValueError(f"HTTP error: {e.response.status_code} {e.response.text}")

        data: GeocodeResponse = response.json()

        if data["status"] == "ZERO_RESULTS":
            return "No maps geocode results found."

        if data["status"] != "OK":
            msg = f"Request failed with status: {data['status']}"
            logger.error(msg)
            raise ValueError(msg)

        results = data["results"]

        if not results:
            return "No maps geocode results found."

        article_parts = []
        for result in results:
            formatted_address = result.get("formatted_address", "N/A")
            types = ", ".join(result.get("types", []))

            # Extract important address components
            address_components = result.get("address_components", [])
            important_components = [
                component["long_name"]
                for component in address_components
                if "country" in component["types"] or "locality" in component["types"]
            ]
            important_components_str = ", ".join(important_components)

            # Extract geometry information
            geometry = result.get("geometry", {})
            location = geometry.get("location", {})
            lat = location.get("lat", "N/A")
            lng = location.get("lng", "N/A")

            article_parts.append(
                f"The most similar or closest address '{formatted_address}' is located in {important_components_str}. "  # noqa: E501
                f"It is positioned at latitude {lat} and longitude {lng}. "
                f"This location is categorized as: {types}."
            )

        return (
            "## Maps Geocode Results\n\n"
            + "\n".join([f"### Place\n\n{p}" for p in article_parts if p]).strip()
            + "\n"
        )


class AddressComponent(TypedDict):
    long_name: str
    short_name: str
    types: List[str]


class Location(TypedDict):
    lat: float
    lng: float


class Bounds(TypedDict):
    northeast: Location
    southwest: Location


class Viewport(TypedDict):
    northeast: Location
    southwest: Location


class Geometry(TypedDict):
    bounds: NotRequired[Bounds]
    location: Location
    location_type: str
    viewport: NotRequired[Viewport]


class PlusCode(TypedDict):
    compound_code: NotRequired[str]
    global_code: str


class GeocodeResult(TypedDict):
    address_components: List[AddressComponent]
    formatted_address: str
    geometry: Geometry
    partial_match: NotRequired[bool]
    place_id: str
    plus_code: NotRequired[PlusCode]
    types: List[str]


class GeocodeResponse(TypedDict):
    results: List[GeocodeResult]
    status: str
