import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import DOCS_DIR
from app.models.schemas import (
    AnalysisResult,
    FunctionInfo,
    ClassInfo,
    ImportInfo,
    GlobalVariableInfo,
    CodeMetrics,
    SyntaxValidation,
    CodeExplanation,
)

class MarkdownDocumentationGenerator:
    """
    Generates professional, comprehensive Markdown documentation
    adhering strictly to the required 10-section format.
    """

    def __init__(self, analysis: AnalysisResult):
        self.analysis = analysis

    def _render_file_overview(self) -> str:
        """Section 1: File Overview"""
        syntax_status = (
            "✅ **Valid Python Syntax** (AST Parsed Successfully)"
            if self.analysis.syntax.is_valid
            else f"❌ **Syntax Error Detected** at Line {self.analysis.syntax.error_line}: {self.analysis.syntax.error_message}"
        )

        return (
            f"## 1. File Overview\n\n"
            f"- **Filename:** `{self.analysis.filename}`\n"
            f"- **Analysis Date & Time:** {self.analysis.analyzed_at}\n"
            f"- **Syntax Status:** {syntax_status}\n"
            f"- **Generator:** [DocuGen AI](http://127.0.0.1:8000) (Automated AST Static Analysis Engine)\n\n"
            f"This document provides full technical and plain-English documentation "
            f"for the Python source file `{self.analysis.filename}`, extracted through safe "
            f"Abstract Syntax Tree (AST) static inspection without runtime execution.\n"
        )

    def _render_general_information(self) -> str:
        """Section 2: General Information Table"""
        m = self.analysis.metrics
        return (
            f"## 2. General Information\n\n"
            f"| Metric Property | Value | Description |\n"
            f"| :--- | :--- | :--- |\n"
            f"| **File Name** | `{self.analysis.filename}` | Name of the analyzed Python source file |\n"
            f"| **File Size** | {self.analysis.file_size_formatted} ({self.analysis.file_size_bytes:,} bytes) | Physical disk storage size |\n"
            f"| **Total Lines** | {m.total_lines:,} | Total lines in the file |\n"
            f"| **Source Code Lines** | {m.code_lines:,} | Executable lines of Python code |\n"
            f"| **Blank Lines** | {m.blank_lines:,} | Empty whitespace lines for readability |\n"
            f"| **Comment Lines** | {m.comment_lines:,} | Dedicated single-line comments (`#`) |\n"
            f"| **Total Functions** | {m.total_functions:,} | Combined count of standalone functions and class methods |\n"
            f"| **Total Classes** | {m.total_classes:,} | User-defined object-oriented class definitions |\n"
            f"| **Total Imports** | {m.total_imports:,} | External and standard library dependencies |\n"
            f"| **Global Variables** | {m.total_globals:,} | Module-level assignments and constants |\n"
        )

    def _render_code_summary(self) -> str:
        """Section 3: Code Summary"""
        expl = self.analysis.explanation
        summary_text = expl.module_summary or "No summary available."
        
        insights_md = ""
        if expl.general_insights:
            insights_md = "\n\n### Key Architectural Insights\n" + "\n".join(
                f"- {insight}" for insight in expl.general_insights
            )

        ai_badge = " *(AI-Augmented)*" if expl.ai_generated else " *(Rule-Based Engine)*"

        return (
            f"## 3. Code Summary{ai_badge}\n\n"
            f"{summary_text}\n"
            f"{insights_md}\n"
        )

    def _render_function_documentation(self) -> str:
        """Section 4: Function Documentation"""
        content = ["## 4. Function Documentation\n"]

        if not self.analysis.functions:
            content.append("*No standalone functions detected at module level.*\n")
            return "".join(content)

        for idx, func in enumerate(self.analysis.functions, start=1):
            async_tag = "*(async)* " if func.is_async else ""
            content.append(f"### 4.{idx}. {async_tag}`def {func.name}`\n")
            content.append(f"- **Lines:** {func.line_start} - {func.line_end}\n")
            
            if func.decorators:
                content.append(f"- **Decorators:** {', '.join(f'`{d}`' for d in func.decorators)}\n")
            
            if func.docstring:
                content.append(f"\n> **Docstring:**\n> {func.docstring.strip().replace(chr(10), chr(10) + '> ')}\n\n")

            if func.explanation:
                content.append(f"**Explanation:** {func.explanation}\n\n")

            # Parameters Table
            if func.parameters:
                content.append("#### Parameters\n\n")
                content.append("| Parameter | Kind | Type Annotation | Default Value | Description |\n")
                content.append("| :--- | :--- | :--- | :--- | :--- |\n")
                for p in func.parameters:
                    ann = f"`{p.type_annotation}`" if p.type_annotation else "*None specified*"
                    dflt = f"`{p.default_value}`" if p.default_value is not None else "*Required*"
                    desc = p.description or "-"
                    content.append(f"| `{p.name}` | {p.kind} | {ann} | {dflt} | {desc} |\n")
                content.append("\n")
            else:
                content.append("#### Parameters\n\n*This function takes no parameters.*\n\n")

            # Return Details
            ret_ann = f"`{func.return_annotation}`" if func.return_annotation else "*None specified*"
            detected = (
                ", ".join(f"`{r}`" for r in func.detected_returns)
                if func.detected_returns
                else "*No static return expressions detected*"
            )
            content.append(f"- **Return Annotation:** {ret_ann}\n")
            content.append(f"- **Detected Returns:** {detected}\n\n")

            if func.nested_functions:
                content.append(f"- **Nested Functions:** {', '.join(f'`{n}`' for n in func.nested_functions)}\n\n")

            content.append("---\n\n")

        return "".join(content)

    def _render_class_documentation(self) -> str:
        """Section 5: Class Documentation"""
        content = ["## 5. Class Documentation\n"]

        if not self.analysis.classes:
            content.append("*No classes detected in this file.*\n")
            return "".join(content)

        for idx, cls in enumerate(self.analysis.classes, start=1):
            content.append(f"### 5.{idx}. `class {cls.name}`\n\n")
            content.append(f"- **Lines:** {cls.line_start} - {cls.line_end}\n")
            
            bases_str = ", ".join(f"`{b}`" for b in cls.bases) if cls.bases else "*None (inherits from object)*"
            content.append(f"- **Inheritance:** {bases_str}\n")

            if cls.decorators:
                content.append(f"- **Decorators:** {', '.join(f'`{d}`' for d in cls.decorators)}\n")

            if cls.docstring:
                content.append(f"\n> **Class Docstring:**\n> {cls.docstring.strip().replace(chr(10), chr(10) + '> ')}\n\n")

            if cls.explanation:
                content.append(f"**Explanation:** {cls.explanation}\n\n")

            # Constructor
            if cls.constructor:
                content.append("#### Constructor (`__init__`)\n\n")
                if cls.constructor.parameters:
                    content.append("| Parameter | Type Annotation | Default | Description |\n")
                    content.append("| :--- | :--- | :--- | :--- |\n")
                    for p in cls.constructor.parameters:
                        ann = f"`{p.type_annotation}`" if p.type_annotation else "-"
                        dflt = f"`{p.default_value}`" if p.default_value is not None else "*Required*"
                        desc = p.description or "-"
                        content.append(f"| `{p.name}` | {ann} | {dflt} | {desc} |\n")
                    content.append("\n")
                else:
                    content.append("*Constructor takes no parameters.*\n\n")

            # Methods Table
            if cls.methods:
                content.append("#### Methods\n\n")
                content.append("| Method Name | Parameters | Return Annotation | Lines | Summary |\n")
                content.append("| :--- | :--- | :--- | :--- | :--- |\n")
                for m in cls.methods:
                    params_summary = ", ".join(p.name for p in m.parameters)
                    ret = f"`{m.return_annotation}`" if m.return_annotation else "-"
                    summary = m.explanation or (m.docstring.strip().split(".")[0] if m.docstring else "-")
                    async_prefix = "*(async)* " if m.is_async else ""
                    content.append(f"| {async_prefix}`{m.name}` | `{params_summary}` | {ret} | L{m.line_start}-{m.line_end} | {summary} |\n")
                content.append("\n")

            if cls.nested_classes:
                content.append(f"- **Nested Classes:** {', '.join(f'`{nc}`' for nc in cls.nested_classes)}\n\n")

            content.append("---\n\n")

        return "".join(content)

    def _render_parameters_and_returns(self) -> str:
        """Section 6: Parameters and Return Values Master Summary"""
        content = ["## 6. Parameters and Return Values\n\n"]
        content.append("Below is the consolidated registry of parameters and return value contracts across all functions and methods:\n\n")

        rows = []
        # Standalone functions
        for f in self.analysis.functions:
            for p in f.parameters:
                rows.append((
                    f"`{f.name}()`",
                    f"`{p.name}`",
                    f"`{p.type_annotation}`" if p.type_annotation else "-",
                    f"`{p.default_value}`" if p.default_value is not None else "*Required*",
                    f"`{f.return_annotation}`" if f.return_annotation else "-",
                ))
        # Class methods
        for c in self.analysis.classes:
            for m in c.methods:
                for p in m.parameters:
                    rows.append((
                        f"`{c.name}.{m.name}()`",
                        f"`{p.name}`",
                        f"`{p.type_annotation}`" if p.type_annotation else "-",
                        f"`{p.default_value}`" if p.default_value is not None else "*Required*",
                        f"`{m.return_annotation}`" if m.return_annotation else "-",
                    ))

        if rows:
            content.append("| Callable | Parameter | Type | Default Value | Return Type |\n")
            content.append("| :--- | :--- | :--- | :--- | :--- |\n")
            for r in rows:
                content.append(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} |\n")
            content.append("\n")
        else:
            content.append("*No callable parameters identified.*\n\n")

        return "".join(content)

    def _render_imports(self) -> str:
        """Section 7: Imports and Dependencies"""
        content = ["## 7. Imports and Dependencies\n\n"]

        if not self.analysis.imports:
            content.append("*No import statements detected in this file.*\n\n")
            return "".join(content)

        content.append("| Line | Import Statement | Module | Symbols / Alias | Purpose |\n")
        content.append("| :--- | :--- | :--- | :--- | :--- |\n")

        for imp in self.analysis.imports:
            if imp.is_from:
                symbols = ", ".join(imp.imported_names)
                stmt = f"`from {imp.module} import {symbols}`"
            else:
                stmt = f"`import {imp.module}`"
                if imp.alias:
                    stmt += f" as {imp.alias}"

            symbols_or_alias = (
                f"`as {imp.alias}`" if imp.alias and not imp.is_from
                else (", ".join(f"`{s}`" for s in imp.imported_names) if imp.imported_names else "-")
            )
            purpose = imp.purpose or "Application utility or third-party dependency."

            content.append(f"| L{imp.lineno} | {stmt} | `{imp.module}` | {symbols_or_alias} | {purpose} |\n")

        content.append("\n")
        return "".join(content)

    def _render_code_structure(self) -> str:
        """Section 8: Code Structure Visual Hierarchy"""
        lines = [
            "## 8. Code Structure\n\n",
            "```text\n",
            f"📄 {self.analysis.filename}\n",
        ]

        # Global variables
        if self.analysis.global_variables:
            lines.append("├── 🌐 Global Variables & Constants\n")
            for i, g in enumerate(self.analysis.global_variables):
                is_last_g = (i == len(self.analysis.global_variables) - 1) and not self.analysis.classes and not self.analysis.functions
                branch = "└──" if is_last_g else "├──"
                ann = f": {g.type_annotation}" if g.type_annotation else ""
                val = f" = {g.value_preview}" if g.value_preview else ""
                lines.append(f"│   {branch} {g.name}{ann}{val}  (L{g.lineno})\n")

        # Classes
        if self.analysis.classes:
            lines.append("├── 🏛️ Classes\n")
            for i, c in enumerate(self.analysis.classes):
                is_last_c = (i == len(self.analysis.classes) - 1) and not self.analysis.functions
                c_branch = "└──" if is_last_c else "├──"
                bases_info = f"({', '.join(c.bases)})" if c.bases else ""
                lines.append(f"│   {c_branch} class {c.name}{bases_info}  (L{c.line_start}-L{c.line_end})\n")
                
                # Class methods
                for j, m in enumerate(c.methods):
                    is_last_m = (j == len(c.methods) - 1)
                    sub_prefix = "    " if is_last_c else "│   "
                    m_branch = "└──" if is_last_m else "├──"
                    params_list = ", ".join(p.name for p in m.parameters)
                    lines.append(f"│   {sub_prefix}{m_branch} def {m.name}({params_list})  (L{m.line_start}-L{m.line_end})\n")

        # Functions
        if self.analysis.functions:
            lines.append("└── ⚡ Standalone Functions\n")
            for i, f in enumerate(self.analysis.functions):
                is_last_f = (i == len(self.analysis.functions) - 1)
                f_branch = "└──" if is_last_f else "├──"
                params_list = ", ".join(p.name for p in f.parameters)
                lines.append(f"    {f_branch} def {f.name}({params_list})  (L{f.line_start}-L{f.line_end})\n")

        if not self.analysis.classes and not self.analysis.functions and not self.analysis.global_variables:
            lines.append("└── (Procedural execution script)\n")

        lines.append("```\n\n")
        return "".join(lines)

    def _render_simple_english_explanation(self) -> str:
        """Section 9: Simple English Explanation"""
        expl = self.analysis.explanation
        content = [
            "## 9. Simple English Explanation\n\n",
            "This section provides an intuitive, non-technical explanation "
            "of how the code operates for beginners and students:\n\n",
        ]

        content.append(f"### What does `{self.analysis.filename}` do?\n\n")
        content.append(f"{expl.module_summary}\n\n")

        if self.analysis.classes:
            content.append("### Understanding the Classes\n\n")
            for cls in self.analysis.classes:
                content.append(f"- **`{cls.name}`:** {cls.explanation or 'Manages structured data and encapsulated routines.'}\n")
            content.append("\n")

        if self.analysis.functions:
            content.append("### Understanding the Functions\n\n")
            for func in self.analysis.functions:
                content.append(f"- **`{func.name}()`:** {func.explanation or 'Executes specific business logic.'}\n")
            content.append("\n")

        content.append(
            "### How the Code Executes\n\n"
            "1. **Initialization:** The script loads the necessary libraries listed in the Imports section.\n"
            "2. **Definition:** All classes and functions are declared and registered into memory without executing side-effects immediately.\n"
            "3. **Execution Flow:** Callers instantiate classes or call functions with designated parameters to process data and retrieve return values.\n\n"
        )

        return "".join(content)

    def _render_code_analysis_summary(self) -> str:
        """Section 10: Code Analysis Summary"""
        m = self.analysis.metrics
        ratio = f"{(m.comment_lines / m.total_lines * 100):.1f}%" if m.total_lines > 0 else "0%"
        
        status = "Production Ready" if self.analysis.syntax.is_valid else "Requires Syntax Fixes"

        return (
            f"## 10. Code Analysis Summary\n\n"
            f"- **Validation Status:** {status}\n"
            f"- **Total Source Elements:** {m.total_functions} Functions, {m.total_classes} Classes, {m.total_imports} Imports\n"
            f"- **Comment Ratio:** {ratio} ({m.comment_lines} comment lines out of {m.total_lines} total lines)\n"
            f"- **Documentation Coverage:** Automatically documented across 10 structured sections.\n"
            f"- **Generated By:** **DocuGen AI** Static Code Analysis Engine\n\n"
            f"---\n\n"
            f"*End of generated documentation for `{self.analysis.filename}`.*\n"
        )

    def generate(self) -> str:
        """Assemble all 10 documentation sections into full Markdown document."""
        sections = [
            f"# Python Code Documentation: `{self.analysis.filename}`\n",
            "> Generated automatically by **DocuGen AI** on "
            f"{self.analysis.analyzed_at}\n\n---\n\n",
            self._render_file_overview(),
            "\n",
            self._render_general_information(),
            "\n",
            self._render_code_summary(),
            "\n",
            self._render_function_documentation(),
            "\n",
            self._render_class_documentation(),
            "\n",
            self._render_parameters_and_returns(),
            "\n",
            self._render_imports(),
            "\n",
            self._render_code_structure(),
            "\n",
            self._render_simple_english_explanation(),
            "\n",
            self._render_code_analysis_summary(),
        ]
        return "".join(sections)

    def save(self, file_id: str) -> Path:
        """Generate markdown, write to generated_docs/<file_id>_doc.md, and return Path."""
        markdown_text = self.generate()
        doc_path = DOCS_DIR / f"{file_id}_doc.md"
        with open(doc_path, "w", encoding="utf-8") as f:
            f.write(markdown_text)
        return doc_path
