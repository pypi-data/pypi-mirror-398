"""
Conversation Database - Gerenciamento de histórico com SQLite
"""
import sqlite3
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path


class ConversationDB:
    """Gerencia conversas e histórico no SQLite"""
    
    def __init__(self, db_path: str = "tiramisu.db"):
        """Inicializa conexão com SQLite"""
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Cria tabelas se não existirem"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabela de conversas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                title TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de mensagens
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                mode TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            )
        """)
        
        # Tabela de contexto RAG (fontes usadas)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rag_sources (
                id TEXT PRIMARY KEY,
                message_id TEXT NOT NULL,
                source TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (message_id) REFERENCES messages(id)
            )
        """)
        
        # Índices para performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_conversation 
            ON messages(conversation_id, created_at)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_rag_message 
            ON rag_sources(message_id)
        """)
        
        conn.commit()
        conn.close()
        
        print("✅ Database SQLite inicializado")
    
    def create_conversation(self, title: str = None) -> str:
        """Cria nova conversa e retorna o ID"""
        conversation_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO conversations (id, title)
            VALUES (?, ?)
        """, (conversation_id, title or "Nova Conversa"))
        
        conn.commit()
        conn.close()
        
        return conversation_id
    
    def add_message(
        self, 
        conversation_id: str, 
        role: str, 
        content: str,
        mode: str = None,
        sources: List[str] = None
    ) -> str:
        """Adiciona mensagem à conversa"""
        message_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Inserir mensagem
        cursor.execute("""
            INSERT INTO messages (id, conversation_id, role, content, mode)
            VALUES (?, ?, ?, ?, ?)
        """, (message_id, conversation_id, role, content, mode))
        
        # Inserir fontes RAG se houver
        if sources:
            for source in sources:
                source_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO rag_sources (id, message_id, source)
                    VALUES (?, ?, ?)
                """, (source_id, message_id, source))
        
        # Atualizar timestamp da conversa
        cursor.execute("""
            UPDATE conversations 
            SET updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        """, (conversation_id,))
        
        conn.commit()
        conn.close()
        
        return message_id
    
    def get_conversation_history(self, conversation_id: str) -> List[Dict]:
        """Retorna histórico completo da conversa"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, role, content, mode, created_at
            FROM messages
            WHERE conversation_id = ?
            ORDER BY created_at ASC
        """, (conversation_id,))
        
        messages = []
        for row in cursor.fetchall():
            messages.append({
                'id': row[0],
                'role': row[1],
                'content': row[2],
                'mode': row[3],
                'created_at': row[4]
            })
        
        conn.close()
        return messages
    
    def get_message_sources(self, message_id: str) -> List[str]:
        """Retorna fontes RAG de uma mensagem"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT source FROM rag_sources
            WHERE message_id = ?
        """, (message_id,))
        
        sources = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return sources
    
    def list_conversations(self, limit: int = 20) -> List[Dict]:
        """Lista conversas recentes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, title, created_at, updated_at
            FROM conversations
            ORDER BY updated_at DESC
            LIMIT ?
        """, (limit,))
        
        conversations = []
        for row in cursor.fetchall():
            conversations.append({
                'id': row[0],
                'title': row[1],
                'created_at': row[2],
                'updated_at': row[3]
            })
        
        conn.close()
        return conversations
    
    def update_conversation_title(self, conversation_id: str, title: str):
        """Atualiza título da conversa"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE conversations 
            SET title = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (title, conversation_id))
        
        conn.commit()
        conn.close()
