import sqlite3
from pathlib import Path
from tabulate import tabulate

def query_pnr(pnr_number, db_path=None):
    """
    Query flight reservation details by PNR number.
    
    Args:
        pnr_number (str): The PNR number to query
        db_path (str, optional): Path to the SQLite database. If None, uses default path.
    """
    # Set default database path if not provided
    if db_path is None:
        base_dir = Path(__file__).parent
        db_path = base_dir / "database" / "sql_db" / "data" / "Flight_reservation.db"
    
    try:
        # Connect to the database
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row  # This enables column access by name
        cursor = conn.cursor()
        
        # Execute the query
        cursor.execute("""
            SELECT * 
            FROM Flight_reservation 
            WHERE PNR_Number = ?;
        """, (pnr_number.upper(),))  # Convert to uppercase for case-insensitive match
        
        # Fetch the result
        result = cursor.fetchone()
        
        if result:
            # Convert row to dict for easier access
            result_dict = dict(result)
            
            # Print the results in a nice format
            print("\n" + "="*80)
            print(f"FLIGHT RESERVATION DETAILS - PNR: {pnr_number.upper()}")
            print("="*80)
            
            # Group related fields together for better readability
            booking_info = {
                "Booking Status": result_dict.get("Booking_Status"),
                "Refund Status": result_dict.get("Refund_Status"),
                "Booking Date": result_dict.get("Booking_Date")
            }
            
            flight_info = {
                "Airline": result_dict.get("Airline"),
                "Flight Number": result_dict.get("Flight_ID"),
                "From": result_dict.get("From_City"),
                "To": result_dict.get("To_City"),
                "Departure": f"{result_dict.get('Departure_Time')} on {result_dict.get('Travel_Date')}",
                "Arrival": result_dict.get('Arrival_Time')
            }
            
            print("\nPASSENGER INFORMATION")
            print("-" * 40)
            print(f"Name: {result_dict.get('Customer_Name')}")
            print(f"PNR: {result_dict.get('PNR_Number')}")
            
            print("\nFLIGHT INFORMATION")
            print("-" * 40)
            for key, value in flight_info.items():
                if value:
                    print(f"{key}: {value}")
            
            print("\nBOOKING INFORMATION")
            print("-" * 40)
            for key, value in booking_info.items():
                if value:
                    print(f"{key}: {value}")
            
            print("="*80 + "\n")
        else:
            print(f"\nNo reservation found for PNR: {pnr_number}\n")
            
    except sqlite3.Error as e:
        print(f"\nDatabase error: {e}\n")
    except Exception as e:
        print(f"\nAn error occurred: {e}\n")
    finally:
        # Close the connection
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    import sys
    
    # Get PNR from command line argument or prompt
    if len(sys.argv) > 1:
        pnr = sys.argv[1]
    else:
        pnr = input("Enter PNR number: ")
    
    query_pnr(pnr)