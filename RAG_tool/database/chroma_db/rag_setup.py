"""
RAG Setup Module

This module contains the RAGSetup class which handles the setup and initialization
of the RAG (Retrieval-Augmented Generation) system.
"""
import os
import logging
from typing import List, Dict, Any, Optional

from .document_loader import DocumentLoader
from .embeddings import VectorStoreManager
from langchain_community.vectorstores import Chroma
from config import Config

logger = logging.getLogger(__name__)

class RAGSetup:
    """
    Handles the setup and initialization of the RAG system.
    """
    
    def __init__(self, persist_directory: str = None):
        """
        Initialize the RAG setup.
        
        Args:
            persist_directory: Directory to persist the ChromaDB. If None, uses Config.CHROMA_DB_DIR
        """
        self.persist_directory = os.path.abspath(persist_directory or Config.CHROMA_DB_DIR)
        self.document_loader = DocumentLoader()
        self.vectorstore_manager = VectorStoreManager()
        self.vectorstore = None
    
    def process_pdf(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Process a PDF file and split it into document chunks.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of document chunks with metadata
        """
        try:
            
            logger.info(f"Processing PDF: {pdf_path}")
            documents = self.document_loader.process_pdf(pdf_path)
            return documents
            
        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            raise
    
    def setup_vectorstore(self, documents: List[Dict[str, Any]] = None, pdf_path = Config.DOCUMENTS_DIR, 
                         force_recreate: bool = False) -> 'Chroma':
        """
        Set up the Chroma vector store with the provided documents or PDF.
        
        Args:
            documents: List of document chunks (optional)
            pdf_path: Path to PDF file (optional, if documents not provided)
            force_recreate: If True, recreate the vector store even if it exists
            
        Returns:
            Initialized Chroma vector store
        """
        try:
            
            if documents is None and pdf_path is None:
                raise ValueError("Either documents or pdf_path must be provided")
            
            if documents is None:
                documents = self.process_pdf(pdf_path)
            
            logger.info("Setting up Chroma vector store...")
            
            # Create or load the vector store
            self.vectorstore = self.vectorstore_manager.create_vectorstore(
                documents=documents,
                force_recreate=force_recreate
            )
            
            logger.info(f"Vector store initialized and persisted to {self.persist_directory}")
            return self.vectorstore
            
        except Exception as e:
            logger.error(f"Error setting up vector store: {str(e)}")
            raise
    
    def get_retriever(self, k: int = 4):
        """
        Get a retriever from the vector store.
        
        Args:
            k: Number of documents to retrieve
            
        Returns:
            A retriever object
        """
        if self.vectorstore is None:
            raise ValueError("Vector store not initialized. Call setup_vectorstore() first.")
            
        return self.vectorstore_manager.get_retriever(k=k)

    def load_existing_vectorstore(self) -> bool:
        
        """
        Load an existing vector store from the persistence directory.
        
        Returns:
            bool: True if the vector store was loaded successfully, False otherwise
        """
        try:
            logger.info(f"Attempting to load existing vector store from {self.persist_directory}")
            self.vectorstore = self.vectorstore_manager.load_vectorstore()
            
            if self.vectorstore is None:
                #logger.warning("No existing vector store found")
                self.vectorstore = self.setup_vectorstore()
                return True
                
            logger.info("Successfully loaded existing vector store")
            return True
            
        except Exception as e:
            logger.error(f"Error loading existing vector store: {str(e)}", exc_info=True)
            return False
