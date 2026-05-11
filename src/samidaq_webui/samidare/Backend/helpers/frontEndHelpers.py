from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any

from .backEndHelpers import (
    send_command,
    validate_choice,
    validate_int_choice,
    validate_int_range,
    run_samdaq_command,
    resolve_from_project_root
)

# =============================================================================
# SAMDAQ basic commands
# =============================================================================

def get_status(
    config_path: str,
    output_path: str | Path,
    settings: dict,
):
    return send_command(
        request={"command": "status"},
        config_path=config_path,
        output_path=output_path,
        settings=settings,
    )


def connect_board(
    config_path: str,
    output_path: str | Path,
    settings: dict,
):
    return run_samdaq_command(
        "connect",
        config_path,
        output_path,
        settings,
    )


def disconnect_board(
    config_path: str,
    output_path: str | Path,
    settings: dict,
):
    return run_samdaq_command(
        "disconnect",
        config_path,
        output_path,
        settings,
    )


# unconnect という名前でも呼べるようにしておく
def unconnect_board(
    config_path: str,
    output_path: str | Path,
    settings: dict,
):
    return disconnect_board(
        config_path=config_path,
        output_path=output_path,
        settings=settings,
    )


def power_on(
    config_path: str,
    output_path: str | Path,
    settings: dict,
):
    return run_samdaq_command(
        "power on",
        config_path,
        output_path,
        settings,
    )


def power_off(
    config_path: str,
    output_path: str | Path,
    settings: dict,
):
    return run_samdaq_command(
        "power off",
        config_path,
        output_path,
        settings,
    )


# typo/別名互換
def power_in(
    config_path: str,
    output_path: str | Path,
    settings: dict,
):
    return power_on(
        config_path=config_path,
        output_path=output_path,
        settings=settings,
    )


# =============================================================================
# SAMDAQ setting commands
# =============================================================================

def set_trigger_type(
    trigger_type: str,
    config_path: str,
    output_path: str | Path,
    settings: dict,
):
    trigger_type = validate_choice(
        "trigger_type",
        trigger_type,
        {"self", "external", "1khz", "1mhz"},
    )

    return run_samdaq_command(
        f"trigger {trigger_type}",
        config_path,
        output_path,
        settings,
    )


def set_trigger_threshold(
    threshold: int | None = None,
    trigger_threshold: int | None = None,
    config_path: str = "",
    output_path: str | Path = "",
    settings: dict | None = None,
):
    if settings is None:
        settings = {}

    value = threshold if threshold is not None else trigger_threshold

    if value is None:
        raise ValueError("Missing threshold")

    value = validate_int_range(
        "trigger_threshold",
        value,
        0,
        1023,
    )

    return run_samdaq_command(
        f"trigger-threshold {value}",
        config_path,
        output_path,
        settings,
    )


def set_polarity(
    polarity: str,
    config_path: str,
    output_path: str | Path,
    settings: dict,
):
    polarity = validate_choice(
        "polarity",
        polarity,
        {"positive", "negative"},
    )

    return run_samdaq_command(
        f"polarity {polarity}",
        config_path,
        output_path,
        settings,
    )


def set_gain(
    gain: int,
    config_path: str,
    output_path: str | Path,
    settings: dict,
):
    gain = validate_int_choice(
        "gain",
        gain,
        {1, 2, 3},
    )

    return run_samdaq_command(
        f"gain {gain}",
        config_path,
        output_path,
        settings,
    )


def set_samples(
    samples: int,
    config_path: str,
    output_path: str | Path,
    settings: dict,
):
    samples = validate_int_choice(
        "samples",
        samples,
        {16, 32, 64, 128},
    )

    return run_samdaq_command(
        f"samples {samples}",
        config_path,
        output_path,
        settings,
    )


def set_pre_samples(
    pre_samples: int,
    config_path: str,
    output_path: str | Path,
    settings: dict,
):
    pre_samples = validate_int_choice(
        "pre_samples",
        pre_samples,
        {0, 4, 8, 16},
    )

    return run_samdaq_command(
        f"pretrigger {pre_samples}",
        config_path,
        output_path,
        settings,
    )


def set_external_clk(
    enabled: bool | str,
    config_path: str,
    output_path: str | Path,
    settings: dict,
):
    if isinstance(enabled, str):
        enabled = enabled.lower() in {"true", "on", "1", "yes"}

    value = "on" if enabled else "off"

    return run_samdaq_command(
        f"external-clk {value}",
        config_path,
        output_path,
        settings,
    )


def set_external_clock(
    enabled: bool | str,
    config_path: str,
    output_path: str | Path,
    settings: dict,
):
    return set_external_clk(
        enabled=enabled,
        config_path=config_path,
        output_path=output_path,
        settings=settings,
    )


def set_output_dir(
    output_dir: str,
    config_path: str,
    output_path: str | Path,
    settings: dict,
):
    output_dir = str(output_dir).strip()

    if not output_dir:
        raise ValueError("output_dir is required")

    return run_samdaq_command(
        f"output-dir {output_dir}",
        config_path,
        output_path,
        settings,
    )


def set_output_file(
    output_file: str,
    config_path: str,
    output_path: str | Path,
    settings: dict,
):
    output_file = str(output_file).strip()

    if not output_file:
        raise ValueError("output_file is required")

    return run_samdaq_command(
        f"output-file {output_file}",
        config_path,
        output_path,
        settings,
    )


# =============================================================================
# DAQ control commands
# =============================================================================

def start_daq(
    config_path: str,
    output_path: str | Path,
    settings: dict,
    header_comment: str | None = None,
):
    # header_comment は現状 SAMDAQ command に渡していない。
    # 必要ならここで comment command を先に送る形にできる。
    return run_samdaq_command(
        "start",
        config_path,
        output_path,
        settings,
    )


def stop_daq(
    config_path: str,
    output_path: str | Path,
    settings: dict,
    ender_comment: str | None = None,
):
    # ender_comment は現状 SAMDAQ command に渡していない。
    return run_samdaq_command(
        "stop",
        config_path,
        output_path,
        settings,
    )


def quit_daq(
    config_path: str,
    output_path: str | Path,
    settings: dict,
):
    return run_samdaq_command(
        "quit",
        config_path,
        output_path,
        settings,
    )


# =============================================================================
# File monitor
# =============================================================================

def get_file_info(
    path: str,
    config_path: str,
    output_path: str | Path | None,
    settings: dict,
):
    file_path = Path(path)

    exists = file_path.exists()
    size_bytes = file_path.stat().st_size if exists else 0

    return {
        "status": "ok",
        "path": str(file_path),
        "exists": exists,
        "size_bytes": size_bytes,
        "size_kb": round(size_bytes / 1024, 3),
        "size_mb": round(size_bytes / 1024 / 1024, 3),
        "timestamp": time.time(),
    }


# =============================================================================
# SAMDAQ tmux launcher
# =============================================================================

def start_samdaq(
    config_path: str,
    output_path: str | Path,
    settings: dict,
    samdaq_dir: str | None = None,
):
    device_settings = settings.get("device", {})

    script_value = device_settings.get(
        "start_script",
        "src/samidaq_webui/samidare/Scripts/start_samdaq.sh",
    )

    script_path = resolve_from_project_root(settings, script_value)

    if not script_path.exists():
        raise FileNotFoundError(f"SAMDAQ start script not found: {script_path}")

    if samdaq_dir is None:
        samdaq_dir = device_settings.get(
            "samdaq_dir",
            "/home/daq/samidare/SAM_DAQ",
        )

    cmd = [str(script_path)]

    if samdaq_dir:
        cmd.append(str(samdaq_dir))

    completed = subprocess.run(
        cmd,
        check=False,
        capture_output=True,
        text=True,
        cwd=str(Path(settings.get("_project_root", "."))),
        env={
            **os.environ,
            "SAMDAQ_SESSION": device_settings.get("start_session", "samdaq"),
            "SAMDAQ_LOG_FILE": str(
                resolve_from_project_root(
                    settings,
                    device_settings.get("log_file", "log/samdaq_tmux.log"),
                )
            ),
        },
    )

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(completed.stdout, encoding="utf-8")

    if completed.returncode != 0:
        raise RuntimeError(
            "start_samdaq failed: "
            f"returncode={completed.returncode}, "
            f"stdout={completed.stdout!r}, "
            f"stderr={completed.stderr!r}"
        )

    return {
        "status": "ok",
        "command": "start_samdaq",
        "script": str(script_path),
        "samdaq_dir": samdaq_dir,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "returncode": completed.returncode,
        "output_path": str(output_path),
    }


# =============================================================================
# Generic helpers for direct use
# =============================================================================

def read_json_file(path: str | Path) -> dict:
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json_file(path: str | Path, data: dict) -> dict:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    return {
        "status": "ok",
        "path": str(path),
    }
