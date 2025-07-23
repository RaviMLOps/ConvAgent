import os
import psycopg2
from typing import Dict, Any, Optional, List, Tuple
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
import logging
import sys

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config import Config

# Set up logging
logging.basicConfig(level=logging.INFO)
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
        #self.db_path = os.path.abspath(db_path or os.path.join(Config.FLIGHT_AVAILABILITY_DB_DIR, "flight_schedule.db"))
        #logger.info(f"Using database at: {self.db_path}")
        
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
        """Set up the SQL generation chain with conversation context."""
        template = """You are a PostgreSQL expert specialized in airline flight schedules. Analyze the conversation and generate a SQL query based on the latest request.
        The conversation is in format [speaker]: [message] with most recent messages last.

        ## CONVERSATION:
        {conversation}

        ## RULES:
        1. For flight-specific information (schedule, status, etc.), Flight ID is required in the WHERE clause
        2. For general flight availability (e.g., flights between cities), use From_city and To_city in WHERE clause
        3. Always use the table name "Flight_availability_and_schedule" in your queries (lowercase)
        4. Available columns: Flight_ID, Airline, From_airport, To_airport, Departure_Time, 
           Flight_duration, Arrival_Time, From_city, To_city, From_airport_code, 
           To_airport_code, From_country, To_country, Departure_days_of_week, 
           Status, Delay, available_seats, total_seats, seat_availability_status, price
        5. Only generate queries for the most recent request in context

        ## EXAMPLE 1: Flight by ID
        Conversation:
        User: What's the schedule for flight AI101?
        SQLQuery: SELECT * FROM "Flight_availability_and_schedule" WHERE "Flight_ID" = 'AI101';

        ## EXAMPLE 2: Flight status
        Conversation:
        User: Is flight AI101 on time?
        SQLQuery: SELECT "Flight_ID", "Status", "Departure_Time", "Arrival_Time", "Delay"
                  FROM "Flight_availability_and_schedule" 
                  WHERE "Flight_ID" = 'AI101';

        ## EXAMPLE 3: Flights between cities
        Conversation:
        User: Show flights from Mumbai to Delhi
        SQLQuery: SELECT "Flight_ID", "Airline", "Departure_Time", "Arrival_Time", "available_seats", "price"
                  FROM "Flight_availability_and_schedule"
                  WHERE "From_city" = 'Mumbai' AND "To_city" = 'Delhi';

        ## EXAMPLE 4: Available flights with seat count
        Conversation:
        User: What flights are available from Bangalore to Delhi tomorrow?
        SQLQuery: SELECT "Flight_ID", "Airline", "Departure_Time", "Arrival_Time", "available_seats", "price"
                  FROM "Flight_availability_and_schedule"
                  WHERE "From_city" = 'Bangalore' 
                    AND "To_city" = 'Delhi'
                    AND "available_seats" > 0;

        Conversation:
        {conversation}
        SQLQuery:
        """
        
        prompt = PromptTemplate(input_variables=["conversation"], template=template)
        
        # Create the SQL generation chain
        return (
            {"conversation": RunnablePassthrough()}
            | prompt
            | self.llm
            | StrOutputParser()
        )
    
    def execute_query(self, query: str) -> str:
        """Execute a PostgreSQL query and return the results."""
        try:
            conn = psycopg2.connect(
                dbname=Config.pg_dbname,
                user=Config.pg_user,
                password=Config.pg_password,
                host=Config.pg_host,
                port=Config.pg_port
            )
            cursor = conn.cursor()
            cursor.execute(query)
            
            if query.strip().upper().startswith(('SELECT', 'WITH', 'SHOW', 'DESCRIBE', 'PRAGMA')):
                results = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                
                if not results:
                    conn.close()
                    return "No matching flight schedule found."
                
                # Format the results as a table
                formatted_results = []
                if columns:
                    formatted_results.append(" | ".join(columns))
                    formatted_results.append("-" * (sum(len(str(col)) for col in columns) + 3 * (len(columns) - 1)))
                
                for row in results:
                    formatted_results.append(" | ".join(str(value) if value is not None else 'N/A' for value in row))
                
                conn.close()
                return "\n".join(formatted_results)
            else:
                conn.commit()
                affected = cursor.rowcount
                conn.close()
                return f"Flight schedule updated successfully. Rows affected: {affected}"
                
        except psycopg2.Error as e:
            error_msg = str(e).strip()
            if "duplicate key" in error_msg.lower():
                return "ERROR: This flight schedule already exists."
            elif "violates foreign key" in error_msg.lower():
                return "ERROR: Invalid reference. Please check the Flight ID and other references."
            elif "does not exist" in error_msg.lower():
                return "ERROR: The requested flight schedule does not exist."
            return f"Database Error: {error_msg}"
        except Exception as e:
            return f"Error processing flight schedule: {str(e)}"
    
    def __call__(self, request: str, conversation_history: list = None) -> str:
        """Process a conversation and return the SQL query results.
        
        Args:
            request: The current user request
            conversation_history: List of previous messages in format [{"role": "user"|"assistant", "content": str}]
        """
        try:
            # Format conversation history for the prompt
            formatted_conversation = []
            if conversation_history:
                for msg in conversation_history:
                    role = "User" if msg['role'] == 'user' else "Assistant"
                    formatted_conversation.append(f"{role}: {msg['content']}")
            
            # Add current request to the conversation
            formatted_conversation.append(f"User: {request}")
            conversation_text = "\n".join(formatted_conversation)
            
            # Generate the SQL query with conversation context
            sql_query = self.schedule_sql_chain.invoke(conversation_text)
            
            # Clean up the SQL query
            if "```sql" in sql_query:
                sql_query = sql_query.split("```sql")[1].split("```")[0].strip()
            elif "```" in sql_query:
                sql_query = sql_query.split("```")[1].strip()
            sql_query = sql_query.replace("SQLQuery:", "").strip()
            
            # Check for error message
            if sql_query.strip().startswith("ERROR:"):
                return sql_query.strip()
                
            # Additional safety check - only require Flight_ID for specific flight queries
            if any(term in request.lower() for term in ['status', 'schedule', 'departure', 'arrival', 'time', 'delay']):
                if "where" in sql_query.lower() and "flight_id" not in sql_query.lower():
                    return "ERROR: For specific flight information, please provide the Flight ID."
            
            # Execute the query
            result = self.execute_query(sql_query)
            
            # Format the response
            response = f"SQL Query: {sql_query}\n\nResult:\n{result}"
            
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
