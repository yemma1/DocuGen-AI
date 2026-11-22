import os
import re
import json
import uuid
import shutil
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import UploadFile, HTTPException

from config import UPLOAD_DIR, DOCS_DIR, METADATA_FILE, MAX_UPLOAD_SIZE, ALLOWED_EXTENSIONS

logger = logging.getLogger("docugen.file_handler")

def format_bytes(size_bytes: int) -> str:
    """Format bytes into human-readable string (B, KB, MB)."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal and invalid characters.
    Ensures safe storage on any operating system.
    """
    if not filename:
        return "unnamed.py"
    # Take basename
    base = os.path.basename(filename)
    # Remove path traversal characters and replace strange chars
    sanitized = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", base)
    if not sanitized.lower().endswith(".py"):
        sanitized += ".py"
    return sanitized

def _load_metadata() -> Dict[str, Any]:
    """Load metadata registry from JSON file safely."""
    if not METADATA_FILE.exists():
        return {}
    try:
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading metadata JSON: {e}")
        return {}

def _save_metadata(data: Dict[str, Any]) -> None:
    """Save metadata registry to JSON file atomically."""
    try:
        temp_file = METADATA_FILE.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        temp_file.replace(METADATA_FILE)
    except Exception as e:
        logger.error(f"Error saving metadata JSON: {e}")

async def save_upload_file(upload_file: UploadFile) -> Dict[str, Any]:
    """
    Validate, sanitize, and save an uploaded Python file.
    Enforces extension check, empty file rejection, and 5MB size limit.
    """
    original_filename = upload_file.filename or "script.py"
    sanitized = sanitize_filename(original_filename)

    # Validate extension
    file_ext = Path(sanitized).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file extension '{file_ext}'. Only Python (.py) source files are accepted."
        )

    # Read content to validate size and empty status
    content = await upload_file.read()
    file_size = len(content)

    if file_size == 0:
        raise HTTPException(
            status_code=400,
            detail="The uploaded Python file is empty (0 bytes). Please upload a valid source file."
        )

    if file_size > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum allowed size of {format_bytes(MAX_UPLOAD_SIZE)}."
        )

    # Generate unique file ID
    file_id = uuid.uuid4().hex[:12]
    saved_filename = f"{file_id}_{sanitized}"
    file_path = UPLOAD_DIR / saved_filename

    # Write file securely to disk
    with open(file_path, "wb") as f:
        f.write(content)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    record = {
        "file_id": file_id,
        "filename": sanitized,
        "saved_filename": saved_filename,
        "file_size_bytes": file_size,
        "file_size_formatted": format_bytes(file_size),
        "uploaded_at": timestamp,
        "is_analyzed": False,
        "has_doc": False,
        "syntax_valid": None,
        "metrics": None,
    }

    metadata = _load_metadata()
    metadata[file_id] = record
    _save_metadata(metadata)

    logger.info(f"Saved file {sanitized} (ID: {file_id}, Size: {format_bytes(file_size)})")
    return record

def get_file_path(file_id: str) -> Optional[Path]:
    """Retrieve Path object for uploaded Python file given file_id."""
    meta = get_metadata(file_id)
    if not meta:
        return None
    file_path = UPLOAD_DIR / meta.get("saved_filename", "")
    return file_path if file_path.exists() else None

def get_doc_path(file_id: str) -> Optional[Path]:
    """Retrieve Path object for generated Markdown documentation."""
    doc_path = DOCS_DIR / f"{file_id}_doc.md"
    return doc_path if doc_path.exists() else None

def get_metadata(file_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve metadata entry for given file_id."""
    metadata = _load_metadata()
    return metadata.get(file_id)

def list_all_files() -> List[Dict[str, Any]]:
    """Return all uploaded file records ordered by uploaded_at descending."""
    metadata = _load_metadata()
    records = list(metadata.values())
    records.sort(key=lambda x: x.get("uploaded_at", ""), reverse=True)
    return records

def update_metadata(file_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update fields in the metadata record for file_id."""
    metadata = _load_metadata()
    if file_id not in metadata:
        return None
    metadata[file_id].update(updates)
    _save_metadata(metadata)
    return metadata[file_id]

def delete_file(file_id: str) -> bool:
    """Delete uploaded Python file, generated markdown, results, and metadata."""
    metadata = _load_metadata()
    if file_id not in metadata:
        return False

    record = metadata.pop(file_id)
    _save_metadata(metadata)

    # Delete source file
    src_file = UPLOAD_DIR / record.get("saved_filename", "")
    if src_file.exists():
        try:
            src_file.unlink()
        except Exception as e:
            logger.warning(f"Failed to unlink source file {src_file}: {e}")

    # Delete generated documentation
    doc_file = DOCS_DIR / f"{file_id}_doc.md"
    if doc_file.exists():
        try:
            doc_file.unlink()
        except Exception as e:
            logger.warning(f"Failed to unlink doc file {doc_file}: {e}")

    # Delete cached analysis json if exists
    results_file = UPLOAD_DIR / f"{file_id}_results.json"
    if results_file.exists():
        try:
            results_file.unlink()
        except Exception as e:
            logger.warning(f"Failed to unlink results file {results_file}: {e}")

    logger.info(f"Deleted file record and assets for file_id: {file_id}")
    return True

def save_analysis_result(file_id: str, analysis_dict: Dict[str, Any]) -> None:
    """Cache the analysis result dictionary as JSON in uploads directory."""
    results_file = UPLOAD_DIR / f"{file_id}_results.json"
    try:
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(analysis_dict, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error saving analysis result for {file_id}: {e}")

def get_analysis_result(file_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve cached analysis result dictionary for file_id."""
    results_file = UPLOAD_DIR / f"{file_id}_results.json"
    if not results_file.exists():
        return None
    try:
        with open(results_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading analysis result for {file_id}: {e}")
        return None
