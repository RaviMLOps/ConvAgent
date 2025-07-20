import os
import psycopg2
from typing import Dict, Any
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScheduleSQLTool:
    """A tool for generating and executing SQL queries based on natural language, using PostgreSQL."""

    def __init__(self, model_name: str = None, temperature: float = None):
        """Initialize the SQL tool.

        Args:
            model_name: Name of the model to use for SQL generation (from ConfigMap env var)
            temperature: Temperature for the model (from ConfigMap env var)
        """
        # PostgreSQL connection info from environment (ConfigMap/Secret)
        self.pg_host = os.getenv("PG_HOST")
        self.pg_port = os.getenv("PG_PORT", "5432")
        self.pg_db = os.getenv("PG_DB")
        self.pg_user = os.getenv("PG_USER")
        self.pg_password = os.getenv("PG_PASSWORD")
        self.model_name = model_name or os.getenv("MODEL_NAME", "gpt-4o")
        self.temperature = float(temperature if temperature is not None else os.getenv("TEMPERATURE", "0"))
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.llm = self._initialize_llm()
        self.schedule_sql_chain = self._setup_schedule_sql_chain()

    def _initialize_llm(self):
        try:
            return ChatOpenAI(
                model_name=self.model_name,
                temperature=self.temperature,
                api_key=self.openai_api_key
            )
        except Exception as e:
            logger.error(f"Failed to initialize language model: {str(e)}")
            raise

    def _setup_schedule_sql_chain(self):
        """Set up the SQL generation chain."""
        template = """You are a PostgreSQL expert. Given an input request, return a syntactically correct PostgreSQL query to run.
        Never query for all columns from a table. You must query only the columns needed to answer the question. 
        Wrap each column name in double quotes (") to denote them as delimited identifiers.
        Pay attention to use only the column names you can see in the tables below. 
        Be careful not to query for columns that do not exist. Also, pay attention to which column is in which table.
        Do not return any new columns nor perform aggregation on columns unless specifically asked.
        
        The column_names in the "Flight_availability_and_schedule" are "Flight_ID",	"Airline",
        "From_airport",	"To_airport", "Departure_Time", "Flight_duration", "Arrival_Time", "From_city",
        "To_city", "From_airport_code", "To_airport_code", "From_country", "To_country", 
        "Departure_days_of_week", "Status", "Delay", "available_seats", "total_seats", 
        "seat_availability_status", "price"

        Pay attention to use only the column names you can see in the "Flight_availability_and_schedule" table. 

        Be careful not to query for columns that do not exist. Also, pay attention to which column is in which table.
        Do not return any new columns nor perform aggregation on columns unless specifically asked.


        Use the following format:

        Request: Request here
        SQLQuery: Generated SQL Query here

        Request: {Request}
        SQLQuery:
        """
        prompt = PromptTemplate(input_variables=["Request"], template=template)

        return (
            {"Request": RunnablePassthrough()}
            | prompt
            | self.llm
            | StrOutputParser()
        )

    def execute_query(self, query: str) -> str:
        """Execute a SQL query and return the results from PostgreSQL."""
        try:
            conn = psycopg2.connect(
                host=self.pg_host,
                port=self.pg_port,
                dbname=self.pg_db,
                user=self.pg_user,
                password=self.pg_password
            )
            cursor = conn.cursor()
            cursor.execute(query)

            if cursor.description:
                results = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                conn.close()
                if not results:
                    return "No results found."
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
        except psycopg2.Error as e:
            return f"Error executing query: {str(e)}"

    def __call__(self, request: str) -> str:
        """Process a natural language request and return the SQL query results."""
        try:
            # Generate the SQL query
            sql_query = self.schedule_sql_chain.invoke(request)

            # Clean up the SQL query (remove any markdown code blocks if present)
            # if "```sql" in sql_query:
            #     sql_query = sql_query.split("```sql")[1].split("```")[0].strip()
            # elif "```" in sql_query:
            #     sql_query = sql_query.split("```")[1].strip()
            for x in ['SQLQuery:', "```sql", "```"]:
                if x in sql_query:
                    sql_query = sql_query.replace(x, '') 
                else:
                    sql_query 

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
