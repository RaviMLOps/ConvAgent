# import os
# import argparse
# import glob
# from pathlib import Path
# from typing import Optional
# from document_loader import DocumentLoader
# from embeddings import VectorStoreManager
# from rag_chain import RAGPipeline
# from app import GradioApp
# from config import Config

# def ensure_documents_dir():
#     """Ensure the documents directory exists."""
#     os.makedirs(Config.DOCUMENTS_DIRECTORY, exist_ok=True)
#     return Config.DOCUMENTS_DIRECTORY

# def get_latest_pdf(directory: str) -> Optional[str]:
#     """Get the most recently modified PDF file in the directory."""
#     pdf_files = glob.glob(os.path.join(directory, '*.pdf'))
#     if not pdf_files:
#         return None
#     return max(pdf_files, key=os.path.getmtime)

# def process_pdf_and_setup_rag(pdf_path: Optional[str] = None):
#     """
#     Process PDF and set up RAG pipeline.
#     If no PDF path is provided, looks for PDFs in the documents directory.
#     """
#     if pdf_path is None:
#         docs_dir = ensure_documents_dir()
#         pdf_path = get_latest_pdf(docs_dir)
#         if pdf_path is None:
#             raise FileNotFoundError(
#                 f"No PDF files found in {docs_dir}. "
#                 f"Please place a PDF file in the {docs_dir} directory."
#             )
#         print(f"Using latest PDF: {pdf_path}")
    
#     # 1. Load and process PDF
#     print(f"Loading and processing PDF: {pdf_path}...")
#     loader = DocumentLoader()
#     documents = loader.process_pdf(pdf_path)
    
#     # 2. Create vector store
#     print("Creating vector store...")
#     vs_manager = VectorStoreManager()
#     vs_manager.create_vectorstore(documents)
#     retriever = vs_manager.get_retriever(k=4)
    
#     # 3. Set up RAG pipeline
#     print("Setting up RAG pipeline...")
#     rag = RAGPipeline()
#     rag_chain = rag.create_rag_chain(retriever)
    
#     return rag_chain

# def main():
#     parser = argparse.ArgumentParser(description="RAG-based Q&A System")
#     parser.add_argument("--pdf", type=str, 
#                        help="Optional: Path to a specific PDF file. If not provided, uses the latest PDF from the documents directory.")
#     args = parser.parse_args()
    
#     try:
#         # Process PDF and set up RAG
#         rag_chain = process_pdf_and_setup_rag(args.pdf)
        
#         # Launch Gradio app
#         print("Launching Gradio interface...")
#         print("You can now ask questions about the document!")
#         app = GradioApp(rag_chain.invoke)
#         app.launch()
#     except Exception as e:
#         print(f"Error: {str(e)}")
#         print(f"Please make sure to place your PDF file in the '{Config.DOCUMENTS_DIRECTORY}/' directory.")

# if __name__ == "__main__":
#     main()
