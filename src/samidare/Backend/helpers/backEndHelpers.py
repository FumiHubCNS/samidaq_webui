from pathlib import Path
import subprocess
import os


def resolve_from_project_root(settings: dict, path_value: str) -> Path:
    project_root = Path(settings.get("_project_root", "."))
    path = Path(path_value)

    if path.is_absolute():
        return path

    return project_root / path


def send_command(
    request: dict,
    config_path: str,
    output_path: str,
    settings: dict,
):
    command = request.get("command")

    if not command:
        raise ValueError("Missing request.command")

    device_settings = settings.get("device", {})

    script_value = device_settings.get("script")
    session = device_settings.get("session", "samdaq:0.0")
    log_file_value = device_settings.get("log_file", "log/samdaq_tmux.log")
    wait_timeout = str(device_settings.get("wait_timeout", 2))
    poll_sec = str(device_settings.get("poll_sec", 0.05))

    if not script_value:
        raise ValueError("Missing device.script in TOML")

    script_path = resolve_from_project_root(settings, script_value)
    log_file = resolve_from_project_root(settings, log_file_value)

    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")

    log_file.parent.mkdir(parents=True, exist_ok=True)

    completed = subprocess.run(
        [str(script_path), command],
        check=True,
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "SAMDAQ_SESSION": session,
            "SAMDAQ_LOG_FILE": str(log_file),
            "SAMDAQ_WAIT_TIMEOUT": wait_timeout,
            "SAMDAQ_POLL_SEC": poll_sec,
        },
    )

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(completed.stdout, encoding="utf-8")

    return {
        "status": "ok",
        "command": command,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "returncode": completed.returncode,
        "output_path": str(output_path),
        "log_file": str(log_file),
    }