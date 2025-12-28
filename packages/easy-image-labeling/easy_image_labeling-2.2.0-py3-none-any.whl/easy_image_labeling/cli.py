import argparse
import os
import subprocess
import signal
import sys

PID_FILE = "easy_image_labeling.pid"


def start():
    """Starts the Flask app and saves the PID."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-debug",
        action=argparse.BooleanOptionalAction,
        help="Start flask server in debug mode.",
    )
    args = parser.parse_args()

    if os.path.exists(PID_FILE):
        print("Flask app already running.")
        return

    # Start the app in a subprocess
    process = subprocess.Popen(
        [sys.executable, "-m", "flask", "run"],
        env={
            **os.environ,
            "FLASK_APP": "easy_image_labeling.main",
            "FLASK_DEBUG": "1" if args.debug else "0",
        },
    )

    with open(PID_FILE, "w") as f:
        f.write(str(process.pid))

    print(f"Flask app started with PID {process.pid}")


def stop():
    """Stops the Flask app using the saved PID."""
    if not os.path.exists(PID_FILE):
        print("No running Flask app found.")
        return

    with open(PID_FILE, "r") as f:
        pid = int(f.read())

    try:
        os.kill(pid, signal.SIGTERM)
        print(f"Flask app with PID {pid} stopped.")
    except ProcessLookupError:
        print("Process not found. It may have already exited.")
    finally:
        os.remove(PID_FILE)
