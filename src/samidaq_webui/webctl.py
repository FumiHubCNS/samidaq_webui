from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional
import os
import subprocess
import threading
import time
from collections import deque

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

APP_DIR = Path(__file__).resolve().parent
TEMPLATES = Jinja2Templates(directory=str(APP_DIR / "templates"))

DATA_DIR = (APP_DIR / "../data").resolve()
SCRIPTS_DIR = (APP_DIR / "../scripts").resolve()
SEND_SH = str((SCRIPTS_DIR / "send.sh").resolve())
RUN_SH  = str((SCRIPTS_DIR / "run.sh").resolve())
STOP_SH = str((SCRIPTS_DIR / "stop.sh").resolve())

FIELD_TO_DAT: Dict[str, str] = {
    "run_number": "run_number.dat",
    "run_name": "run_name.dat",
    "setting1": "trig_type.dat",
    "setting2": "output_dir.dat",
    "setting3": "file_name.dat",
    "setting4": "polarity.dat",
    "setting5": "gain.dat",
    "setting6": "num_sample.dat",
    "setting7": "pre_sample.dat",
    "setting8": "clock_type.dat",
    "setting9": "trig_value.dat",
    "setting10": "comment.dat",
}

@dataclass
class FileStatus:
    path: Optional[Path] = None
    last_size: Optional[int] = None
    last_time: Optional[float] = None
    size: int = 0
    rate: float = 0.0
    running: bool = False

FILE_STATUS = FileStatus()

HISTORY_SECONDS = 60
size_history: deque[tuple[float, int]] = deque()

monitor_stop_event = threading.Event()
monitor_thread: Optional[threading.Thread] = None

app = FastAPI()


def read_dat_values() -> Dict[str, str]:
    vals: Dict[str, str] = {}
    for field, datname in FIELD_TO_DAT.items():
        p = DATA_DIR / datname
        vals[field] = p.read_text(encoding="utf-8").strip() if p.is_file() else ""
    return vals


def build_output_filepath(values: dict) -> Path:
    out_dir = values["setting2"]
    fname   = values["setting3"]
    runname = values["run_name"]
    runnum  = values["run_number"]

    base = Path(out_dir) / f"{fname}_{runname}_{runnum}"

    for cand in [base.with_suffix(".bin"), base.with_suffix(".root"), base]:
        if cand.exists():
            return cand

    return base.with_suffix(".bin")


def run_script(script_path: str, values: Dict[str, str]) -> str:
    env = os.environ.copy()
    env["RUN_NUMBER"] = values.get("run_number", "")
    env["RUN_NAME"] = values.get("run_name", "")
    for i in range(1, 11):
        env[f"SETTING{i}"] = values.get(f"setting{i}", "")

    cp = subprocess.run(
        ["/usr/bin/env", "bash", script_path],
        cwd=str(SCRIPTS_DIR),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    out = (cp.stdout or "")
    err = (cp.stderr or "")

    header = (
        f"[webctl] script={script_path}\n"
        f"[webctl] cwd={SCRIPTS_DIR}\n"
        f"[webctl] returncode={cp.returncode}\n"
        f"[webctl] DATA_DIR={DATA_DIR}\n"
    )
    return (header + "\n--- stdout ---\n" + out + "\n--- stderr ---\n" + err).strip()


def start_script_detached(script_path: str, values: Dict[str, str]) -> None:
    env = os.environ.copy()
    env["RUN_NUMBER"] = values.get("run_number", "")
    env["RUN_NAME"] = values.get("run_name", "")
    for i in range(1, 11):
        env[f"SETTING{i}"] = values.get(f"setting{i}", "")

    subprocess.Popen(
        ["/usr/bin/env", "bash", script_path],
        cwd=str(SCRIPTS_DIR),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def monitor_loop():
    while not monitor_stop_event.is_set():
        if FILE_STATUS.running and FILE_STATUS.path:
            p = FILE_STATUS.path

            if p.exists():
                now = time.time()
                size = p.stat().st_size

                if FILE_STATUS.last_time is not None and FILE_STATUS.last_size is not None:
                    dt = now - FILE_STATUS.last_time
                    if dt > 0:
                        FILE_STATUS.rate = (size - FILE_STATUS.last_size) / dt

                FILE_STATUS.size = size
                FILE_STATUS.last_size = size
                FILE_STATUS.last_time = now

                size_history.append((now, size))
                while size_history and size_history[0][0] < now - HISTORY_SECONDS:
                    size_history.popleft()

        time.sleep(1)


@app.on_event("startup")
def _startup():
    global monitor_thread
    monitor_stop_event.clear()
    monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
    monitor_thread.start()


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    values = read_dat_values()
    return TEMPLATES.TemplateResponse(
        "index.html",
        {"request": request, "values": values, "message": "", "log": ""},
    )


async def _handle_post(request: Request, script_path: str, ok_msg: str):
    form = await request.form()
    values = read_dat_values()
    for key in FIELD_TO_DAT.keys():
        if key in form:
            values[key] = str(form[key]).strip()

    log = run_script(script_path, values)
    values2 = read_dat_values()
    return TEMPLATES.TemplateResponse(
        "index.html",
        {"request": request, "values": values2, "message": ok_msg, "log": log},
    )


@app.post("/apply", response_class=HTMLResponse)
async def apply(request: Request):
    return await _handle_post(request, SEND_SH, "Applied settings (send.sh executed).")


@app.post("/run", response_class=HTMLResponse)
async def run(request: Request):
    form = await request.form()

    values = read_dat_values()
    for key in FIELD_TO_DAT.keys():
        if key in form:
            values[key] = str(form[key]).strip()

    FILE_STATUS.running = True
    FILE_STATUS.last_size = None
    FILE_STATUS.last_time = None
    FILE_STATUS.size = 0
    FILE_STATUS.rate = 0.0

    output_path = build_output_filepath(values)
    FILE_STATUS.path = output_path

    size_history.clear()

    start_script_detached(RUN_SH, values)

    return TEMPLATES.TemplateResponse(
        "index.html",
        {
            "request": request,
            "values": read_dat_values(),
            "message": f"Run started. Monitoring: {output_path}",
            "log": "",
        },
    )


@app.post("/stop", response_class=HTMLResponse)
async def stop(request: Request):
    FILE_STATUS.running = False
    _ = run_script(STOP_SH, read_dat_values())
    return TEMPLATES.TemplateResponse(
        "index.html",
        {"request": request, "values": read_dat_values(), "message": "Stopped.", "log": ""},
    )


@app.get("/status")
def status():
    BYTES_PER_MB = 1024 * 1024
    return {
        "path": str(FILE_STATUS.path) if FILE_STATUS.path else "",
        "exists": (FILE_STATUS.path.exists() if FILE_STATUS.path else False),
        "size_mb": round(FILE_STATUS.size / BYTES_PER_MB, 3),
        "rate_mb_s": round(FILE_STATUS.rate / BYTES_PER_MB, 3),
        "running": FILE_STATUS.running,
    }


@app.get("/status/history")
def status_history():
    if not size_history:
        return {"t": [], "size_mb": []}

    t0 = size_history[0][0]
    BYTES_PER_MB = 1024 * 1024
    times = [t - t0 for t, _ in size_history]
    sizes = [s / BYTES_PER_MB for _, s in size_history]
    return {"t": times, "size_mb": sizes}


def main(reload=True, host="0.0.0.0", port=8000)-> None:
    import uvicorn
    uvicorn.run("samidaq_webui.webctl:app", reload=reload, host=host, port=port)

if __name__ == "__main__": 
    main()