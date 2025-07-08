"""
PDF to VectorDB Processor

This script processes PDF files from the data directory and creates a ChromaDB vector store.
It uses DocumentLoader for PDF processing and VectorStoreManager for vector database operations.
"""
import os
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any

import sys
import os

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.append(project_root)

# Import local modules
from database.chroma_db.document_loader import DocumentLoader
from database.chroma_db.embeddings import VectorStoreManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_pdfs(directory: str) -> List[Dict[str, Any]]:
    """
    Process all PDF files in the given directory using DocumentLoader.
    
    Args:
        directory: Path to directory containing PDF files
        
    Returns:
        List of processed documents with text chunks and metadata
    """
    loader = DocumentLoader()
    all_documents = []
    pdf_dir = Path(directory)
    
    logger.info(f"Looking for PDFs in: {pdf_dir.absolute()}")
    
    if not pdf_dir.exists():
        logger.error(f"Directory not found: {pdf_dir.absolute()}")
        return []
    
    pdf_files = list(pdf_dir.glob("*.pdf"))
    if not pdf_files:
        logger.warning(f"No PDF files found in {pdf_dir.absolute()}")
        return []
    
    logger.info(f"Found {len(pdf_files)} PDF file(s) to process...")
    
    for pdf_file in pdf_files:
        try:
            logger.info(f"Processing: {pdf_file.name}")
            # Load and process the PDF
            documents = loader.process_pdf(str(pdf_file.absolute()))
            if documents:
                all_documents.extend(documents)
                logger.info(f"  - Extracted {len(documents)} chunks")
                logger.debug(f"First chunk preview: {documents[0].page_content[:100]}...")
        except Exception as e:
            logger.error(f"Error processing {pdf_file.name}: {str(e)}")
            continue
    
    logger.info(f"Total chunks processed: {len(all_documents)}")
    return all_documents

def main():
    """Main function to process PDFs and create/update a vector store."""
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Process PDFs and create a ChromaDB vector store")
    parser.add_argument(
        "--data-dir",
        type=str,
        default=os.path.join(os.path.dirname(__file__), "data"),
        help="Directory containing PDF files (default: ./data)"
    )
    parser.add_argument(
        "--persist-dir",
        type=str,
        default=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "chroma_db", "data"),
        help="Directory to persist the vector store (default: ../chroma_db/data)"
    )
    parser.add_argument(
        "--collection",
        type=str,
        default="pdf_documents",
        help="Name for the collection in ChromaDB (default: pdf_documents)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force recreation of the vector store (default: False)"
    )
  
    args = parser.parse_args()
    
    # Set logging level
    #logging.basicConfig(level=logging.INFO)
    
    logger.info("\n=== PDF to VectorDB Processor ===")
    logger.info(f"Data directory: {os.path.abspath(args.data_dir)}")
    logger.info(f"Persist directory: {os.path.abspath(args.persist_dir)}")
    logger.info(f"Collection name: {args.collection}")
    logger.info(f"Force recreation: {args.force}")
    
    # Ensure persist directory exists
    os.makedirs(args.persist_dir, exist_ok=True)
    
    try:
        # Process PDFs
        logger.info("\n=== Processing PDFs ===")
        documents = process_pdfs(args.data_dir)
        
        if not documents:
            logger.error("No documents were processed. Exiting.")
            return 1
            
        logger.info(f"\n=== Creating Vector Store ===")
        logger.info(f"Number of document chunks: {len(documents)}")
        
        # Initialize vector store manager with custom persist directory
        from config import Config
        
        # Override the persist directory in Config
        Config.PERSIST_DIRECTORY = args.persist_dir
        
        logger.info(f"Initializing VectorStoreManager with persist directory: {Config.PERSIST_DIRECTORY}")
        vectorstore_manager = VectorStoreManager(collection_name="pdf_documents_new")
        
        # Create or update the vector store
        logger.info("Creating/Updating vector store...")
        vectorstore = vectorstore_manager.create_vectorstore(
            documents=documents,
            force_recreate=args.force
        )
        
        # Explicitly persist the vector store
        if vectorstore is not None:
            logger.info(f"Persisting vector store to: {Config.PERSIST_DIRECTORY}")
            vectorstore.persist()
            logger.info("Vector store persisted successfully")
        
        if vectorstore is None:
            logger.error("Failed to create or load vector store")
            return 1
            
        logger.info("\n=== Vector Store Ready ===")
        logger.info(f"Total documents: {len(documents)}")
            
        return 0
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    main()
