import subprocess


def run_command(command: list[str]) -> tuple[str, str]:
    process = subprocess.run(
        command,
        capture_output=True,
        text=True
    )
    return process.stdout, process.stderr
