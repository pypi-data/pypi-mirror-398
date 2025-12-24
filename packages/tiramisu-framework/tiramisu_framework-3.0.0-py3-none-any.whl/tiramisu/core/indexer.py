"""
Document Indexer for FAISS
Copyright (c) 2025 Jony Wolff. All rights reserved.
"""
from pathlib import Path
from typing import List
import logging
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader, PDFPlumberLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
import os

logger = logging.getLogger(__name__)

class DocumentIndexer:
    """Handles document loading and FAISS index creation"""
    
    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 150):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
    
    def build_from_directory(self, docs_path: Path, index_path: Path) -> int:
        """
        Build FAISS index from documents directory
        
        Returns:
            Number of chunks created
        """
        # Load documents
        documents = self._load_documents(docs_path)
        
        if not documents:
            logger.warning("No documents found to index")
            return 0
        
        # Split into chunks
        chunks = self.text_splitter.split_documents(documents)
        logger.info(f"Created {len(chunks)} chunks from {len(documents)} documents")
        
        # Create embeddings
        embeddings = OpenAIEmbeddings()
        
        # Create FAISS index
        index_path.mkdir(parents=True, exist_ok=True)
        vector_store = FAISS.from_documents(chunks, embeddings)
        
        # Save index
        vector_store.save_local(str(index_path))
        logger.info(f"Index saved to {index_path}")
        
        return len(chunks)
    
    def _load_documents(self, docs_path: Path) -> List:
        """Load all documents from directory"""
        documents = []
        
        # Load text files
        for file in docs_path.glob("*.txt"):
            loader = TextLoader(str(file))
            documents.extend(loader.load())
            logger.info(f"Loaded: {file.name}")
        
        # Load PDFs if available
        for file in docs_path.glob("*.pdf"):
            loader = PDFPlumberLoader(str(file))
            documents.extend(loader.load())
            logger.info(f"Loaded: {file.name}")
        
        return documents

def build_faiss_index(docs_path: Path, index_path: Path) -> int:
    """Convenience function for CLI"""
    indexer = DocumentIndexer()
    return indexer.build_from_directory(docs_path, index_path)
