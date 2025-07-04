import os
import sqlite3
from typing import Dict, Any, Optional
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
import logging
from config import Config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SQLTool:
    """A tool for generating and executing SQL queries based on natural language."""
    
    def __init__(self, db_path: str = None, model_name: str = None, temperature: float = 0.0):
        """Initialize the SQL tool.
        
        Args:
            db_path: Path to the SQLite database file
            model_name: Name of the model to use for SQL generation
            temperature: Temperature for the model
        """
        # Use provided path or default to the new location in the database directory
        self.db_path = os.path.abspath(db_path or os.path.join(Config.SQL_DB_DIR, "airline.db"))
        logger.info(f"Using database at: {self.db_path}")
        
        self.model_name = model_name or Config.MODEL_NAME
        self.temperature = temperature
        self.llm = self._initialize_llm()
        self.sql_chain = self._setup_sql_chain()
    
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
    
    def _setup_sql_chain(self):
        """Set up the SQL generation chain."""
        # Build prompt
        template = """You are a SQLite expert. Given an input request, return a syntactically correct SQLite query to run.
        Never query for all columns from a table. You must query only the columns needed to answer the question. 
        Wrap each column name in double quotes (") to denote them as delimited identifiers.
        Pay attention to use only the column names you can see in the tables below. 
        Be careful not to query for columns that do not exist. Also, pay attention to which column is in which table.
        Do not return any new columns nor perform aggregation on columns unless specifically asked.
        In case of cancellation query , do confirm with user that the PNR_Number is correct and share information about cancellation policy and refund amount. 
        In case of cancellation query, update the Flight_reservation table setting Booking_Status to "Cancelled" 
        and Refund_Status to "Refunded" for the specified PNR_Number.
        
        The database {airline.db} contains flight reservation data, and the PNR_Number column is used to identify reservations.
        Always verify the PNR_Number before making any updates.
        
        Use the following format:
        
        Request: Request here
        SQLQuery: Generated SQL Query here
        
        Only use the following tables:
        CREATE TABLE IF NOT EXISTS Flight_reservation (
            PNR_Number VARCHAR(10) PRIMARY KEY,
            Customer_Name VARCHAR(50),
            Flight_ID VARCHAR(50),
            Airline VARCHAR(50),
            From_City VARCHAR(50),
            To_City VARCHAR(50),
            Departure_Time TIME,
            Arrival_Time TIME,
            Travel_Date DATE,
            Booking_Date DATE,
            Booking_Status VARCHAR(20),
            Refund_Status VARCHAR(20)
        )
        
        Request: {request}
        SQLQuery:
        """
        
        prompt = PromptTemplate(input_variables=["request"], template=template)
        
        # Create the SQL generation chain
        return (
            {"request": RunnablePassthrough()}
            | prompt
            | self.llm
            | StrOutputParser()
        )
    
    def execute_query(self, query: str) -> str:
        """Execute a SQL query and return the results."""
        try:
            conn = sqlite3.connect(self.db_path)
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
            sql_query = self.sql_chain.invoke(request)
            
            # Clean up the SQL query (remove any markdown code blocks if present)
            if "```sql" in sql_query:
                sql_query = sql_query.split("```sql")[1].split("```")[0].strip()
            elif "```" in sql_query:
                sql_query = sql_query.split("```")[1].strip()
            
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

def get_sql_tool() -> Dict[str, Any]:
    """Create and return the SQL tool configuration for the ReAct agent."""
    sql_tool = SQLTool()
    
    return {
        "name": "sql_query",
        "description": """Use this tool to query or update flight reservation information in the database.
        It can be used to:
        - Check flight details by PNR
        - View booking status
        - Cancel flights and update refund status
        - Get information about flights, passengers, and bookings
        
        For cancellations, the tool will automatically update the booking and refund status.
        """,
        "func": sql_tool.__call__,
        "return_direct": False
    }
