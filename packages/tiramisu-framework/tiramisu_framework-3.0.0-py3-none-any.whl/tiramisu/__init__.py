"""
Tiramisu Framework - RAO Multi-Agent Colaborativo
Sistema de Governanca de Decisoes em IA

Copyright (c) 2025 Jony Wolff. All rights reserved.
Licensed under MIT License.
"""
__version__ = "3.0.0"
__author__ = "Jony Wolff"
__email__ = "frameworktiramisu@gmail.com"

from tiramisu.personas import PersonaK, PersonaM, PersonaG
from tiramisu.rao import RAO4Validator, RAO5Analyzer, RAO6Planner
from tiramisu.governance import GovernanceOrchestrator

__all__ = [
    "__version__",
    "PersonaK",
    "PersonaM", 
    "PersonaG",
    "RAO4Validator",
    "RAO5Analyzer",
    "RAO6Planner",
    "GovernanceOrchestrator"
]
