import io
from fastapi.testclient import TestClient
try:
    import pytest
except ImportError:
    pytest = None

from main import app

client = TestClient(app)

SAMPLE_PYTHON_CONTENT = b"""
def greet(name: str = 'World') -> str:
    \"\"\"Greet a user.\"\"\"
    return f"Hello, {name}!"
"""

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app_name"] == "DocuGen AI"

def test_upload_empty_file():
    file_bytes = io.BytesIO(b"")
    response = client.post(
        "/api/upload",
        files={"file": ("empty.py", file_bytes, "text/x-python")},
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()

def test_upload_invalid_extension():
    file_bytes = io.BytesIO(b"some content")
    response = client.post(
        "/api/upload",
        files={"file": ("document.txt", file_bytes, "text/plain")},
    )
    assert response.status_code == 400
    assert "Invalid file extension" in response.json()["detail"]

def test_full_workflow_upload_analyze_doc_download_delete():
    # 1. Upload valid Python file
    file_bytes = io.BytesIO(SAMPLE_PYTHON_CONTENT)
    upload_res = client.post(
        "/api/upload",
        files={"file": ("greeter.py", file_bytes, "text/x-python")},
    )
    assert upload_res.status_code == 200
    upload_data = upload_res.json()
    assert upload_data["status"] == "success"
    file_id = upload_data["file_id"]
    assert file_id is not None
    assert upload_data["filename"] == "greeter.py"

    # 2. List files
    list_res = client.get("/api/files")
    assert list_res.status_code == 200
    files = list_res.json()
    assert any(f["file_id"] == file_id for f in files)

    # 3. Analyze file
    analyze_res = client.post(f"/api/analyze/{file_id}")
    assert analyze_res.status_code == 200
    analysis = analyze_res.json()
    assert analysis["file_id"] == file_id
    assert analysis["syntax"]["is_valid"] is True
    assert len(analysis["functions"]) == 1
    assert analysis["functions"][0]["name"] == "greet"

    # 4. Get cached results
    results_res = client.get(f"/api/results/{file_id}")
    assert results_res.status_code == 200
    assert results_res.json()["file_id"] == file_id

    # 5. Get documentation content
    doc_res = client.get(f"/api/documentation/{file_id}")
    assert doc_res.status_code == 200
    doc_data = doc_res.json()
    assert "## 1. File Overview" in doc_data["markdown_content"]
    assert "## 4. Function Documentation" in doc_data["markdown_content"]

    # 6. Download documentation
    download_res = client.get(f"/api/download/{file_id}")
    assert download_res.status_code == 200
    assert "text/markdown" in download_res.headers.get("content-type", "")
    assert b"# Python Code Documentation" in download_res.content

    # 7. Delete file and verify cleanup
    del_res = client.delete(f"/api/files/{file_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "success"

    # 8. Verify 404 after deletion
    after_del_res = client.get(f"/api/results/{file_id}")
    assert after_del_res.status_code == 404
