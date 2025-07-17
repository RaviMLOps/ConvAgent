import os
from typing import List
from PyPDF2 import PdfReader
from langchain_core.documents import Document
from config import Config

class DocumentLoader:
    def __init__(self, pdf_dir: str = Config.PDF_DIRECTORY):
        self.pdf_dir = pdf_dir

    def load_documents(self) -> List[Document]:
        documents = []
        for filename in os.listdir(self.pdf_dir):
            if filename.endswith(".pdf"):
                file_path = os.path.join(self.pdf_dir, filename)
                reader = PdfReader(file_path)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() or ""
                documents.append(Document(page_content=text, metadata={"source": filename}))
        return documents
