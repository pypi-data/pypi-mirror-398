from typing import Dict, List
from .base import PersonaBase, ValidationGap, ActionPlan, Severity

class PersonaM(PersonaBase):
    def __init__(self):
        super().__init__(
            persona_id="M",
            expertise="Digital Marketing",
            focus=["digital_channels", "metrics", "content", "engagement", "technology"]
        )
        
        self.required_fields = {
            "current_channels": Severity.HIGH,
            "digital_budget": Severity.MEDIUM,
            "current_metrics": Severity.MEDIUM,
            "online_audience": Severity.MEDIUM,
            "digital_goals": Severity.LOW
        }
    
    def validate_gaps(self, context: Dict) -> List[ValidationGap]:
        gaps = []
        for field, severity in self.required_fields.items():
            if field not in context or not context[field]:
                gaps.append(ValidationGap(
                    field=field,
                    severity=severity,
                    message=f"Persona M: missing information about {field}"
                ))
        return gaps
    
    def analyze(self, query: str, context: Dict) -> Dict:
        return {
            "persona": "M",
            "type": "main_analysis",
            "focus": "digital",
            "query": query,
            "diagnosis": None,
            "recommended_channels": None,
            "target_metrics": None
        }
    
    def supplement(self, query: str, context: Dict, leader_analysis: Dict) -> Dict:
        return {
            "persona": "M",
            "type": "supplement",
            "insight": None,
            "gap_covered": "digital_presence"
        }
    
    def generate_action(self, analysis: Dict) -> ActionPlan:
        return ActionPlan(
            description="Activate presence on priority channels",
            priority=2,
            impact="medium",
            deadline="14 days"
        )
