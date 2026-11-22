import ast
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from app.models.schemas import (
    ParameterInfo,
    FunctionInfo,
    ClassInfo,
    ImportInfo,
    GlobalVariableInfo,
    CodeMetrics,
    SyntaxValidation,
)

logger = logging.getLogger("docugen.analyzer")

KNOWN_MODULE_PURPOSES: Dict[str, str] = {
    "os": "Operating system interactions, environment variables, and filesystem paths.",
    "sys": "System-specific parameters, runtime configuration, and command-line arguments.",
    "pathlib": "Object-oriented filesystem paths and directory management.",
    "typing": "Type hints and type annotations for static analysis and IDE support.",
    "ast": "Abstract Syntax Tree processing and static code analysis without execution.",
    "json": "JSON serialization, deserialization, and data interchange.",
    "re": "Regular expression pattern matching and string search operations.",
    "math": "Mathematical functions, trigonometry, logarithms, and constants.",
    "datetime": "Date, time, timezone manipulation, and timestamp formatting.",
    "time": "Time access, measurement, and execution delays.",
    "random": "Pseudo-random number generation and random selections.",
    "uuid": "Universally Unique Identifier (UUID) generation.",
    "shutil": "High-level file and directory operations (copy, move, delete).",
    "logging": "Flexible event logging and diagnostic message formatting.",
    "collections": "Specialized container datatypes (namedtuple, defaultdict, Counter, deque).",
    "itertools": "Functions creating iterators for efficient looping and combinations.",
    "functools": "Higher-order functions and operations on callable objects (cache, partial).",
    "dataclasses": "Structured data-holding classes with automatic special methods.",
    "asyncio": "Asynchronous I/O, event loops, and coroutine execution.",
    "subprocess": "Spawning processes, connecting to pipes, and obtaining return codes.",
    "fastapi": "Modern, high-performance web framework for building APIs.",
    "pydantic": "Data validation and settings management using Python type annotations.",
    "uvicorn": "Lightning-fast ASGI web server implementation.",
    "requests": "HTTP library for making web and REST API requests.",
    "httpx": "Next-generation HTTP client with async and sync support.",
    "pytest": "Testing framework for writing simple and scalable unit tests.",
    "numpy": "High-performance multidimensional arrays and numerical computing.",
    "pandas": "Data manipulation, DataFrame analysis, and CSV/Excel processing.",
}

class PythonCodeAnalyzer:
    """
    Static code analyzer using Python's built-in AST module.
    Analyzes Python source files safely without executing code.
    """

    def __init__(self, source_code: str, filename: str = "source.py"):
        self.source_code = source_code
        self.filename = filename
        self.lines = source_code.splitlines()

    def validate_syntax(self) -> Tuple[SyntaxValidation, Optional[ast.Module]]:
        """Validate Python syntax using ast.parse without code execution."""
        try:
            tree = ast.parse(self.source_code, filename=self.filename)
            return (
                SyntaxValidation(is_valid=True),
                tree,
            )
        except SyntaxError as e:
            logger.warning(f"SyntaxError in {self.filename} at line {e.lineno}: {e.msg}")
            error_text = ""
            if e.text:
                error_text = e.text.strip()
            elif e.lineno and 1 <= e.lineno <= len(self.lines):
                error_text = self.lines[e.lineno - 1].strip()

            return (
                SyntaxValidation(
                    is_valid=False,
                    error_message=e.msg or "Invalid Python syntax",
                    error_line=e.lineno,
                    error_column=e.offset,
                    error_text=error_text,
                ),
                None,
            )
        except Exception as e:
            logger.error(f"Unexpected parsing error in {self.filename}: {e}")
            return (
                SyntaxValidation(
                    is_valid=False,
                    error_message=str(e),
                    error_line=None,
                    error_column=None,
                    error_text=None,
                ),
                None,
            )

    def calculate_line_metrics(self) -> CodeMetrics:
        """Calculate line metrics: total, code, blank, and comment lines."""
        total_lines = len(self.lines)
        blank_lines = 0
        comment_lines = 0
        code_lines = 0

        for line in self.lines:
            stripped = line.strip()
            if not stripped:
                blank_lines += 1
            elif stripped.startswith("#"):
                comment_lines += 1
            else:
                code_lines += 1

        return CodeMetrics(
            total_lines=total_lines,
            code_lines=code_lines,
            blank_lines=blank_lines,
            comment_lines=comment_lines,
        )

    def extract_imports(self, tree: ast.Module) -> List[ImportInfo]:
        """Extract all import statements and identify module purposes."""
        imports: List[ImportInfo] = []

        for node in tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name
                    purpose = KNOWN_MODULE_PURPOSES.get(module_name.split(".")[0])
                    imports.append(
                        ImportInfo(
                            module=module_name,
                            imported_names=[],
                            alias=alias.asname,
                            lineno=node.lineno,
                            is_from=False,
                            purpose=purpose,
                        )
                    )
            elif isinstance(node, ast.ImportFrom):
                module_name = node.module or ""
                names = [alias.name for alias in node.names]
                primary_base = module_name.split(".")[0] if module_name else ""
                purpose = KNOWN_MODULE_PURPOSES.get(primary_base)
                
                # Check for single alias if 1 item imported
                singular_alias = node.names[0].asname if len(node.names) == 1 else None

                imports.append(
                    ImportInfo(
                        module=module_name,
                        imported_names=names,
                        alias=singular_alias,
                        lineno=node.lineno,
                        is_from=True,
                        purpose=purpose,
                    )
                )

        return imports

    def extract_global_variables(self, tree: ast.Module) -> List[GlobalVariableInfo]:
        """Extract module-level global variables, constants, and annotated assignments."""
        globals_list: List[GlobalVariableInfo] = []

        for node in tree.body:
            if isinstance(node, ast.Assign):
                # Multiple targets: a = b = 1
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        val_str = ""
                        try:
                            val_str = ast.unparse(node.value)
                            if len(val_str) > 60:
                                val_str = val_str[:57] + "..."
                        except Exception:
                            val_str = "<expression>"
                        globals_list.append(
                            GlobalVariableInfo(
                                name=target.id,
                                type_annotation=None,
                                value_preview=val_str,
                                lineno=node.lineno,
                            )
                        )
            elif isinstance(node, ast.AnnAssign):
                if isinstance(node.target, ast.Name):
                    ann_str = None
                    try:
                        ann_str = ast.unparse(node.annotation)
                    except Exception:
                        ann_str = None

                    val_str = None
                    if node.value is not None:
                        try:
                            val_str = ast.unparse(node.value)
                            if len(val_str) > 60:
                                val_str = val_str[:57] + "..."
                        except Exception:
                            val_str = "<expression>"

                    globals_list.append(
                        GlobalVariableInfo(
                            name=node.target.id,
                            type_annotation=ann_str,
                            value_preview=val_str,
                            lineno=node.lineno,
                        )
                    )

        return globals_list

    def extract_parameters(self, args_node: ast.arguments) -> List[ParameterInfo]:
        """
        Extract parameters including positional-only, keyword-only,
        varargs, kwargs, type annotations, and mapped default values.
        """
        parameters: List[ParameterInfo] = []

        # Positional-only args
        posonly_count = len(getattr(args_node, "posonlyargs", []))
        reg_args_count = len(args_node.args)
        total_pos = posonly_count + reg_args_count

        # Map defaults to positional args (they apply to the rightmost total_pos items)
        defaults_list = list(args_node.defaults)
        defaults_map: Dict[int, str] = {}
        first_default_idx = total_pos - len(defaults_list)

        for i, default_expr in enumerate(defaults_list):
            pos_index = first_default_idx + i
            try:
                defaults_map[pos_index] = ast.unparse(default_expr)
            except Exception:
                defaults_map[pos_index] = "..."

        curr_pos = 0

        # 1. Positional-only args
        for arg in getattr(args_node, "posonlyargs", []):
            ann = None
            if arg.annotation:
                try:
                    ann = ast.unparse(arg.annotation)
                except Exception:
                    pass
            default_val = defaults_map.get(curr_pos)
            parameters.append(
                ParameterInfo(
                    name=arg.arg,
                    type_annotation=ann,
                    default_value=default_val,
                    kind="positional_only",
                )
            )
            curr_pos += 1

        # 2. Regular positional/keyword args
        for arg in args_node.args:
            ann = None
            if arg.annotation:
                try:
                    ann = ast.unparse(arg.annotation)
                except Exception:
                    pass
            default_val = defaults_map.get(curr_pos)
            parameters.append(
                ParameterInfo(
                    name=arg.arg,
                    type_annotation=ann,
                    default_value=default_val,
                    kind="positional_or_keyword",
                )
            )
            curr_pos += 1

        # 3. Vararg (*args)
        if args_node.vararg:
            ann = None
            if args_node.vararg.annotation:
                try:
                    ann = ast.unparse(args_node.vararg.annotation)
                except Exception:
                    pass
            parameters.append(
                ParameterInfo(
                    name=f"*{args_node.vararg.arg}",
                    type_annotation=ann,
                    default_value=None,
                    kind="var_positional",
                )
            )

        # 4. Keyword-only args and their defaults
        for arg, default_expr in zip(args_node.kwonlyargs, args_node.kw_defaults):
            ann = None
            if arg.annotation:
                try:
                    ann = ast.unparse(arg.annotation)
                except Exception:
                    pass
            def_str = None
            if default_expr is not None:
                try:
                    def_str = ast.unparse(default_expr)
                except Exception:
                    def_str = "..."
            parameters.append(
                ParameterInfo(
                    name=arg.arg,
                    type_annotation=ann,
                    default_value=def_str,
                    kind="keyword_only",
                )
            )

        # 5. Kwarg (**kwargs)
        if args_node.kwarg:
            ann = None
            if args_node.kwarg.annotation:
                try:
                    ann = ast.unparse(args_node.kwarg.annotation)
                except Exception:
                    pass
            parameters.append(
                ParameterInfo(
                    name=f"**{args_node.kwarg.arg}",
                    type_annotation=ann,
                    default_value=None,
                    kind="var_keyword",
                )
            )

        return parameters

    def extract_detected_returns(self, func_node: ast.AST) -> List[str]:
        """Statically detect all return expressions within function body."""
        returns: List[str] = []

        def visitor(node: ast.AST):
            for child in ast.iter_child_nodes(node):
                # Do not descend into nested functions or nested classes to prevent return leakage
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    continue
                if isinstance(child, ast.Return):
                    if child.value is None:
                        returns.append("None")
                    else:
                        try:
                            val_str = ast.unparse(child.value)
                            returns.append(val_str)
                        except Exception:
                            returns.append("<expression>")
                visitor(child)

        visitor(func_node)
        # Deduplicate while preserving order
        seen = set()
        deduped = []
        for r in returns:
            if r not in seen:
                seen.add(r)
                deduped.append(r)
        return deduped

    def extract_function_info(
        self,
        node: ast.AST,
        is_method: bool = False,
        parent_class: Optional[str] = None,
    ) -> FunctionInfo:
        """Extract comprehensive metadata for a function or method."""
        is_async = isinstance(node, ast.AsyncFunctionDef)
        name = node.name

        # Return annotation
        return_ann = None
        if getattr(node, "returns", None) is not None:
            try:
                return_ann = ast.unparse(node.returns)
            except Exception:
                return_ann = "<annotation>"

        # Docstring
        docstring = ast.get_docstring(node)

        # Decorators
        decorators: List[str] = []
        for d in getattr(node, "decorator_list", []):
            try:
                decorators.append(f"@{ast.unparse(d)}")
            except Exception:
                decorators.append("@decorator")

        # Parameters
        parameters = self.extract_parameters(node.args)

        # Detected return statements
        detected_returns = self.extract_detected_returns(node)

        # Nested functions
        nested: List[str] = []
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                nested.append(child.name)

        line_start = node.lineno
        line_end = getattr(node, "end_lineno", node.lineno)

        return FunctionInfo(
            name=name,
            parameters=parameters,
            return_annotation=return_ann,
            detected_returns=detected_returns,
            docstring=docstring,
            decorators=decorators,
            line_start=line_start,
            line_end=line_end,
            is_async=is_async,
            is_method=is_method,
            parent_class=parent_class,
            nested_functions=nested,
        )

    def extract_classes(self, tree: ast.Module) -> List[ClassInfo]:
        """Extract classes, their inheritance, docstrings, constructor, and methods."""
        classes: List[ClassInfo] = []

        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                # Bases (inheritance)
                bases: List[str] = []
                for base in node.bases:
                    try:
                        bases.append(ast.unparse(base))
                    except Exception:
                        bases.append("<base>")

                # Decorators
                decorators: List[str] = []
                for d in node.decorator_list:
                    try:
                        decorators.append(f"@{ast.unparse(d)}")
                    except Exception:
                        decorators.append("@decorator")

                docstring = ast.get_docstring(node)
                line_start = node.lineno
                line_end = getattr(node, "end_lineno", node.lineno)

                methods: List[FunctionInfo] = []
                constructor: Optional[FunctionInfo] = None
                nested_classes: List[str] = []

                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        method_info = self.extract_function_info(
                            item, is_method=True, parent_class=node.name
                        )
                        methods.append(method_info)
                        if item.name == "__init__":
                            constructor = method_info
                    elif isinstance(item, ast.ClassDef):
                        nested_classes.append(item.name)

                classes.append(
                    ClassInfo(
                        name=node.name,
                        bases=bases,
                        docstring=docstring,
                        decorators=decorators,
                        line_start=line_start,
                        line_end=line_end,
                        methods=methods,
                        constructor=constructor,
                        nested_classes=nested_classes,
                    )
                )

        return classes

    def extract_standalone_functions(self, tree: ast.Module) -> List[FunctionInfo]:
        """Extract module-level functions (excluding class methods)."""
        functions: List[FunctionInfo] = []

        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_info = self.extract_function_info(node, is_method=False, parent_class=None)
                functions.append(func_info)

        return functions

    def analyze(self) -> Dict[str, Any]:
        """
        Execute full AST static analysis.
        Returns parsed components or syntax error details.
        """
        metrics = self.calculate_line_metrics()
        syntax, tree = self.validate_syntax()

        if not syntax.is_valid or tree is None:
            return {
                "syntax": syntax,
                "metrics": metrics,
                "functions": [],
                "classes": [],
                "imports": [],
                "global_variables": [],
            }

        imports = self.extract_imports(tree)
        globals_list = self.extract_global_variables(tree)
        functions = self.extract_standalone_functions(tree)
        classes = self.extract_classes(tree)

        # Update metrics with counts
        total_methods = sum(len(c.methods) for c in classes)
        metrics.total_functions = len(functions) + total_methods
        metrics.total_classes = len(classes)
        metrics.total_imports = len(imports)
        metrics.total_globals = len(globals_list)

        return {
            "syntax": syntax,
            "metrics": metrics,
            "functions": functions,
            "classes": classes,
            "imports": imports,
            "global_variables": globals_list,
        }
