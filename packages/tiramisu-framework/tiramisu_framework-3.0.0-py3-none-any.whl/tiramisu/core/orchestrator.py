from langchain.chains import RetrievalQA
from langchain.memory import ConversationBufferMemory
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain_core.documents import Document
from tiramisu.config import settings
from typing import Dict, Any

def _fix_pydantic_compatibility(self, state):
    if "__fields_set__" not in state:
        state["__fields_set__"] = set()
    if "__pydantic_private__" not in state:
        state["__pydantic_private__"] = None
    for key, value in state.items():
        if key not in ("__fields_set__", "__pydantic_private__"):
            object.__setattr__(self, key, value)

Document.__setstate__ = _fix_pydantic_compatibility

class TiramisuOrchestrator:
    def __init__(self):
        # Embeddings sem parâmetros problemáticos
        self.embeddings = OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        self.llm = ChatOpenAI(
            model="gpt-4o",  # Usar 3.5 para economizar
            temperature=0.7,
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        try:
            self.vector_store = FAISS.load_local(
                "data/faiss_index", 
                self.embeddings,
                allow_dangerous_deserialization=True
            )
        except:
            print("⚠️ Vector store não encontrado")
            self.vector_store = None
        
        if self.vector_store:
            self.retriever = self.vector_store.as_retriever(
                search_kwargs={"k": 5}
            )
            self.qa_chain = self._create_qa_chain()
        else:
            self.retriever = None
            self.qa_chain = None
        
        self.memory = ConversationBufferMemory()
    
    def _create_qa_chain(self):
        prompt = PromptTemplate(
            template="""Você é a Tiramisu, consultora de marketing que combina conhecimento de Strategy Expert, Digital Expert e Tech Expert.
            
            Contexto: {context}
            Pergunta: {question}
            
            Responda de forma estruturada e profissional.""",
            input_variables=["context", "question"]
        )
        
        return RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": prompt}
        )
    
    def analyze(self, query: str, context: str = None) -> Dict[str, Any]:
        if not self.qa_chain:
            return {"answer": "Sistema não inicializado", "sources": []}
        
        full_query = f"{query}\nContexto: {context}" if context else query
        result = self.qa_chain({"query": full_query})
        return {
            "answer": result["result"],
            "sources": [doc.metadata.get("source", "") for doc in result.get("source_documents", [])]
        }
    
    def chat(self, message: str) -> Dict[str, Any]:
        if not self.qa_chain:
            return {"answer": "Sistema não inicializado", "sources": []}
        
        result = self.qa_chain({"query": message})
        return {
            "answer": result["result"],
            "sources": [doc.metadata.get("source", "") for doc in result.get("source_documents", [])]
        }
    
    def clear_memory(self):
        self.memory.clear()
