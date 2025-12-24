from typing import Dict, List
from dataclasses import dataclass
from ..personas import PersonaK, PersonaM, PersonaG, ActionPlan

@dataclass
class Plan:
    actions: List[ActionPlan]
    quality_score: float
    summary: str
    decision_log: str

class RAO6Planner:
    def __init__(self):
        self.persona_k = PersonaK()
        self.persona_m = PersonaM()
        self.persona_g = PersonaG()
    
    def generate_plan(self, analysis) -> Plan:
        actions = []
        
        leader = analysis.leader
        leader_action = self._get_persona(leader).generate_action(analysis.main_analysis)
        leader_action.priority = 1
        actions.append(leader_action)
        
        priority = 2
        for supplement in analysis.supplements:
            persona_id = supplement.get("persona")
            action = self._get_persona(persona_id).generate_action(supplement)
            action.priority = priority
            actions.append(action)
            priority += 1
        
        score = self._calculate_score(analysis, actions)
        summary = self._generate_summary(actions)
        log = self._generate_log(actions, score)
        
        return Plan(
            actions=actions,
            quality_score=score,
            summary=summary,
            decision_log=log
        )
    
    def _get_persona(self, persona_id: str):
        mapping = {
            "K": self.persona_k,
            "M": self.persona_m,
            "G": self.persona_g
        }
        return mapping[persona_id]
    
    def _calculate_score(self, analysis, actions: List[ActionPlan]) -> float:
        score = 100.0
        
        if analysis.routing_confidence == "low":
            score -= 20
        elif analysis.routing_confidence == "medium":
            score -= 10
        
        if len(actions) < 3:
            score -= 15
        
        return max(0, score)
    
    def _generate_summary(self, actions: List[ActionPlan]) -> str:
        lines = ["Prioritized Action Plan:"]
        for action in sorted(actions, key=lambda a: a.priority):
            lines.append(f"  P{action.priority}: {action.description} ({action.deadline})")
        return "\n".join(lines)
    
    def _generate_log(self, actions: List[ActionPlan], score: float) -> str:
        log_lines = [
            f"RAO-6 Collaborative Plan",
            f"Actions generated: {len(actions)}",
            f"Quality score: {score}%",
            f"Priorities: {[a.priority for a in actions]}"
        ]
        return " | ".join(log_lines)
