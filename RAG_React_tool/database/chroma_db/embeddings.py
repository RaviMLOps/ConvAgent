import os
import logging
from typing import List, Optional, Dict, Any
import chromadb
from chromadb.config import Settings
from chromadb.api.types import Documents, EmbeddingFunction
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.schema import Document
from config import Config

logger = logging.getLogger(__name__)

class ChromaCompatibleEmbeddings:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        logger.info(f"Initializing embedding model: {model_name}")
        
        try:
            # Force the model name to ensure it's what we expect
            if "onnx" in model_name.lower():
                logger.warning(f"ONNX model detected: {model_name}. Forcing to standard model.")
                model_name = "sentence-transformers/all-MiniLM-L6-v2"
                
            self.embedding_model = HuggingFaceEmbeddings(
                model_name=model_name,
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
            logger.info(f"Successfully initialized model: {model_name}")
            logger.info(f"Model type: {type(self.embedding_model).__name__}")
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {e}")
            raise

    def __call__(self, input: List[str]) -> List[List[float]]:
        """Make the class callable for ChromaDB compatibility."""
        return self.embed_documents(input)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of texts using the underlying embedding model."""
        try:
            if hasattr(self.embedding_model, 'embed_documents'):
                return self.embedding_model.embed_documents(texts)
            elif hasattr(self.embedding_model, 'encode'):
                return [self.embedding_model.encode(text) for text in texts]
            else:
                return [self.embed_query(text) for text in texts]
        except Exception as e:
            logger.error(f"Error in embed_documents: {str(e)}", exc_info=True)
            raise

    def embed_query(self, text: str) -> List[float]:
        """Embed a single query text using the underlying embedding model."""
        try:
            if hasattr(self.embedding_model, 'embed_query'):
                return self.embedding_model.embed_query(text)
            elif hasattr(self.embedding_model, 'encode'):
                return self.embedding_model.encode(text).tolist()
            else:
                return self.embed_documents([text])[0]
        except Exception as e:
            logger.error(f"Error in embed_query: {str(e)}", exc_info=True)
            raise
    
class VectorStoreManager:
    def __init__(self, collection_name: str = "documents"):
        """Initialize the VectorStoreManager with HuggingFace embeddings."""
        try:
            self.collection_name = collection_name
            logger.info(f"Initializing VectorStoreManager with collection: {collection_name}")
            
            # Initialize the embedding model
            logger.info("Loading embedding model...")
            self.embedding_function = ChromaCompatibleEmbeddings(Config.EMBEDDING_MODEL)
            
            # Ensure persistence directory exists
            os.makedirs(Config.PERSIST_DIRECTORY, exist_ok=True)
            logger.info(f"Vector store will be persisted to: {Config.PERSIST_DIRECTORY}")
            
            # Initialize Chroma client
            self.client = chromadb.PersistentClient(
                path=Config.PERSIST_DIRECTORY,
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Test the embedding function
            test_embeddings = self.embedding_function(["test document"])
            logger.info(f"Test embedding successful. Vector size: {len(test_embeddings[0])}")
            
        except Exception as e:
            logger.error(f"Failed to initialize VectorStoreManager: {str(e)}", exc_info=True)
            raise

    def create_vectorstore(self, documents: List[Document], force_recreate: bool = False) -> Optional[Chroma]:
        """Create or load a Chroma vector store from documents."""
        if not documents:
            raise ValueError("No documents provided for vector store creation")
            
        try:
            # Log document information
            logger.info(f"Processing {len(documents)} documents for vector store")
            if documents:
                logger.info(f"First document metadata: {documents[0].metadata}")
                logger.info(f"First document content preview: {documents[0].page_content[:200]}...")
            
            # Check if we should recreate the vector store
            collection_exists = any(
                collection.name == self.collection_name 
                for collection in self.client.list_collections()
            )
            
            if force_recreate and collection_exists:
                logger.info(f"Deleting existing collection: {self.collection_name}")
                self.client.delete_collection(self.collection_name)
                collection_exists = False
            
            if not collection_exists:
                logger.info("Creating new Chroma vector store...")
                try:
                    # Create LangChain Chroma instance
                    self.vectorstore = Chroma(
                        client=self.client,
                        collection_name=self.collection_name,
                        embedding_function=self.embedding_function,
                        persist_directory=Config.PERSIST_DIRECTORY
                    )
                    
                    # Add documents
                    logger.info(f"Adding {len(documents)} documents to vector store...")
                    texts = [doc.page_content for doc in documents]
                    metadatas = [doc.metadata for doc in documents]
                    self.vectorstore.add_texts(texts=texts, metadatas=metadatas)
                    logger.info("Successfully created new vector store")
                    
                except Exception as e:
                    logger.error(f"Error creating vector store: {str(e)}", exc_info=True)
                    raise
            else:
                logger.info("Loading existing vector store...")
                try:
                    self.vectorstore = Chroma(
                        client=self.client,
                        collection_name=self.collection_name,
                        embedding_function=self.embedding_function,
                        persist_directory=Config.PERSIST_DIRECTORY
                    )
                    logger.info(f"Loaded existing vector store with {self.vectorstore._collection.count()} documents")
                except Exception as e:
                    logger.error(f"Error loading existing vector store: {str(e)}", exc_info=True)
                    raise
                    
            return self.vectorstore
            
        except Exception as e:
            logger.error(f"Error in create_vectorstore: {str(e)}", exc_info=True)
            return None

    def get_retriever(self, k: int = 4):
        """Get a retriever from the current vector store."""
        if not hasattr(self, 'vectorstore') or self.vectorstore is None:
            raise ValueError(
                "Vector store not initialized. Call create_vectorstore() first."
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
    
    def load_vectorstore(self) -> Optional[Chroma]:
        """Load an existing Chroma vector store if it exists."""
        try:
            # Check if collection exists
            collection_exists = any(
                collection.name == self.collection_name 
                for collection in self.client.list_collections()
            )
        
            if not collection_exists:
                logger.warning(f"Collection '{self.collection_name}' does not exist")
                return None
            
            logger.info(f"Loading existing vector store from {Config.PERSIST_DIRECTORY}")
            self.vectorstore = Chroma(
                client=self.client,
                collection_name=self.collection_name,
                embedding_function=self.embedding_function,
                persist_directory=Config.PERSIST_DIRECTORY
            )
        
            # Verify the collection has documents
            count = self.vectorstore._collection.count()
            logger.info(f"Successfully loaded vector store with {count} documents")
            return self.vectorstore
        
        except Exception as e:
            logger.error(f"Error loading vector store: {str(e)}", exc_info=True)
            return None