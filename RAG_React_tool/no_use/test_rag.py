# """
# Test script to verify RAG setup and ChromaDB vector store.
# """
# import os
# import sys
# import logging
# from pathlib import Path

# # Add project root to Python path
# project_root = str(Path(__file__).parent.absolute())
# if project_root not in sys.path:
#     sys.path.insert(0, project_root)

# # Set up logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     handlers=[
#         logging.StreamHandler(),
#         logging.FileHandler('test_rag.log')
#     ]
# )
# logger = logging.getLogger(__name__)

# def test_chromadb_setup():
#     """Test if ChromaDB is properly set up."""
#     try:
#         logger.info("Testing ChromaDB setup...")
#         from database.chroma_db.rag_setup import RAGSetup
        
#         logger.info("Initializing RAGSetup...")
#         rag_setup = RAGSetup()
        
#         logger.info("Loading existing vector store...")
#         if rag_setup.load_existing_vectorstore():
#             logger.info("Successfully loaded existing vector store!")
#             logger.info(f"Vector store type: {type(rag_setup.vectorstore)}")
            
#             # Try a simple similarity search
#             logger.info("Testing similarity search...")
#             results = rag_setup.vectorstore.similarity_search("test", k=1)
#             logger.info(f"Search results: {len(results)} documents found")
#             if results:
#                 logger.info(f"First document: {results[0].page_content[:200]}...")
#             return True
#         else:
#             logger.error("Failed to load vector store")
#             return False
            
#     except Exception as e:
#         logger.exception("Error testing ChromaDB setup:")
#         return False

# def main():
#     logger.info("Starting RAG setup test...")
    
#     # Print environment info
#     logger.info(f"Python version: {sys.version}")
#     logger.info(f"Current working directory: {os.getcwd()}")
    
#     # Test ChromaDB setup
#     if test_chromadb_setup():
#         logger.info("ChromaDB setup test completed successfully!")
#         return 0
#     else:
#         logger.error("ChromaDB setup test failed!")
#         return 1

# if __name__ == "__main__":
#     sys.exit(main())
