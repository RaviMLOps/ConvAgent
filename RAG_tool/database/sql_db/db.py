import sqlite3
import csv

# Connect to or create the database
conn = sqlite3.connect('airline.db')
cursor = conn.cursor()


def create_and_insert_Data(conn, cursor):

    cursor.execute('''
    create table IF NOT EXISTS Flight_reservation (
        PNR_Number VARCHAR(10),
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
    )''')



    with open('data.csv', 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        # Accessing header names
        header = reader.fieldnames
        print(f"Header: {header}")

        # Iterating through rows as dictionaries
        for row in reader:
            print(row) # Each 'row' is a dictionary
            # Example: Accessing data by header name
            # print(f"Name: {row['Name']}, Age: {row['Age']}")
            query = f"""insert into Flight_reservation (PNR_Number, Customer_Name, Flight_ID, Airline, From_City, To_City,
    Departure_Time, Arrival_Time, Travel_Date, Booking_Date, Booking_Status, Refund_Status)
    values ("{row['PNR_Number']}", "{row['Customer_Name']}", "{row['Flight_ID']}", "{row['Airline']}", "{row['From_City']}", 
    "{row['To_City']}", "{row['Departure_Time']}", "{row['Arrival_Time']}", "{row['Travel_Date']}","{row['Booking_Date']}", 
    "{row['Booking_Status']}","{row['Refund_Status']}")"""
            
            print(f"=======\n {query}")
            cursor.execute(query);
            
    conn.commit()



# Create a table
# cursor.execute('''
#     CREATE TABLE IF NOT EXISTS users (
#         id INTEGER PRIMARY KEY,
#         name TEXT,
#         email TEXT
#     )
# ''')


#check if table exists

listOfTables = cursor.execute(
  """SELECT name FROM sqlite_master WHERE type='table'
  AND name='Flight_reservation'; """).fetchall()

if listOfTables == []:
    create_and_insert_Data(conn, cursor)
else:
    print('Table found!')



# Query data
def get_all_data(cursor):
    cursor.execute("SELECT * FROM Flight_reservation")
    for row in cursor.fetchall():
        print(row)

    # Close the connection
conn.close()

