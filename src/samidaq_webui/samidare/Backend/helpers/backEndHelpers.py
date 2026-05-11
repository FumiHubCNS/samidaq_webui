from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any


# =============================================================================
# Path helpers
# =============================================================================

def resolve_from_project_root(settings: dict, path_value: str | Path) -> Path:
    """
    settings["_project_root"] を基準に相対パスを絶対パスへ変換する。
    絶対パスが渡された場合はそのまま返す。
    """
    project_root = Path(settings.get("_project_root", "."))
    path = Path(path_value)

    if path.is_absolute():
        return path

    return project_root / path


# =============================================================================
# Validation helpers
# =============================================================================

def validate_choice(name: str, value: str, allowed: set[str]) -> str:
    value = str(value).lower()

    if value not in allowed:
        allowed_text = ", ".join(sorted(allowed))
        raise ValueError(f"Invalid {name}: {value}. Allowed: {allowed_text}")

    return value


def validate_int_choice(name: str, value: int, allowed: set[int]) -> int:
    value = int(value)

    if value not in allowed:
        allowed_text = ", ".join(str(v) for v in sorted(allowed))
        raise ValueError(f"Invalid {name}: {value}. Allowed: {allowed_text}")

    return value


def validate_int_range(name: str, value: int, min_value: int, max_value: int) -> int:
    value = int(value)

    if not min_value <= value <= max_value:
        raise ValueError(f"Invalid {name}: {value}. Must be {min_value}-{max_value}")

    return value

# =============================================================================
# Status parsing
# =============================================================================

def parse_bool_yes_no(value: str) -> bool:
    return str(value).strip().lower() in {"yes", "true", "on", "1"}


def parse_first_int(value: str) -> int | None:
    try:
        return int(str(value).strip().split()[0])
    except (ValueError, IndexError):
        return None


def parse_board_status(stdout: str) -> dict:
    """
    SAMDAQ の status 出力を JSON 化する。

    例:
      IP Address: 192.168.1.192
      Connected: Yes
      Power: On
      Trigger Type: Self-trigger
      Trigger Threshold: 0
      ...
    """
    status: dict[str, Any] = {}

    key_map = {
        "IP Address": "ip_address",
        "Connected": "connected",
        "Power": "power",
        "Trigger Type": "trigger_type",
        "Trigger Threshold": "trigger_threshold",
        "Polarity": "polarity",
        "Gain": "gain",
        "Shaping": "shaping",
        "Samples": "samples",
        "Pre Samples": "pre_samples",
        "External Clock": "clock_type",
        "Clock Type": "clock_type",
        "Last Update": "last_update",
        "Output Directory": "output_directory",
        "Output Filename": "output_filename",
        "Acquisition": "acquisition",
    }

    for raw_line in stdout.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        if line.startswith("---") or line.startswith("----------------"):
            continue

        if ":" not in line:
            continue

        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()

        output_key = key_map.get(key, key.lower().replace(" ", "_"))

        if output_key == "connected":
            status[output_key] = parse_bool_yes_no(value)

        elif output_key == "trigger_threshold":
            try:
                status[output_key] = int(value)
            except ValueError:
                status[output_key] = value

        elif output_key == "samples":
            status[output_key] = value
            samples_count = parse_first_int(value)
            if samples_count is not None:
                status["samples_count"] = samples_count

        elif output_key == "pre_samples":
            status[output_key] = value
            pre_samples_count = parse_first_int(value)
            if pre_samples_count is not None:
                status["pre_samples_count"] = pre_samples_count

        else:
            status[output_key] = value

    return status


# =============================================================================
# current-pageinfo helpers
# =============================================================================

def load_current_pageinfo_from_file(settings: dict) -> dict | None:
    """
    FastAPI 側が保存している current-pageinfo latest JSON を読む。
    start / stop の戻り値に HTML の状態を付けたい場合に使う。
    """
    path_value = settings.get("_current_pageinfo_path")

    if not path_value:
        return None

    path = Path(path_value)

    if not path.exists():
        return None

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


# =============================================================================
# Low-level SAMDAQ command runner
# =============================================================================

def send_command(
    request: dict,
    config_path: str,
    output_path: str | Path,
    settings: dict,
):
    """
    SAMDAQ 用のコマンドを tmux 経由で実行し、結果を収集する。

    request は {"command": "..."} を想定する。
    """
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
        check=False,
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
    # output_path.parent.mkdir(parents=True, exist_ok=True)
    # output_path.write_text(completed.stdout, encoding="utf-8")

    if completed.returncode != 0:
        raise RuntimeError(
            "SAMDAQ command failed: "
            f"command={command!r}, "
            f"returncode={completed.returncode}, "
            f"stdout={completed.stdout!r}, "
            f"stderr={completed.stderr!r}"
        )

    result = {
        "status": "ok",
        "command": command,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "returncode": completed.returncode,
        "output_path": str(output_path),
        "log_file": str(log_file),
    }

    if command == "status":
        result["board_status"] = parse_board_status(completed.stdout)

    if command in {"start", "stop"}:
        result["current_pageinfo"] = load_current_pageinfo_from_file(settings)

    return result


def run_samdaq_command(
    command: str,
    config_path: str,
    output_path: str | Path,
    settings: dict,
):
    return send_command(
        request={"command": command},
        config_path=config_path,
        output_path=output_path,
        settings=settings,
    )