import json
import subprocess
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parent.parent.parent
IMAGE_SUBMISSION = BASE_DIR / "test_submissions/ggr274_homework5/image_test1/student_submission.ipynb"
IMAGE_SUBMISSION_IMAGE = BASE_DIR / "test_submissions/ggr274_homework5/image_test1/student_submission.png"
IMAGE_SCHEMA_PATH = BASE_DIR / "ai_feedback/data/schema/image_annotation_schema.json"


def run_image_cli(model_name: str) -> list:
    command = [
        "python3",
        "-m",
        "ai_feedback",
        "--prompt",
        "image_analyze_annotations",
        "--scope",
        "image",
        "--submission",
        str(IMAGE_SUBMISSION),
        "--submission_image",
        str(IMAGE_SUBMISSION_IMAGE),
        "--question",
        "Question 5b",
        "--model",
        model_name,
        "--json_schema",
        str(IMAGE_SCHEMA_PATH),
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode == 0, f"{model_name} failed: {result.stderr}"

    output = result.stdout.strip()
    
    if "```json" in output:
        json_start = output.find("```json") + 7
        json_end = output.find("```", json_start)
        json_text = output[json_start:json_end].strip()
    else:
        json_start = output.find("[")
        assert json_start != -1, f"{model_name} output has no JSON array"
        bracket_count = 0
        json_end = json_start
        for i, char in enumerate(output[json_start:], json_start):
            if char == '[':
                bracket_count += 1
            elif char == ']':
                bracket_count -= 1
                if bracket_count == 0:
                    json_end = i + 1
                    break
        json_text = output[json_start:json_end]

    return json.loads(json_text)


def validate_image_annotation_schema(result: list):
    assert isinstance(result, list), "Result must be a list"
    for item in result:
        assert isinstance(item, dict), "Each annotation must be an object"
        for key in ["description", "location"]:
            assert key in item, f"Missing key: {key}"
        assert isinstance(item["description"], str), "description must be a string"
        assert isinstance(item["location"], list), "location must be a list"
        assert len(item["location"]) == 4, "location must have exactly 4 coordinates"
        for coord in item["location"]:
            assert isinstance(coord, (int, float)), "coordinates must be numbers"


@pytest.mark.parametrize(
    "model",
    [
        "openai",
        "llama3.2-vision:90b",
    ],
)
def test_model_outputs_valid_image_annotation_schema(model):
    result = run_image_cli(model)
    validate_image_annotation_schema(result)
 