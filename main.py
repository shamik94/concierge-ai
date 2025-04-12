import os
import requests
from dotenv import load_dotenv
from typing import Dict, List, Any, Optional
from openai import OpenAI
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
from fastapi.middleware.cors import CORSMiddleware
import yaml
from agents.query_classifier import QueryClassifier
from agents.agent_factory import AgentFactory

# Load environment variables
load_dotenv()

# API Keys
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
openai_client = OpenAI(
    api_key=OPENAI_API_KEY
)

# Create FastAPI app
app = FastAPI(title="Smart Location Intelligence API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str

@app.post("/search")
async def search(request: QueryRequest):
    try:
        # Step 1: Classify the query
        classifier = QueryClassifier(openai_client)
        classification = classifier.classify(request.query)
        print(f"Classification: {classification}")
        
        query_type = classification.get("query_type", "unclassified")
        confidence = classification.get("confidence", 0.0)
        params = classification.get("extracted_params", {})
        params["query"] = request.query  # Add original query to params
        
        # Step 2: Initialize required agents based on query type
        agents = []
        if query_type == "place_search_temporal":
            from agents.query_analysis_agent import QueryAnalysisAgent
            from agents.location_analysis_agent import LocationAnalysisAgent
            from agents.time_analysis_agent import TimeAnalysisAgent
            
            agents = [
                QueryAnalysisAgent(openai_client),
                LocationAnalysisAgent(GOOGLE_MAPS_API_KEY),
                TimeAnalysisAgent()
            ]
        elif query_type == "place_attribute_check":
            from agents.place_validation_agent import PlaceValidationAgent
            from agents.attribute_check_agent import AttributeCheckAgent
            
            agents = [
                PlaceValidationAgent(GOOGLE_MAPS_API_KEY),
                AttributeCheckAgent(GOOGLE_MAPS_API_KEY, openai_client)
            ]
        elif query_type == "nearby_search":
            from agents.location_analysis_agent import LocationAnalysisAgent
            
            agents = [
                LocationAnalysisAgent(GOOGLE_MAPS_API_KEY)
            ]
        else:
            from agents.generic_query_agent import GenericQueryAgent
            agents = [GenericQueryAgent(openai_client)]
        
        # Step 3: Process query through agent pipeline
        context = params
        for agent in agents:
            result = agent.process(context)
            if not agent.validate_response(result):
                raise ValueError(f"Invalid response from agent {agent.__class__.__name__}")
            context.update(result)
        
        # Step 4: Format response
        response = {
            "query_type": query_type,
            "confidence": confidence,
            "results": context
        }
        
        return response

    except Exception as e:
        print(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ping")
async def ping():
    return {"status": "ok", "message": "Server is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)