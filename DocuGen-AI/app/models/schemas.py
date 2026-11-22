from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ParameterInfo(BaseModel):
    name: str
    type_annotation: Optional[str] = None
    default_value: Optional[str] = None
    kind: str = "positional_or_keyword"  # positional_only, positional_or_keyword, var_positional, keyword_only, var_keyword
    description: Optional[str] = None

class FunctionInfo(BaseModel):
    name: str
    parameters: List[ParameterInfo] = []
    return_annotation: Optional[str] = None
    detected_returns: List[str] = []
    docstring: Optional[str] = None
    decorators: List[str] = []
    line_start: int
    line_end: int
    is_async: bool = False
    is_method: bool = False
    parent_class: Optional[str] = None
    nested_functions: List[str] = []
    explanation: Optional[str] = None

class ClassInfo(BaseModel):
    name: str
    bases: List[str] = []
    docstring: Optional[str] = None
    decorators: List[str] = []
    line_start: int
    line_end: int
    methods: List[FunctionInfo] = []
    constructor: Optional[FunctionInfo] = None
    nested_classes: List[str] = []
    explanation: Optional[str] = None

class ImportInfo(BaseModel):
    module: str
    imported_names: List[str] = []
    alias: Optional[str] = None
    lineno: int
    is_from: bool = False
    purpose: Optional[str] = None

class GlobalVariableInfo(BaseModel):
    name: str
    type_annotation: Optional[str] = None
    value_preview: Optional[str] = None
    lineno: int

class CodeMetrics(BaseModel):
    total_lines: int = 0
    code_lines: int = 0
    blank_lines: int = 0
    comment_lines: int = 0
    total_functions: int = 0
    total_classes: int = 0
    total_imports: int = 0
    total_globals: int = 0

class SyntaxValidation(BaseModel):
    is_valid: bool
    error_message: Optional[str] = None
    error_line: Optional[int] = None
    error_column: Optional[int] = None
    error_text: Optional[str] = None

class CodeExplanation(BaseModel):
    module_summary: str = ""
    function_explanations: Dict[str, str] = {}
    class_explanations: Dict[str, str] = {}
    general_insights: List[str] = []
    ai_generated: bool = False

class AnalysisResult(BaseModel):
    file_id: str
    filename: str
    file_size_bytes: int
    file_size_formatted: str
    analyzed_at: str
    syntax: SyntaxValidation
    metrics: CodeMetrics
    functions: List[FunctionInfo] = []
    classes: List[ClassInfo] = []
    imports: List[ImportInfo] = []
    global_variables: List[GlobalVariableInfo] = []
    explanation: CodeExplanation

class FileUploadResponse(BaseModel):
    file_id: str
    filename: str
    file_size_bytes: int
    file_size_formatted: str
    uploaded_at: str
    status: str
    message: str

class FileRecord(BaseModel):
    file_id: str
    filename: str
    saved_filename: str
    file_size_bytes: int
    file_size_formatted: str
    uploaded_at: str
    is_analyzed: bool = False
    has_doc: bool = False
    syntax_valid: Optional[bool] = None
    metrics: Optional[CodeMetrics] = None

class DocumentationResponse(BaseModel):
    file_id: str
    filename: str
    markdown_content: str
    download_url: str
    generated_at: str

class HealthResponse(BaseModel):
    status: str
    app_name: str
    version: str
    ai_enabled: bool
