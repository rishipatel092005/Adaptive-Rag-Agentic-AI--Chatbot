"""
Main FastAPI application entry point.
"""

from fastapi import FastAPI

from src.api.routes import router

app = FastAPI(title="Adaptive RAG API")
app.include_router(router)
app.state.description_ = ""


@app.get("/")
async def root():
    """Root endpoint to verify API is running."""
    return {"message": "Adaptive RAG API is running"}
