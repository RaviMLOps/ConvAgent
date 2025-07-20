from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from config import Config

class VectorStoreManager:
    def __init__(self, persist_directory: str = Config.VECTOR_STORE_PATH):
        self.persist_directory = persist_directory
        self.embedding_function = HuggingFaceEmbeddings(model_name=Config.EMBEDDING_MODEL)

    def create_vectorstore(self, documents):
        return Chroma.from_documents(
            documents,
            self.embedding_function,
            persist_directory=self.persist_directory
        )

    def load_vectorstore(self):
        return Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embedding_function
        )
