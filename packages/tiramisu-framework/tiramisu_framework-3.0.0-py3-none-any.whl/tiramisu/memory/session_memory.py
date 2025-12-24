"""
Memória de Sessão com Contexto
Fase 3: RAO Nível 3 - Memória Contextual
"""
from typing import Dict, List, Optional
from datetime import datetime
from tiramisu.memory.redis_manager import RedisManager

class SessionMemory:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.redis = RedisManager()
        self.context_window = []
        self.max_context = 5
        
        # Carregar histórico existente
        self.load_session()
    
    def load_session(self):
        """Carrega contexto anterior da sessão"""
        history = self.redis.get_history(self.session_id)
        if history:
            self.context_window = history[-self.max_context:]
            print(f"📚 Contexto carregado: {len(self.context_window)} interações anteriores")
    
    def add_interaction(self, query: str, consultant: str, response: str):
        """Adiciona nova interação ao contexto"""
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "consultant": consultant,
            "response": response[:500]  # Guarda só preview
        }
        
        # Adiciona ao contexto local
        self.context_window.append(interaction)
        if len(self.context_window) > self.max_context:
            self.context_window.pop(0)
        
        # Salva no Redis
        self.redis.append_to_history(self.session_id, interaction)
        
        # Atualiza sessão
        self.redis.set_session(self.session_id, {
            "last_interaction": datetime.now().isoformat(),
            "total_interactions": len(self.context_window),
            "consultants_used": list(set(i["consultant"] for i in self.context_window))
        })
    
    def get_context_summary(self) -> str:
        """Retorna resumo do contexto para o LLM"""
        if not self.context_window:
            return ""
        
        summary = "CONTEXTO DAS INTERAÇÕES ANTERIORES:\n"
        for i, interaction in enumerate(self.context_window, 1):
            summary += f"\n{i}. Pergunta: {interaction['query']}\n"
            summary += f"   Consultor: {interaction['consultant']}\n"
            summary += f"   Resumo: {interaction['response'][:200]}...\n"
        
        return summary
    
    def suggest_followup(self) -> List[str]:
        """Sugere perguntas de follow-up baseadas no contexto"""
        if not self.context_window:
            return []
        
        last_consultant = self.context_window[-1]["consultant"]
        suggestions = []
        
        if last_consultant == "Strategy Expert":
            suggestions = [
                "Como implementar essa estratégia?",
                "Quais métricas devo acompanhar?",
                "Pode detalhar o plano de ação?"
            ]
        elif last_consultant == "Digital Expert":
            suggestions = [
                "Quantas vezes postar por dia?",
                "Que tipo de conteúdo funciona melhor?",
                "Como medir engajamento?"
            ]
        elif last_consultant == "Tech Expert":
            suggestions = [
                "Quais ferramentas você recomenda?",
                "Como integrar com sistemas existentes?",
                "Qual o investimento necessário?"
            ]
        
        return suggestions
