import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Add the project root to Python path first
project_root = Path(__file__).parent.parent.parent.parent  # Points to ConvAgent directory
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
    print(f"Added to path: {project_root}")
    #print(sys.path)
# Now import the modules

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
print("Config imports successful!")

from RAG_tool.rag_chain import RAGPipeline
print("RAGPipeline imports successful!")
from langchain.vectorstores import Chroma
print("Chroma imports successful!")
from langchain.embeddings import OpenAIEmbeddings
print("OpenAIEmbeddings imports successful!")


# Configure logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# Load environment variables from .env file in the RAG_tool directory
rag_tool_dir = project_root / "RAG_tool"
load_dotenv(rag_tool_dir / ".env")
print(f"RAG_tool directory: {rag_tool_dir}")
print(f"Current working directory: {os.getcwd()}")
print(f"Python path: {sys.path}")

# Test the imports
try:
    config = Config()
    print(f"Config loaded. Model: {config.MODEL_NAME}")
except Exception as e:
    print(f"Error initializing config: {e}")