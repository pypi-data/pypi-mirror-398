"""
Supervisor - Routes queries to appropriate experts
Generic version for framework
"""
from typing import Literal
from langchain_openai import ChatOpenAI

class Supervisor:
    def __init__(self, model_name: str = "gpt-4"):
        self.llm = ChatOpenAI(model=model_name, temperature=0)
        
        self.strategy_keywords = [
            "strategy", "positioning", "swot", "framework",
            "planning", "segmentation", "targeting"
        ]
        
        self.digital_keywords = [
            "social", "instagram", "tiktok", "content",
            "engagement", "viral", "posts", "stories"
        ]
        
        self.tech_keywords = [
            "ai", "automation", "technology", "data",
            "digital transformation", "software", "api"
        ]
    
    def route(self, query: str) -> str:
        query_lower = query.lower()
        
        # Check keywords
        strategy_score = sum(1 for kw in self.strategy_keywords if kw in query_lower)
        digital_score = sum(1 for kw in self.digital_keywords if kw in query_lower)
        tech_score = sum(1 for kw in self.tech_keywords if kw in query_lower)
        
        if digital_score > strategy_score and digital_score > tech_score:
            return "digital"
        elif tech_score > strategy_score and tech_score > digital_score:
            return "tech"
        else:
            return "strategy"
