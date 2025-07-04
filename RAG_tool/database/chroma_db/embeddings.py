import os
import logging
from typing import List, Optional
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.schema import Document
from config import Config

# Set up logging
logger = logging.getLogger(__name__)

class VectorStoreManager:
    def __init__(self):
        """Initialize the VectorStoreManager with HuggingFace embeddings."""
        try:
            logger.info(f"Initializing embedding model: {Config.EMBEDDING_MODEL}")
            self.embedding_function = HuggingFaceEmbeddings(
                model_name=Config.EMBEDDING_MODEL
            )
            self.vectorstore = None
            # Ensure persistence directory exists
            os.makedirs(Config.PERSIST_DIRECTORY, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to initialize VectorStoreManager: {str(e)}")
            raise
    
    def create_vectorstore(self, documents: List[Document], force_recreate: bool = False) -> Optional[Chroma]:
        """
        Create or load a Chroma vector store from documents.
        
        Args:
            documents: List of Document objects to be vectorized
            force_recreate: If True, recreate the vector store even if it exists
            
        Returns:
            Chroma: The created or loaded vector store, or None if an error occurs
            
        Raises:
            ValueError: If no documents are provided
        """
        if not documents:
            raise ValueError("No documents provided for vector store creation")
            
        try:
            # Check if we should recreate the vector store
            vectorstore_exists = os.path.exists(os.path.join(Config.PERSIST_DIRECTORY, 'chroma-embeddings.parquet'))
            
            if force_recreate or not vectorstore_exists:
                if force_recreate and vectorstore_exists:
                    logger.info("Forcing recreation of vector store...")
                elif not vectorstore_exists:
                    logger.info("No existing vector store found, creating a new one...")
                    
                self.vectorstore = Chroma.from_documents(
                    documents=documents,
                    embedding=self.embedding_function,
                    persist_directory=Config.PERSIST_DIRECTORY
                )
                logger.info(f"Created new vector store with {len(documents)} documents")
                
                # Explicitly persist the vector store
                self.vectorstore.persist()
                logger.info(f"Vector store persisted to {Config.PERSIST_DIRECTORY}")
            else:
                logger.info("Loading existing vector store...")
                self.vectorstore = Chroma(
                    persist_directory=Config.PERSIST_DIRECTORY,
                    embedding_function=self.embedding_function
                )
                logger.info(f"Vector store loaded from {Config.PERSIST_DIRECTORY}")
                
            return self.vectorstore
            
        except Exception as e:
            logger.error(f"Error creating/loading vector store: {str(e)}", exc_info=True)
            return None
    
    def load_vectorstore(self) -> Optional[Chroma]:
        """
        Load an existing Chroma vector store from the persistence directory.
        
        Returns:
            Chroma: The loaded vector store, or None if loading fails
        """
        try:
            # Check if any ChromaDB files exist in the directory
            if not os.path.exists(Config.PERSIST_DIRECTORY) or not any(
                fname.endswith(('.parquet', '.bin', '.sqlite3')) 
                for fname in os.listdir(Config.PERSIST_DIRECTORY)
            ):
                logger.warning(f"No ChromaDB files found in {Config.PERSIST_DIRECTORY}")
                return None
                
            logger.info(f"Loading existing vector store from {Config.PERSIST_DIRECTORY}")
            self.vectorstore = Chroma(
                persist_directory=Config.PERSIST_DIRECTORY,
                embedding_function=self.embedding_function
            )
            logger.info("Vector store loaded successfully")
            return self.vectorstore
            
        except Exception as e:
            logger.error(f"Error loading vector store: {str(e)}", exc_info=True)
            return None
            
    def get_retriever(self, k: int = 4):
        """
        Get a retriever from the current vector store.
        
        Args:
            k: Number of documents to retrieve (default: 4)
            
        Returns:
            A retriever object
            
        Raises:
            ValueError: If vector store is not initialized
        """
        if self.vectorstore is None:
            # Try to load the vector store if it exists
            self.vectorstore = self.load_vectorstore()
            if self.vectorstore is None:
                raise ValueError(
                    "Vector store not initialized and could not be loaded. "
                    "Call create_vectorstore() first with valid documents."
                )
            
        try:
            retriever = self.vectorstore.as_retriever(
                search_kwargs={"k": k}
            )
            logger.info(f"Retriever created with k={k}")
            return retriever
            
        except Exception as e:
            logger.error(f"Error creating retriever: {str(e)}", exc_info=True)
            raise
