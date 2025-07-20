

from fastapi import FastAPI
from fastapi.responses import FileResponse
import uvicorn
import logging
from pathlib import Path
from uvicorn import Config, Server

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
# Configuration
GRADIO_BASE_URL = "http://13.200.143.143:7860"


app = FastAPI()

@app.get("/")
def serve_page():
   current_dir = Path(__file__).resolve()
   project_root = current_dir.parents[3] 
   file_path = project_root / "frontend_static" / "flight_booking_ui.html"
   if not file_path.exists():
        raise RuntimeError(f"File at path {file_path} does not exist.")
    
   return FileResponse(file_path)


def run__UI_fastapi():
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    logger.info("Launching fastAPI ")
    run__UI_fastapi() 
   
   



