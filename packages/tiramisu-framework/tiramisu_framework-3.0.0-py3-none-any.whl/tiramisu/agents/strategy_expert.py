"""
Strategy Expert - Marketing Strategy Specialist
Generic version for framework
"""
from typing import Dict, List
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

class StrategyExpert:
    def __init__(self, model_name: str = "gpt-4"):
        self.llm = ChatOpenAI(model=model_name, temperature=0.3)
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
        self.name = "Strategy Expert"
        self.expertise = "Strategic planning, frameworks, positioning"
        
    def analyze(self, query: str) -> str:
        prompt = f"""You are a strategic marketing expert.
        Focus on: frameworks, SWOT analysis, positioning, long-term planning.
        Provide structured, analytical responses.
        
        Query: {query}"""
        
        response = self.llm.invoke(prompt)
        return response.content
