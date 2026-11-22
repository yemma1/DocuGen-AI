import logging
from typing import List
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from config import APP_NAME, APP_VERSION, OPENAI_API_KEY
from app.models.schemas import (
    DocumentationResponse,
    FileRecord,
    HealthResponse,
)
from app.utils.file_handler import (
    get_metadata,
    get_doc_path,
    list_all_files,
    delete_file,
)

logger = logging.getLogger("docugen.routes.docs")

router = APIRouter(prefix="/api", tags=["Documentation & Files"])

@router.get(
    "/documentation/{file_id}",
    response_model=DocumentationResponse,
    summary="Get Generated Documentation",
    description="Retrieve generated Markdown documentation content as text.",
)
async def get_documentation(file_id: str):
    """Return generated Markdown documentation content for previewing."""
    meta = get_metadata(file_id)
    if not meta:
        raise HTTPException(status_code=404, detail=f"File with ID '{file_id}' not found.")

    doc_path = get_doc_path(file_id)
    if not doc_path or not doc_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Documentation has not been generated yet for file '{file_id}'. Please analyze the file first.",
        )

    try:
        with open(doc_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        logger.error(f"Error reading documentation file {doc_path}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to read documentation file: {str(e)}")

    return DocumentationResponse(
        file_id=file_id,
        filename=meta["filename"],
        markdown_content=content,
        download_url=f"/api/download/{file_id}",
        generated_at=meta.get("uploaded_at", ""),
    )

@router.get(
    "/download/{file_id}",
    summary="Download Markdown Documentation",
    description="Download the generated Markdown (.md) documentation file directly.",
)
async def download_documentation(file_id: str):
    """Serve the generated .md file as a downloadable file attachment."""
    meta = get_metadata(file_id)
    if not meta:
        raise HTTPException(status_code=404, detail=f"File with ID '{file_id}' not found.")

    doc_path = get_doc_path(file_id)
    if not doc_path or not doc_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Documentation file for '{file_id}' does not exist on disk. Please analyze the file first.",
        )

    base_name = meta["filename"].replace(".py", "")
    download_filename = f"{base_name}_documentation.md"

    return FileResponse(
        path=str(doc_path),
        filename=download_filename,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{download_filename}"'},
    )

@router.get(
    "/files",
    response_model=List[FileRecord],
    summary="List Uploaded Files",
    description="Retrieve metadata list of all uploaded Python source files and their analysis statuses.",
)
async def list_files():
    """Return list of all uploaded files with their metadata and analysis states."""
    records = list_all_files()
    return [FileRecord(**rec) for rec in records]

@router.delete(
    "/files/{file_id}",
    summary="Delete File",
    description="Permanently delete an uploaded Python file and its generated documentation.",
)
async def remove_file(file_id: str):
    """Delete uploaded Python source file, generated markdown, and metadata entry."""
    meta = get_metadata(file_id)
    if not meta:
        raise HTTPException(status_code=404, detail=f"File with ID '{file_id}' not found.")

    success = delete_file(file_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete file from disk.")

    return {
        "status": "success",
        "file_id": file_id,
        "message": f"File '{meta['filename']}' and its associated documentation were deleted successfully.",
    }

@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Status",
    description="Return system health status and configuration details.",
)
async def health_check():
    """Check API health, version, and AI availability status."""
    return HealthResponse(
        status="healthy",
        app_name=APP_NAME,
        version=APP_VERSION,
        ai_enabled=bool(OPENAI_API_KEY.strip()),
    )
