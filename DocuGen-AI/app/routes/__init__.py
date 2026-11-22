from app.routes.upload import router as upload_router
from app.routes.analysis import router as analysis_router
from app.routes.documentation import router as docs_router

__all__ = ["upload_router", "analysis_router", "docs_router"]
