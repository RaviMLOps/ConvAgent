from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
import os
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Cancel Service")

class QueryRequest(BaseModel):
    query: str

class HealthCheck(BaseModel):
    status: str

# Database config from env
DB_HOST = os.getenv("PG_HOST", "localhost")
DB_PORT = int(os.getenv("PG_PORT", "5432"))
DB_NAME = os.getenv("PG_DB", "postgres")
DB_USER = os.getenv("PG_USER", "postgres")
DB_PASS = os.getenv("PG_PASSWORD", "")

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
        )
        return conn
    except psycopg2.Error as e:
        logger.error(f"Database connection error: {str(e)}")
        raise

def extract_pnr(query: str) -> str:
    """Extract PNR from the query using regex after 'pnr' (case-insensitive)."""
    match = re.search(r"pnr[\s:]*([A-Za-z0-9]+)", query, re.IGNORECASE)
    if match:
        return match.group(1)
    return ""

@app.get("/health", response_model=HealthCheck)
async def health_check():
    return {"status": "ok"}

@app.post("/query")
async def query(request: QueryRequest):
    """Handle reservation-related queries."""
    try:
        query_text = request.query

        if "status" in query_text.lower() and "pnr" in query_text.lower():
            pnr = extract_pnr(query_text)
            if not pnr:
                return {"error": "PNR not found in the query."}
            return await get_reservation(pnr)

        if "cancel" in query_text.lower() and "pnr" in query_text.lower():
            pnr = extract_pnr(query_text)
            if not pnr:
                return {"error": "PNR not found in the query."}
            return await cancel_reservation(pnr)

        return {"result": "Please provide a valid reservation query with PNR number"}

    except Exception as e:
        logger.error(f"Error processing reservation query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reservations/{pnr}")
async def get_reservation(pnr: str):
    """Get reservation details by PNR."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM "Flight_reservation" WHERE UPPER("PNR_Number") = %s', (pnr.upper(),))
        result = cursor.fetchone()
        colnames = [desc[0] for desc in cursor.description] if cursor.description else []
        if not result:
            return {"error": f"No reservation found for PNR: {pnr}"}
        return dict(zip(colnames, result))
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        if conn:
            conn.close()

@app.post("/cancel/{pnr}")
async def cancel_reservation(pnr: str):
    """Cancel reservation by PNR."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT "Booking_Status", "Refund_Status" FROM "Flight_reservation" WHERE UPPER("PNR_Number") = %s', (pnr.upper(),))
        row = cursor.fetchone()
        if not row:
            return {"error": f"No reservation found for PNR: {pnr}"}
        if row[0].lower() == "cancelled":
            return {"message": "Reservation already cancelled", "refund_status": row[1]}
        # Update the status
        cursor.execute(
            'UPDATE "Flight_reservation" SET "Booking_Status" = %s, "Refund_Status" = %s WHERE UPPER("PNR_Number") = %s',
            ("Cancelled", "Refunded", pnr.upper())
        )
        conn.commit()
        return {"message": "Reservation cancelled", "pnr": pnr, "refund_status": "Refunded"}
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
