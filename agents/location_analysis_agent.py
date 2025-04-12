from typing import Dict, Any
from .base_agent import BaseAgent
import requests

class LocationAnalysisAgent(BaseAgent):
    def __init__(self, google_api_key: str, **kwargs):
        self.google_api_key = google_api_key
        self.base_url = "https://maps.googleapis.com/maps/api"

    def process(self, params: Dict[str, Any]) -> Dict[str, Any]:
        # Handle both direct location string and nested location object
        location = params.get("location", "")
        if isinstance(location, dict):
            # If location is a nested object, construct the location string
            area = location.get("area", "")
            city = location.get("city", "")
            country = location.get("country", "")
            location = " ".join(filter(None, [area, city, country]))
        elif not location and "extracted_params" in params:
            # Try to get location from extracted_params
            extracted = params["extracted_params"]
            if isinstance(extracted, dict):
                location = extracted.get("location", "")

        if not location:
            return {"valid": False, "error": "Location not provided"}

        geocode_url = f"{self.base_url}/geocode/json"
        params = {
            "address": location,
            "key": self.google_api_key
        }
        
        response = requests.get(geocode_url, params=params)
        data = response.json()
        
        if data.get("status") != "OK":
            return {"valid": False, "error": "Location not found"}
            
        result = data["results"][0]
        return {
            "valid": True,
            "formatted_address": result["formatted_address"],
            "coordinates": result["geometry"]["location"],
            "place_id": result.get("place_id"),
            "types": result.get("types", [])
        }

    def validate_response(self, response: Dict[str, Any]) -> bool:
        return response.get("valid", False) 