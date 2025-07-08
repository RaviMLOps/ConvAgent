# rag_service/app/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import logging
import json
import requests
import chromadb
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import RAG components with error handling
try:
    from langchain.chains import RetrievalQA
    from langchain.prompts import PromptTemplate
    from langchain_community.chat_models import ChatOpenAI
    from langchain_community.vectorstores import Chroma
    from langchain_community.embeddings import HuggingFaceEmbeddings
    print("LangChain imports successful!")
except ImportError as e:
    logger.error(f"Failed to import LangChain components: {str(e)}")
    raise

try:
    from config import Config
    print("Config import successful!")
except ImportError as e:
    logger.error(f"Failed to import Config: {str(e)}")
    raise

# Import RAG pipeline
try:
    from RAG_tool.rag_chain import RAGPipeline
    print("RAGPipeline imports successful!")
except ImportError as e:
    logger.error(f"Failed to import RAGPipeline: {str(e)}")
    raise

app = FastAPI(
    title="RAG Service API",
    description="API for RAG (Retrieval-Augmented Generation) service",
    version="1.0.0"
)

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint that provides information about the API."""
    return {
        "message": "Welcome to the RAG Service API",
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_schema": "/openapi.json"
        },
        "endpoints": {
            "health": "/health",
            "query": "/query"
        }
    }


class QueryRequest(BaseModel):
    query: str

class HealthCheck(BaseModel):
    status: str

# Initialize RAG components
try:
    logger.info("Starting RAG service initialization...")
    
    # Check environment variables
    logger.info("Checking environment variables...")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    
    # Initialize ChromaDB HTTP client with direct API endpoint
    logger.info(f"Initializing ChromaDB connection to {Config.CHROMA_SERVER_HOST}")
    
    try:
        # Create a custom HTTP client that works with the server's API
        logger.debug("Creating custom HTTP client for ChromaDB...")
        
        # Initialize embeddings first
        logger.info("Initializing HuggingFace embeddings...")
        embeddings = HuggingFaceEmbeddings(
            model_name=Config.EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True}
        )
        
        # Create Chroma vector store with direct API endpoint
        logger.debug("Creating Chroma vector store with direct API...")
        vectorstore = Chroma(
            collection_name=Config.CHROMA_COLLECTION_NAME,
            embedding_function=embeddings,
            client_settings={
                "chroma_api_impl": "rest",
                "chroma_server_host": "18.200.248.198",
                "chroma_server_http_port": "8000",
                "chroma_server_ssl_enabled": False,
                "chroma_server_headers": {"Content-Type": "application/json"}
            }
        )
        
        # Test the vector store connection
        try:
            # Try to get collection info to test the connection
            collection_info = vectorstore._collection.get()
            doc_count = len(collection_info.get('ids', []))
            logger.info(f"Successfully connected to ChromaDB. Collection contains {doc_count} documents.")
            
            # If collection is empty, log a warning
            if doc_count == 0:
                logger.warning("Collection is empty. Consider adding documents to the vector store.")
                
            # Store vectorstore in app state
            app.vectorstore = vectorstore
            logger.info("Vector store initialized and stored in app state.")
                
        except Exception as e:
            logger.error(f"Failed to connect to ChromaDB collection: {str(e)}")
            logger.error("Please verify that the ChromaDB server is running and accessible at the configured address.")
            logger.error(f"Server URL: {Config.CHROMA_SERVER_HOST}")
            logger.error("You can test the server connection manually with: curl http://18.200.248.198:8000/chroma/status")
            raise
            
    except Exception as e:
        logger.error(f"Fatal error initializing ChromaDB client: {str(e)}")
        raise
    app.vectorstore = vectorstore
    
    # Initialize RAG pipeline
    logger.info("Initializing RAG pipeline...")
    rag_pipeline = RAGPipeline()
    app.rag_pipeline = rag_pipeline
    
    logger.info(f"RAG service initialized successfully with vector store at: {Config.CHROMA_DB_DIR}")
    
except Exception as e:
    logger.error(f"Failed to initialize RAG service: {str(e)}", exc_info=True)
    raise

@app.get("/health", response_model=HealthCheck)
async def health_check():
    return {"status": "ok"}

@app.post("/query")
async def query(request: QueryRequest):
    """Query the RAG system with a question."""
    try:
        if not hasattr(app, 'vectorstore'):
            raise HTTPException(status_code=500, detail="RAG system not initialized")
        
        # Configure retriever and RAG chain
        retriever = vectorstore.as_retriever(
            search_kwargs={"k": 3}  # Return top 3 most relevant documents
        )

        print("retriever_results:", retriever)
        
        # Create the RAG chain
        rag_chain = (
            {"context": retriever | rag_pipeline.format_docs, 
             "question": RunnablePassthrough()}
            | rag_pipeline.prompt
            | rag_pipeline.llm
            | StrOutputParser()
        )
        
        # Get the response from the RAG chain
        response = rag_chain.invoke(request.query)
        
        # Get the source documents for reference
        docs = retriever.get_relevant_documents(request.query)
        
        # Format the results
        results = {
            "answer": response,
            "sources": [{
                "content": doc.page_content,
                "metadata": doc.metadata
            } for doc in docs]
        }

        print("results:", results)
        
        return results
        
    except Exception as e:
        logger.error(f"Error in RAG query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting RAG service on port 8001...")
    logger.info(f"Using vector store from: {Config.CHROMA_DB_DIR}")
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )