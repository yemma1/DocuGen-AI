import ast
from pathlib import Path
try:
    import pytest
except ImportError:
    pytest = None

from app.services.analyzer import PythonCodeAnalyzer
from app.services.explanation_engine import ExplanationEngine
from app.services.documentation_generator import MarkdownDocumentationGenerator
from app.models.schemas import AnalysisResult

SAMPLE_CODE = """
import math
from typing import List, Optional

GLOBAL_LIMIT: int = 100

class Animal:
    \"\"\"Base animal class.\"\"\"
    def __init__(self, name: str, age: int = 0) -> None:
        self.name = name
        self.age = age

    def speak(self) -> str:
        return f"{self.name} makes a noise"

class Dog(Animal):
    \"\"\"Domestic canine class.\"\"\"
    def bark(self, volume: int = 5) -> str:
        return "Woof!"

def calculate_discount(price: float, rate: float = 0.1, /) -> float:
    \"\"\"Calculate discounted price.\"\"\"
    return price * (1.0 - rate)

def process_items(*items: str, prefix: str = "item_", **options) -> List[str]:
    \"\"\"Processes multiple items.\"\"\"
    def helper_format(x: str) -> str:
        return f"{prefix}{x}"
    return [helper_format(i) for i in items]
"""

INVALID_SYNTAX_CODE = """
def broken_function(:
    print("Missing parameter syntax")
"""

def test_syntax_validation_valid():
    analyzer = PythonCodeAnalyzer(SAMPLE_CODE, filename="sample.py")
    syntax, tree = analyzer.validate_syntax()
    assert syntax.is_valid is True
    assert tree is not None
    assert syntax.error_message is None

def test_syntax_validation_invalid():
    analyzer = PythonCodeAnalyzer(INVALID_SYNTAX_CODE, filename="broken.py")
    syntax, tree = analyzer.validate_syntax()
    assert syntax.is_valid is False
    assert tree is None
    assert syntax.error_line is not None
    assert syntax.error_message is not None

def test_import_extraction():
    analyzer = PythonCodeAnalyzer(SAMPLE_CODE)
    data = analyzer.analyze()
    imports = data["imports"]
    assert len(imports) == 2
    modules = [imp.module for imp in imports]
    assert "math" in modules
    assert "typing" in modules

def test_global_variables():
    analyzer = PythonCodeAnalyzer(SAMPLE_CODE)
    data = analyzer.analyze()
    globals_list = data["global_variables"]
    assert len(globals_list) == 1
    assert globals_list[0].name == "GLOBAL_LIMIT"
    assert globals_list[0].type_annotation == "int"

def test_class_extraction_and_inheritance():
    analyzer = PythonCodeAnalyzer(SAMPLE_CODE)
    data = analyzer.analyze()
    classes = data["classes"]
    assert len(classes) == 2

    # Animal
    animal = next(c for c in classes if c.name == "Animal")
    assert animal.docstring == "Base animal class."
    assert animal.bases == []
    assert animal.constructor is not None
    assert len(animal.methods) == 2

    # Dog
    dog = next(c for c in classes if c.name == "Dog")
    assert dog.bases == ["Animal"]
    assert len(dog.methods) == 1
    assert dog.methods[0].name == "bark"

def test_function_extraction():
    analyzer = PythonCodeAnalyzer(SAMPLE_CODE)
    data = analyzer.analyze()
    functions = data["functions"]
    assert len(functions) == 2
    func_names = [f.name for f in functions]
    assert "calculate_discount" in func_names
    assert "process_items" in func_names

def test_parameter_extraction():
    analyzer = PythonCodeAnalyzer(SAMPLE_CODE)
    data = analyzer.analyze()
    discount_func = next(f for f in data["functions"] if f.name == "calculate_discount")
    
    params = discount_func.parameters
    assert len(params) == 2
    assert params[0].name == "price"
    assert params[0].kind == "positional_only"
    assert params[0].type_annotation == "float"
    assert params[0].default_value is None

    assert params[1].name == "rate"
    assert params[1].kind == "positional_only"
    assert params[1].default_value == "0.1"

def test_return_annotation_and_detected_returns():
    analyzer = PythonCodeAnalyzer(SAMPLE_CODE)
    data = analyzer.analyze()
    discount_func = next(f for f in data["functions"] if f.name == "calculate_discount")
    assert discount_func.return_annotation == "float"
    assert len(discount_func.detected_returns) > 0
    assert "price * (1.0 - rate)" in discount_func.detected_returns

def test_nested_function_extraction():
    analyzer = PythonCodeAnalyzer(SAMPLE_CODE)
    data = analyzer.analyze()
    proc_func = next(f for f in data["functions"] if f.name == "process_items")
    assert "helper_format" in proc_func.nested_functions

def test_explanation_engine():
    analyzer = PythonCodeAnalyzer(SAMPLE_CODE)
    data = analyzer.analyze()
    explainer = ExplanationEngine(use_ai=False)
    explanation = explainer.explain(
        filename="sample.py",
        metrics=data["metrics"],
        functions=data["functions"],
        classes=data["classes"],
        imports=data["imports"],
    )
    assert explanation.module_summary != ""
    assert "Animal" in explanation.class_explanations
    assert "calculate_discount" in explanation.function_explanations

def test_markdown_documentation_generator():
    analyzer = PythonCodeAnalyzer(SAMPLE_CODE, filename="sample.py")
    data = analyzer.analyze()
    explainer = ExplanationEngine(use_ai=False)
    explanation = explainer.explain(
        filename="sample.py",
        metrics=data["metrics"],
        functions=data["functions"],
        classes=data["classes"],
        imports=data["imports"],
    )

    analysis_result = AnalysisResult(
        file_id="test1234",
        filename="sample.py",
        file_size_bytes=len(SAMPLE_CODE.encode("utf-8")),
        file_size_formatted="1.2 KB",
        analyzed_at="2026-01-01 12:00:00",
        syntax=data["syntax"],
        metrics=data["metrics"],
        functions=data["functions"],
        classes=data["classes"],
        imports=data["imports"],
        global_variables=data["global_variables"],
        explanation=explanation,
    )

    generator = MarkdownDocumentationGenerator(analysis_result)
    markdown = generator.generate()

    # Verify all 10 required sections are present
    assert "## 1. File Overview" in markdown
    assert "## 2. General Information" in markdown
    assert "## 3. Code Summary" in markdown
    assert "## 4. Function Documentation" in markdown
    assert "## 5. Class Documentation" in markdown
    assert "## 6. Parameters and Return Values" in markdown
    assert "## 7. Imports and Dependencies" in markdown
    assert "## 8. Code Structure" in markdown
    assert "## 9. Simple English Explanation" in markdown
    assert "## 10. Code Analysis Summary" in markdown
