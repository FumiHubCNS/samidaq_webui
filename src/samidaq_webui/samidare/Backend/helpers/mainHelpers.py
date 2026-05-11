from __future__ import annotations

import importlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


def load_toml_config(path: str | Path) -> dict:
    """
    TOML 設定ファイルを読み込む。
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"TOML config not found: {path}")

    with path.open("rb") as f:
        return tomllib.load(f)


def import_from_string(import_path: str):
    """
    'package.module:function_name' 形式から関数/オブジェクトを import する。
    """
    if ":" not in import_path:
        raise ValueError(f"Invalid import path: {import_path}")

    module_name, attr_name = import_path.split(":", 1)
    module = importlib.import_module(module_name)

    return getattr(module, attr_name)


def get_required_function(settings: dict, name: str):
    """
    [functions] から必須関数を取得する。
    """
    functions = settings.get("functions", {})
    import_path = functions.get(name)

    if not import_path:
        raise ValueError(f"Missing function '{name}' in TOML [functions]")

    return import_from_string(import_path)


def get_optional_function(settings: dict, name: str):
    """
    [functions] から任意関数を取得する。なければ None。
    """
    functions = settings.get("functions", {})
    import_path = functions.get(name)

    if not import_path:
        return None

    return import_from_string(import_path)


def get_setting(settings: dict, key: str, default: Any = None):
    """
    TOML 内の設定値を取得する。

    優先順位:
      1. [paths]
      2. [defaults]
      3. [api]
      4. [device]

    paths に値があればそれを使い、なければ defaults を使う。
    """
    value = (
        settings.get("paths", {}).get(key)
        or settings.get("defaults", {}).get(key)
        or settings.get("api", {}).get(key)
        or settings.get("device", {}).get(key)
    )

    if value is None:
        return default

    return value


def resolve_path(project_root: Path, path_value: str | Path | None) -> Path:
    """
    project_root 基準で path_value を絶対パス化する。
    絶対パスならそのまま返す。
    """
    if path_value is None:
        raise ValueError("path_value is None")

    path = Path(path_value)

    if path.is_absolute():
        return path

    return project_root / path


def make_output_paths(prefix: str, save_dir: Path) -> tuple[Path, Path]:
    """
    コマンド実行ごとの request JSON / stdout txt の保存パスを生成する。
    """
    save_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    json_filename = save_dir / f"samidare_{prefix}_request_{timestamp}.json"
    output_filename = save_dir / f"samidare_{prefix}_output_{timestamp}.txt"

    return json_filename, output_filename


def get_initial_params(params_path: str | Path) -> dict:
    """
    WebUI 初期パラメータ JSON を読み込む。
    """
    params_path = Path(params_path)

    if not params_path.exists():
        raise FileNotFoundError(f"params JSON not found: {params_path}")

    with params_path.open("r", encoding="utf-8") as f:
        params = json.load(f)

    return {
        "status": "ok",
        "params_path": str(params_path),
        "params": params,
    }


def save_json(path: str | Path, data: dict) -> dict:
    """
    dict を JSON として保存する。
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    return {
        "status": "ok",
        "path": str(path),
    }


def load_json(path: str | Path) -> dict:
    """
    JSON ファイルを dict として読み込む。
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)
