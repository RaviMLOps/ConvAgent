import os
from config import Config
from document_loader import DocumentLoader
from embeddings import VectorStoreManager
from langchain.schema import Document  # If needed

class RAGSetup:
    def __init__(self, persist_directory: str = None):
        self.persist_directory = os.path.abspath(persist_directory or Config.VECTOR_STORE_PATH)
        self.document_loader = DocumentLoader()
        self.vectorstore_manager = VectorStoreManager(self.persist_directory)
        self.vectorstore = None

    def setup_vectorstore(self, force_recreate=False):
        if force_recreate or not os.path.exists(self.persist_directory):
            documents = self.document_loader.load_documents()
            self.vectorstore = self.vectorstore_manager.create_vectorstore(documents)
            self.vectorstore.persist()
        else:
            self.vectorstore = self.vectorstore_manager.load_vectorstore()
        return self.vectorstore

    def load_existing_vectorstore(self):
        if os.path.exists(self.persist_directory):
            self.vectorstore = self.vectorstore_manager.load_vectorstore()
            return True
        return False

    
    def query(self, question, k=3):
        """
        Retrieve relevant context/docs from Chroma for a given question.
        Uses semantic similarity search.
        """
        if not self.vectorstore:
            return "Vectorstore not loaded."
        try:
            # Basic similarity search (change k for more/less results)
            results = self.vectorstore.similarity_search(question, k=k)
            # `results` is a list of Document objects (from langchain)
            docs = [doc.page_content for doc in results]
            return docs if docs else "No relevant content found."
        except Exception as e:
            return f"Error querying vectorstore: {str(e)}"
