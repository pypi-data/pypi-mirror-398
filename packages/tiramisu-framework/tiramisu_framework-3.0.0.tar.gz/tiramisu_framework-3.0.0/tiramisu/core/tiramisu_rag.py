"""
Tiramisu RAG - High-level wrapper for the framework
Copyright (c) 2025 Jony Wolff. All rights reserved.
"""
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from tiramisu.core.orchestrator import TiramisuOrchestrator
from tiramisu.core.conversation_manager import ConversationManager
from tiramisu.core.conversation_db import ConversationDB
from tiramisu.core.indexer import DocumentIndexer
import logging

logger = logging.getLogger(__name__)

class TiramisuRAG:
    """
    High-level interface for Tiramisu Framework
    Wraps the orchestrator with additional convenience methods
    """
    
    def __init__(
        self,
        documents_path: str = "./documents",
        experts: List[str] = None,
        model: str = "gpt-4o",
        chunk_size: int = 800,
        chunk_overlap: int = 150,
        db_path: str = "tiramisu.db"
    ):
        """
        Initialize TiramisuRAG system
        
        Args:
            documents_path: Path to documents directory
            experts: List of expert domains
            model: OpenAI model to use
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
            db_path: Path to SQLite database
        """
        self.documents_path = Path(documents_path)
        self.experts = experts or ["expert1", "expert2", "expert3"]
        self.model = model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.db_path = db_path
        
        # Initialize components
        self.orchestrator = None
        self.conversation_db = ConversationDB(db_path)
        self.conversation_manager = ConversationManager(self.conversation_db)
        self.indexer = DocumentIndexer(chunk_size, chunk_overlap)
        
        # Initialize orchestrator if index exists
        if Path("data/faiss_index").exists():
            self._initialize_orchestrator()
    
    def _initialize_orchestrator(self):
        """Initialize the orchestrator with existing index"""
        try:
            self.orchestrator = TiramisuOrchestrator()
            logger.info("Orchestrator initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {e}")
            self.orchestrator = None
    
    def build_index(self, force: bool = False) -> int:
        """
        Build FAISS index from documents
        
        Args:
            force: Force rebuild even if index exists
            
        Returns:
            Number of chunks indexed
        """
        index_path = Path("data/faiss_index")
        
        if index_path.exists() and not force:
            logger.info("Index already exists. Use force=True to rebuild.")
            return 0
        
        # Build index
        num_chunks = self.indexer.build_from_directory(
            self.documents_path,
            index_path
        )
        
        # Initialize orchestrator with new index
        self._initialize_orchestrator()
        
        return num_chunks
    
    def analyze(self, query: str, context: str = None) -> Dict[str, Any]:
        """
        Single-shot analysis without conversation memory
        
        Args:
            query: User query
            context: Optional additional context
            
        Returns:
            Dict with answer and sources
        """
        if not self.orchestrator:
            return {
                "answer": "System not initialized. Please build index first.",
                "sources": []
            }
        
        return self.orchestrator.analyze(query, context)
    
    def chat(self, message: str) -> Dict[str, Any]:
        """
        Simple chat without persistent memory
        
        Args:
            message: User message
            
        Returns:
            Dict with answer and sources
        """
        if not self.orchestrator:
            return {
                "answer": "System not initialized. Please build index first.",
                "sources": []
            }
        
        return self.orchestrator.chat(message)
    
    def start_conversation(self, title: str = None) -> str:
        """
        Start a new conversation with persistent memory
        
        Args:
            title: Optional conversation title
            
        Returns:
            Conversation ID
        """
        title = title or "New Conversation"
        conversation_id = self.conversation_manager.create_conversation(title)
        return conversation_id
    
    def continue_conversation(
        self, 
        conversation_id: str, 
        message: str
    ) -> str:
        """
        Continue an existing conversation
        
        Args:
            conversation_id: ID of the conversation
            message: User message
            
        Returns:
            Bot response
        """
        if not self.orchestrator:
            return "System not initialized. Please build index first."
        
        # Get conversation history
        history = self.conversation_manager.get_conversation_history(conversation_id)
        
        # Build context from history
        context = self._build_context_from_history(history)
        
        # Get response from orchestrator
        response = self.orchestrator.analyze(message, context)
        
        # Save to conversation
        self.conversation_manager.add_message(
            conversation_id,
            "user",
            message
        )
        self.conversation_manager.add_message(
            conversation_id,
            "assistant",
            response["answer"]
        )
        
        # Save sources if any
        if response.get("sources"):
            self.conversation_manager.save_rag_sources(
                conversation_id,
                response["sources"]
            )
        
        return response["answer"]
    
    def get_conversation_history(self, conversation_id: str) -> List[Dict]:
        """
        Get full conversation history
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            List of messages
        """
        return self.conversation_manager.get_conversation_history(conversation_id)
    
    def list_conversations(self) -> List[Dict]:
        """
        List all conversations
        
        Returns:
            List of conversation metadata
        """
        return self.conversation_manager.list_conversations()
    
    def _build_context_from_history(self, history: List[Dict]) -> str:
        """
        Build context string from conversation history
        
        Args:
            history: List of messages
            
        Returns:
            Context string
        """
        if not history:
            return ""
        
        context_parts = []
        for msg in history[-10:]:  # Last 10 messages for context
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            context_parts.append(f"{role}: {content}")
        
        return "\n".join(context_parts)
    
    def clear_memory(self):
        """Clear orchestrator's temporary memory"""
        if self.orchestrator:
            self.orchestrator.clear_memory()
    
    def run_server(self, host: str = "127.0.0.1", port: int = 8000):
        """
        Start the API server
        
        Args:
            host: Host to bind to
            port: Port to run on
        """
        import uvicorn
        uvicorn.run(
            "tiramisu.api.main:app",
            host=host,
            port=port,
            reload=True
        )
