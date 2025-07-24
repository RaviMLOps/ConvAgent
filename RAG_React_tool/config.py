import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Model configuration
    MODEL_NAME = "gpt-4o"
    #EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    #EMBEDDING_MODEL = "ONNXMiniLM_L6_V2"
    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  # Use this standard model instead
    TEMPERATURE = 0
    
    # Text processing
    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 50
    
    # Base directories
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATABASE_DIR = os.path.join(BASE_DIR, "database")
    
    # ChromaDB Server Configuration
    CHROMA_SERVER_HOST = "13.200.143.143"
    CHROMA_SERVER_PORT = 22
    CHROMA_SERVER_BASE = f"{CHROMA_SERVER_HOST}:{CHROMA_SERVER_PORT}/chroma"
    CHROMA_STATUS_ENDPOINT = f"{CHROMA_SERVER_BASE}/status"
    CHROMA_QUERY_ENDPOINT = f"{CHROMA_SERVER_BASE}/query"
   
    # Collection name to use in ChromaDB
    CHROMA_COLLECTION_NAME = "documents"
    
    # Postgresql setup
    pg_dbname = "Flight_reservation"
    pg_user = "postgres"
    pg_password = "mlcohort@4"
    pg_host = "13.200.143.143"
    pg_port = 5432
    
    # Database paths
    SQL_DB_DIR = os.path.join(DATABASE_DIR, "sql_db", "data")
    FLIGHT_AVAILABILITY_DB_DIR = os.path.join(DATABASE_DIR, "flight_availability_db", "data")

    
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
