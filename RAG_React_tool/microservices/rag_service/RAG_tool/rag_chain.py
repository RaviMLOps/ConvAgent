import logging
import os
from typing import Dict, Any, List, Union
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableSerializable
from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.documents import Document

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGPipeline:
    """Implements a RAG (Retrieval-Augmented Generation) pipeline."""

    def __init__(self, model_name: str = None, temperature: float = None):
        """
        Initialize the RAG pipeline.

        Args:
            model_name: Name of the language model to use (defaults to env or 'gpt-4o')
            temperature: Temperature for model generation (0-2; defaults to env or 0)
        """
        self.model_name = model_name or os.getenv("MODEL_NAME", "gpt-4o")
        self.temperature = temperature if temperature is not None else float(os.getenv("TEMPERATURE", "0"))
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.llm = self._initialize_llm()
        self.prompt = self._create_prompt()

    def _initialize_llm(self) -> BaseChatModel:
        """Initialize the language model with error handling."""
        try:
            logger.info(f"Initializing language model: {self.model_name}")
            if not self.api_key:
                raise ValueError("OPENAI_API_KEY is not set in environment variables.")
            return ChatOpenAI(
                model_name=self.model_name,
                temperature=self.temperature,
                api_key=self.api_key
            )
        except Exception as e:
            logger.error(f"Failed to initialize language model: {str(e)}")
            raise

    def _create_prompt(self) -> PromptTemplate:
        """Create the prompt template for the RAG pipeline."""
        template = """Use the following pieces of context to answer the question at the end.
        If you don't know the answer, just say that you don't know, don't try to make up an answer.
        Always provide the citation for your answer.
        Always say "Let me know if you need further help" at the end of the answer.

        Context: {context}

        Question: {question}

        Helpful Answer:"""

        try:
            return PromptTemplate(
                input_variables=["context", "question"],
                template=template
            )
        except Exception as e:
            logger.error(f"Failed to create prompt template: {str(e)}")
            raise

    def format_docs(self, docs: List[Union[Document, str]]) -> str:
        """Format a list of documents into a single string."""
        if not docs:
            logger.warning("No documents provided to format_docs")
            return ""

        try:
            return "\n\n".join(
                doc.page_content if hasattr(doc, 'page_content') else str(doc)
                for doc in docs
            )
        except Exception as e:
            logger.error(f"Error formatting documents: {str(e)}")
            raise

    def create_rag_chain(self, retriever) -> RunnableSerializable:
        """Create a RAG (Retrieval-Augmented Generation) chain."""
        if not retriever:
            raise ValueError("Retriever must be provided to create RAG chain")

        try:
            logger.info("Creating RAG chain...")
            return (
                {"context": retriever | self.format_docs, "question": RunnablePassthrough()}
                | self.prompt
                | self.llm
                | StrOutputParser()
            )
        except Exception as e:
            logger.error(f"Failed to create RAG chain: {str(e)}")
            raise
