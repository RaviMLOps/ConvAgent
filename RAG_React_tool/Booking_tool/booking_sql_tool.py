import os
import re
import sqlite3
import psycopg2
from typing import Dict, Any, Optional
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
import logging
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
        self.pg_sql_chain = self.pg_setup_sql_chain()
    
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
    
    def pg_setup_sql_chain(self):
        """Set up the SQL generation chain."""
        # Build prompt
        template = """You are a Postgresql expert. Given an input data, return a syntactically correct Postgresql query to run.
        Never query for all columns from a table. You must query only the columns needed to answer the question. 
        Wrap each column name in double quotes (") to denote them as delimited identifiers.

        The column names in the "Flight_reservation" table are "PNR_Number","Customer_Name","Flight_ID",
        "Airline","From_City","To_City","Departure_Time","Arrival_Time","Travel_Date","Booking_Date",
        "Booking_Status","Refund_Status".

        The column_names in the "Flight_availability_and_schedule" are "Flight_ID",	"Airline",
        "From_airport",	"To_airport", "Departure_Time", "Flight_duration", "Arrival_Time", "From_city",
        "To_city", "From_airport_code", "To_airport_code", "From_country", "To_country", 
        "Departure_days_of_week", "Status", "Delay", "available_seats", "total_seats", 
        "seat_availability_status", "price"

        Pay attention to use only the column names you can see in the "Flight_reservation" 
        and "Flight_availability_and_schedule" tables. 

        Be careful not to query for columns that do not exist. Also, pay attention to which column is in which table.
        Do not return any new columns nor perform aggregation on columns unless specifically asked.
        
        Then follow the steps below:
            1.  change to "Travel_Date" field to date format dd/mm/yyyy.  
                Please note that Trave
                from the current date.

            2.  please generate a 6-digit alpha-numeric text in CAPITAL letters. After generating
                use the text for PNR_Number.

            3.  Using the "Flight_ID"  select only the "Airline", "Departure_Time","Arrival_Time",
                from the "Flight_availability_and_schedule" table.
        
            4.  Finally, with all the above information, insert the "Flight_reservation" table setting current date 
                as "Booking_Date", "Booking_Status" to "Confirmed" and "Refund_Status" to "Not applicable".
        
        Do not return any other text other than the required sql query. 
        Do not return any new columns nor perform aggregation on columns unless specifically asked.
    
        
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
            
            if query.strip().upper().startswith('INSERT'):
                
                text = query.split("SELECT\n")[-1].split(",")
                for ele in text:
                    if "Customer_Name" in ele:
                        customer_name = str(ele).split('AS')[0]
                query = f"""SELECT * FROM "Flight_reservation" WHERE "Customer_Name" = {customer_name}"""
                
                cursor = conn.cursor()
                cursor.execute(query)
                
            if query.strip().upper().startswith(('SELECT', 'PRAGMA')):
                results = cursor.fetchall()
                columns = [description[0] for description in cursor.description] if cursor.description else []
                
                if not results:
                    return "No results found."
                    
                # Format the results as a table
                formatted_results = []
                if columns:
                    formatted_results.append(" | ".join(columns))
                    formatted_results.append("-" * (sum(len(str(col)) for col in columns) + 3 * (len(columns) - 1)))
                
                for row in results:
                    formatted_results.append(" | ".join(str(value) for value in row))
                conn.commit()
                conn.close()
                return "\n".join(formatted_results)
            else:
                conn.commit()
                conn.close()
                return "Query executed successfully!"
                
        except Exception as e:
            return f"Error executing query: {str(e)}"
    
    def __call__(self, request: str) -> str:
        """Process a natural language request and return the SQL query results."""
        try:
            # Generate the SQL query
            sql_query = self.pg_sql_chain.invoke(request)
            for x in ['SQLQuery:', "```sql", "```"]:
                if x in sql_query:
                    sql_query = sql_query.replace(x, '') 
                else:
                    sql_query 
            # Clean up the SQL query (remove any markdown code blocks if present)
      
            pnr_pattern = r'\bselect\b|\bupdate\b|\binsert\b'
            match = re.search(pnr_pattern, sql_query, re.IGNORECASE)
            if not match:
                response = sql_query
                return response
            
            # Execute the query
            result = self.execute_query(sql_query)
            # Format the response
            response = f"SQL Query: {sql_query}\n\nResult:\n{result}"
            
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
        - Flight bookings
        - Check flight details by PNR
        - View booking status
        - Cancel flights and update refund status
        - Get information about flights, passengers, and bookings
        
        For cancellations, the tool will automatically update the booking and refund status.
        """,
        "func": sql_tool.__call__,
        "return_direct": False
    }
