"""
Conversation Routes - Endpoints para conversas contínuas
"""
from fastapi import APIRouter, HTTPException
from typing import Optional
from datetime import datetime

from tiramisu.schemas import (
    ConversationStartRequest,
    ConversationStartResponse,
    ContinueConversationRequest,
    ContinueConversationResponse,
    ConversationHistoryResponse,
    ConversationMessage,
    ConversationListResponse,
    ConversationListItem
)
from tiramisu.core.analyzer import TiramisuAnalyzer

router = APIRouter(prefix="/conversation", tags=["Conversas"])

# Cache de analyzers por conversa
_analyzer_cache = {}


def get_analyzer(conversation_id: str = None) -> TiramisuAnalyzer:
    """Retorna analyzer para conversa específica"""
    if conversation_id and conversation_id in _analyzer_cache:
        return _analyzer_cache[conversation_id]
    
    analyzer = TiramisuAnalyzer(conversation_id=conversation_id)
    
    if conversation_id:
        _analyzer_cache[conversation_id] = analyzer
    
    return analyzer


@router.post("/start", response_model=ConversationStartResponse)
async def start_conversation(request: ConversationStartRequest):
    """
    Inicia uma nova conversa
    
    Returns:
        ConversationStartResponse: ID e detalhes da conversa criada
    """
    try:
        analyzer = get_analyzer()
        conversation_id = analyzer.start_conversation(request.title)
        
        # Armazenar analyzer no cache
        _analyzer_cache[conversation_id] = analyzer
        
        return ConversationStartResponse(
            conversation_id=conversation_id,
            title=request.title or "Nova Conversa",
            created_at=datetime.now().isoformat()
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{conversation_id}/continue", response_model=ContinueConversationResponse)
async def continue_conversation(
    conversation_id: str,
    request: ContinueConversationRequest
):
    """
    Continua uma conversa existente
    
    Args:
        conversation_id: ID da conversa
        request: Mensagem e modo
    
    Returns:
        ContinueConversationResponse: Resposta da Tiramisu
    """
    try:
        # Validar modo
        if request.mode not in ["consult", "plan"]:
            raise HTTPException(
                status_code=400, 
                detail="Modo inválido. Use 'consult' ou 'plan'"
            )
        
        # Obter analyzer da conversa
        analyzer = get_analyzer(conversation_id)
        
        # Continuar conversa
        response = analyzer.continue_conversation(
            user_message=request.message,
            mode=request.mode
        )
        
        return ContinueConversationResponse(
            message_id="",  # TODO: retornar ID real
            response=response,
            conversation_id=conversation_id
        )
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{conversation_id}/history", response_model=ConversationHistoryResponse)
async def get_conversation_history(conversation_id: str):
    """
    Retorna histórico completo de uma conversa
    
    Args:
        conversation_id: ID da conversa
    
    Returns:
        ConversationHistoryResponse: Histórico completo
    """
    try:
        analyzer = get_analyzer(conversation_id)
        
        # Obter histórico do banco
        history = analyzer.conversation_manager.db.get_conversation_history(conversation_id)
        
        if not history:
            raise HTTPException(status_code=404, detail="Conversa não encontrada")
        
        # Obter info da conversa
        conn = analyzer.conversation_manager.db.db_path
        import sqlite3
        db = sqlite3.connect(conn)
        cursor = db.cursor()
        cursor.execute(
            "SELECT title FROM conversations WHERE id = ?",
            (conversation_id,)
        )
        result = cursor.fetchone()
        db.close()
        
        title = result[0] if result else "Sem título"
        
        # Converter para schema
        messages = [
            ConversationMessage(
                id=msg['id'],
                role=msg['role'],
                content=msg['content'],
                mode=msg['mode'],
                created_at=msg['created_at']
            )
            for msg in history
        ]
        
        return ConversationHistoryResponse(
            conversation_id=conversation_id,
            title=title,
            messages=messages,
            total_messages=len(messages)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", response_model=ConversationListResponse)
async def list_conversations(limit: int = 20):
    """
    Lista conversas recentes
    
    Args:
        limit: Número máximo de conversas (padrão: 20)
    
    Returns:
        ConversationListResponse: Lista de conversas
    """
    try:
        # Criar analyzer temporário para acessar DB
        analyzer = TiramisuAnalyzer()
        
        conversations = analyzer.conversation_manager.list_conversations(limit)
        
        items = [
            ConversationListItem(
                id=conv['id'],
                title=conv['title'],
                created_at=conv['created_at'],
                updated_at=conv['updated_at']
            )
            for conv in conversations
        ]
        
        return ConversationListResponse(
            conversations=items,
            total=len(items)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """
    Deleta uma conversa (TODO: implementar)
    
    Args:
        conversation_id: ID da conversa
    """
    # TODO: Implementar deleção no banco
    raise HTTPException(status_code=501, detail="Não implementado ainda")
