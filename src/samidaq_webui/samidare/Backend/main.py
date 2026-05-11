from __future__ import annotations

from datetime import datetime
import json
import socket
from pathlib import Path

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .helpers.mainHelpers import (
    load_toml_config,
    get_required_function,
    get_optional_function,
    get_setting,
    resolve_path,
    make_output_paths,
    get_initial_params,
    should_save_log,
)


PROJECT_ROOT = Path(__file__).resolve().parents[4]
CONFIG_PATH = PROJECT_ROOT / "config" / "samidare.toml"

if 1:
    print("Project Root:", PROJECT_ROOT)
    print("Config Path:", CONFIG_PATH)

settings = load_toml_config(CONFIG_PATH)
settings["_project_root"] = str(PROJECT_ROOT)

backend_value = get_setting(settings, "backend")
config_value = get_setting(settings, "config")
save_dir_value = get_setting(settings, "save_dir")

backend_path = resolve_path(PROJECT_ROOT, backend_value)
config_path = resolve_path(PROJECT_ROOT, config_value)
save_dir_base = resolve_path(PROJECT_ROOT, save_dir_value)

SAVE_DIR = save_dir_base / f"configs_{datetime.now():%Y%m%d}"
SAVE_DIR.mkdir(parents=True, exist_ok=True)

settings["_current_pageinfo_path"] = str(
    SAVE_DIR / "samidare_current_pageinfo_latest.json"
)
settings["_data_name_state_path"] = str(
    SAVE_DIR / "samidare_data_name_state.json"
)

sendCommand = get_required_function(settings, "send_command")

current_pageinfo_cache = None

def load_data_name_state() -> dict:
    path = Path(settings["_data_name_state_path"])

    if not path.exists():
        return {
            "enabled": False,
            "run_name": "run",
            "run_number": 0,
        }

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_data_name_state(state: dict) -> None:
    path = Path(settings["_data_name_state_path"])
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        json.dump(state, f, indent=4, ensure_ascii=False)


data_name_state = load_data_name_state()

app = FastAPI()

api_settings = settings.get("api", {})

api_prefix = api_settings.get("prefix", "/api/samidare")
run_route = api_settings.get("run_route", "/run")
status_route = api_settings.get("status_route", "/status")
server_name = api_settings.get("server", None)


def build_cors_origins(server_name: str | None) -> list[str]:
    url_list = [
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ]

    if not server_name:
        return url_list

    try:
        ip_address = socket.gethostbyname(server_name)
        print(f"OK: {server_name} -> {ip_address}")

        url_list.append(f"http://{server_name}:8080")

        if server_name != ip_address:
            url_list.append(f"http://{ip_address}:8080")

    except socket.gaierror as e:
        print(f"NG: cannot resolve hostname '{server_name}': {e}")

    return url_list


url_list = build_cors_origins(server_name)

print("CORS allow_origins:")
for url in url_list:
    print("  ", url)


app.add_middleware(
    CORSMiddleware,
    allow_origins=url_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

samidare_router = APIRouter(prefix=api_prefix, tags=["samidare"])


@app.get("/")
async def root():
    return {
        "message": "FastAPI backend is running",
        "devices": {
            "samidare": {
                "root_endpoint": api_prefix,
                "run_endpoint": f"{api_prefix}{run_route}",
                "initial_params_endpoint": f"{api_prefix}{status_route}/initial-param",
                "current_pageinfo_endpoint": f"{api_prefix}{status_route}/current-pageinfo",
                "data_name_endpoint": f"{api_prefix}{status_route}/data-name",
            }
        },
        "cors_origins": url_list,
    }


@samidare_router.get("/")
async def samidare_root():
    return {
        "message": "SAMIDARE API is running",
        "run_endpoint": f"{api_prefix}{run_route}",
        "initial_params_endpoint": f"{api_prefix}{status_route}/initial-param",
        "current_pageinfo_endpoint": f"{api_prefix}{status_route}/current-pageinfo",
        "data_name_endpoint": f"{api_prefix}{status_route}/data-name",
        "available_functions": sorted(settings.get("functions", {}).keys()),
        "cors_origins": url_list,
    }


@samidare_router.post(run_route)
async def run_backend_function(request: dict):
    try:
        function_name = request.get("function")
        params = request.get("params", {})

        if not function_name:
            return JSONResponse(
                content={
                    "message": "Missing required field: function",
                    "example": {
                        "function": "get_status",
                        "params": {},
                    },
                },
                status_code=400,
            )

        if not isinstance(params, dict):
            return JSONResponse(
                content={
                    "message": "params must be an object",
                    "example": {
                        "function": "set_gain",
                        "params": {
                            "gain": 3,
                        },
                    },
                },
                status_code=400,
            )

        func = get_required_function(settings, function_name)

        save_log = should_save_log(function_name, settings)
        json_filename, output_filename = make_output_paths(
            function_name,
            SAVE_DIR,
            save_log=save_log,
        )

        result = func(
            **params,
            config_path=str(config_path),
            output_path=str(output_filename),
            settings=settings,
        )

        response_content = {
            "message": f"Successfully executed {function_name}",
            "function": function_name,
            "params": params,
            "command_result": result,
            "json_file": str(json_filename),
            "output_file": str(output_filename),
        }

        if save_log and json_filename is not None:
            json_filename.parent.mkdir(parents=True, exist_ok=True)

            with json_filename.open("w", encoding="utf-8") as f:
                json.dump(response_content, f, indent=4, ensure_ascii=False)

        return JSONResponse(content=response_content)

    except Exception as e:
        function_name = request.get("function", "unknown")
        params = request.get("params", {})

        save_log = should_save_log(function_name, settings)

        error_content = {
            "message": f"Error executing backend function: {e}",
            "function": function_name,
            "params": params,
            "log_saved": False,
            "json_file": None,
        }

        if save_log:
            try:
                json_filename, _ = make_output_paths(
                    f"{function_name}_error",
                    SAVE_DIR,
                    save_log=True,
                )

                if json_filename is not None:
                    with json_filename.open("w", encoding="utf-8") as f:
                        json.dump(error_content, f, indent=4, ensure_ascii=False)

                    error_content["json_file"] = str(json_filename)
                    error_content["log_saved"] = True

            except Exception as save_error:
                error_content["json_save_error"] = str(save_error)

        return JSONResponse(
            content=error_content,
            status_code=500,
        )


@samidare_router.get(f"{status_route}/initial-param")
async def get_initial_parameters():
    try:
        params_result = get_initial_params(config_path)

        return JSONResponse(
            content={
                "message": "SAMIDARE initial parameters",
                "params": params_result["params"],
                "params_path": params_result["params_path"],
            }
        )

    except Exception as e:
        return JSONResponse(
            content={
                "message": f"Error loading SAMIDARE initial parameters: {e}",
            },
            status_code=500,
        )


@samidare_router.post(f"{status_route}/current-pageinfo")
async def post_current_pageinfo(request: dict):
    global current_pageinfo_cache

    current_pageinfo_cache = {
        "saved_at": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "current_pageinfo": request,
        "data_name_increment": data_name_state,
    }

    latest_path = Path(settings["_current_pageinfo_path"])
    latest_path.parent.mkdir(parents=True, exist_ok=True)

    with latest_path.open("w", encoding="utf-8") as f:
        json.dump(current_pageinfo_cache, f, indent=4, ensure_ascii=False)

    return JSONResponse(
        content={
            "message": "Received current page info",
            "json_file": str(latest_path),
            **current_pageinfo_cache,
        }
    )


@samidare_router.get(f"{status_route}/current-pageinfo")
async def get_current_pageinfo():
    global current_pageinfo_cache

    if current_pageinfo_cache is not None:
        return JSONResponse(
            content={
                "message": "Successfully loaded current page info",
                **current_pageinfo_cache,
                "data_name_increment": data_name_state,
            }
        )

    latest_path = Path(settings["_current_pageinfo_path"])

    if latest_path.exists():
        with latest_path.open("r", encoding="utf-8") as f:
            current_pageinfo_cache = json.load(f)

        return JSONResponse(
            content={
                "message": "Successfully loaded current page info",
                "json_file": str(latest_path),
                **current_pageinfo_cache,
                "data_name_increment": data_name_state,
            }
        )

    return JSONResponse(
        content={
            "message": "No current page info received yet",
            "current_pageinfo": None,
            "data_name_increment": data_name_state,
            "json_file": str(latest_path),
        }
    )


@samidare_router.get(f"{status_route}/data-name")
async def get_data_name_state():
    return JSONResponse(
        content={
            "message": "Successfully loaded data name state",
            "data_name_increment": data_name_state,
        }
    )


@samidare_router.post(f"{status_route}/data-name")
async def update_data_name_state(request: dict):
    global data_name_state

    try:
        if "enabled" in request:
            data_name_state["enabled"] = bool(request["enabled"])

        if "run_name" in request:
            run_name = str(request["run_name"]).strip()
            if not run_name:
                raise ValueError("run_name must not be empty")
            data_name_state["run_name"] = run_name

        if "run_number" in request:
            data_name_state["run_number"] = int(request["run_number"])

        save_data_name_state(data_name_state)

        return JSONResponse(
            content={
                "message": "Successfully updated data name state",
                "data_name_increment": data_name_state,
                "json_file": settings["_data_name_state_path"],
            }
        )

    except Exception as e:
        return JSONResponse(
            content={
                "message": f"Error updating data name state: {e}",
            },
            status_code=500,
        )


@samidare_router.post(f"{status_route}/data-name/increment")
async def increment_data_name_run_number():
    global data_name_state

    data_name_state["run_number"] = int(data_name_state.get("run_number", 0)) + 1
    save_data_name_state(data_name_state)

    return JSONResponse(
        content={
            "message": "Successfully incremented run number",
            "data_name_increment": data_name_state,
            "json_file": settings["_data_name_state_path"],
        }
    )


app.include_router(samidare_router)
