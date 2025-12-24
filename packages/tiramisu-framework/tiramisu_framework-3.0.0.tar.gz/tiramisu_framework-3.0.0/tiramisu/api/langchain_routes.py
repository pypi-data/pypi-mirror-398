from fastapi import APIRouter, HTTPException
from tiramisu.core.langchain_orchestrator_simple import TiramisuOrchestrator
from tiramisu.schemas import AnalysisRequest, AnalysisResponse
from typing import Dict, Any
import json

router = APIRouter(prefix="/v2", tags=["LangChain"])

orchestrator = TiramisuOrchestrator()

@router.post("/analyze")
async def analyze_with_langchain(request: AnalysisRequest) -> Dict[str, Any]:
    try:
        result = orchestrator.analyze(
            query=request.content,
            context=request.context
        )
        
        return {
            "summary": result["answer"],
            "sources": result["sources"],
            "type": request.type
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat")
async def chat_with_langchain(message: Dict[str, str]) -> Dict[str, Any]:
    try:
        result = orchestrator.chat(message["content"])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reset")
async def reset_conversation():
    orchestrator.clear_memory()
    return {"status": "conversation reset"}

@router.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0-langchain"}
