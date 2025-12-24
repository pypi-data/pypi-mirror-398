"""
Schemas Pydantic para a API Tiramisu
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from enum import Enum


class AnalysisType(str, Enum):
    """Tipos de análise disponíveis"""
    POST_SOCIAL = "post_social"
    EMAIL_MARKETING = "email_marketing"
    LANDING_PAGE = "landing_page"
    AD_COPY = "ad_copy"
    STRATEGY = "strategy"
    PITCH = "pitch"
    VIDEO_SCRIPT = "video_script"
    OTHER = "other"


class AnalysisRequest(BaseModel):
    """Request para análise"""
    type: AnalysisType = Field(..., description="Tipo de análise")
    content: str = Field(..., description="Conteúdo a ser analisado")
    context: Optional[str] = Field(None, description="Contexto adicional (objetivo, público-alvo, etc)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "post_social",
                "content": "Acabamos de lançar o GaiaLex, um sistema RAG revolucionário...",
                "context": "Objetivo: gerar leads de desenvolvedores. Público: CTOs e Tech Leads"
            }
        }


class ThreeTreesAnalysis(BaseModel):
    """Análise das 3 Árvores"""
    roots: str = Field(..., description="RAÍZES: Diagnóstico profundo")
    trunk: str = Field(..., description="TRONCO: Execução atual")
    branches: str = Field(..., description="GALHOS: Melhorias e alternativas")


class TriadInsights(BaseModel):
    """Insights dos 3 autores"""
    strategy_expert: str = Field(..., description="Visão estratégica")
    digital_expert: str = Field(..., description="Visão de execução digital")
    tech_expert: str = Field(..., description="Visão tecnológica")


class Proposal(BaseModel):
    """Proposta de solução"""
    improved_version: Optional[str] = Field(None, description="Versão melhorada do conteúdo")
    action_plan: List[str] = Field(..., description="Plano de ação em passos")
    key_recommendations: List[str] = Field(..., description="Recomendações-chave")
    expected_results: str = Field(..., description="Resultados esperados")


class AnalysisResponse(BaseModel):
    """Response completa da análise"""
    summary: str = Field(..., description="Resumo executivo")
    three_trees: ThreeTreesAnalysis
    triad_insights: TriadInsights
    proposal: Proposal
    rag_sources: List[str] = Field(..., description="Fontes consultadas no RAG")
    
    class Config:
        json_schema_extra = {
            "example": {
                "summary": "Análise completa do post sobre GaiaLex...",
                "three_trees": {
                    "roots": "O post foi criado com objetivo de...",
                    "trunk": "Atualmente o conteúdo apresenta...",
                    "branches": "Principais oportunidades de melhoria..."
                },
                "triad_insights": {
                    "strategy_expert": "Do ponto de vista estratégico...",
                    "digital_expert": "Na execução prática...",
                    "tech_expert": "Considerando a tecnologia..."
                },
                "proposal": {
                    "improved_version": "Versão reescrita do post...",
                    "action_plan": ["Passo 1", "Passo 2"],
                    "key_recommendations": ["Rec 1", "Rec 2"],
                    "expected_results": "Com essas mudanças..."
                },
                "rag_sources": ["Strategic Marketing Guide", "Digital Execution Guide"]
            }
        }


class AvailableTypesResponse(BaseModel):
    """Lista de tipos disponíveis"""
    types: List[Dict[str, str]]
    
    class Config:
        json_schema_extra = {
            "example": {
                "types": [
                    {"id": "post_social", "name": "Post Redes Sociais", "description": "..."},
                    {"id": "email_marketing", "name": "Email Marketing", "description": "..."}
                ]
            }
        }


# ============================================================
# SCHEMAS PARA CONVERSAS CONTÍNUAS
# ============================================================

class ConversationStartRequest(BaseModel):
    """Request para iniciar conversa"""
    message: str = Field(..., description="Mensagem inicial do usuário")
    title: Optional[str] = Field(None, description="Título da conversa")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Estratégia Marketing SaaS"
            }
        }


class ConversationStartResponse(BaseModel):
    """Response ao iniciar conversa"""
    conversation_id: str = Field(..., description="ID da conversa criada")
    title: str = Field(..., description="Título da conversa")
    created_at: str = Field(..., description="Data de criação")


class ContinueConversationRequest(BaseModel):
    """Request para continuar conversa"""
    message: str = Field(..., description="Mensagem do usuário")
    mode: str = Field("consult", description="Modo: 'consult' ou 'plan'")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Como aumentar vendas do meu SaaS?",
                "mode": "consult"
            }
        }


class ContinueConversationResponse(BaseModel):
    """Response ao continuar conversa"""
    message_id: str = Field(..., description="ID da mensagem")
    response: str = Field(..., description="Resposta da Tiramisu formatada")
    conversation_id: str = Field(..., description="ID da conversa")


class ConversationMessage(BaseModel):
    """Mensagem individual"""
    id: str
    role: str
    content: str
    mode: Optional[str] = None
    created_at: str


class ConversationHistoryResponse(BaseModel):
    """Histórico completo da conversa"""
    conversation_id: str
    title: str
    messages: List[ConversationMessage]
    total_messages: int


class ConversationListItem(BaseModel):
    """Item da lista de conversas"""
    id: str
    title: str
    created_at: str
    updated_at: str


class ConversationListResponse(BaseModel):
    """Lista de conversas"""
    conversations: List[ConversationListItem]
    total: int
