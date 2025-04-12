from typing import Dict, Any
from .base_agent import BaseAgent
from openai import OpenAI
import json

class QueryAnalysisAgent(BaseAgent):
    def __init__(self, openai_client: OpenAI, **kwargs):
        self.openai_client = openai_client

    def process(self, params: Dict[str, Any]) -> Dict[str, Any]:
        query = params.get("query", "")
        system_prompt = """You are a query analysis agent that returns JSON responses. Analyze the following query and extract structured information in JSON format."""

        user_prompt = """Query: {query}

Extract the following information:
1. intent: The main purpose of the query (e.g., "find restaurants", "search for cafes")
2. place_type: The type of place being searched for
3. location: The location details including area, city, and country
4. temporal: Any time-related requirements (opening hours, days)

Return the response in JSON format with the following structure:
{{
    "intent": "string",
    "place_type": "string",
    "location": {{
        "area": "string",
        "city": "string",
        "country": "string"
    }},
    "temporal": {{
        "time": "string",
        "day": "string"
    }}
}}

If any field is not specified in the query, return an empty string or empty object for that field."""

        response = self.openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt.format(query=query)}
            ],
            response_format={"type": "json_object"}
        )
        
        try:
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON response from OpenAI")

    def validate_response(self, response: Dict[str, Any]) -> bool:
        required_fields = ["intent", "place_type", "location"]
        return all(field in response for field in required_fields) 