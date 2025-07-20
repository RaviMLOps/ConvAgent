"""First, using the "From_City" and "To_City" in the "Flight_availability_and_schedule" table, 
        select only the "Flight_ID", "Airline", "Departure_Time","Arrival_Time",
        "seat_availability_status" and "price". 
        
        Once you receive the "Flight_ID", check the availability of seats in "seat_availability_status" in the 
        "Flight_availability_and_schedule" table.  If seats are closed, please do not generate query and 
        return to user that the seats are closed. """

"""#Once you receive all necessary information, please return
        #text in natural language requesting to book flight with 
        #all the information you received. """

"""import sqlite3
try:
    db_path = r'E:\ConvAgent\RAG_React_tool\database\sql_db\Flight_reservation.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    #query = "SELECT name FROM sqlite_master WHERE type='table';"
    #query = "SELECT * FROM FLIGHT_RESERVATION WHERE PNR_Number = 'AZ8339'"
    #query = "SELECT * FROM FLIGHT_RESERVATION LIMIT 5"
    #query = "SELECT * FROM FLIGHT_RESERVATION WHERE Customer_Name = 'Demetri'"
    #query = "PRAGMA table_info(FLIGHT_RESERVATION)"
    query = "SELECT * FROM FLIGHT_RESERVATION"
    print("sql_tool.py line 92: ", query)
    cursor.execute(query)
    result = cursor.fetchall()
    print("Result: ", result)
    conn.commit()
    conn.close()
except Exception as e:
    print(e)
"""
"""import psycopg2
import pandas as pd
#from sqlalchemy import create_engine

try:
    conn = psycopg2.connect(
        dbname = "Flight_reservation",
        user = "postgres",
        password = "XXXXXX!",
        host = "localhost",
        port = 5432
    )
    print("Connected!")
    conn.close()
    #data = pd.read_excel("E:\ConvAgent\RAG_React_tool\database\sql_db\data.csv")
    #for row in data:

except Exception as e:
    print(str(e))
"""
import psycopg2
import pandas as pd
from sqlalchemy import create_engine



#data = pd.read_csv("E:\ConvAgent\RAG_React_tool\database\sql_db\data.csv")
data = pd.read_csv("E:\ConvAgent_V0\RAG_React_tool\database\sql_db\Flight_availability_and_schedule.csv")
try:
    dbname = "Flight_reservation",
    user = "postgres",
    password = "XXXXXX",
    host = "13.200.143.143",
    port = 5432
    #conn_string = 'postgresql+psycopg2://postgres:XXXXXXX@13.200.143.143:5432/Flight_reservation'
    #engine = create_engine(conn_string)

    conn = psycopg2.connect(
                dbname = dbname,
                user = user,
                password = password,
                host = "13.200.143.143",
                port = port,
                )
    
    cursor = conn.cursor()
    query = f"""SELECT "Customer_Name" FROM "Flight_reservation" WHERE "PNR_Number" = "UUW15Y" """
    cursor.execute(query)
    results = cursor.fetchall()
    print(results)
    #print("Connected!")
    #data.to_sql('Flight_availability_and_schedule', con = conn, if_exists = 'replace', index = False)
    #print("data copied!")
    conn.commit()
    conn.close()
except Exception as e:
    print(str(e))
