import subprocess


def call_api(prompt: str, vars: dict, tools: list = None) -> str:
    result = subprocess.run(
        [
            "python3",
            "-m",
            "ai_feedback",
            "--scope",
            "code",
            "--submission",
            vars["submission_file"],
            "--solution",
            vars["solution_file"],
            "--model",
            vars["model"],
            "--prompt",
            vars["prompt"],
            "--prompt_text",
            prompt,
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        return f"[ERROR] {result.stderr}"

    return result.stdout
