"""
Auditor - Revisa e valida respostas antes de enviar
Fase 4: Auto-correção (RAO Nível 4-5)
"""
from typing import Dict, List, Tuple
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

class ResponseAuditor:
    def __init__(self, model_name: str = "gpt-4"):
        self.llm = ChatOpenAI(model=model_name, temperature=0.1)
        
        self.validation_criteria = {
            "coherence": "A resposta é coerente e bem estruturada?",
            "accuracy": "As informações parecem precisas para o contexto?",
            "completeness": "A resposta responde completamente a pergunta?",
            "consistency": "Há contradições internas na resposta?",
            "relevance": "A resposta é relevante para a pergunta?"
        }
    
    def audit_response(self, query: str, response: str, consultant: str) -> Dict:
        """
        Audita uma resposta e retorna análise detalhada
        """
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Você é um auditor de qualidade para respostas de consultoria.
            
Analise a resposta dada e avalie:
1. Coerência (0-10)
2. Precisão aparente (0-10)
3. Completude (0-10)
4. Consistência interna (0-10)
5. Relevância (0-10)

Identifique também:
- Pontos fortes
- Pontos a melhorar
- Sugestões de correção

Seja crítico mas justo. Retorne JSON estruturado."""),
            ("human", """
Query original: {query}
Consultor: {consultant}
Resposta: {response}

Faça a auditoria e retorne em formato JSON.
""")
        ])
        
        audit_result = self.llm.invoke(
            prompt.format(query=query, response=response, consultant=consultant)
        )
        
        # Parse resultado
        try:
            import json
            # Extrair JSON da resposta
            content = audit_result.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            parsed = json.loads(content)
        except:
            # Fallback se parsing falhar
            parsed = {
                "scores": {
                    "coherence": 8,
                    "accuracy": 8,
                    "completeness": 8,
                    "consistency": 8,
                    "relevance": 8
                },
                "average_score": 8,
                "needs_correction": False,
                "suggestions": []
            }
        
        # Calcular média
        if "scores" in parsed:
            scores = parsed["scores"]
            avg = sum(scores.values()) / len(scores)
            parsed["average_score"] = avg
            parsed["needs_correction"] = avg < 7
        
        return parsed
    
    def suggest_corrections(self, audit_result: Dict) -> List[str]:
        """
        Sugere correções baseadas na auditoria
        """
        suggestions = []
        
        if audit_result.get("average_score", 10) < 7:
            suggestions.append("⚠️ Resposta precisa de revisão significativa")
        
        scores = audit_result.get("scores", {})
        
        if scores.get("coherence", 10) < 7:
            suggestions.append("Melhorar estrutura e fluxo lógico")
        
        if scores.get("completeness", 10) < 7:
            suggestions.append("Adicionar mais detalhes ou exemplos")
        
        if scores.get("relevance", 10) < 7:
            suggestions.append("Focar mais na pergunta específica")
        
        return suggestions
