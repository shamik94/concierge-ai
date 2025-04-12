from typing import Dict, Any
import json
from openai import OpenAI

class QueryClassifier:
    def __init__(self, openai_client: OpenAI):
        self.openai_client = openai_client

    def classify(self, query: str) -> Dict[str, Any]:
        system_prompt = """You are a query classifier that returns JSON responses. Classify the given query into one of the specified types and return the result in JSON format."""

        user_prompt = f"""Classify this query into one of these types:
        1. place_search_temporal - for queries about places with time requirements
           Example: "find restaurants open till 11 pm"
        2. place_attribute_check - for queries about specific place attributes
           Example: "does Starbucks have wifi"
        3. nearby_search - for queries about finding places near a location
           Example: "find restaurants near Central Park"
        4. unclassified - for queries that don't match the above types

        Query: "{query}"

        Return a JSON object with:
        1. query_type: one of the above types
        2. confidence: a score between 0 and 1
        3. extracted_params: relevant parameters from the query

        Example response:
        {{
            "query_type": "place_search_temporal",
            "confidence": 0.95,
            "extracted_params": {{
                "place_type": "restaurants",
                "location": "Berlin",
                "time": "11 pm",
                "day": "Tuesday",
                "attributes": ["vegan"]
            }}
        }}"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            if not isinstance(result, dict):
                raise ValueError("Response is not a dictionary")
            return result
        except Exception as e:
            print(f"Error in query classification: {str(e)}")
            return {
                "query_type": "unclassified",
                "confidence": 0.0,
                "extracted_params": {
                    "error": str(e),
                    "original_query": query
                }
            } 