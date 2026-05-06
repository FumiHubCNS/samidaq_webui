from pathlib import Path
import importlib
import tomllib
from datetime import datetime

def load_toml_config(path: str | Path) -> dict:
    """
    TOMLファイルを読み込み、辞書として返す。

    Args:
        path (str | Path): TOMLファイルのパス。

    Returns:
        dict: TOMLファイルの内容を表す辞書。
    """
    path = Path(path)
    with path.open("rb") as f:
        return tomllib.load(f)


def import_from_string(import_path: str):
    """
    文字列からモジュールと関数をインポートして返す。

    Args:
        import_path (str): "module:function" 形式のインポートパス。

    Returns:
        Any: インポートされた関数またはオブジェクト。

    Example:
        helpers.backEndHelpers:bitValueConversionAGASAv3
    """
    module_name, function_name = import_path.split(":", 1)
    module = importlib.import_module(module_name)
    return getattr(module, function_name)


def get_required_function(settings: dict, name: str):
    """
    設定から必須の関数を取得する。

    Args:
        settings (dict): 設定辞書。
        name (str): 関数名。

    Returns:
        Any: インポートされた関数。

    Raises:
        KeyError: 関数設定が見つからない場合。
    """
    import_path = settings.get("functions", {}).get(name)

    if not import_path:
        raise KeyError(f"Missing function setting: functions.{name}")

    return import_from_string(import_path)


def get_optional_function(settings: dict, name: str):
    """
    設定からオプションの関数を取得する。

    Args:
        settings (dict): 設定辞書。
        name (str): 関数名。

    Returns:
        Any | None: インポートされた関数、またはNone。
    """
    import_path = settings.get("functions", {}).get(name)

    if not import_path:
        return None

    return import_from_string(import_path)


def resolve_path(project_root: Path, path_value: str | Path) -> Path:
    """
    プロジェクトルートを基準にパスを解決する。

    Args:
        project_root (Path): プロジェクトのルートパス。
        path_value (str | Path): 解決するパス。

    Returns:
        Path: 解決された絶対パス。
    """
    path = Path(path_value)
    if path.is_absolute():
        return path
    return project_root / path


def get_setting(settings: dict, key: str, *, required: bool = True):
    """
    設定から値を取得する。

    Args:
        settings (dict): 設定辞書。
        key (str): 設定キー。
        required (bool, optional): 必須かどうか。デフォルトはTrue。

    Returns:
        Any: 設定値。

    Raises:
        KeyError: 必須の設定が見つからない場合。
    """
    value = (
        settings.get("paths", {}).get(key)
        or settings.get("defaults", {}).get(key)
    )

    if required and not value:
        raise KeyError(f"Missing setting: set paths.{key} or defaults.{key} in TOML")

    return value

def make_output_paths(prefix: str, save_dir_base: Path) -> tuple[Path, Path]:
    """"
    出力ファイルのパスを生成する。

    Args:
        prefix (str): ファイル名の接頭辞。

    Returns:
        tuple[Path, Path]: JSONファイルと出力ファイルのパス。
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_filename = save_dir_base / f"samidare_{prefix}_request_{timestamp}.json"
    output_filename = save_dir_base / f"samidare_{prefix}_output_{timestamp}.txt"
    return json_filename, output_filename
