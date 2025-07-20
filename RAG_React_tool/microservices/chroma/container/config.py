class Config:
    VECTOR_STORE_PATH = "chroma-data"
    PDF_DIRECTORY = "data/"
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
