import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Model configuration
    MODEL_NAME = "gpt-4o"
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    TEMPERATURE = 0
    
    # Text processing
    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 50
    
    # Base directories
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATABASE_DIR = os.path.join(BASE_DIR, "database")
    
    # Database directories
    # ChromaDB data storage - using direct path since the database was created in the root directory
    CHROMA_DB_DIR = os.path.join(BASE_DIR, "chroma_db", "data")
    SQL_DB_DIR = os.path.join(DATABASE_DIR, "sql_db", "data")  # SQLite database files
    DOCUMENTS_DIR = os.path.join(DATABASE_DIR, "documents")  # For storing source documents
    
    # Backward compatibility
    PERSIST_DIRECTORY = CHROMA_DB_DIR  # For backward compatibility
    DOCUMENTS_DIRECTORY = DOCUMENTS_DIR  # For backward compatibility
    
    # API Keys (load from environment variables)
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    @classmethod
    def setup_directories(cls):
        """Create necessary directories if they don't exist."""
        os.makedirs(cls.CHROMA_DB_DIR, exist_ok=True)
        os.makedirs(cls.SQL_DB_DIR, exist_ok=True)
        os.makedirs(cls.DOCUMENTS_DIR, exist_ok=True)
    
    @classmethod
    def validate_config(cls):
        """Validate that all required configurations are set."""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is not set")

# Setup directories and validate configuration
Config.setup_directories()
Config.validate_config()
