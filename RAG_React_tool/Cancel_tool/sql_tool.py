import os
import sqlite3
import psycopg2
from typing import Dict, Any, Optional
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
import logging
import re
try:
    from ..config import Config
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config import Config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SQLTool:
    """A tool for generating and executing SQL queries based on natural language."""
    
    def __init__(self, db_path: str = None, model_name: str = None, temperature: float = 0.0):
        """Initialize the SQL tool.
        
        Args:
            db_path: Path to the Postgres database file
            model_name: Name of the model to use for SQL generation
            temperature: Temperature for the model
        """
        # Use provided path or default to the new location in the database directory
        #self.db_path = os.path.abspath(db_path or os.path.join(Config.SQL_DB_DIR, "Flight_reservation.db"))
        #logger.info(f"Using database at: {self.db_path}")
        
        self.model_name = model_name or Config.MODEL_NAME
        self.temperature = temperature
        self.llm = self._initialize_llm()
        self.sql_chain = self._setup_sql_chain()
    
    def _initialize_llm(self):
        """Initialize the language model."""
        print("initializing llm")
        try:
            return ChatOpenAI(
                model_name=self.model_name,
                temperature=self.temperature,
                api_key=Config.OPENAI_API_KEY
            )
        except Exception as e:
            print("Exception: ", str(e))
            logger.error(f"Failed to initialize language model: {str(e)}")
            raise
    
    def _setup_sql_chain(self):
        """Set up the SQL generation chain with conversation context."""
        template = """You are a helpful flight booking assistant with expertise in PostgreSQL. Analyze the entire conversation history to understand the context and generate an appropriate SQL query based on the conversation.
        The conversation is in format [speaker]: [message] with messages in chronological order. Pay attention to:
        1. Any PNR numbers mentioned earlier in the conversation
        2. The type of action being requested (cancellation, status check, etc.)
        3. Any specific conditions or filters mentioned

        Use the following rules for generating SQL queries:
        1. Always use double quotes for table and column names
        2. Use single quotes for string literals
        3. For date comparisons, use the format 'DD-MM-YYYY'
        4. For time comparisons, use the format 'HH:MI AM/PM'
        5. When querying for a specific PNR, always include it in the WHERE clause
        6. For cancellations, follow these steps:
           a. First, retrieve the booking details to confirm the current status
           b. If status is 'Confirmed', generate an UPDATE query to cancel the booking
           c. If status is already 'Cancelled', inform the user
           d. The cancellation should update both Booking_Status and Refund_Status
        7. For UPDATE queries, always include a WHERE clause with PNR_Number
        8. Consider the entire conversation context to understand what action is being requested
        
        IMPORTANT: When user wants to cancel a ticket, you MUST follow these exact steps:
        1. First, check the current status of the booking
        2. If status is 'Confirmed', generate an UPDATE query to cancel it
        3. If status is already 'Cancelled', return a message saying it's already cancelled
        4. Always include the PNR in your WHERE clause
        5. Update both Booking_Status and Refund_Status together

        ## EXAMPLE 1: Check Booking Status
        Conversation:
        User: My PNR is AI1234
        User: What's my booking status?
        SQLQuery: SELECT "PNR_Number", "Airline", "From_City", "To_City",
                         "Departure_Time", "Arrival_Time", "Travel_Date",
                         "Booking_Status", "Refund_Status"
                  FROM "Flight_reservation"
                  WHERE "PNR_Number" = 'AI1234';

        ## EXAMPLE 2: Cancel a Booking (First Check Status)
        Conversation:
        User: I want to cancel my booking with PNR AI1234
        SQLQuery: SELECT "PNR_Number", "Airline", "From_City", "To_City",
                         "Departure_Time", "Arrival_Time", "Travel_Date",
                         "Booking_Status", "Refund_Status"
                  FROM "Flight_reservation"
                  WHERE "PNR_Number" = 'AI1234';

        ## EXAMPLE 3: Execute Cancellation (After Confirming Status is 'Confirmed')
        Conversation:
        User: I want to cancel my booking with PNR AI1234
        [Previous query showed status is 'Confirmed']
        SQLQuery: 
        -- First, confirm the booking exists and is confirmed
        WITH check_booking AS (
            SELECT "PNR_Number", "Booking_Status"
            FROM "Flight_reservation"
            WHERE "PNR_Number" = 'AI1234'
            FOR UPDATE
        )
        UPDATE "Flight_reservation" fr
        SET "Booking_Status" = 'Cancelled',
            "Refund_Status" = 'Refunded',
            "Last_Updated" = CURRENT_TIMESTAMP
        FROM check_booking cb
        WHERE fr."PNR_Number" = cb."PNR_Number"
        AND cb."Booking_Status" = 'Confirmed'
        RETURNING fr."PNR_Number", fr."Booking_Status", fr."Refund_Status";

        ## EXAMPLE 4: Already Cancelled Booking
        Conversation:
        User: I want to cancel my booking with PNR AI1234
        [Previous query showed status is 'Cancelled']
        SQLQuery: SELECT 'Booking with PNR AI1234 is already cancelled' as message;

        ## EXAMPLE 5: Flight Details
        Conversation:
        User: What are the details of my flight with PNR AI1234?
        SQLQuery: SELECT "PNR_Number", "Airline", "From_City", "To_City",
                         "Departure_Time", "Arrival_Time", "Travel_Date",
                         "Booking_Status", "Refund_Status"
                  FROM "Flight_reservation"
                  WHERE "PNR_Number" = 'AI1234';
                  FROM "Flight_reservation" 
                  WHERE "PNR_Number" = 'AI1234';

        ## EXAMPLE 4: Complete Cancellation Flow
        Conversation:
        User: I want to cancel my booking with PNR AM9650
        
        -- First, check the current status
        SQLQuery: SELECT "Booking_Status" FROM "Flight_reservation" WHERE "PNR_Number" = 'AM9650';
        
        -- If status is 'Confirmed', then cancel it
        SQLQuery: UPDATE "Flight_reservation"
                  SET "Booking_Status" = 'Cancelled',
                      "Cancellation_Date" = CURRENT_TIMESTAMP,
                      "Refund_Amount" = (SELECT "Total_Fare" * 0.8 FROM "Flight_reservation" WHERE "PNR_Number" = 'AM9650')
                  WHERE "PNR_Number" = 'AM9650' AND "Booking_Status" = 'Confirmed'
                  RETURNING "PNR_Number", "Booking_Status", "Refund_Amount";
                  
        -- If status is already 'Cancelled', return a message
        -- SQLQuery: SELECT 'Booking is already cancelled' as message;

        ## EXAMPLE 5: Check Cancellation Status with Refund
        Conversation:
        User: What's the status of my cancellation for PNR AM9650?
        SQLQuery: SELECT 
                    "PNR_Number", 
                    "Booking_Status", 
                    CASE 
                        WHEN "Booking_Status" = 'Cancelled' THEN 'Your booking has been cancelled. Refund will be processed within 7-10 business days.'
                        WHEN "Booking_Status" = 'Confirmed' THEN 'Your booking is still active.'
                        ELSE 'Status unknown.'
                    END as message
                  FROM "Flight_reservation"
                  WHERE "PNR_Number" = 'AM9650';

        ## EXAMPLE 6: Multiple Queries
        Conversation:
        User: My PNR is NZ8553
        Assistant: What would you like to know about this booking?
        User: When does it depart and what's the status?
        SQLQuery: SELECT "PNR_Number", "Departure_Time", "Travel_Date", "Booking_Status"
                  FROM "Flight_reservation" 
                  WHERE "PNR_Number" = 'NZ8553';

        Conversation:
        {conversation}
        SQLQuery:
        """
        prompt = PromptTemplate(input_variables=["conversation"], template=template)
        print("Setting up SQL chain with conversation context")
        
        return (
            {"conversation": RunnablePassthrough()}
            | prompt
            | self.llm
            | StrOutputParser()
        )
    
    def execute_query(self, query: str) -> str:
        """Execute a SQL query and return the results."""
        try:
            conn = psycopg2.connect(
                dbname=Config.pg_dbname,
                user=Config.pg_user,
                password=Config.pg_password,
                host=Config.pg_host,
                port=Config.pg_port,
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
                print("formatted_results: ", formatted_results)
                return "\n".join(formatted_results)
            else:
                conn.commit()
                conn.close()
                return "Query executed successfully."
                
        except Exception as e:
            error_msg = f"Error executing query: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    # def __call__(self, request: str, conversation_history: list = None) -> str:
    #     """Process a conversation and return the SQL query results.
        
    #     Args:
    #         request: The current user request
    #         conversation_history: List of previous messages in format [{"role": "user"|"assistant", "content": str}]
    #     """
    #     try:
    #         # Format conversation history for the prompt
    #         formatted_conversation = []
    #         if conversation_history:
    #             for msg in conversation_history:
    #                 role = "User" if msg['role'] == 'user' else "Assistant"
    #                 formatted_conversation.append(f"{role}: {msg['content']}")
            
    #         # Add current request to the conversation
    #         formatted_conversation.append(f"User: {request}")
    #         conversation_text = "\n".join(formatted_conversation)
            
    #         print(f"Processing conversation:\n{conversation_text}")
            
    #         # Generate the SQL query with conversation context
    #         sql_query = self.sql_chain.invoke(conversation_text)
    #         print(f"Generated SQL query: {sql_query}")
            
    #         # Clean up the SQL query
    #         if "```sql" in sql_query:
    #             sql_query = sql_query.split("```sql")[1].split("```")[0].strip()
    #         elif "```" in sql_query:
    #             sql_query = sql_query.split("```")[1].strip()
    #         sql_query = sql_query.replace("SQLQuery:", "").strip()
            
    #         # Check for error message
    #         if sql_query.strip().startswith("ERROR:"):
    #             return sql_query.strip()
            
    #         # Execute the query
    #         result = self.execute_query(sql_query)
            
    #         # Format the response
    #         response = f"SQL Query: {sql_query}\n\nResult:\n{result}"
           
    #         # Special handling for cancellation
    #         if "cancel" in request.lower():
    #             response += "\n\nNote: Please confirm the cancellation details above. " \
    #                       "Refund will be processed as per the airline's cancellation policy."
            
    #         return response
            
    #     except Exception as e:
    #         print("Exception: ", str(e))
    #         logger.error(f"Failed to connect to database: {str(e)}")
    #         raise

    def __call__(self, request: str, conversation_history: list = None) -> str:
        """Process a conversation and execute the appropriate SQL query.
        
        Args:
            request: The current user request
            conversation_history: List of previous messages in format [{"role": "user"|"assistant", "content": str}]
            
        Returns:
            str: The response to the user's query
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
            
            print(f"Processing conversation:\n{conversation_text}")
            
            # Generate the SQL query with conversation context
            sql_query = self.sql_chain.invoke(conversation_text)
            print(f"Generated SQL query: {sql_query}")
            
            # Clean up the SQL query
            if "```sql" in sql_query:
                sql_query = sql_query.split("```sql")[1].split("```")[0].strip()
            elif "```" in sql_query:
                sql_query = sql_query.split("```")[1].strip()
            sql_query = sql_query.replace("SQLQuery:", "").strip()
            
            # Check for error message
            if sql_query.strip().startswith("ERROR:"):
                return sql_query.strip()
                
            # Additional safety check
            if "where" in sql_query.lower() and "pnr_number" not in sql_query.lower():
                return "ERROR: PNR number is required. Please provide a valid PNR number."
            
            # Execute the query
            result = self.execute_query(sql_query)
            
            # Format the response based on the query type
            if "ERROR:" in result:
                return result  # Return error messages as-is
                
            # Check for cancellation query
            if "UPDATE" in sql_query.upper() and "cancelled" in sql_query.lower():
                if "1 row" in result or "1 row affected" in result:
                    return "✅ Your booking has been successfully cancelled. Refund will be processed as per the airline's cancellation policy."
                elif "0 rows" in result:
                    return "ℹ️ No changes were made. The booking might have already been cancelled or does not exist."
                return result
                
            # For SELECT queries, return the results as-is
            return result
            
        except Exception as e:
            error_msg = f"Error processing request: {str(e)}"
            print(f"Exception: {error_msg}")
            logger.error(error_msg)
            return error_msg

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
