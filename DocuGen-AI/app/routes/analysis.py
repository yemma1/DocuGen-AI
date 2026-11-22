import logging
import ast
from datetime import datetime
from fastapi import APIRouter, HTTPException

from app.models.schemas import AnalysisResult
from app.utils.file_handler import (
    get_file_path,
    get_metadata,
    update_metadata,
    save_analysis_result,
    get_analysis_result,
)
from app.services.analyzer import PythonCodeAnalyzer
from app.services.explanation_engine import ExplanationEngine
from app.services.documentation_generator import MarkdownDocumentationGenerator

logger = logging.getLogger("docugen.routes.analysis")

router = APIRouter(prefix="/api", tags=["Code Analysis"])

@router.post(
    "/analyze/{file_id}",
    response_model=AnalysisResult,
    summary="Analyze Python Source File",
    description="Perform AST static code analysis, generate explanations and documentation.",
)
async def analyze_file(file_id: str):
    """
    Execute AST static analysis on uploaded Python file:
    - Validates Python syntax without code execution
    - Extracts functions, methods, parameters, and return types
    - Extracts classes, constructors, and inheritance
    - Extracts imports, global variables, and line metrics
    - Generates simple English explanations
    - Generates full 10-section Markdown documentation
    """
    meta = get_metadata(file_id)
    if not meta:
        raise HTTPException(status_code=404, detail=f"File with ID '{file_id}' not found.")

    file_path = get_file_path(file_id)
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=404, detail="Underlying source file not found on disk.")

    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            source_code = f.read()
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise HTTPException(status_code=500, detail=f"Could not read source file: {str(e)}")

    # 1. Run AST Static Analyzer
    analyzer = PythonCodeAnalyzer(source_code=source_code, filename=meta["filename"])
    analysis_data = analyzer.analyze()

    # Extract top-level docstring if present
    top_docstring = None
    try:
        parsed_tree = ast.parse(source_code)
        top_docstring = ast.get_docstring(parsed_tree)
    except Exception:
        pass

    # 2. Run Explanation Engine
    explainer = ExplanationEngine(use_ai=True)
    explanation = explainer.explain(
        filename=meta["filename"],
        metrics=analysis_data["metrics"],
        functions=analysis_data["functions"],
        classes=analysis_data["classes"],
        imports=analysis_data["imports"],
        source_code=source_code,
        top_docstring=top_docstring,
    )

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 3. Assemble Analysis Result
    result = AnalysisResult(
        file_id=file_id,
        filename=meta["filename"],
        file_size_bytes=meta["file_size_bytes"],
        file_size_formatted=meta["file_size_formatted"],
        analyzed_at=now_str,
        syntax=analysis_data["syntax"],
        metrics=analysis_data["metrics"],
        functions=analysis_data["functions"],
        classes=analysis_data["classes"],
        imports=analysis_data["imports"],
        global_variables=analysis_data["global_variables"],
        explanation=explanation,
    )

    # 4. Generate and Save Markdown Documentation
    doc_gen = MarkdownDocumentationGenerator(result)
    doc_gen.save(file_id)

    # 5. Persist Results & Update Metadata
    save_analysis_result(file_id, result.model_dump())
    update_metadata(
        file_id,
        {
            "is_analyzed": True,
            "has_doc": True,
            "syntax_valid": analysis_data["syntax"].is_valid,
            "metrics": analysis_data["metrics"].model_dump(),
        },
    )

    logger.info(f"Analysis completed successfully for {meta['filename']} (ID: {file_id})")
    return result

@router.get(
    "/results/{file_id}",
    response_model=AnalysisResult,
    summary="Get Analysis Results",
    description="Retrieve cached AST static code analysis results for a given file ID.",
)
async def get_results(file_id: str):
    """Retrieve previously generated analysis results in JSON format."""
    meta = get_metadata(file_id)
    if not meta:
        raise HTTPException(status_code=404, detail=f"File with ID '{file_id}' not found.")

    cached = get_analysis_result(file_id)
    if not cached:
        raise HTTPException(
            status_code=404,
            detail=f"Analysis results for file '{file_id}' have not been generated yet. Please call POST /api/analyze/{file_id} first.",
        )

    return AnalysisResult(**cached)
