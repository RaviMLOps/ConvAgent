

import psycopg2
from config import Config

conn = psycopg2.connect(
    dbname = Config.pg_dbname,
    user = Config.pg_user,
    password = Config.pg_password,
    host = Config.pg_host,
    port = Config.pg_port,
    )

query = """SELECT * FROM "Flight_reservation" WHERE "PNR_Number"='S9VD2P';"""
cursor = conn.cursor()
cursor.execute(query)

results = cursor.fetchall()

print(results)