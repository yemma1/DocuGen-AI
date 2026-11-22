import os
import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from config import (
    APP_NAME,
    APP_DESCRIPTION,
    APP_VERSION,
    FRONTEND_DIR,
    CORS_ORIGINS,
    HOST,
    PORT,
)
from app.routes.upload import router as upload_router
from app.routes.analysis import router as analysis_router
from app.routes.documentation import router as docs_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("docugen.main")

# Initialize FastAPI application
app = FastAPI(
    title=APP_NAME,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(upload_router)
app.include_router(analysis_router)
app.include_router(docs_router)

# Mount frontend static files
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

# Frontend Web Dashboard Routes
@app.get("/", summary="Web Dashboard", tags=["Frontend"])
async def serve_index():
    """Serve the primary DocuGen AI SaaS dashboard."""
    index_file = FRONTEND_DIR / "index.html"
    return FileResponse(str(index_file))

@app.get("/dashboard", summary="Dashboard View", tags=["Frontend"])
async def serve_dashboard():
    """Serve the dashboard view."""
    dash_file = FRONTEND_DIR / "dashboard.html"
    if dash_file.exists():
        return FileResponse(str(dash_file))
    return FileResponse(str(FRONTEND_DIR / "index.html"))

@app.get("/results", summary="Results View", tags=["Frontend"])
async def serve_results():
    """Serve the results view."""
    results_file = FRONTEND_DIR / "results.html"
    if results_file.exists():
        return FileResponse(str(results_file))
    return FileResponse(str(FRONTEND_DIR / "index.html"))

@app.get("/about", summary="About View", tags=["Frontend"])
async def serve_about():
    """Serve the about view."""
    about_file = FRONTEND_DIR / "about.html"
    if about_file.exists():
        return FileResponse(str(about_file))
    return FileResponse(str(FRONTEND_DIR / "index.html"))

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting {APP_NAME} on http://{HOST}:{PORT}")
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)
