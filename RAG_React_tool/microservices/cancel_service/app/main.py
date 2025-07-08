# reservation_service/app/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import sqlite3
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Cancel Service")

class QueryRequest(BaseModel):
    query: str

class HealthCheck(BaseModel):
    status: str

# Database configuration
DB_PATH = os.getenv("DB_PATH", "/data/flight_reservation.db")

def get_db_connection():
    """Create a database connection."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {str(e)}")
        raise

def init_db():
    """Initialize the database with required tables if they don't exist."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create Flight_reservation table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Flight_reservation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            PNR_Number TEXT UNIQUE NOT NULL,
            Passenger_Name TEXT NOT NULL,
            Flight_Number TEXT NOT NULL,
            Departure_Date TEXT NOT NULL,
            Booking_Status TEXT DEFAULT 'Confirmed',
            Refund_Status TEXT DEFAULT 'N/A',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create an index on PNR_Number for faster lookups
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_pnr ON Flight_reservation (PNR_Number)
        ''')
        
        conn.commit()
        logger.info("Database initialized successfully")
    except sqlite3.Error as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise
    finally:
        if conn:
            conn.close()

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    init_db()

@app.get("/health", response_model=HealthCheck)
async def health_check():
    return {"status": "ok"}

@app.post("/query")
async def query(request: QueryRequest):
    """Handle reservation-related queries."""
    try:
        query_lower = request.query.lower()
        
        if "status" in query_lower and "pnr" in query_lower:
            # Extract PNR from query (simplified - in production, use NLP)
            pnr = "".join([c for c in query_lower if c.isdigit() or c.isalpha()])
            return await get_reservation(pnr.upper())
            
        return {"result": "Please provide a valid reservation query with PNR number"}
        
    except Exception as e:
        logger.error(f"Error processing reservation query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reservations/{pnr}")
async def get_reservation(pnr: str):
    """Get reservation details by PNR."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM Flight_reservation WHERE PNR_Number = ?",
            (pnr,)
        )
        result = cursor.fetchone()
        
        if not result:
            return {"error": f"No reservation found for PNR: {pnr}"}
        
        # Convert Row to dict
        return dict(result)
        
    except sqlite3.Error as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)