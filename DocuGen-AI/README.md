# DocuGen AI ⚡
> **Professional Python Code Documentation Generator** powered by FastAPI, Python AST Static Code Analysis, and an Intelligent Plain-English Explanation Engine.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688.svg?style=flat&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg?style=flat&logo=Python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Swagger](https://img.shields.io/badge/API_Docs-Swagger_UI-85EA2D.svg?logo=Swagger&logoColor=black)](http://127.0.0.1:8000/docs)

---

## 📖 Table of Contents
1. [Project Overview](#1-project-overview)
2. [Key Features](#2-key-features)
3. [Technology Stack](#3-technology-stack)
4. [Application Architecture](#4-application-architecture)
5. [Folder Structure](#5-folder-structure)
6. [Windows Installation Guide](#6-windows-installation-guide)
7. [Running the Application](#7-running-the-application)
8. [API Endpoint Documentation](#8-api-endpoint-documentation)
9. [Swagger UI Usage](#9-swagger-ui-usage)
10. [End-to-End Workflow](#10-end-to-end-workflow)
11. [Automated Testing Suite](#11-automated-testing-suite)
12. [Security Features](#12-security-features)
13. [Future Enhancements](#13-future-enhancements)

---

## 1. Project Overview

**DocuGen AI** is a production-ready, full-stack developer tooling application built to automatically analyze Python source files and generate clean, standardized, beginner-friendly Markdown technical documentation.

Unlike runtime inspection tools that execute untrusted code (such as `inspect` or `pydoc`), DocuGen AI parses source code into an **Abstract Syntax Tree (AST)** using Python's built-in `ast` module. This guarantees **zero code execution**, eliminating sandbox escape risks and making it 100% safe to inspect arbitrary Python files.

### Why DocuGen AI?
- **Zero Runtime Risk:** Analyzes uploaded Python scripts without ever importing or executing them.
- **Rule-Based by Default:** Works completely offline without paid API keys, while offering optional OpenAI integration for augmented summaries.
- **10-Section Standardized Output:** Generates structured Markdown documentation with tables, hierarchy trees, and explanations.
- **Modern SaaS Dashboard:** Clean white and light-blue design with real-time statistics, drag-and-drop file upload, and dual-tab Markdown preview.

---

## 2. Key Features

- **Drag-and-Drop File Upload:** Secure upload accepting `.py` files up to 5 MB with instant validation.
- **AST Static Code Analysis:**
  - Extracts standalone functions, async functions, and class methods.
  - Resolves parameter contracts (positional-only, positional/keyword, `*args`, keyword-only, `**kwargs`, and mapped default values).
  - Captures return type annotations and detects AST `return` statements.
  - Identifies class definitions, inheritance hierarchies, constructor signatures (`__init__`), and nested classes.
  - Parses module-level imports, symbols, aliases, and maps standard library purposes.
  - Identifies module-level global variables and type annotations.
- **Syntax Validation:** Catches `SyntaxError` with line numbers, columns, and code snippets without crashing.
- **Simple English Explanation Engine:** Translates snake_case identifiers, docstrings, parameters, and AST structures into clear, beginner-friendly English explanations.
- **Markdown Documentation Generator:** Produces 10 structured sections:
  1. *File Overview*
  2. *General Information*
  3. *Code Summary*
  4. *Function Documentation*
  5. *Class Documentation*
  6. *Parameters and Return Values*
  7. *Imports and Dependencies*
  8. *Code Structure (Visual Hierarchy Tree)*
  9. *Simple English Explanation*
  10. *Code Analysis Summary*
- **Interactive Markdown Preview & Download:** View styled HTML documentation or copy raw Markdown with one click, or download `.md` files directly.
- **Interactive Swagger Documentation:** Built-in interactive API playground at `/docs`.

---

## 3. Technology Stack

### Backend
- **Python 3.11+**
- **FastAPI:** High-performance, modern web framework for building APIs.
- **Uvicorn:** Blazing fast ASGI server.
- **Pydantic v2:** Robust data validation, schemas, and serialization.
- **Python AST Module (`ast`):** Static code parsing without runtime code execution.
- **Python Pathlib & Logging:** Cross-platform path management and structured logging.

### Frontend
- **HTML5 & CSS3:** Custom SaaS theme with white and light-blue palette, rounded cards (`border-radius: 14px`), and soft shadows.
- **Vanilla ES6 JavaScript:** Reactive UI state, drag-and-drop file upload, dynamic API data binding, and clipboard actions.
- **Bootstrap Icons:** Clean, professional iconography.

### API & Testing
- **RESTful Architecture:** JSON response contracts, status codes, and error models.
- **OpenAPI 3.1 & Swagger UI:** Automated interactive documentation.
- **Pytest & FastAPI TestClient (`httpx`):** Comprehensive automated test coverage.

---

## 4. Application Architecture

```
                  ┌──────────────────────────────────────────────┐
                  │          Client Browser (Frontend)           │
                  │  Modern SaaS Dashboard (HTML5 / CSS3 / JS)   │
                  └──────────────┬───────────────────────────────┘
                                 │ HTTP / JSON / Multipart
                                 ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        FastAPI Backend Engine                          │
│                                                                        │
│  ┌────────────────────┐ ┌────────────────────┐ ┌────────────────────┐  │
│  │   Upload Router    │ │  Analysis Router   │ │Documentation Router│  │
│  │  POST /api/upload  │ │ POST /api/analyze  │ │  GET /api/download │  │
│  └─────────┬──────────┘ └─────────┬──────────┘ └─────────┬──────────┘  │
│            │                      │                      │             │
│            ▼                      ▼                      ▼             │
│  ┌────────────────────┐ ┌────────────────────┐ ┌────────────────────┐  │
│  │    File Handler    │ │ Python AST Engine  │ │ Markdown Generator │  │
│  │ (Sanitize/Storage) │ │ (Safe Static Parse)│ │(10 Structured Secs)│  │
│  └─────────┬──────────┘ └─────────┬──────────┘ └─────────┬──────────┘  │
│            │                      │                      │             │
│            ▼                      ▼                      ▼             │
│  ┌────────────────────┐ ┌────────────────────┐ ┌────────────────────┐  │
│  │   uploads/ &       │ │ Explanation Engine │ │  generated_docs/   │  │
│  │   metadata.json    │ │(Rule-Based/OpenAI) │ │    (.md Files)     │  │
│  └────────────────────┘ └────────────────────┘ └────────────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Folder Structure

```
DocuGen-AI/
│
├── main.py                     # FastAPI application entrypoint & static mounts
├── config.py                   # Centralized configuration & environment settings
├── requirements.txt            # Python dependencies
├── .env                        # Local environment variables
├── .env.example                # Example environment variables template
├── .gitignore                  # Git ignore rules for virtualenvs, cache & logs
├── README.md                   # Complete project documentation
│
├── app/
│   ├── __init__.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── upload.py           # File upload endpoint & validation
│   │   ├── analysis.py         # AST analysis & results endpoints
│   │   └── documentation.py    # Markdown preview, download & file management
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── analyzer.py         # Python AST Static Analysis Engine
│   │   ├── explanation_engine.py # Rule-based & AI English explanation engine
│   │   └── documentation_generator.py # 10-Section Markdown generator
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py          # Pydantic schemas for request/response validation
│   │
│   └── utils/
│       ├── __init__.py
│       └── file_handler.py     # Secure file storage, sanitization & metadata
│
├── frontend/
│   ├── index.html              # Primary SaaS Dashboard single-page application
│   ├── dashboard.html          # Dashboard route redirector
│   ├── results.html            # Results route redirector
│   ├── about.html              # About route redirector
│   ├── css/
│   │   └── style.css           # White & light-blue SaaS design system
│   └── js/
│       └── script.js           # Client-side state, API calls & markdown viewer
│
├── uploads/                    # Secure storage directory for uploaded files
├── generated_docs/             # Storage for generated .md documentation
│
└── tests/
    ├── test_analyzer.py        # Unit tests for AST parsing & explanation engine
    ├── test_api.py             # Integration tests for FastAPI endpoints
    └── sample.py               # Comprehensive Python code sample for testing
```

---

## 6. Windows Installation Guide

Follow these steps to set up DocuGen AI on **Windows 10 / 11**:

### Step 1: Open Terminal
Open **PowerShell** or **Command Prompt** and navigate to your project directory:
```powershell
cd C:\Users\<YourUsername>\... \DocuGen-AI
```

### Step 2: Create a Virtual Environment
```powershell
python -m venv venv
```

### Step 3: Activate the Virtual Environment
```powershell
# On Windows PowerShell:
venv\Scripts\Activate.ps1

# Or on Command Prompt (CMD):
venv\Scripts\activate.bat
```
*(If PowerShell shows an execution policy error, run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` once).*

### Step 4: Install Dependencies
```powershell
pip install -r requirements.txt
```

---

## 7. Running the Application

### Start the FastAPI Server
With your virtual environment active, run:
```powershell
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### Access the Application
- **Web Dashboard:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Documentation:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 8. API Endpoint Documentation

| Method | Endpoint | Description | Request Body | Response |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/` | Serves the web dashboard UI | None | HTML |
| `POST` | `/api/upload` | Upload & validate Python source file | `multipart/form-data` (`file`) | `FileUploadResponse` (JSON) |
| `POST` | `/api/analyze/{file_id}` | Run AST analysis & generate docs | None | `AnalysisResult` (JSON) |
| `GET` | `/api/results/{file_id}` | Get cached AST analysis results | None | `AnalysisResult` (JSON) |
| `GET` | `/api/documentation/{file_id}`| Get Markdown documentation text | None | `DocumentationResponse` (JSON) |
| `GET` | `/api/download/{file_id}` | Download generated `.md` file | None | `.md` File attachment |
| `GET` | `/api/files` | List uploaded files & metadata | None | `List[FileRecord]` (JSON) |
| `DELETE`| `/api/files/{file_id}` | Delete file & its documentation | None | JSON confirmation |
| `GET` | `/api/health` | System health & status check | None | `HealthResponse` (JSON) |

---

## 9. Swagger UI Usage

FastAPI automatically produces an OpenAPI specification accessible directly in the browser:
1. Navigate to [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).
2. Expand the `POST /api/upload` endpoint, click **Try it out**, select any `.py` file, and click **Execute**.
3. Copy the returned `file_id`.
4. Expand `POST /api/analyze/{file_id}`, paste the `file_id`, and click **Execute** to view the structured JSON analysis.
5. Expand `GET /api/download/{file_id}` and click **Execute** to download the Markdown document directly through Swagger!

---

## 10. End-to-End Workflow

1. **Upload:**
   - Drag and drop any `.py` file into the upload zone or click **Try Sample File** for an instant demo.
   - The system checks that the extension is `.py`, the file size is under 5 MB, and the file is not empty.
2. **Static AST Analysis:**
   - The backend parses the Python file into an Abstract Syntax Tree.
   - Functions, parameters (positional, keyword, `*args`, `**kwargs`), return types, classes, methods, imports, and global variables are identified.
3. **Simple English Explanation:**
   - The explanation engine analyzes function names, docstrings, and signatures to generate beginner-friendly explanations.
4. **Markdown Generation:**
   - All 10 documentation sections are compiled and saved to `generated_docs/<file_id>_doc.md`.
5. **Preview & Export:**
   - View rendered Markdown or raw Markdown with code formatting.
   - Click **Download Markdown (.md)** or **Copy to Clipboard**.

---

## 11. Automated Testing Suite

The project includes unit and integration tests covering all 14 mandatory test areas:
1. File upload
2. Function extraction
3. Class extraction
4. Parameter extraction
5. Return annotation extraction
6. Import extraction
7. Nested functions
8. Class inheritance
9. Invalid Python syntax handling
10. Empty file rejection
11. Invalid file extension rejection
12. Markdown documentation generation
13. FastAPI REST endpoints
14. File download

### Run Tests
```powershell
# Run the complete test suite
pytest -v
```

---

## 12. Security Features

- **No Code Execution:** Uses Python's built-in `ast` module; source files are parsed into tokens and node graphs without ever executing them.
- **File Sanitization:** File names are stripped of directory traversal characters (`..`, `/`, `\`, null bytes) and isolated using UUID prefixes.
- **Upload Restrictions:** Enforces a 5 MB maximum file size limit and accepts only `.py` extensions. Empty files (0 bytes) are rejected immediately.
- **API Key Isolation:** Any optional OpenAI API keys are kept strictly on the backend via environment variables and never exposed to the frontend.

---

## 13. Future Enhancements

- [ ] Export to PDF and HTML formats.
- [ ] Support multi-file Python packages and folder uploads (ZIP extraction).
- [ ] Interactive Mermaid class and dependency diagram generation.
- [ ] Database migration support (SQLite / PostgreSQL) via SQLAlchemy models.
- [ ] Automated docstring insertion tool to push generated docstrings back into the source file.

---

## 📄 License
This project is open-source under the MIT License. Developed for software engineering portfolios and technical interviews.
