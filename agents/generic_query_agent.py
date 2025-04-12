from typing import Dict, Any
from .base_agent import BaseAgent
from openai import OpenAI

class GenericQueryAgent(BaseAgent):
    def __init__(self, openai_client: OpenAI, **kwargs):
        self.openai_client = openai_client

    def process(self, params: Dict[str, Any]) -> Dict[str, Any]:
        query = params.get("query", "")
        prompt = """You are a helpful assistant for location-based queries.
        Please provide a general response to the following query.
        
        Query: {query}
        
        Provide a helpful response that guides the user to rephrase their query
        in a way that matches one of our supported query types."""
        
        response = self.openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": query}
            ]
        )
        
        return {
            "valid": True,
            "response_text": response.choices[0].message.content
        }

    def validate_response(self, response: Dict[str, Any]) -> bool:
        return response.get("valid", False) and "response_text" in response 