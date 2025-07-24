import os
import sqlite3
from typing import Dict, Any, Optional
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
import logging
import sys
import os

import psycopg2

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config import Config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class ScheduleSQLTool:
    """A tool for generating and executing SQL queries based on natural language."""
    
    def __init__(self, db_path: str = None, model_name: str = None, temperature: float = 0.0):
        """Initialize the SQL tool.
        
        Args:
            db_path: Path to the SQLite database file
            model_name: Name of the model to use for SQL generation
            temperature: Temperature for the model
        """
        # Use provided path or default to the new location in the database directory
        self.db_path = os.path.abspath(db_path or os.path.join(Config.FLIGHT_AVAILABILITY_DB_DIR, "flight_schedule.db"))
        logger.info(f"Using database at: {self.db_path}")
        
        self.model_name = model_name or Config.MODEL_NAME
        self.temperature = temperature
        self.llm = self._initialize_llm()
        self.schedule_sql_chain = self._setup_schedule_sql_chain()
    
    def _initialize_llm(self):
        """Initialize the language model."""
        try:
            return ChatOpenAI(
                model_name=self.model_name,
                temperature=self.temperature,
                api_key=Config.OPENAI_API_KEY
            )
        except Exception as e:
            logger.error(f"Failed to initialize language model: {str(e)}")
            raise
    
    def _setup_schedule_sql_chain(self):
        """Set up the SQL generation chain."""
        # Build prompt
        template = """You are a SQLite expert specialized in airline reservation systems. Your task is to generate syntactically correct SQLite queries based on the user’s natural language request.

        ### General Guidelines:
        - **Never** select all columns (`SELECT *`). Always select only the columns needed to answer the question.
        - **Always wrap** column names in double quotes (`"column_name"`).
        - Use **only the column names and tables explicitly provided**—do not guess.
        - Avoid using or generating any columns that don't exist.
        - Do **not perform aggregations (SUM, COUNT, AVG, etc.)** unless specifically asked.

        ### Flight Schedule Queries:
        If the request is related to **flight schedule**:
        - **First**, confirm with the user whether the provided **Flight ID (flight number)** is correct.
        - Then, respond with the **airline's schedule policy** and **refund amount**.
        - You must **not** write or return a query for flight schedule if no valid Flight ID is provided.
        - Do **not** attempt to extract schedules based on origin/destination or date — schedules are accessible **only via Flight ID**.

        Use the following format:
        
        Request: Request here
        SQLQuery: Generated SQL Query here
    
        Request: {Request}
        SQLQuery:
        """
        
        prompt = PromptTemplate(input_variables=["Request"], template=template)
        
        # Create the SQL generation chain
        return (
            {"Request": RunnablePassthrough()}
            | prompt
            | self.llm
            | StrOutputParser()
        )
    
    def execute_query(self, query: str) -> str:
        """Execute a SQL query and return the results."""
        try:
            conn = psycopg2.connect(
                dbname = Config.pg_dbname,
                user = Config.pg_user,
                password = Config.pg_password,
                host = Config.pg_host,
                port = Config.pg_port,
                )
            cursor = conn.cursor()
            cursor.execute(query)
            
            if query.strip().upper().startswith(('SELECT', 'PRAGMA')):
                results = cursor.fetchall()
                columns = [description[0] for description in cursor.description] if cursor.description else []
                conn.close()
                
                if not results:
                    return "No results found."
                    
                # Format the results as a table
                formatted_results = []
                if columns:
                    formatted_results.append(" | ".join(columns))
                    formatted_results.append("-" * (sum(len(str(col)) for col in columns) + 3 * (len(columns) - 1)))
                
                for row in results:
                    formatted_results.append(" | ".join(str(value) for value in row))
                
                return "\n".join(formatted_results)
            else:
                conn.commit()
                conn.close()
                return "Query executed successfully."
                
        except sqlite3.Error as e:
            return f"Error executing query: {str(e)}"
    
    def __call__(self, request: str) -> str:
        """Process a natural language request and return the SQL query results."""
        try:
            # Generate the SQL query
            sql_query = self.schedule_sql_chain.invoke(request)
            
            # Clean up the SQL query (remove any markdown code blocks if present)
            if "```sql" in sql_query:
                sql_query = sql_query.split("```sql")[1].split("```")[0].strip()
            elif "```" in sql_query:
                sql_query = sql_query.split("```")[1].strip()
            
            sql_query = sql_query.replace("SQLQuery:", "")
            ind = sql_query.find("SELECT")
            sql_query = sql_query[ind::]
            print("sql_query: ", sql_query)
            # Execute the query
            result = self.execute_query(sql_query)
            
            # Format the response
            response = f"SQL Query: {sql_query}\n\nResult:\n{result}"
            
            # Special handling for cancellation
            if "cancelled" in request.lower() or "cancel" in request.lower():
                response += "\n\nNote: Please confirm the cancellation details above. " \
                          "Refund will be processed as per the airline's cancellation policy."
            
            return response
            
        except Exception as e:
            return f"Error processing request: {str(e)}"

def get_schedule_sql_tool() -> Dict[str, Any]:
    """Create and return the SQL tool configuration for the ReAct agent."""
    schedule_sql_tool = ScheduleSQLTool()
    
    return {
        "name": "sql_query",
        "description": """Use this tool to query flight schedule information in the database.
        It can be used to:
        - Check flight details
        - View flight schedule
        - Get information about flights schedules

        """,
        "func": schedule_sql_tool.__call__,
        "return_direct": False
    }
