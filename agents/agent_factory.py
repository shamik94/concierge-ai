from typing import Dict, Type
from .base_agent import BaseAgent
from .query_analysis_agent import QueryAnalysisAgent
from .location_analysis_agent import LocationAnalysisAgent
from .time_analysis_agent import TimeAnalysisAgent
from .place_validation_agent import PlaceValidationAgent
from .attribute_check_agent import AttributeCheckAgent
from .generic_query_agent import GenericQueryAgent

class AgentFactory:
    _agents: Dict[str, Type[BaseAgent]] = {
        "QueryAnalysisAgent": QueryAnalysisAgent,
        "LocationAnalysisAgent": LocationAnalysisAgent,
        "TimeAnalysisAgent": TimeAnalysisAgent,
        "PlaceValidationAgent": PlaceValidationAgent,
        "AttributeCheckAgent": AttributeCheckAgent,
        "GenericQueryAgent": GenericQueryAgent
    }

    @classmethod
    def create_agent(cls, agent_type: str, **kwargs) -> BaseAgent:
        if agent_type not in cls._agents:
            raise ValueError(f"Unknown agent type: {agent_type}")
        return cls._agents[agent_type](**kwargs) 