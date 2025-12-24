from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from tiramisu.api.routes import router
from tiramisu.api.conversation_routes import router as conversation_router
from tiramisu.api.langchain_routes import router as langchain_router

app = FastAPI(
    title="🍰 Tiramisu API",
    description="API da Consultora de Marketing & Vendas - Multi-Expert Framework",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api", tags=["Tiramisu"])
app.include_router(conversation_router, prefix="/api")
app.include_router(langchain_router, prefix="/api")

@app.get("/")
async def root():
    return {
        "message": "🍰 Tiramisu API - Consultora de Marketing & Vendas",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Chain-of-Thought routes
from tiramisu.api.cot_routes import router as cot_router
app.include_router(cot_router, prefix="/api")
