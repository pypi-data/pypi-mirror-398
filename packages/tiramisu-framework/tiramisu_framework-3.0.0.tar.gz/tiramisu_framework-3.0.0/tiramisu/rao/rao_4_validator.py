from typing import Dict, List
from dataclasses import dataclass
from ..personas import PersonaK, PersonaM, PersonaG, ValidationGap, Severity, ConfidenceLevel

@dataclass
class ValidationResult:
    approved: bool
    confidence: ConfidenceLevel
    gaps_by_persona: Dict[str, List[ValidationGap]]
    total_gaps: int
    can_proceed_with: List[str]
    decision_log: str

class RAO4Validator:
    def __init__(self):
        self.persona_k = PersonaK()
        self.persona_m = PersonaM()
        self.persona_g = PersonaG()
    
    def validate(self, query: str, context: Dict) -> ValidationResult:
        gaps_k = self.persona_k.validate_gaps(context)
        gaps_m = self.persona_m.validate_gaps(context)
        gaps_g = self.persona_g.validate_gaps(context)
        
        all_gaps = gaps_k + gaps_m + gaps_g
        confidence = self._classify_confidence(all_gaps)
        approved = confidence != ConfidenceLevel.BLOCKED
        can_proceed = self._evaluate_sufficiency(all_gaps)
        
        log = self._generate_log(confidence, all_gaps)
        
        return ValidationResult(
            approved=approved,
            confidence=confidence,
            gaps_by_persona={"K": gaps_k, "M": gaps_m, "G": gaps_g},
            total_gaps=len(all_gaps),
            can_proceed_with=can_proceed,
            decision_log=log
        )
    
    def _classify_confidence(self, gaps: List[ValidationGap]) -> ConfidenceLevel:
        critical = [g for g in gaps if g.severity == Severity.CRITICAL]
        high = [g for g in gaps if g.severity == Severity.HIGH]
        medium = [g for g in gaps if g.severity == Severity.MEDIUM]
        
        if len(critical) > 0:
            return ConfidenceLevel.BLOCKED
        elif len(high) > 2:
            return ConfidenceLevel.VERIFY
        elif len(high) > 0 or len(medium) > 3:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.HIGH
    
    def _evaluate_sufficiency(self, gaps: List[ValidationGap]) -> List[str]:
        sufficient_for = []
        high_gaps = [g for g in gaps if g.severity in [Severity.CRITICAL, Severity.HIGH]]
        
        if len(high_gaps) == 0:
            sufficient_for.extend(["full_analysis", "action_plan", "diagnosis"])
        elif len(high_gaps) <= 2:
            sufficient_for.extend(["partial_diagnosis", "general_recommendations"])
        else:
            sufficient_for.append("guidance_only")
        
        return sufficient_for
    
    def _generate_log(self, confidence: ConfidenceLevel, gaps: List[ValidationGap]) -> str:
        log_lines = [
            f"RAO-4 Collaborative Validation",
            f"Confidence: {confidence.value}",
            f"Total gaps: {len(gaps)}",
            "Decision: " + ("APPROVED" if confidence != ConfidenceLevel.BLOCKED else "BLOCKED")
        ]
        return " | ".join(log_lines)
