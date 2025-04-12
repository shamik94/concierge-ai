from typing import Dict, Any
from .base_agent import BaseAgent
import requests

class AttributeCheckAgent(BaseAgent):
    def __init__(self, google_api_key: str, openai_client: Any, **kwargs):
        self.google_api_key = google_api_key
        self.openai_client = openai_client
        self.base_url = "https://maps.googleapis.com/maps/api"

    def process(self, params: Dict[str, Any]) -> Dict[str, Any]:
        place_id = params.get("place_details", {}).get("place_id")
        attribute = params.get("attribute", "")
        
        if not place_id or not attribute:
            return {"valid": False, "error": "Missing place_id or attribute"}
        
        # Get place details
        details_url = f"{self.base_url}/place/details/json"
        details_params = {
            "place_id": place_id,
            "fields": "name,editorial_summary,reviews,types,amenities",
            "key": self.google_api_key
        }
        
        response = requests.get(details_url, params=details_params)
        data = response.json()
        
        if data.get("status") != "OK":
            return {"valid": False, "error": "Could not fetch place details"}
        
        # Use OpenAI to analyze if the place has the attribute
        analysis_prompt = f"""Based on the following place details, determine if the place has {attribute}.
        Place details: {data['result']}
        
        Return a JSON with:
        - has_attribute: boolean
        - confidence: float (0-1)
        - explanation: string
        """
        
        analysis = self.openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "user", "content": analysis_prompt}],
            response_format={"type": "json_object"}
        )
        
        return {
            "valid": True,
            "attribute_analysis": analysis.choices[0].message.content
        }

    def validate_response(self, response: Dict[str, Any]) -> bool:
        return response.get("valid", False) 