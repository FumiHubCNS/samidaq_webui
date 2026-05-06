from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import json
from pathlib import Path
import subprocess
from .helpers.mainHelpers import (
    load_toml_config,
    get_required_function,
    get_optional_function,
    get_setting,
    resolve_path,
    make_output_paths,
)

from fastapi.responses import JSONResponse

PROJECT_ROOT = Path(__file__).resolve().parents[4]
CONFIG_PATH = PROJECT_ROOT / "config" / "samidare.toml"

if 1: # Debug: Print resolved paths
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

sendCommand = get_required_function(settings, "send_command")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_settings = settings.get("api", {})

api_prefix = api_settings.get("prefix", "/api/samidare")
run_route = api_settings.get("run_route", "/run")

samidare_router = APIRouter(prefix=api_prefix, tags=["samidare"])


@app.get("/")
async def root():
    return {
        "message": "FastAPI backend is running",
        "devices": {
            "samidare": {
                "root_endpoint": api_prefix,
                "run_endpoint": f"{api_prefix}/run",
            }
        },
    }


@samidare_router.get("/")
async def samidare_root():
    return {
        "message": "SAMIDARE API is running",
        "run_endpoint": f"{api_prefix}/run",
        "available_functions": sorted(settings.get("functions", {}).keys()),
    }


@samidare_router.post("/run")
async def run_backend_function(request: dict):
    try:
        function_name = request.get("function")
        params = request.get("params", {})

        if not function_name:
            return JSONResponse(
                content={"message": "Missing required field: function"},
                status_code=400,
            )

        if not isinstance(params, dict):
            return JSONResponse(
                content={"message": "params must be an object"},
                status_code=400,
            )

        func = get_required_function(settings, function_name)
        json_filename, output_filename = make_output_paths(function_name, SAVE_DIR)

        result = func(
            **params,
            config_path=str(config_path),
            output_path=output_filename,
            settings=settings,
        )

        return JSONResponse(
            content={
                "message": f"Successfully executed {function_name}",
                "function": function_name,
                "params": params,
                "command_result": result,
                "json_file": str(json_filename),
                "output_file": str(output_filename),
            }
        )

    except Exception as e:
        return JSONResponse(
            content={
                "message": f"Error executing backend function: {e}",
            },
            status_code=500,
        )

app.include_router(samidare_router)