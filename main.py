import os
import requests
from dotenv import load_dotenv
from typing import Dict, List, Any, Optional
from openai import OpenAI
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables
load_dotenv()

# API Keys
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
openai_client = OpenAI(
    api_key=OPENAI_API_KEY
)

class QueryAnalysisAgent:
    """Agent responsible for understanding and structuring natural language queries"""
    
    def __init__(self, openai_client: OpenAI):
        self.openai_client = openai_client

    def analyze(self, query: str) -> Dict[str, Any]:
        prompt = """You are a specialized agent for understanding location-based queries.
        Analyze the following query and extract structured information.
        
        Consider:
        1. Intent (finding places, checking hours, getting directions, etc.)
        2. Place type and attributes
        3. Location details
        4. Temporal requirements (if any)
        5. Special requirements or preferences
        
        Query: {query}
        
        Provide a detailed JSON response with these fields:
        - intent: primary purpose of the query
        - place_type: main type of establishment (e.g., restaurant, cafe)
        - attributes: list of specific attributes or requirements (e.g., ["biryani", "muslim-style"])
        - location: specific location or area
        - temporal: any time-related requirements (can be empty if none specified)
          - day: day of week (if specified)
          - time: specific time (if specified)
          - time_context: "open_until", "open_from", or "open_at" (if specified)
        - preferences: additional preferences or requirements
        
        For queries without time requirements, return an empty object for temporal.
        """
        
        response = self.openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": query}
            ],
            response_format={ "type": "json_object" }
        )
        
        return json.loads(response.choices[0].message.content)

class LocationAnalysisAgent:
    """Agent responsible for analyzing and validating location information"""
    
    def __init__(self, google_api_key: str):
        self.google_api_key = google_api_key
        self.base_url = "https://maps.googleapis.com/maps/api"

    def validate_and_enhance_location(self, location: str) -> Dict[str, Any]:
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
            "types": result.get("types", []),
            "bounds": result.get("geometry", {}).get("bounds")
        }

class TimeAnalysisAgent:
    """Agent responsible for parsing and validating temporal requirements"""
    
    def parse_time_requirement(self, temporal_info: Dict[str, Any]) -> Dict[str, Any]:
        day_mapping = {
            "monday": 1, "tuesday": 2, "wednesday": 3, "thursday": 4,
            "friday": 5, "saturday": 6, "sunday": 0
        }
        
        try:
            day = temporal_info.get("day", "").lower()
            time_str = temporal_info.get("time", "")
            context = temporal_info.get("time_context", "open_until")
            
            # Convert time to 24-hour format
            if isinstance(time_str, str) and ("am" in time_str.lower() or "pm" in time_str.lower()):
                time_parts = time_str.lower().replace(".", "").strip().split()
                hour = int(time_parts[0])
                if "pm" in time_parts[1] and hour != 12:
                    hour += 12
                elif "am" in time_parts[1] and hour == 12:
                    hour = 0
            else:
                hour = int(time_str) if time_str else None

            return {
                "day_number": day_mapping.get(day, -1),
                "day_name": day,
                "hour_24": hour,
                "context": context,
                "valid": bool(day in day_mapping and hour is not None)
            }
        except Exception as e:
            return {"valid": False, "error": str(e)}

class GoogleMapsLLMIntegration:
    """
    Enhanced integration class using specialized agents for better query understanding
    """
    
    def __init__(self, google_api_key: str, openai_client: OpenAI):
        self.query_agent = QueryAnalysisAgent(openai_client)
        self.location_agent = LocationAnalysisAgent(google_api_key)
        self.time_agent = TimeAnalysisAgent()
        self.google_api_key = google_api_key
        self.base_url = "https://maps.googleapis.com/maps/api"

    def process_query(self, user_query: str) -> List[Dict[str, Any]]:
        """
        Enhanced query processing using multiple agents
        """
        try:
            # Step 1: Analyze the query using the QueryAnalysisAgent
            print("Step 1: Analyzing query...")
            query_analysis = self.query_agent.analyze(user_query)
            print(f"Query analysis: {query_analysis}")

            # Step 2: Validate and enhance location information
            print("Step 2: Validating location...")
            location_info = self.location_agent.validate_and_enhance_location(query_analysis["location"])
            if not location_info["valid"]:
                raise ValueError(f"Invalid location: {location_info.get('error')}")
            print(f"Location info: {location_info}")

            # Step 3: Parse temporal requirements (only if present)
            has_time_requirements = query_analysis.get("temporal") and any(query_analysis["temporal"].values())
            time_info = None
            if has_time_requirements:
                print("Step 3: Analyzing temporal requirements...")
                time_info = self.time_agent.parse_time_requirement(query_analysis["temporal"])
                if not time_info["valid"]:
                    raise ValueError(f"Invalid time requirement: {time_info.get('error')}")
                print(f"Time info: {time_info}")
            else:
                print("No temporal requirements specified, skipping time validation...")

            # Step 4: Search for places using enhanced information
            search_params = {
                "location": f"{location_info['coordinates']['lat']},{location_info['coordinates']['lng']}",
                "radius": 1500,
                "type": query_analysis["place_type"].lower(),
                "keyword": " ".join(query_analysis["attributes"]),
                "key": self.google_api_key
            }
            
            places_url = f"{self.base_url}/place/nearbysearch/json"
            places_response = requests.get(places_url, params=search_params)
            places_data = places_response.json()

            if places_data.get("status") != "OK":
                return []

            # Step 5: Filter and enhance results
            results = []
            for place in places_data.get("results", []):
                # Only validate timing if temporal requirements exist
                if has_time_requirements:
                    if self._validate_place_timing(place["place_id"], time_info):
                        details = self._get_place_details(place["place_id"])
                        if details:
                            results.append(details)
                else:
                    details = self._get_place_details(place["place_id"])
                    if details:
                        results.append(details)

            return self.format_results(results)

        except Exception as e:
            print(f"Error in process_query: {str(e)}")
            return []

    def _validate_place_timing(self, place_id: str, time_info: Dict[str, Any]) -> bool:
        """Validate if a place meets the temporal requirements"""
        details_url = f"{self.base_url}/place/details/json"
        details_params = {
            "place_id": place_id,
            "fields": "opening_hours",
            "key": self.google_api_key
        }
        
        response = requests.get(details_url, params=details_params)
        data = response.json()
        
        if data.get("status") != "OK":
            return False
            
        opening_hours = data.get("result", {}).get("opening_hours", {})
        if not opening_hours:
            return False
            
        periods = opening_hours.get("periods", [])
        for period in periods:
            if period.get("open", {}).get("day") == time_info["day_number"]:
                close_time = period.get("close", {}).get("time")
                if close_time and int(close_time) >= time_info["hour_24"] * 100:
                    return True
        
        return False

    def _get_place_details(self, place_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a place"""
        details_url = f"{self.base_url}/place/details/json"
        details_params = {
            "place_id": place_id,
            "fields": "name,place_id,formatted_address,opening_hours,website,formatted_phone_number,rating,user_ratings_total",
            "key": self.google_api_key
        }
        
        response = requests.get(details_url, params=details_params)
        data = response.json()
        
        if data.get("status") != "OK":
            return None
        
        return data.get("result")

    def format_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format the search results into a structured list."""
        if not results:
            return []
        
        formatted_results = []
        for place in results:
            formatted_place = {
                "name": place.get("name", "Unnamed place"),
                "address": place.get("formatted_address", "No address available"),
                "rating": place.get("rating", None),
                "website": place.get("website", None),
                "phone": place.get("formatted_phone_number", None),
                "opening_hours": place.get("opening_hours", {}).get("weekday_text", []) if place.get("opening_hours") else None,
                "user_ratings_total": place.get("user_ratings_total", None)
            }
            formatted_results.append(formatted_place)
        
        return formatted_results

# Create FastAPI app
app = FastAPI(title="Restaurant Finder API")

# Add CORS middleware to the app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define request model
class QueryRequest(BaseModel):
    query: str

# Define API endpoints
@app.post("/search")
async def search_places(request: QueryRequest):
    """
    Search for places based on natural language query
    """
    try:
        print("\n=== New search request received ===")
        print(f"Request body: {request}")
        print(f"Query content: {request.query}")
        
        # Log environment variables (masked)
        print(f"Google Maps API Key present: {'Yes' if GOOGLE_MAPS_API_KEY else 'No'}")
        print(f"OpenAI API Key present: {'Yes' if OPENAI_API_KEY else 'No'}")
        
        # Initialize integration
        print("Initializing GoogleMapsLLMIntegration...")
        maps_llm = GoogleMapsLLMIntegration(GOOGLE_MAPS_API_KEY, openai_client)
        
        # Process query
        print("Processing query...")
        results = maps_llm.process_query(request.query)
        
        print("=== Request processing completed ===")
        print(f"Results type: {type(results)}")
        print(f"Results length: {len(results) if results else 0}")
        
        response_data = {"results": results}
        print(f"Sending response: {response_data}")
        
        return response_data
        
    except Exception as e:
        print("\n=== Error in API endpoint ===")
        print(f"Error type: {type(e)}")
        print(f"Error message: {str(e)}")
        import traceback
        print(f"Traceback:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

# Add a test endpoint to verify the server is running
@app.get("/ping")
async def ping():
    return {"status": "ok", "message": "Server is running"}

# Modified main section
if __name__ == "__main__":
    import uvicorn
    print("\n=== Starting FastAPI server ===")
    print(f"CORS origins enabled for: http://localhost:3000")
    print(f"API endpoints available:")
    print(f"  - POST /search")
    print(f"  - GET /ping")
    uvicorn.run(app, host="0.0.0.0", port=8000)