from fastapi import FastAPI, APIRouter
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
)

from fastapi.responses import JSONResponse

PROJECT_ROOT = Path(__file__).resolve().parents[3]
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

api_settings = settings.get("api", {})

api_prefix = api_settings.get("prefix", "/api/samidare")
status_route = api_settings.get("status_route", "/status")
command_route = api_settings.get("command_route", "/command")

samidare_router = APIRouter(prefix=api_prefix, tags=["samidare"])


@app.get("/")
async def root():
    return {
        "message": "FastAPI backend is running",
        "devices": {
            "samidare": {
                "root_endpoint": api_prefix,
                "status_endpoint": f"{api_prefix}{status_route}",
                "command_endpoint": f"{api_prefix}{command_route}",
            }
        },
    }


@samidare_router.get("/")
async def samidare_root():
    return {
        "message": "SAMIDARE API is running",
        "status_endpoint": f"{api_prefix}{status_route}",
        "command_endpoint": f"{api_prefix}{command_route}",
    }


@samidare_router.get(status_route)
async def get_samidare_status():
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        json_filename = SAVE_DIR / f"samidare_status_request_{timestamp}.json"
        output_filename = SAVE_DIR / f"samidare_status_output_{timestamp}.txt"

        request = {
            "command": "status",
        }

        with json_filename.open("w") as f:
            json.dump(request, f, indent=4)

        command_result = sendCommand(
            request=request,
            config_path=str(config_path),
            output_path=str(output_filename),
            settings=settings,
        )

        return JSONResponse(
            content={
                "message": "Successfully sent SAMIDARE status command",
                "json_file": str(json_filename),
                "output_file": str(output_filename),
                "command_result": command_result,
            }
        )

    except Exception as e:
        return JSONResponse(
            content={
                "message": f"Error sending SAMIDARE status command: {e}",
            },
            status_code=500,
        )


@samidare_router.post(command_route)
async def post_samidare_command(request: dict):
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        json_filename = SAVE_DIR / f"samidare_command_request_{timestamp}.json"
        output_filename = SAVE_DIR / f"samidare_command_output_{timestamp}.txt"

        with json_filename.open("w") as f:
            json.dump(request, f, indent=4)

        command_result = sendCommand(
            request=request,
            config_path=str(config_path),
            output_path=str(output_filename),
            settings=settings,
        )

        return JSONResponse(
            content={
                "message": "Successfully sent SAMIDARE command",
                "json_file": str(json_filename),
                "output_file": str(output_filename),
                "command_result": command_result,
            }
        )

    except Exception as e:
        return JSONResponse(
            content={
                "message": f"Error sending SAMIDARE command: {e}",
            },
            status_code=500,
        )


app.include_router(samidare_router)