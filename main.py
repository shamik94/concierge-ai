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

class GoogleMapsLLMIntegration:
    """
    A class that integrates Google Maps API with an LLM to process natural language queries
    about locations, restaurants, and other points of interest.
    """
    
    def __init__(self, google_api_key: str, openai_client: OpenAI):
        """Initialize with API keys."""
        self.google_api_key = google_api_key
        self.openai_client = openai_client
        self.base_url = "https://maps.googleapis.com/maps/api"
    
    def parse_query(self, user_query: str) -> Dict[str, Any]:
        """
        Use the LLM to parse the natural language query into structured parameters
        for the Google Maps API.
        """
        print(f"Parsing query: {user_query}")
        prompt = f"""
        Extract the following information from this query about places:
        1. Type of place (restaurant, cafe, bar, etc.)
        2. Specific attributes (vegan, Italian, etc.) - return as a list
        3. Location/neighborhood
        4. Opening hours requirement
        5. Day of week
        
        Query: {user_query}
        
        Format your response as a JSON object with these keys:
        place_type, attributes (as a list), location, open_until, day_of_week

        Example format:
        {{
            "place_type": "restaurant",
            "attributes": ["vegan", "organic"],
            "location": "Manhattan",
            "open_until": "10 pm",
            "day_of_week": "Friday"
        }}
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4.5-preview-2025-02-27",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                response_format={ "type": "json_object" }
            )
            print(f"OpenAI response: {response}")
            
            # Extract the JSON from the LLM response
            parsed_json = json.loads(response.choices[0].message.content)
            
            # Ensure attributes is a list
            if isinstance(parsed_json.get('attributes'), str):
                parsed_json['attributes'] = [parsed_json['attributes']]
            
            print(f"Parsed JSON: {parsed_json}")
            return parsed_json
        except Exception as e:
            print(f"Error in parse_query: {str(e)}")
            print(f"Error type: {type(e)}")
            return self._fallback_parsing(user_query)
    
    def _fallback_parsing(self, query: str) -> Dict[str, Any]:
        """Simple fallback parsing if JSON extraction fails."""
        params = {
            "place_type": "restaurant",
            "attributes": [],
            "location": "",
            "open_until": None,
            "day_of_week": None
        }
        
        # Basic extraction
        if "vegan" in query.lower():
            params["attributes"].append("vegan")
            
        if "restaurant" in query.lower():
            params["place_type"] = "restaurant"
            
        # Extract location
        if "in" in query.lower():
            parts = query.lower().split("in")
            if len(parts) > 1:
                location_part = parts[1].strip()
                if "which" in location_part:
                    location_part = location_part.split("which")[0].strip()
                params["location"] = location_part
        
        # Extract time
        if "till" in query.lower() or "until" in query.lower():
            for part in query.lower().replace("till", "until").split("until"):
                if "pm" in part or "am" in part:
                    time_parts = part.strip().split()
                    params["open_until"] = time_parts[0]
        
        # Extract day
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        for day in days:
            if day in query.lower():
                params["day_of_week"] = day
                
        return params
    
    def search_places(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search for places using the Google Maps Places API based on the extracted parameters.
        """
        try:
            # Validate API key
            print(f"Using Google Maps API key: {self.google_api_key[:6]}...")  # Only print first 6 chars for security
            if not self.google_api_key:
                print("Error: Google Maps API key is missing")
                return []

            # Build the query
            place_type = params.get("place_type", "restaurant")
            attributes = params.get("attributes", [])
            location = params.get("location", "")
            
            print(f"Searching for: type={place_type}, attributes={attributes}, location={location}")
            
            # Format the query for the Places API
            keyword = " ".join([place_type] + attributes)
            
            # First, test the API key with a simple geocoding request
            test_url = f"{self.base_url}/geocode/json"
            test_params = {
                "address": "New York",  # Simple test address
                "key": self.google_api_key
            }
            
            print("Testing API key with simple geocoding request...")
            test_response = requests.get(test_url, params=test_params)
            test_data = test_response.json()
            print(f"Test API response status: {test_data.get('status')}")
            print(f"Test API full response: {test_data}")
            
            if test_data.get('error_message'):
                print(f"API Error Message: {test_data.get('error_message')}")
                return []
            
            # Now proceed with actual geocoding request
            geocode_url = f"{self.base_url}/geocode/json"
            geocode_params = {
                "address": location,
                "key": self.google_api_key
            }
            
            print(f"Making geocoding request for: {location}")
            print(f"Full geocoding URL: {geocode_url}?address={location}&key=[HIDDEN]")
            
            geocode_response = requests.get(geocode_url, params=geocode_params)
            geocode_data = geocode_response.json()
            
            if geocode_data.get('error_message'):
                print(f"Geocoding Error Message: {geocode_data.get('error_message')}")
                return []
            
            print(f"Geocoding response status: {geocode_data.get('status')}")
            
            if geocode_data.get("status") != "OK" or not geocode_data.get("results"):
                print(f"Geocoding failed with status: {geocode_data.get('status')}")
                return []
            
            # Extract location coordinates
            location_coords = geocode_data["results"][0]["geometry"]["location"]
            latitude = location_coords["lat"]
            longitude = location_coords["lng"]
            
            print(f"Found coordinates: lat={latitude}, lng={longitude}")
            
            # Now search for places using the Places API
            places_url = f"{self.base_url}/place/nearbysearch/json"
            places_params = {
                "location": f"{latitude},{longitude}",
                "radius": 1500,  # 1.5km radius
                "type": place_type.lower(),
                "keyword": " ".join(attributes),
                "key": self.google_api_key
            }
            
            print(f"Making places search request...")
            print(f"Places search parameters: {places_params}")
            
            places_response = requests.get(places_url, params=places_params)
            places_data = places_response.json()
            
            if places_data.get('error_message'):
                print(f"Places API Error Message: {places_data.get('error_message')}")
                return []
            
            print(f"Places API response status: {places_data.get('status')}")
            
            if places_data.get("status") != "OK":
                print(f"Places API failed with status: {places_data.get('status')}")
                return []
            
            results = places_data.get("results", [])
            print(f"Found {len(results)} places before filtering")
            
            # Filter based on opening hours if specified
            filtered_results = []
            
            day_of_week = params.get("day_of_week")
            open_until = params.get("open_until")
            
            if not (day_of_week and open_until):
                return results
            
            # For each place, check if it's open until the specified time on the specified day
            for place in results:
                place_id = place.get("place_id")
                if not place_id:
                    continue
                
                # Get place details to check opening hours
                details_url = f"{self.base_url}/place/details/json"
                details_params = {
                    "place_id": place_id,
                    "fields": "name,place_id,formatted_address,opening_hours,website,formatted_phone_number,rating,review",
                    "key": self.google_api_key
                }
                
                details_response = requests.get(details_url, params=details_params)
                details_data = details_response.json()
                
                if details_data.get("status") != "OK" or not details_data.get("result"):
                    continue
                
                place_details = details_data["result"]
                
                # Check if the place has opening hours information
                if "opening_hours" in place_details and "periods" in place_details["opening_hours"]:
                    periods = place_details["opening_hours"]["periods"]
                    
                    # Map day of week to number (0 = Sunday, 1 = Monday, etc.)
                    day_map = {
                        "sunday": 0, "monday": 1, "tuesday": 2, "wednesday": 3,
                        "thursday": 4, "friday": 5, "saturday": 6
                    }
                    
                    day_num = day_map.get(day_of_week.lower(), -1)
                    
                    if day_num == -1:
                        continue
                    
                    # Find the period for the specified day
                    day_period = None
                    for period in periods:
                        if period.get("open", {}).get("day") == day_num:
                            day_period = period
                            break
                    
                    if not day_period:
                        continue
                    
                    # Check if the place is open until the specified time
                    close_time = day_period.get("close", {}).get("time")
                    if not close_time:
                        continue
                    
                    # Convert times to 24-hour format for comparison
                    requested_hours, requested_minutes = self._parse_time(open_until)
                    requested_time = requested_hours * 100 + requested_minutes
                    
                    # The time in Google API is in 24-hour format (e.g., "2300" for 11:00 PM)
                    if int(close_time) >= requested_time:
                        filtered_results.append(place_details)
            
            return filtered_results
        
        except Exception as e:
            print(f"Error in search_places: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return []
    
    def _parse_time(self, time_str: str) -> tuple:
        """Parse time string (e.g., '11 pm') to hours and minutes."""
        parts = time_str.lower().strip().split()
        time_val = int(parts[0])
        
        if "pm" in parts[1] and time_val < 12:
            time_val += 12
        elif "am" in parts[1] and time_val == 12:
            time_val = 0
            
        return time_val, 0  # Assuming minutes are always 0 for simplicity
    
    def format_results(self, results: List[Dict[str, Any]]) -> str:
        """Format the search results into a human-readable response."""
        if not results:
            return "I couldn't find any places matching your criteria."
        
        response = f"I found {len(results)} places matching your criteria:\n\n"
        
        for i, place in enumerate(results, 1):
            name = place.get("name", "Unnamed place")
            address = place.get("formatted_address", "No address available")
            rating = place.get("rating", "No rating")
            website = place.get("website", "No website available")
            phone = place.get("formatted_phone_number", "No phone number available")
            
            response += f"{i}. {name}\n"
            response += f"   Address: {address}\n"
            response += f"   Rating: {rating} ⭐\n"
            response += f"   Phone: {phone}\n"
            response += f"   Website: {website}\n\n"
        
        return response
    
    def process_query(self, user_query: str) -> str:
        """
        Main method to process a natural language query about places.
        """
        try:
            print(f"\n--- Processing new query: {user_query} ---")
            
            # Step 1: Parse the query using the LLM
            print("Step 1: Parsing query")
            params = self.parse_query(user_query)
            print(f"Parsed parameters: {params}")
            
            # Step 2: Search for places using the Google Maps API
            print("Step 2: Searching places")
            results = self.search_places(params)
            print(f"Search results count: {len(results)}")
            
            # Step 3: Format and return the results
            print("Step 3: Formatting results")
            formatted_results = self.format_results(results)
            print("Query processing completed successfully")
            return formatted_results
        
        except Exception as e:
            print(f"Error in process_query: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return f"An error occurred while processing your query: {str(e)}"

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
