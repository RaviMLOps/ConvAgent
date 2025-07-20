import os, glob
import logging
from typing import List, Optional
from PyPDF2 import PdfReader
from PyPDF2.errors import PdfReadError
from langchain.schema import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import Config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentLoader:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP
        )
    
    def load_pdf(self, file_path: str) -> str:
        """
        Extract text from a PDF file.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Extracted text from the PDF
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            PdfReadError: If the file is not a valid PDF
            Exception: For other unexpected errors
        """
        logger.info(f"Loading PDF from: {file_path}")
        print(f"Loading PDF from: {file_path}")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found at {file_path}")
        
        if not file_path.lower().endswith('.pdf'):
            logger.warning(f"File {file_path} does not have a .pdf extension")
            
        text = ""
        try:
            with open(file_path, "rb") as file:
                pdf_reader = PdfReader(file)
                num_pages = len(pdf_reader.pages)
                logger.info(f"Processing {num_pages} pages...")
                
                for i, page in enumerate(pdf_reader.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                    except Exception as e:
                        logger.warning(f"Error processing page {i}: {str(e)}")
                        continue
                        
            if not text.strip():
                logger.warning("No text could be extracted from the PDF")
                
            logger.info(f"Successfully extracted text from {file_path}")
            return text
            
        except PdfReadError as e:
            logger.error(f"Error reading PDF: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error processing {file_path}: {str(e)}")
            raise
    
    def split_text(self, text: str) -> List[Document]:
        """Split text into chunks and convert to Document objects."""
        chunks = self.text_splitter.split_text(text)
        return [Document(page_content=chunk) for chunk in chunks]
    
    def process_pdf(self, file_path: str) -> List[Document]:
        print("\ndocument_loader.py process_pdf\n**********************")
        """Process a PDF file or directory of PDFs and return Document objects.
        
        Args:
            file_path: Path to a PDF file or directory containing PDFs
            
        Returns:
            List of Document objects containing the split text
            
        Raises:
            ValueError: If no text could be extracted from the PDF
        """
        all_text = []
        
        # Check if path is a directory or file
        if os.path.isdir(file_path):
            # Process all PDFs in directory
            pdf_files = glob.glob(os.path.join(file_path, "*.pdf"))
            if not pdf_files:
                raise ValueError(f"No PDF files found in directory: {file_path}")
        else:
            # Single file provided
            if not file_path.lower().endswith('.pdf'):
                raise ValueError("File must be a PDF")
            pdf_files = [file_path]
        
        logger.info(f"Found {len(pdf_files)} PDF file(s) to process...")
        
        for file in pdf_files:
            logger.info(f"Processing file: {file}")
            try:
                text = self.load_pdf(file)
                if text and text.strip():
                    all_text.append(text)
                    logger.info(f"Successfully extracted text from {os.path.basename(file)}")
                else:
                    logger.warning(f"No text extracted from {os.path.basename(file)}")
            except Exception as e:
                logger.error(f"Error processing {os.path.basename(file)}: {str(e)}", exc_info=True)
                continue
        
        if not all_text:
            raise ValueError("No text content could be extracted from any PDF files")
            
        # Combine all text from all files
        combined_text = "\n\n".join(all_text)
        logger.info(f"Combined text length: {len(combined_text)} characters")
        
        documents = self.split_text(combined_text)
        logger.info(f"Split PDFs into {len(documents)} total chunks")
        return documents
