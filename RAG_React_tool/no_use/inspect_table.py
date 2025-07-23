# #!/usr/bin/env python3
# import psycopg2
# import logging
# from config import Config

# # Set up logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# def get_table_columns():
#     """Fetch and display column information for the flight_availability_and_schedule table."""
#     try:
#         # Establish a connection to the database
#         conn = psycopg2.connect(
#             dbname=Config.pg_dbname,
#             user=Config.pg_user,
#             password=Config.pg_password,
#             host=Config.pg_host,
#             port=Config.pg_port
#         )
        
#         # Create a cursor object
#         cursor = conn.cursor()
        
#         # Query to get column information
#         query = """
#         SELECT 
#             column_name, 
#             data_type,
#             is_nullable,
#             column_default,
#             character_maximum_length
#         FROM 
#             information_schema.columns 
#         WHERE 
#             table_name = 'Flight_availability_and_schedule'
#         ORDER BY 
#             ordinal_position;
#         """
        
#         # Execute the query
#         cursor.execute(query)
        
#         # Fetch all rows
#         columns = cursor.fetchall()
#         print(columns)
        
#         if not columns:
#             print("No columns found. The table might not exist or be empty.")
#             return
        
#         # Print table header
#         header_format = "\n{:<30} {:<20} {:<10} {:<30} {:<10}"
#         print(header_format.format(
#             "COLUMN NAME", "DATA TYPE", "NULLABLE", "DEFAULT", "MAX LENGTH"
#         ))
#         print("-" * 100)
        
#         # Print each column's information
#         for col in columns:
#             print("{:<30} {:<20} {:<10} {:<30} {:<10}".format(
#                 col[0],  # column_name
#                 col[1],  # data_type
#                 col[2],  # is_nullable
#                 str(col[3])[:25] + '...' if col[3] else 'NULL',  # column_default (truncated)
#                 str(col[4]) if col[4] else 'N/A'  # character_maximum_length
#             ))
            
        
#         # Print sample data
#         print("\nSample data (first 5 rows):")
#         print("-" * 100)
#         cursor.execute("SELECT * FROM Flight_availability_and_schedule LIMIT 5;")
#         rows = cursor.fetchall()
        
#         if rows:
#             # Get column names
#             col_names = [desc[0] for desc in cursor.description]
#             print(" | ".join(f"{name:<20}" for name in col_names))
#             print("-" * (len(col_names) * 22))
            
#             # Print each row
#             for row in rows:
#                 print(" | ".join(f"{str(value)[:18]:<20}" for value in row))
#         else:
#             print("No data found in the table.")
        
#     except Exception as e:
#         logger.error(f"Error inspecting table: {str(e)}")
#     finally:
#         # Close the cursor and connection
#         if 'cursor' in locals():
#             cursor.close()
#         if 'conn' in locals():
#             conn.close()

# if __name__ == "__main__":
#     print("Inspecting table: Flight_availability_and_schedule")
#     print("=" * 50)
#     get_table_columns()
