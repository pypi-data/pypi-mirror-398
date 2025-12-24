from typing import Dict, List, Optional
from dataclasses import dataclass
from ..personas import PersonaK, PersonaM, PersonaG, ConfidenceLevel

@dataclass
class AnalysisResult:
    leader: str
    routing_confidence: str
    main_analysis: Dict
    supplements: List[Dict]
    routing_method: str
    decision_log: str

class RAO5Analyzer:
    def __init__(self):
        self.persona_k = PersonaK()
        self.persona_m = PersonaM()
        self.persona_g = PersonaG()
        
        self.keywords = {
            "K": ["strategy", "positioning", "segment", "market", "4ps", "swot", "price", "competitor"],
            "M": ["digital", "social media", "instagram", "tiktok", "metric", "engagement", "seo", "ads", "online"],
            "G": ["video", "content", "youtube", "personal brand", "community", "viral", "post", "authenticity"]
        }
    
    def analyze(self, query: str, context: Dict) -> AnalysisResult:
        leader, confidence, method = self._route(query)
        
        main_analysis = self._get_persona(leader).analyze(query, context)
        
        supplements = []
        for pid in ["K", "M", "G"]:
            if pid != leader:
                supplement = self._get_persona(pid).supplement(query, context, main_analysis)
                supplements.append(supplement)
        
        log = self._generate_log(leader, confidence, method)
        
        return AnalysisResult(
            leader=leader,
            routing_confidence=confidence,
            main_analysis=main_analysis,
            supplements=supplements,
            routing_method=method,
            decision_log=log
        )
    
    def _route(self, query: str) -> tuple:
        query_lower = query.lower()
        
        scores = {"K": 0, "M": 0, "G": 0}
        for persona, kws in self.keywords.items():
            for kw in kws:
                if kw in query_lower:
                    scores[persona] += 1
        
        max_score = max(scores.values())
        
        if max_score >= 2:
            leader = max(scores, key=scores.get)
            return (leader, "high", "keywords")
        elif max_score == 1:
            leader = max(scores, key=scores.get)
            return (leader, "medium", "keywords")
        else:
            return ("K", "low", "fallback")
    
    def _get_persona(self, persona_id: str):
        mapping = {
            "K": self.persona_k,
            "M": self.persona_m,
            "G": self.persona_g
        }
        return mapping[persona_id]
    
    def _generate_log(self, leader: str, confidence: str, method: str) -> str:
        log_lines = [
            f"RAO-5 Collaborative Analysis",
            f"Leader: Persona {leader}",
            f"Confidence: {confidence}",
            f"Method: {method}",
            f"Support: {[p for p in ['K','M','G'] if p != leader]}"
        ]
        return " | ".join(log_lines)
