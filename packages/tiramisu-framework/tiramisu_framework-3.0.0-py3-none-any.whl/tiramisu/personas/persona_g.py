from typing import Dict, List
from .base import PersonaBase, ValidationGap, ActionPlan, Severity

class PersonaG(PersonaBase):
    def __init__(self):
        super().__init__(
            persona_id="G",
            expertise="Execution and Content",
            focus=["video_content", "personal_brand", "community", "authenticity", "fast_action"]
        )
        
        self.required_fields = {
            "video_presence": Severity.MEDIUM,
            "posting_frequency": Severity.MEDIUM,
            "communication_tone": Severity.LOW,
            "production_resources": Severity.LOW,
            "current_audience": Severity.MEDIUM
        }
    
    def validate_gaps(self, context: Dict) -> List[ValidationGap]:
        gaps = []
        for field, severity in self.required_fields.items():
            if field not in context or not context[field]:
                gaps.append(ValidationGap(
                    field=field,
                    severity=severity,
                    message=f"Persona G: missing information about {field}"
                ))
        return gaps
    
    def analyze(self, query: str, context: Dict) -> Dict:
        return {
            "persona": "G",
            "type": "main_analysis",
            "focus": "execution",
            "query": query,
            "diagnosis": None,
            "content_format": None,
            "focus_platform": None
        }
    
    def supplement(self, query: str, context: Dict, leader_analysis: Dict) -> Dict:
        return {
            "persona": "G",
            "type": "supplement",
            "insight": None,
            "gap_covered": "practical_execution"
        }
    
    def generate_action(self, analysis: Dict) -> ActionPlan:
        return ActionPlan(
            description="Create authentic content",
            priority=3,
            impact="medium",
            deadline="7 days"
        )
