"""
RAG Agent Module

This module implements the ReActRAGAgent class which provides RAG capabilities
using a ReAct agent with access to various tools.
"""
import os
import logging
import datetime as dt
from typing import Optional, List, Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import necessary modules
from langchain.agents import load_tools, AgentExecutor, create_react_agent
from langchain import hub
from langchain.tools import Tool
from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel

# Import from existing modules
from config import Config
from database.chroma_db.rag_setup import RAGSetup
from Cancel_tool import get_sql_tool

# Import RAGPipeline from the same package
from RAG_tool.rag_chain import RAGPipeline

def get_current_time(text: str = "") -> str:
    """Returns current date and time in Indian timezone."""
    dt_india = dt.datetime.utcnow() + dt.timedelta(hours=5, minutes=30)
    return dt_india.strftime('%Y-%m-%d %H:%M:%S')

class ReActRAGAgent:
    """A ReAct agent with RAG capabilities."""
    
    def __init__(self, model_name: str = None, temperature: float = None):
        """Initialize the ReAct RAG agent.
        
        Args:
            model_name: Name of the model to use. If None, uses Config.MODEL_NAME
            temperature: Temperature for the model. If None, uses Config.TEMPERATURE
        """
        self.model_name = model_name or Config.MODEL_NAME
        self.temperature = temperature if temperature is not None else Config.TEMPERATURE
        self.llm = self._initialize_llm()
        self.tools = []
        self.agent_executor = None
        self.rag_chain = None
    
    def _initialize_llm(self) -> BaseChatModel:
        """Initialize the language model with error handling."""
        try:
            logger.info(f"Initializing language model: {self.model_name}")
            return ChatOpenAI(
                model_name=self.model_name,
                temperature=self.temperature,
                api_key=Config.OPENAI_API_KEY
            )
        except Exception as e:
            logger.error(f"Failed to initialize language model: {str(e)}")
            raise
    
    def _setup_tools(self):
        """Set up the tools for the agent."""
        # Time tool
        time_tool = Tool(
            name="time_tool",
            func=get_current_time,
            description="""Returns current date and time, use this for any \
            questions related to knowing current date and Indian time. \
            The input should always be an empty string."""
        )
        
        # RAG tool
        rag_tool = Tool(
            name="rag_query",
            func=self.rag_chain.invoke,
            description="""Useful for when you need to answer questions related to kohinoor airline policy.
            Input should be a clear and specific question about the policy.
            Questions related to baggage policy, ticket modification and flight check-in can be answered by this tool.
            The tool will retrieve relevant information and provide an answer."""
        )
        
        # SQL tool for flight reservations
        sql_tool_config = get_sql_tool()
        sql_tool = Tool(
            name=sql_tool_config['name'],
            func=sql_tool_config['func'],
            description=sql_tool_config['description'],
            return_direct=sql_tool_config.get('return_direct', False)
        )
        
        # Load basic tools and add custom ones
        self.tools = load_tools([], llm=self.llm) + [time_tool, rag_tool, sql_tool]
    
    def _initialize_agent(self):
        """Initialize the ReAct agent."""
        # Get the ReAct prompt
        prompt = hub.pull("hwchase17/react")
        
        # Create the ReAct agent
        agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        # Create the agent executor
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True
        )

    def initialize(self) -> bool:
        """Initialize all components of the agent.
        
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        try:
            # Set up RAG with existing ChromaDB
            logger.info("Loading existing ChromaDB vector store...")
            rag_setup = RAGSetup()
            if not rag_setup.load_existing_vectorstore():
                logger.error("No existing ChromaDB vector store found")
                return False
            
            # Create RAG pipeline
            logger.info("Setting up RAG chain...")
            rag_pipeline = RAGPipeline()
            self.rag_chain = rag_pipeline.create_rag_chain(
                retriever=rag_setup.vectorstore.as_retriever()
            )
            
            # Set up tools
            self._setup_tools()
            
            # Initialize agent
            self._initialize_agent()
            
            logger.info("ReAct RAG agent initialized successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize agent: {str(e)}")
            return False
    
    def query(self, question: str) -> str:
        """Query the agent with a question."""
        if not self.agent_executor:
            return "Error: Agent not initialized. Please call initialize() first."
        
        try:
            result = self.agent_executor.invoke({"input": question})
            return result.get("output", "No response generated.")
        except Exception as e:
            error_msg = f"Error in query: {str(e)}"
            logger.error(error_msg)
            return error_msg
