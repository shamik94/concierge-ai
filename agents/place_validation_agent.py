from typing import Dict, Any
from .base_agent import BaseAgent
import requests

class PlaceValidationAgent(BaseAgent):
    def __init__(self, google_api_key: str, **kwargs):
        self.google_api_key = google_api_key
        self.base_url = "https://maps.googleapis.com/maps/api"

    def process(self, params: Dict[str, Any]) -> Dict[str, Any]:
        place_name = params.get("place", "")
        location = params.get("location", "")
        
        # First, search for the place
        search_url = f"{self.base_url}/place/findplacefromtext/json"
        search_params = {
            "input": f"{place_name} {location}",
            "inputtype": "textquery",
            "fields": "place_id,name,formatted_address",
            "key": self.google_api_key
        }
        
        response = requests.get(search_url, params=search_params)
        data = response.json()
        
        if data.get("status") != "OK":
            return {"valid": False, "error": "Place not found"}
            
        return {
            "valid": True,
            "place_details": data["candidates"][0]
        }

    def validate_response(self, response: Dict[str, Any]) -> bool:
        return response.get("valid", False) 