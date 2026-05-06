from pathlib import Path
import subprocess
import os


def resolve_from_project_root(settings: dict, path_value: str) -> Path:
    """
    プロジェクトルートを基準にパスを解決する。

    Args:
        settings (dict): 設定辞書。"_project_root"キーを参照する。
        path_value (str): 解決する相対または絶対パス。

    Returns:
        Path: 解決されたPathオブジェクト。
    """
    project_root = Path(settings.get("_project_root", "."))
    path = Path(path_value)

    if path.is_absolute():
        return path

    return project_root / path


def parse_board_status(stdout: str) -> dict:
    """
    samdaqのstatusコマンド出力をパースして辞書に変換する。

    Args:
        stdout (str): samdaq statusコマンドの標準出力文字列。

    Returns:
        dict: board_status情報を表す辞書。
    """
    status = {}

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
        "Last Update": "last_update",
        "Output Directory": "output_directory",
        "Output Filename": "output_filename",
        "Acquisition": "acquisition",
    }

    for line in stdout.splitlines():
        line = line.strip()

        if not line:
            continue

        if line.startswith("---"):
            continue

        if line.startswith("--- Board Status"):
            continue

        if ":" not in line:
            continue

        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()

        output_key = key_map.get(key, key.lower().replace(" ", "_"))

        if output_key == "connected":
            status[output_key] = value.lower() == "yes"
        elif output_key == "trigger_threshold":
            status[output_key] = int(value)
        elif output_key == "samples":
            status[output_key] = value
            try:
                status["samples_count"] = int(value.split()[0])
            except (ValueError, IndexError):
                pass
        else:
            status[output_key] = value

    return status


def send_command(
    request: dict,
    config_path: str,
    output_path: str,
    settings: dict,
):
    """
    samdaq用のコマンドを実行し、結果を収集する。

    Args:
        request (dict): コマンド情報を含むリクエスト辞書。"command"キーを期待する。
        config_path (str): 設定ファイルのパス（現在はコマンド生成に間接的に使用）。
        output_path (str): samdaqコマンドの標準出力を書き込むパス。
        settings (dict): 全体設定辞書。

    Returns:
        dict: 実行結果を表す辞書。"status", "stdout", "stderr", "returncode"などを含む。

    Raises:
        ValueError: request.commandがない場合やデバイス設定が不正な場合。
        FileNotFoundError: 実行スクリプトが存在しない場合。
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

    stdout = completed.stdout

    result = {
        "status": "ok",
        "command": command,
        "stdout": stdout,
        "stderr": completed.stderr,
        "returncode": completed.returncode,
        "output_path": str(output_path),
        "log_file": str(log_file),
    }

    if command == "status":
        result["board_status"] = parse_board_status(stdout)

    return result



def _run_samdaq_command(
    command: str,
    config_path: str,
    output_path: str,
    settings: dict,
):
    """
    samdaqコマンドを送信する内部ヘルパー。

    Args:
        command (str): samdaqに渡すコマンド文字列。
        config_path (str): 設定ファイルのパス。
        output_path (str): 出力保存先パス。
        settings (dict): 全体設定辞書。

    Returns:
        dict: send_commandの実行結果。
    """
    return send_command(
        request={"command": command},
        config_path=config_path,
        output_path=output_path,
        settings=settings,
    )


def _validate_choice(name: str, value: str, allowed: set[str]) -> str:
    """
    文字列選択肢を検証する。

    Args:
        name (str): パラメータ名。
        value (str): 検証する値。
        allowed (set[str]): 許可される文字列の集合。

    Returns:
        str: 小文字化された検証済み値。

    Raises:
        ValueError: 許可されていない値の場合。
    """
    value = str(value).lower()

    if value not in allowed:
        allowed_text = ", ".join(sorted(allowed))
        raise ValueError(f"Invalid {name}: {value}. Allowed: {allowed_text}")

    return value


def _validate_int_choice(name: str, value: int, allowed: set[int]) -> int:
    """
    整数選択肢を検証する。

    Args:
        name (str): パラメータ名。
        value (int): 検証する値。
        allowed (set[int]): 許可される整数の集合。

    Returns:
        int: 検証済みの整数値。

    Raises:
        ValueError: 許可されていない値の場合。
    """
    value = int(value)

    if value not in allowed:
        allowed_text = ", ".join(str(v) for v in sorted(allowed))
        raise ValueError(f"Invalid {name}: {value}. Allowed: {allowed_text}")

    return value


def _validate_int_range(name: str, value: int, min_value: int, max_value: int) -> int:
    """
    整数値が指定範囲内にあるか検証する。

    Args:
        name (str): パラメータ名。
        value (int): 検証する値。
        min_value (int): 許容下限。
        max_value (int): 許容上限。

    Returns:
        int: 検証済みの整数値。

    Raises:
        ValueError: 範囲外の場合。
    """
    value = int(value)

    if not min_value <= value <= max_value:
        raise ValueError(f"Invalid {name}: {value}. Must be {min_value}-{max_value}")

    return value


def get_status(config_path: str, output_path: str | None, settings: dict):
    """
    samdaqのステータスを取得する。
    Args:
        config_path (str): 設定ファイルのパス。
        output_path (str | None): 出力保存先パス。Noneの場合は一時ファイルを使用。
        settings (dict): 全体設定辞書。
    Returns:
        dict: send_commandの実行結果。
    """
    return send_command(
        request={"command": "status"},
        config_path=config_path,
        output_path=output_path,
        settings=settings,
    )


def connect_board(config_path: str, output_path: str, settings: dict):
    """
    samdaqボードに接続する。

    Args:
        config_path (str): 設定ファイルのパス。
        output_path (str): 標準出力保存先パス。
        settings (dict): 全体設定辞書。

    Returns:
        dict: 実行結果。
    """
    return _run_samdaq_command("connect", config_path, output_path, settings)


def disconnect_board(config_path: str, output_path: str, settings: dict):
    """
    samdaqボードから切断する。

    Args:
        config_path (str): 設定ファイルのパス。
        output_path (str): 標準出力保存先パス。
        settings (dict): 全体設定辞書。

    Returns:
        dict: 実行結果。
    """
    return _run_samdaq_command("disconnect", config_path, output_path, settings)


def power_on(config_path: str, output_path: str, settings: dict):
    """
    samdaqの電源をオンにする。

    Args:
        config_path (str): 設定ファイルのパス。
        output_path (str): 標準出力保存先パス。
        settings (dict): 全体設定辞書。

    Returns:
        dict: 実行結果。
    """
    return _run_samdaq_command("power on", config_path, output_path, settings)


def power_off(config_path: str, output_path: str, settings: dict):
    """
    samdaqの電源をオフにする。

    Args:
        config_path (str): 設定ファイルのパス。
        output_path (str): 標準出力保存先パス。
        settings (dict): 全体設定辞書。

    Returns:
        dict: 実行結果。
    """
    return _run_samdaq_command("power off", config_path, output_path, settings)


def set_trigger_type(
    trigger_type: str,
    config_path: str,
    output_path: str,
    settings: dict,
):
    """
    トリガーの種類を設定する。

    Args:
        trigger_type (str): "self", "external", "1khz", "1mhz" のいずれか。
        config_path (str): 設定ファイルのパス。
        output_path (str): 標準出力保存先パス。
        settings (dict): 全体設定辞書。

    Returns:
        dict: 実行結果。
    """
    trigger_type = _validate_choice(
        "trigger_type",
        trigger_type,
        {"self", "external", "1khz", "1mhz"},
    )

    return _run_samdaq_command(
        f"trigger {trigger_type}",
        config_path,
        output_path,
        settings,
    )


def set_trigger_threshold(
    threshold: int,
    config_path: str,
    output_path: str,
    settings: dict,
):
    """
    トリガー閾値を設定する。

    Args:
        threshold (int): 0から1023までの閾値。
        config_path (str): 設定ファイルのパス。
        output_path (str): 標準出力保存先パス。
        settings (dict): 全体設定辞書。

    Returns:
        dict: 実行結果。
    """
    threshold = _validate_int_range(
        "trigger_threshold",
        threshold,
        0,
        1023,
    )

    return _run_samdaq_command(
        f"trigger-threshold {threshold}",
        config_path,
        output_path,
        settings,
    )


def set_polarity(
    polarity: str,
    config_path: str,
    output_path: str,
    settings: dict,
):
    """
    入力信号の極性を設定する。

    Args:
        polarity (str): "positive" または "negative"。
        config_path (str): 設定ファイルのパス。
        output_path (str): 標準出力保存先パス。
        settings (dict): 全体設定辞書。

    Returns:
        dict: 実行結果。
    """
    polarity = _validate_choice(
        "polarity",
        polarity,
        {"positive", "negative"},
    )

    return _run_samdaq_command(
        f"polarity {polarity}",
        config_path,
        output_path,
        settings,
    )


def set_gain(
    gain: int,
    config_path: str,
    output_path: str,
    settings: dict,
):
    """
    増幅ゲインを設定する。

    Args:
        gain (int): 1, 2, 3 のいずれか。
        config_path (str): 設定ファイルのパス。
        output_path (str): 標準出力保存先パス。
        settings (dict): 全体設定辞書。

    Returns:
        dict: 実行結果。
    """
    gain = _validate_int_choice(
        "gain",
        gain,
        {1, 2, 3},
    )

    return _run_samdaq_command(
        f"gain {gain}",
        config_path,
        output_path,
        settings,
    )


def set_samples(
    samples: int,
    config_path: str,
    output_path: str,
    settings: dict,
):
    """
    取得サンプル数を設定する。

    Args:
        samples (int): 16, 32, 64, 128 のいずれか。
        config_path (str): 設定ファイルのパス。
        output_path (str): 標準出力保存先パス。
        settings (dict): 全体設定辞書。

    Returns:
        dict: 実行結果。
    """
    samples = _validate_int_choice(
        "samples",
        samples,
        {16, 32, 64, 128},
    )

    return _run_samdaq_command(
        f"samples {samples}",
        config_path,
        output_path,
        settings,
    )


def set_pre_samples(
    pre_samples: int,
    config_path: str,
    output_path: str,
    settings: dict,
):
    """
    プリサンプル（トリガー前サンプル数）を設定する。

    Args:
        pre_samples (int): 0, 4, 8, 16 のいずれか。
        config_path (str): 設定ファイルのパス。
        output_path (str): 標準出力保存先パス。
        settings (dict): 全体設定辞書。

    Returns:
        dict: 実行結果。
    """
    pre_samples = _validate_int_choice(
        "pre_samples",
        pre_samples,
        {0, 4, 8, 16},
    )

    return _run_samdaq_command(
        f"pretrigger {pre_samples}",
        config_path,
        output_path,
        settings,
    )


def set_external_clk(
    enabled: bool,
    config_path: str,
    output_path: str,
    settings: dict,
):
    """
    外部クロックの使用を設定する。

    Args:
        enabled (bool): Trueで外部クロックを有効にし、Falseで無効にする。
        config_path (str): 設定ファイルのパス。
        output_path (str): 標準出力保存先パス。
        settings (dict): 全体設定辞書。

    Returns:
        dict: 実行結果。
    """
    value = "on" if enabled else "off"

    return _run_samdaq_command(
        f"external-clk {value}",
        config_path,
        output_path,
        settings,
    )


def start_daq(config_path: str, output_path: str, settings: dict):
    """
    DAQを開始する。

    Args:
        config_path (str): 設定ファイルのパス。
        output_path (str): 標準出力保存先パス。
        settings (dict): 全体設定辞書。

    Returns:
        dict: 実行結果。
    """
    return _run_samdaq_command("start", config_path, output_path, settings)


def stop_daq(config_path: str, output_path: str, settings: dict):
    """
    DAQを停止する。

    Args:
        config_path (str): 設定ファイルのパス。
        output_path (str): 標準出力保存先パス。
        settings (dict): 全体設定辞書。

    Returns:
        dict: 実行結果。
    """
    return _run_samdaq_command("stop", config_path, output_path, settings)


def quit_daq(config_path: str, output_path: str, settings: dict):
    """
    samdaqを終了する。

    Args:
        config_path (str): 設定ファイルのパス。
        output_path (str): 標準出力保存先パス。
        settings (dict): 全体設定辞書。

    Returns:
        dict: 実行結果。
    """
    return _run_samdaq_command("quit", config_path, output_path, settings)


def set_output_dir(
    output_dir: str,
    config_path: str,
    output_path: str,
    settings: dict,
):
    """
    出力保存先ディレクトリを設定する。

    Args:
        output_dir (str): 出力ディレクトリ。
        config_path (str): 設定ファイルのパス。
        output_path (str): 標準出力保存先パス。
        settings (dict): 全体設定辞書。

    Returns:
        dict: 実行結果。

    Raises:
        ValueError: output_dirが空の場合。
    """
    if not output_dir:
        raise ValueError("output_dir is required")

    return _run_samdaq_command(
        f"output-dir {output_dir}",
        config_path,
        output_path,
        settings,
    )


def set_output_file(
    output_file: str,
    config_path: str,
    output_path: str,
    settings: dict,
):
    """
    出力ファイル名を設定する。

    Args:
        output_file (str): 出力ファイル名。
        config_path (str): 設定ファイルのパス。
        output_path (str): 標準出力保存先パス。
        settings (dict): 全体設定辞書。

    Returns:
        dict: 実行結果。

    Raises:
        ValueError: output_fileが空の場合。
    """
    if not output_file:
        raise ValueError("output_file is required")

    return _run_samdaq_command(
        f"output-file {output_file}",
        config_path,
        output_path,
        settings,
    )