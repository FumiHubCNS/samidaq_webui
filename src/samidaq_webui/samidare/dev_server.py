from __future__ import annotations

import signal
import subprocess
import sys
from pathlib import Path

import click


@click.command()
@click.option(
    "--start-samdaq/--no-start-samdaq",
    "-s/-n",
    default=False,
    help="Start SAMDAQ tmux session before launching the WebUI.",
)
@click.option(
    "--samdaq-dir",
    default=None,
    help="Optional SAM_DAQ directory passed to start_samdaq.sh.",
)
def main(start_samdaq: bool, samdaq_dir: str | None) -> None:
    project_root = Path(__file__).resolve().parents[3]

    frontend_dir = (
        project_root
        / "src"
        / "samidaq_webui"
        / "samidare"
        / "Frontend"
    )

    start_samdaq_script = (
        project_root
        / "src"
        / "samidaq_webui"
        / "samidare"
        / "Scripts"
        / "start_samdaq.sh"
    )

    if not frontend_dir.exists():
        raise FileNotFoundError(f"Frontend directory not found: {frontend_dir}")

    if start_samdaq and not start_samdaq_script.exists():
        raise FileNotFoundError(f"SAMDAQ start script not found: {start_samdaq_script}")

    if start_samdaq:
        cmd = [str(start_samdaq_script)]

        if samdaq_dir:
            cmd.append(samdaq_dir)

        print(f"[INFO] Starting SAMDAQ with: {' '.join(cmd)}")
        subprocess.run(
            cmd,
            cwd=project_root,
            check=True,
        )

    backend_cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "src.samidaq_webui.samidare.Backend.main:app",
        "--reload",
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
    ]

    frontend_cmd = [
        sys.executable,
        "-m",
        "http.server",
        "8080",
    ]

    processes: list[subprocess.Popen] = []

    try:
        print("[INFO] Starting FastAPI backend: http://127.0.0.1:8000")
        backend = subprocess.Popen(
            backend_cmd,
            cwd=project_root,
        )
        processes.append(backend)

        print("[INFO] Starting frontend: http://127.0.0.1:8080")
        frontend = subprocess.Popen(
            frontend_cmd,
            cwd=frontend_dir,
        )
        processes.append(frontend)

        print("[INFO] Press Ctrl+C to stop both servers.")

        for process in processes:
            process.wait()

    except KeyboardInterrupt:
        print("\n[INFO] Stopping servers...")

    finally:
        for process in processes:
            if process.poll() is None:
                process.send_signal(signal.SIGINT)

        for process in processes:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()

        print("[INFO] Stopped.")


if __name__ == "__main__":
    main()