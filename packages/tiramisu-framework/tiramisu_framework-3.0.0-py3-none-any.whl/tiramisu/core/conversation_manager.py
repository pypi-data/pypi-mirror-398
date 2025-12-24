"""
Conversation Manager - Gerencia conversas contínuas com contexto
"""
from typing import List, Dict, Optional, Tuple
from tiramisu.core.conversation_db import ConversationDB


class ConversationManager:
    """Gerencia conversas com contexto acumulado"""
    
    def __init__(self, db_path: str = "tiramisu.db"):
        """Inicializa o gerenciador"""
        self.db = ConversationDB(db_path)
        print("✅ ConversationManager inicializado")
    
    def start_conversation(self, title: str = None) -> str:
        """Inicia nova conversa"""
        conversation_id = self.db.create_conversation(title)
        print(f"🆕 Nova conversa criada: {conversation_id}")
        return conversation_id
    
    def add_user_message(self, conversation_id: str, content: str) -> str:
        """Adiciona mensagem do usuário"""
        message_id = self.db.add_message(
            conversation_id=conversation_id,
            role="user",
            content=content
        )
        return message_id
    
    def add_assistant_message(
        self, 
        conversation_id: str, 
        content: str,
        mode: str = None,
        sources: List[str] = None
    ) -> str:
        """Adiciona resposta da Tiramisu"""
        message_id = self.db.add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=content,
            mode=mode,
            sources=sources
        )
        return message_id
    
    def get_conversation_context(self, conversation_id: str) -> str:
        """
        Monta contexto completo da conversa para passar ao LLM
        Formato: histórico de mensagens anteriores
        """
        history = self.db.get_conversation_history(conversation_id)
        
        if not history:
            return ""
        
        # Montar contexto em formato de conversa
        context_parts = ["HISTÓRICO DA CONVERSA:\n"]
        
        for msg in history:
            role = "Usuário" if msg['role'] == 'user' else "Tiramisu"
            context_parts.append(f"\n{role}: {msg['content'][:500]}...")
        
        context_parts.append("\n\n---\n")
        
        return "\n".join(context_parts)
    
    def get_last_messages(self, conversation_id: str, n: int = 3) -> List[Dict]:
        """Retorna as últimas N mensagens"""
        history = self.db.get_conversation_history(conversation_id)
        return history[-n:] if history else []
    
    def list_conversations(self, limit: int = 20) -> List[Dict]:
        """Lista conversas recentes"""
        return self.db.list_conversations(limit)
    
    def update_title(self, conversation_id: str, title: str):
        """Atualiza título da conversa"""
        self.db.update_conversation_title(conversation_id, title)
    
    def format_conversation_for_display(self, conversation_id: str) -> str:
        """Formata conversa para exibição bonita"""
        history = self.db.get_conversation_history(conversation_id)
        
        if not history:
            return "Conversa vazia"
        
        output = []
        output.append("="*70)
        output.append("💬 HISTÓRICO DA CONVERSA")
        output.append("="*70)
        
        for i, msg in enumerate(history, 1):
            role_emoji = "👤" if msg['role'] == 'user' else "��"
            role_name = "Você" if msg['role'] == 'user' else "Tiramisu"
            
            output.append(f"\n{role_emoji} {role_name} ({msg['created_at']}):")
            output.append("-" * 70)
            output.append(msg['content'][:500] + ("..." if len(msg['content']) > 500 else ""))
            
            # Mostrar fontes se for resposta da Tiramisu
            if msg['role'] == 'assistant':
                sources = self.db.get_message_sources(msg['id'])
                if sources:
                    output.append(f"\n📚 Fontes: {', '.join(sources)}")
        
        output.append("\n" + "="*70)
        
        return "\n".join(output)
