import signal
import subprocess
import time


def start_llama_server():
    """Starts the llama server and loads teh Deepsee-v3 model"""
    cmd = [
        "/data1/llama.cpp/bin/llama-server",
        "-m",
        "DeepSeek-V3-0324-UD-Q2_K_XL/DeepSeek-V3-0324-UD-Q2_K_XL.gguf",
        "--n-gpu-layers",
        "40",
    ]
    # start server in its own process
    proc = subprocess.Popen(
        cmd,
        cwd='/data1/GGUF',
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return proc


def stop_process(proc: subprocess.Popen):
    # try graceful first
    proc.send_signal(signal.SIGINT)
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()


def run_promptfoo_tests(test_path: str, output_file: str):
    """
    run the promptfoo tests at test_path
    """
    try:
        subprocess.run(
            [
                "npx",
                "promptfoo",
                "eval",
                "--tests",
                test_path,
                "--verbose",
                "-o",
                f"output/{output_file}",
            ],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print("failed to run promptfoo tests", e)


def main():
    llama_proc = start_llama_server()
    time.sleep(10)

    try:
        run_promptfoo_tests("tests/deepseek-v3_tests.yaml", "deepseek-v3_results.json")
    finally:
        stop_process(llama_proc)
        time.sleep(5)

    run_promptfoo_tests("tests/deepseek_r1_tests.yaml", "deepseek_r1_results.json")


if __name__ == "__main__":
    main()
