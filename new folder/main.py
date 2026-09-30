"""LegalEase - FastAPI Main Application.

Entry point for the backend REST API server.
"""

import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from routes import router

load_dotenv()

app = FastAPI(
    title="LegalEase – AI-Powered Legal Document Generator",
    description="REST API for generating, previewing, and exporting formal legal contracts with Google Gemini.",
    version="1.0.0",
)

# Enable CORS for local Streamlit frontend and external access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)


@app.get("/")
def root():
    """Health and status check endpoint."""
    return {
        "status": "ok",
        "application": "LegalEase",
        "version": "1.0.0",
        "docs_url": "/docs",
    }


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host=host, port=port, reload=True)
