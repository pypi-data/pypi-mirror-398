from typing import Dict
from dataclasses import dataclass
from ..rao import RAO4Validator, RAO5Analyzer, RAO6Planner

@dataclass
class GovernanceResult:
    success: bool
    validation: object
    analysis: object
    plan: object
    logs: list
    final_message: str

class GovernanceOrchestrator:
    def __init__(self):
        self.rao4 = RAO4Validator()
        self.rao5 = RAO5Analyzer()
        self.rao6 = RAO6Planner()
    
    def execute(self, query: str, context: Dict) -> GovernanceResult:
        logs = []
        
        validation = self.rao4.validate(query, context)
        logs.append(validation.decision_log)
        
        if not validation.approved:
            return GovernanceResult(
                success=False,
                validation=validation,
                analysis=None,
                plan=None,
                logs=logs,
                final_message=f"Blocked: confidence {validation.confidence.value}"
            )
        
        analysis = self.rao5.analyze(query, context)
        logs.append(analysis.decision_log)
        
        plan = self.rao6.generate_plan(analysis)
        logs.append(plan.decision_log)
        
        return GovernanceResult(
            success=True,
            validation=validation,
            analysis=analysis,
            plan=plan,
            logs=logs,
            final_message=f"Plan generated with score {plan.quality_score}%"
        )
    
    def display_logs(self, result: GovernanceResult) -> str:
        lines = [
            "=" * 50,
            "TIRAMISU 3.0 - Decision Governance",
            "=" * 50
        ]
        for log in result.logs:
            lines.append(f">> {log}")
        lines.append("=" * 50)
        lines.append(f"Result: {result.final_message}")
        lines.append("=" * 50)
        return "\n".join(lines)
