from abc import ABC, abstractmethod
from typing import Dict, List
from dataclasses import dataclass
from enum import Enum

class Severity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class ConfidenceLevel(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    VERIFY = "verify"
    BLOCKED = "blocked"

@dataclass
class ValidationGap:
    field: str
    severity: Severity
    message: str

@dataclass
class ActionPlan:
    description: str
    priority: int
    impact: str
    deadline: str

class PersonaBase(ABC):
    def __init__(self, persona_id: str, expertise: str, focus: List[str]):
        self.persona_id = persona_id
        self.expertise = expertise
        self.focus = focus
    
    @abstractmethod
    def validate_gaps(self, context: Dict) -> List[ValidationGap]:
        pass
    
    @abstractmethod
    def analyze(self, query: str, context: Dict) -> Dict:
        pass
    
    @abstractmethod
    def supplement(self, query: str, context: Dict, leader_analysis: Dict) -> Dict:
        pass
    
    @abstractmethod
    def generate_action(self, analysis: Dict) -> ActionPlan:
        pass
