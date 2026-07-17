"""WSGI entry point for PythonAnywhere deployment"""
import sys
from pathlib import Path

# Add backend directory to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

# Import the FastAPI app
from app.main import app as application

# For local testing
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(application, host="0.0.0.0", port=8000)
