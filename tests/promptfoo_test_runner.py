import os
import subprocess


def call_api(prompt: str, context: dict, metadata: dict) -> dict:
    """
    Function that promptfoo will call

    Args:
        prompt (str): The prompt to be called
        context (dict): The context of the tests
        metadata (dict): The all metadata that is associated with the test

    Returns:
        dict: The output of the command or error message
    """
    options = metadata['vars']

    try:
        env = os.environ.copy()

        result = subprocess.run(
            [
                "python3",
                "-m",
                "ai_feedback",
                "--scope",
                options['scope'],
                "--submission",
                options["submission_file"],
                "--solution",
                options["solution_file"],
                "--model",
                options["model"],
                "--prompt",
                options["prompt"],
                "--llama_mode",
                "cli",
            ],
            capture_output=True,
            env=env,
            text=True,
        )

        if result.returncode != 0:
            raise RuntimeError(f"ai_feedback failed (rc={result.returncode}):\n{result.stderr}")
        else:
            output = result.stdout.strip()

    except Exception as e:
        raise RuntimeError(f"[EXCEPTION] {e}")

    return {"output": output}
