import re
import logging
from typing import List, Dict, Any, Optional
import urllib.request
import json

from config import OPENAI_API_KEY, OPENAI_MODEL
from app.models.schemas import (
    FunctionInfo,
    ClassInfo,
    ImportInfo,
    ParameterInfo,
    CodeMetrics,
    CodeExplanation,
)

logger = logging.getLogger("docugen.explanation")

VERB_TRANSLATIONS = {
    "get": "Retrieves and returns",
    "fetch": "Fetches",
    "set": "Sets or updates",
    "is": "Checks whether",
    "has": "Verifies if there is",
    "check": "Verifies and checks",
    "calculate": "Calculates and computes",
    "compute": "Computes",
    "format": "Formats and structures",
    "validate": "Validates and ensures correctness of",
    "verify": "Verifies",
    "generate": "Generates and produces",
    "create": "Creates and initializes",
    "build": "Builds and constructs",
    "make": "Creates",
    "parse": "Parses and decodes",
    "extract": "Extracts specific information from",
    "load": "Loads and deserializes",
    "read": "Reads data from",
    "save": "Saves and persists",
    "write": "Writes data out to",
    "dump": "Serializes and dumps",
    "delete": "Deletes or removes",
    "remove": "Removes",
    "clear": "Clears and resets",
    "send": "Sends or dispatches",
    "post": "Transmits or posts",
    "handle": "Processes and handles",
    "process": "Processes",
    "convert": "Converts and transforms",
    "transform": "Transforms",
    "find": "Searches for and locates",
    "search": "Searches through",
    "filter": "Filters items based on criteria in",
    "sort": "Sorts items according to",
    "run": "Executes and runs",
    "execute": "Executes",
    "init": "Initializes setup for",
    "clean": "Cleans and sanitizes",
    "sanitize": "Sanitizes input data for",
    "update": "Updates existing",
    "render": "Renders UI or template output for",
}

COMMON_PARAM_DESCRIPTIONS = {
    "self": "Reference to the current instance of the class.",
    "cls": "Reference to the class object itself.",
    "*args": "Allows passing any number of additional positional arguments.",
    "**kwargs": "Allows passing any number of arbitrary keyword arguments.",
    "file_path": "The file system path pointing to the target file.",
    "filename": "The name of the file being processed.",
    "path": "The file or directory path.",
    "url": "Web URL endpoint address.",
    "data": "The input data payload to be processed.",
    "payload": "The request or response payload data.",
    "items": "A sequence or list of items to iterate over.",
    "name": "The identifier or display name.",
    "id": "Unique identification key.",
    "user_id": "Identifier corresponding to a specific user.",
    "count": "Numerical quantity or counter.",
    "limit": "Maximum number of records to return or process.",
    "offset": "Starting index or pagination offset.",
    "key": "Lookup key or hash map index.",
    "value": "Value associated with a key or property.",
    "status": "State indicator or HTTP status code.",
    "config": "Configuration dictionary or settings object.",
    "timeout": "Maximum duration (in seconds) to wait before timing out.",
    "query": "Search query text or database query string.",
    "text": "Textual string content to be analyzed or formatted.",
    "message": "Human-readable message or notification string.",
    "error": "Error details or caught exception object.",
}

TYPE_FRIENDLY_DESCRIPTIONS = {
    "str": "text string",
    "int": "integer number",
    "float": "decimal number",
    "bool": "boolean flag (True or False)",
    "list": "list of items",
    "dict": "dictionary of key-value pairs",
    "tuple": "fixed tuple sequence",
    "set": "collection of unique elements",
    "bytes": "raw byte data",
    "none": "null or None",
    "any": "value of any datatype",
    "path": "filesystem path",
}

def split_words(identifier: str) -> List[str]:
    """Split snake_case or camelCase into individual lowercase words."""
    # Handle snake_case and kebab-case
    parts = re.split(r"[_\-]+", identifier)
    words = []
    for part in parts:
        # Split CamelCase
        subparts = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\d|\W|$)|\d+", part)
        if subparts:
            words.extend([w.lower() for w in subparts])
        elif part:
            words.append(part.lower())
    return [w for w in words if w]

class ExplanationEngine:
    """
    Translates AST static analysis into simple, beginner-friendly English explanations.
    Uses a robust rule-based engine by default, with optional OpenAI enhancement if configured.
    """

    def __init__(self, use_ai: bool = True):
        self.use_ai = use_ai and bool(OPENAI_API_KEY.strip())

    def explain_parameter(self, param: ParameterInfo) -> str:
        """Explain what a single parameter does in plain English."""
        name = param.name.lstrip("*")

        # Check known common parameters
        if param.name in COMMON_PARAM_DESCRIPTIONS:
            base_desc = COMMON_PARAM_DESCRIPTIONS[param.name]
        elif name in COMMON_PARAM_DESCRIPTIONS:
            base_desc = COMMON_PARAM_DESCRIPTIONS[name]
        else:
            words = split_words(name)
            joined = " ".join(words) if words else name
            base_desc = f"Represents the '{joined}' input parameter."

        # Enhance with type annotation
        type_note = ""
        if param.type_annotation:
            ann_lower = param.type_annotation.lower().strip()
            friendly_type = None
            for k, v in TYPE_FRIENDLY_DESCRIPTIONS.items():
                if k in ann_lower:
                    friendly_type = v
                    break
            if friendly_type:
                type_note = f" (Expected type: {param.type_annotation} - {friendly_type})"
            else:
                type_note = f" (Type: {param.type_annotation})"

        # Enhance with default value
        default_note = ""
        if param.default_value is not None:
            default_note = f". Defaults to `{param.default_value}` if omitted"

        return f"{base_desc}{type_note}{default_note}."

    def explain_function(self, func: FunctionInfo) -> str:
        """Generate a beginner-friendly explanation of a function's purpose."""
        # 1. If high quality docstring exists, start from it
        if func.docstring and len(func.docstring.strip()) > 5:
            first_sentence = func.docstring.strip().split(".")[0].strip()
            if len(first_sentence) > 10:
                doc_summary = f"{first_sentence}."
            else:
                doc_summary = func.docstring.strip()
            return doc_summary

        # 2. Deconstruct name
        words = split_words(func.name)
        if not words:
            return f"Executes the `{func.name}` routine."

        first_word = words[0]
        remaining = " ".join(words[1:]) if len(words) > 1 else ""

        if first_word in VERB_TRANSLATIONS:
            verb_phrase = VERB_TRANSLATIONS[first_word]
            if remaining:
                explanation = f"{verb_phrase} the {remaining}."
            else:
                explanation = f"{verb_phrase} required operation."
        else:
            joined = " ".join(words)
            explanation = f"Performs {joined} logic."

        # Mention async behavior
        if func.is_async:
            explanation = f"Asynchronously {explanation[0].lower() + explanation[1:]}"

        # Mention return
        if func.return_annotation:
            explanation += f" Returns a value of type `{func.return_annotation}`."
        elif func.detected_returns:
            distinct = ", ".join(f"`{r}`" for r in func.detected_returns[:2])
            explanation += f" Detects return statement(s) yielding {distinct}."

        return explanation

    def explain_class(self, cls_info: ClassInfo) -> str:
        """Generate an explanation of what a class represents and does."""
        # Check docstring first
        if cls_info.docstring and len(cls_info.docstring.strip()) > 5:
            first_sentence = cls_info.docstring.strip().split(".")[0].strip()
            return f"{first_sentence}."

        words = split_words(cls_info.name)
        joined_name = " ".join(words).title() if words else cls_info.name

        desc = f"Represents a `{cls_info.name}` entity or data structure ({joined_name})."

        # Mention inheritance
        if cls_info.bases:
            bases_str = ", ".join(f"`{b}`" for b in cls_info.bases)
            desc += f" Inherits core behavior and attributes from {bases_str}."

        # Mention methods
        method_count = len(cls_info.methods)
        if method_count > 0:
            method_names = [m.name for m in cls_info.methods if not m.name.startswith("__")]
            if method_names:
                sample_methods = ", ".join(f"`{m}`" for m in method_names[:3])
                desc += f" Provides {method_count} method(s), including {sample_methods}."
            else:
                desc += f" Implements {method_count} special and internal method(s)."

        return desc

    def generate_module_summary(
        self,
        filename: str,
        metrics: CodeMetrics,
        functions: List[FunctionInfo],
        classes: List[ClassInfo],
        imports: List[ImportInfo],
        docstring: Optional[str] = None,
    ) -> str:
        """Create a cohesive 2-3 paragraph overview of what the Python script does."""
        paragraphs: List[str] = []

        # Paragraph 1: High level purpose
        if docstring and len(docstring.strip()) > 10:
            clean_doc = docstring.strip().replace("\n", " ")
            p1 = f"**{filename}** is a Python module designed to: {clean_doc}"
        else:
            stem = filename.replace(".py", "")
            words = " ".join(split_words(stem)).title()
            p1 = (
                f"**{filename}** is a Python module implementing `{words}` functionality. "
                f"It comprises **{metrics.total_lines} lines of code** with a clean modular structure."
            )
        paragraphs.append(p1)

        # Paragraph 2: Components breakdown
        comp_parts = []
        if classes:
            class_names = ", ".join(f"`{c.name}`" for c in classes[:4])
            comp_parts.append(f"defines **{len(classes)} class(es)** ({class_names})")
        if functions:
            func_names = ", ".join(f"`{f.name}`" for f in functions[:5])
            comp_parts.append(f"provides **{len(functions)} standalone function(s)** ({func_names})")

        if comp_parts:
            p2 = f"Architecturally, this file {' and '.join(comp_parts)} to organize business logic."
        else:
            p2 = "This file contains procedural script commands and execution statements."
        paragraphs.append(p2)

        # Paragraph 3: Dependencies and integration
        if imports:
            dep_names = [imp.module.split(".")[0] for imp in imports if imp.module]
            unique_deps = sorted(list(set(dep_names)))[:5]
            deps_str = ", ".join(f"`{d}`" for d in unique_deps)
            p3 = (
                f"For its runtime dependencies, the module relies on {deps_str} "
                f"to perform standard operations, static interactions, and data processing."
            )
            paragraphs.append(p3)

        return "\n\n".join(paragraphs)

    def _try_openai_explanation(
        self,
        source_code_snippet: str,
        filename: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Attempt AI explanation via OpenAI REST endpoint using standard library urllib.
        Does not require the 'openai' package. Fails gracefully to None.
        """
        if not self.use_ai or not OPENAI_API_KEY.strip():
            return None

        try:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {OPENAI_API_KEY.strip()}",
                "Content-Type": "application/json",
            }
            prompt = (
                f"Analyze this Python source file '{filename}'. Explain in simple English:\n"
                f"1. A cohesive 2-paragraph module summary.\n"
                f"2. Three key architectural insights.\n\n"
                f"Code snippet (first 2000 chars):\n{source_code_snippet[:2000]}\n\n"
                f"Respond in valid JSON with keys 'module_summary' and 'insights' (list of strings)."
            )
            payload = {
                "model": OPENAI_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert Python educator explaining code clearly to beginners. Output valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.3,
                "response_format": {"type": "json_object"},
            }

            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=8) as response:
                result = json.loads(response.read().decode("utf-8"))
                choice = result["choices"][0]["message"]["content"]
                parsed = json.loads(choice)
                return parsed
        except Exception as e:
            logger.info(f"OpenAI explanation skipped or timed out: {e}. Falling back to rule-based engine.")
            return None

    def explain(
        self,
        filename: str,
        metrics: CodeMetrics,
        functions: List[FunctionInfo],
        classes: List[ClassInfo],
        imports: List[ImportInfo],
        source_code: str = "",
        top_docstring: Optional[str] = None,
    ) -> CodeExplanation:
        """
        Execute full code explanation generation.
        Populates explanations for each function, class, and the overall module.
        """
        # Explain each standalone function and method
        func_explanations: Dict[str, str] = {}
        for func in functions:
            expl = self.explain_function(func)
            func.explanation = expl
            func_explanations[func.name] = expl

            # Populate parameter explanations
            for p in func.parameters:
                p.description = self.explain_parameter(p)

        # Explain each class and its internal methods
        class_explanations: Dict[str, str] = {}
        for cls in classes:
            expl = self.explain_class(cls)
            cls.explanation = expl
            class_explanations[cls.name] = expl

            for method in cls.methods:
                m_expl = self.explain_function(method)
                method.explanation = m_expl
                func_explanations[f"{cls.name}.{method.name}"] = m_expl
                for p in method.parameters:
                    p.description = self.explain_parameter(p)

        # Rule-based module summary
        rule_summary = self.generate_module_summary(
            filename=filename,
            metrics=metrics,
            functions=functions,
            classes=classes,
            imports=imports,
            docstring=top_docstring,
        )

        general_insights = [
            f"The file defines {metrics.total_functions} total functions and {metrics.total_classes} classes across {metrics.total_lines} lines.",
            f"Maintains {metrics.code_lines} lines of code and {metrics.comment_lines} comment lines.",
            f"Incorporates {metrics.total_imports} external or standard module imports.",
        ]

        ai_generated = False
        final_summary = rule_summary

        # Try optional OpenAI enhancement if configured
        if self.use_ai:
            ai_data = self._try_openai_explanation(source_code, filename)
            if ai_data and "module_summary" in ai_data:
                final_summary = ai_data["module_summary"]
                if "insights" in ai_data and isinstance(ai_data["insights"], list):
                    general_insights = ai_data["insights"]
                ai_generated = True

        return CodeExplanation(
            module_summary=final_summary,
            function_explanations=func_explanations,
            class_explanations=class_explanations,
            general_insights=general_insights,
            ai_generated=ai_generated,
        )
