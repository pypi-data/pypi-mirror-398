from typing import Dict, List
from .base import PersonaBase, ValidationGap, ActionPlan, Severity

class PersonaK(PersonaBase):
    def __init__(self):
        super().__init__(
            persona_id="K",
            expertise="Marketing Strategy",
            focus=["positioning", "segmentation", "4ps", "value_proposition", "competition"]
        )
        
        self.required_fields = {
            "product": Severity.HIGH,
            "target_market": Severity.HIGH,
            "price": Severity.MEDIUM,
            "competitors": Severity.MEDIUM,
            "value_proposition": Severity.MEDIUM
        }
    
    def validate_gaps(self, context: Dict) -> List[ValidationGap]:
        gaps = []
        for field, severity in self.required_fields.items():
            if field not in context or not context[field]:
                gaps.append(ValidationGap(
                    field=field,
                    severity=severity,
                    message=f"Persona K: missing information about {field}"
                ))
        return gaps
    
    def analyze(self, query: str, context: Dict) -> Dict:
        return {
            "persona": "K",
            "type": "main_analysis",
            "focus": "strategy",
            "query": query,
            "diagnosis": None,
            "framework_applied": None,
            "recommendation": None
        }
    
    def supplement(self, query: str, context: Dict, leader_analysis: Dict) -> Dict:
        return {
            "persona": "K",
            "type": "supplement",
            "insight": None,
            "gap_covered": "strategic_vision"
        }
    
    def generate_action(self, analysis: Dict) -> ActionPlan:
        return ActionPlan(
            description="Define strategic positioning",
            priority=1,
            impact="high",
            deadline="30 days"
        )
