import json
import os
import sys
from typing import Any, Dict, List

import jsonschema
import pytest
from jsonschema import ValidationError, validate

# Add the markus_test_scripts path to import llm_helpers
sys.path.append(os.path.join(os.path.dirname(__file__), '../markus_test_scripts/python_tester'))
from llm_helpers import extract_json


class TestJsonExtraction:
    """Test cases for extract_json function - ensuring correct line number extraction."""

    @pytest.fixture
    def annotation_schema(self):
        """JSON schema for annotation validation."""
        return {
            "type": "object",
            "required": ["annotations"],
            "properties": {
                "annotations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["filename", "content", "line_start", "line_end"],
                        "properties": {
                            "filename": {"type": "string"},
                            "content": {"type": "string"},
                            "line_start": {"type": "integer", "minimum": 1},
                            "line_end": {"type": "integer", "minimum": 1},
                            "column_start": {"type": "integer", "minimum": 0},
                            "column_end": {"type": "integer", "minimum": 0},
                        },
                        "additionalProperties": True,
                    },
                }
            },
        }

    @pytest.fixture
    def sample_student_code(self):
        """Sample student code for testing line number accuracy."""
        return [
            "import pandas as pd",
            "import matplotlib.pyplot as plt",
            "",
            "def load_data(file_path):",
            "    return pd.read_csv(file_path)",
            "",
            "def plot_data(data):",
            "    unused_variable = 42",
            "    plt.plot(data)",
            "    plt.show()",
            "",
            "data = load_data('test.csv')",
            "plot_data(data",
        ]

    @pytest.fixture
    def sample_test_output(self):
        """Sample test output containing errors with line references."""
        return """
======================================================================
FAIL: test_data_loading (test_assignment.TestDataAnalysis)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "test_assignment.py", line 15, in test_data_loading
    self.assertIsNotNone(result)
  File "student_code.py", line 5, in load_data
    return pd.read_csv(file_path)
NameError: name 'pd' is not defined. Did you forget to import pandas?

======================================================================
FAIL: test_plot_function (test_assignment.TestDataAnalysis)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "test_assignment.py", line 22, in test_plot_function
    plot_data(sample_data)
  File "student_code.py", line 13, in plot_data
    plot_data(data
SyntaxError: '(' was never closed
    """

    def test_basic_json_extraction_with_line_numbers(self):
        """Test basic JSON extraction functionality with various scenarios."""
        response = '''Analysis complete:
        {"annotations": [{"filename": "test.py", "content": "Variable 'x' is unused.", "line_start": 5, "line_end": 5}]}
        End of analysis.'''

        result = extract_json(response)
        assert len(result) == 1
        annotation = result[0]["annotations"][0]
        assert annotation["filename"] == "test.py"
        assert annotation["line_start"] == 5
        assert annotation["line_end"] == 5

        multi_response = '''First issue:
        {"annotations": [{"filename": "test.py", "content": "Missing import", "line_start": 1, "line_end": 1}]}
        Second issue:
        {"annotations": [{"filename": "test.py", "content": "Syntax error", "line_start": 10, "line_end": 12}]}'''

        multi_result = extract_json(multi_response)
        assert len(multi_result) == 2
        assert multi_result[0]["annotations"][0]["line_start"] == 1
        assert multi_result[1]["annotations"][0]["line_start"] == 10

        multi_anno_response = '''
        {"annotations": [
            {"filename": "code.py", "content": "Issue 1", "line_start": 5, "line_end": 5},
            {"filename": "code.py", "content": "Issue 2", "line_start": 15, "line_end": 17}
        ]}'''

        multi_anno_result = extract_json(multi_anno_response)
        assert len(multi_anno_result) == 1
        assert len(multi_anno_result[0]["annotations"]) == 2

    def test_json_schema_validation(self, annotation_schema):
        """Test JSON schema validation for correct and incorrect formats."""
        valid_response = '''
        {"annotations": [
            {"filename": "test.py", "content": "Variable unused", "line_start": 5, "line_end": 5}
        ]}'''

        result = extract_json(valid_response)
        validate(instance=result[0], schema=annotation_schema)

        invalid_response = '''
        {"annotations": [
            {"filename": "test.py", "content": "Error description"}
        ]}'''

        invalid_result = extract_json(invalid_response)
        with pytest.raises(ValidationError):
            validate(instance=invalid_result[0], schema=annotation_schema)

        invalid_lines_response = '''
        {"annotations": [
            {"filename": "test.py", "content": "Error", "line_start": 0, "line_end": 5}
        ]}'''

        invalid_lines_result = extract_json(invalid_lines_response)
        with pytest.raises(ValidationError):
            validate(instance=invalid_lines_result[0], schema=annotation_schema)

    def test_line_number_accuracy_and_bounds(self, sample_student_code):
        """Test that line numbers accurately point to correct content and stay within file bounds."""
        file_length = len(sample_student_code)

        response = '''
        {"annotations": [
            {"filename": "student.py", "content": "Unused variable 'unused_variable'", "line_start": 8, "line_end": 8},
            {"filename": "student.py", "content": "Syntax error: missing closing parenthesis", "line_start": 13, "line_end": 13},
            {"filename": "student.py", "content": "Function definition", "line_start": 4, "line_end": 4}
        ]}'''

        result = extract_json(response)
        annotations = result[0]["annotations"]

        unused_var_annotation = annotations[0]
        line_content = sample_student_code[unused_var_annotation["line_start"] - 1]
        assert "unused_variable" in line_content

        syntax_error_annotation = annotations[1]
        syntax_line = sample_student_code[syntax_error_annotation["line_start"] - 1]
        assert "plot_data(data" in syntax_line and ")" not in syntax_line.split("(")[-1]

        func_annotation = annotations[2]
        func_line = sample_student_code[func_annotation["line_start"] - 1]
        assert "def load_data" in func_line

        boundary_response = f'''
        {{"annotations": [
            {{"filename": "student.py", "content": "First line", "line_start": 1, "line_end": 1}},
            {{"filename": "student.py", "content": "Last line", "line_start": {file_length}, "line_end": {file_length}}}
        ]}}'''

        boundary_result = extract_json(boundary_response)
        boundary_annotations = boundary_result[0]["annotations"]

        assert boundary_annotations[0]["line_start"] == 1
        assert boundary_annotations[1]["line_start"] == file_length
        assert "import pandas" in sample_student_code[0]
        assert "plot_data(data" in sample_student_code[-1]

    def test_edge_cases_and_data_types(self):
        """Test edge cases, data types, and error handling."""
        response = '{"annotations": [{"filename": "test.py", "line_start": 42, "line_end": 45, "content": "Error"}]}'
        result = extract_json(response)
        annotation = result[0]["annotations"][0]
        assert isinstance(annotation["line_start"], int)
        assert isinstance(annotation["line_end"], int)

        range_response = '''
        {"annotations": [
            {"filename": "code.py", "content": "Multi-line issue", "line_start": 10, "line_end": 15},
            {"filename": "code.py", "content": "Single line issue", "line_start": 7, "line_end": 7}
        ]}'''

        range_result = extract_json(range_response)
        range_annotations = range_result[0]["annotations"]
        assert range_annotations[0]["line_end"] > range_annotations[0]["line_start"]
        assert range_annotations[1]["line_start"] == range_annotations[1]["line_end"]

        no_json_response = "This is just regular text with no JSON objects."
        no_json_result = extract_json(no_json_response)
        assert len(no_json_result) == 0

        mixed_response = '''
        Malformed: {"annotations": [{"filename": "test.py", "line_start": 5, missing_brace
        Valid: {"annotations": [{"filename": "valid.py", "content": "Good", "line_start": 10, "line_end": 10}]}'''

        mixed_result = extract_json(mixed_response)
        assert len(mixed_result) == 1
        assert mixed_result[0]["annotations"][0]["filename"] == "valid.py"

    def validate_annotation_against_source(self, annotation: Dict[str, Any], source_lines: List[str]) -> bool:
        """Helper method to validate annotation line numbers against source code."""
        line_start = annotation["line_start"]
        line_end = annotation["line_end"]

        if line_start < 1 or line_end < 1:
            return False
        if line_start > len(source_lines) or line_end > len(source_lines):
            return False
        if line_start > line_end:
            return False

        return True

    def test_test_output_to_json_annotation_workflow(self, sample_student_code, sample_test_output, annotation_schema):
        """Test complete workflow: test_output → model analysis → JSON annotation → line number validation."""

        model_response_from_test_output = '''
        Based on the test output, I found the following issues in the student's code:

        {"annotations": [
            {"filename": "student_code.py", "content": "Missing pandas import: NameError on line 5", "line_start": 1, "line_end": 1},
            {"filename": "student_code.py", "content": "Import pandas as pd is missing", "line_start": 5, "line_end": 5},
            {"filename": "student_code.py", "content": "SyntaxError: unclosed parenthesis", "line_start": 13, "line_end": 13}
        ]}
        '''

        result = extract_json(model_response_from_test_output)
        assert len(result) == 1

        validate(instance=result[0], schema=annotation_schema)

        annotations = result[0]["annotations"]
        assert len(annotations) == 3

        import_annotation = annotations[0]
        assert import_annotation["line_start"] == 1
        assert "import pandas" in sample_student_code[import_annotation["line_start"] - 1]

        # The error refers to line 5 where pd is used but not defined
        error_line_annotation = annotations[1]
        assert error_line_annotation["line_start"] == 5
        assert "pd.read_csv" in sample_student_code[error_line_annotation["line_start"] - 1]

        # Syntax error on line 13
        syntax_annotation = annotations[2]
        assert syntax_annotation["line_start"] == 13
        syntax_line = sample_student_code[syntax_annotation["line_start"] - 1]
        assert "plot_data(data" in syntax_line and syntax_line.count("(") > syntax_line.count(")")

    def test_test_output_line_number_extraction_accuracy(self, sample_test_output):
        """Test that line numbers extracted from test output match JSON annotation line numbers."""

        test_output_lines = []
        for line in sample_test_output.split('\n'):
            if 'File "student_code.py", line' in line:
                parts = line.split('line ')
                if len(parts) > 1:
                    line_num = int(parts[1].split(',')[0])
                    test_output_lines.append(line_num)

        model_response = '''
        {"annotations": [
            {"filename": "student_code.py", "content": "pd not defined error", "line_start": 5, "line_end": 5},
            {"filename": "student_code.py", "content": "Syntax error in function call", "line_start": 13, "line_end": 13}
        ]}
        '''

        result = extract_json(model_response)
        annotations = result[0]["annotations"]

        json_line_numbers = [ann["line_start"] for ann in annotations]
        for line_num in json_line_numbers:
            assert line_num in test_output_lines, f"Line {line_num} not found in test output references"

    def test_test_output_validation_with_wrong_line_numbers(self, sample_student_code, sample_test_output):
        """Test validation catches when JSON annotations have incorrect line numbers relative to test output."""

        incorrect_model_response = '''
        {"annotations": [
            {"filename": "student_code.py", "content": "Missing import", "line_start": 2, "line_end": 2},
            {"filename": "student_code.py", "content": "Syntax error", "line_start": 8, "line_end": 8}
        ]}
        '''

        result = extract_json(incorrect_model_response)
        annotations = result[0]["annotations"]

        import_annotation = annotations[0]
        line_2_content = sample_student_code[import_annotation["line_start"] - 1]
        assert "import" in line_2_content

        syntax_annotation = annotations[1]
        line_8_content = sample_student_code[syntax_annotation["line_start"] - 1]
        assert "unused_variable" in line_8_content
        assert "plot_data(data" not in line_8_content

    def test_comprehensive_validation_realistic_scenario(self, sample_student_code, annotation_schema):
        """Comprehensive test combining schema validation with realistic source code accuracy."""
        llm_response = '''
        I found several issues in the student's code:

        {"annotations": [
            {"filename": "student_analysis.py", "content": "Import statement at top", "line_start": 1, "line_end": 2},
            {"filename": "student_analysis.py", "content": "Function definition issue", "line_start": 4, "line_end": 4},
            {"filename": "student_analysis.py", "content": "Unused variable in function", "line_start": 8, "line_end": 8},
            {"filename": "student_analysis.py", "content": "Syntax error at end", "line_start": 13, "line_end": 13}
        ]}
        '''

        result = extract_json(llm_response)

        validate(instance=result[0], schema=annotation_schema)

        annotations = result[0]["annotations"]
        for annotation in annotations:
            assert self.validate_annotation_against_source(annotation, sample_student_code)

            line_start = annotation["line_start"]
            line_end = annotation["line_end"]
            referenced_lines = sample_student_code[line_start - 1 : line_end]

            content_lower = annotation["content"].lower()
            if "import statement" in content_lower:
                assert any("import" in line for line in referenced_lines)
            elif "function definition" in content_lower:
                assert any("def " in line for line in referenced_lines)
            elif "unused variable" in content_lower:
                assert any("unused_variable" in line for line in referenced_lines)
            elif "syntax error" in content_lower:
                assert any("(" in line and ")" not in line.split("(")[-1] for line in referenced_lines)

    def test_multiple_files_line_tracking(self):
        """Test that line numbers are correctly tracked across multiple files."""
        response = '''
        {"annotations": [
            {"filename": "file1.py", "content": "Error in file1", "line_start": 5, "line_end": 5},
            {"filename": "file2.py", "content": "Error in file2", "line_start": 3, "line_end": 7},
            {"filename": "file1.py", "content": "Another error in file1", "line_start": 10, "line_end": 10}
        ]}'''

        result = extract_json(response)
        annotations = result[0]["annotations"]

        file1_annotations = [a for a in annotations if a["filename"] == "file1.py"]
        file2_annotations = [a for a in annotations if a["filename"] == "file2.py"]

        assert len(file1_annotations) == 2
        assert len(file2_annotations) == 1
        assert file1_annotations[0]["line_start"] == 5
        assert file1_annotations[1]["line_start"] == 10
        assert file2_annotations[0]["line_start"] == 3
