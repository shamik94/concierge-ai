from typing import Dict, Any
from .base_agent import BaseAgent

class TimeAnalysisAgent(BaseAgent):
    def __init__(self, **kwargs):
        self.day_mapping = {
            "monday": 1, "tuesday": 2, "wednesday": 3, "thursday": 4,
            "friday": 5, "saturday": 6, "sunday": 0
        }

    def process(self, params: Dict[str, Any]) -> Dict[str, Any]:
        temporal = params.get("temporal", {})
        if not temporal:
            return {"valid": True, "has_temporal": False}

        try:
            day = temporal.get("day", "").lower()
            time_str = temporal.get("time", "")
            context = temporal.get("time_context", "open_until")
            
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
                "valid": True,
                "has_temporal": True,
                "day_number": self.day_mapping.get(day, -1),
                "day_name": day,
                "hour_24": hour,
                "context": context
            }
        except Exception as e:
            return {"valid": False, "error": str(e)}

    def validate_response(self, response: Dict[str, Any]) -> bool:
        return response.get("valid", False) 