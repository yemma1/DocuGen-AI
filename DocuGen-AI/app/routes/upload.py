import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.models.schemas import FileUploadResponse
from app.utils.file_handler import save_upload_file

logger = logging.getLogger("docugen.routes.upload")

router = APIRouter(prefix="/api", tags=["File Upload"])

@router.post(
    "/upload",
    response_model=FileUploadResponse,
    summary="Upload Python File",
    description="Upload a Python (.py) source file for static AST code analysis. Max size: 5MB.",
)
async def upload_file(file: UploadFile = File(...)):
    """
    Handle Python file upload with strict validation:
    - Enforces .py file extension
    - Rejects empty files (0 bytes)
    - Rejects files exceeding 5MB
    - Sanitizes filename to prevent directory traversal
    """
    try:
        record = await save_upload_file(file)
        return FileUploadResponse(
            file_id=record["file_id"],
            filename=record["filename"],
            file_size_bytes=record["file_size_bytes"],
            file_size_formatted=record["file_size_formatted"],
            uploaded_at=record["uploaded_at"],
            status="success",
            message=f"File '{record['filename']}' successfully uploaded and validated.",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during file upload: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process file upload: {str(e)}")
