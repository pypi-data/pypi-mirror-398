"""
Fact Checker - Verifica fatos e consistência
Fase 4: Auto-correção (RAO Nível 4-5)
"""
from typing import Dict, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

class FactChecker:
    def __init__(self, model_name: str = "gpt-4"):
        self.llm = ChatOpenAI(model=model_name, temperature=0)
        
        # Base de conhecimento para validação
        self.known_facts = {
            "4ps": ["produto", "preço", "praça", "promoção"],
            "swot": ["forças", "fraquezas", "oportunidades", "ameaças"],
            "consultores": {
                "Strategy Expert": "estratégia e marketing tradicional",
                "Digital Expert": "redes sociais e execução",
                "Tech Expert": "tecnologia e transformação digital"
            }
        }
    
    def check_facts(self, response: str, consultant: str) -> Dict:
        """
        Verifica fatos na resposta
        """
        
        issues = []
        confidence = 100
        
        # Verificar menções aos 4Ps
        if "4p" in response.lower() or "4 ps" in response.lower():
            for p in self.known_facts["4ps"]:
                if p not in response.lower():
                    issues.append(f"4Ps incompleto - falta {p}")
                    confidence -= 5
        
        # Verificar SWOT
        if "swot" in response.lower():
            for item in self.known_facts["swot"]:
                if item not in response.lower():
                    issues.append(f"SWOT incompleto - falta {item}")
                    confidence -= 5
        
        # Verificar atribuição correta
        if consultant in self.known_facts["consultores"]:
            expertise = self.known_facts["consultores"][consultant]
            if consultant == "Strategy Expert" and "tiktok" in response.lower():
                issues.append("Strategy Expert falando sobre TikTok (fora da expertise)")
                confidence -= 10
            elif consultant == "Digital Expert" and "matriz bcg" in response.lower():
                issues.append("Digital Expert falando sobre BCG (fora da expertise)")
                confidence -= 10
        
        return {
            "confidence": confidence,
            "issues": issues,
            "needs_verification": len(issues) > 0
        }
    
    def cross_check(self, response1: str, response2: str) -> Dict:
        """
        Verifica consistência entre duas respostas
        """
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Compare duas respostas e identifique:
1. Contradições diretas
2. Inconsistências de dados
3. Diferenças significativas de abordagem

Retorne análise estruturada."""),
            ("human", """
Resposta 1: {response1}

Resposta 2: {response2}

Há contradições ou inconsistências?
""")
        ])
        
        check_result = self.llm.invoke(
            prompt.format(response1=response1[:500], response2=response2[:500])
        )
        
        return {
            "analysis": check_result.content,
            "has_contradictions": "contradiç" in check_result.content.lower()
        }
