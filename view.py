#!/usr/bin/env python3
"""
View the colony.

Builds the viewer if needed, then starts the server.
Opens http://localhost:5000 in your browser.

Usage:
    python view.py           # Build and serve
    python view.py --dev     # Use Vite dev server (hot reload)
    python view.py --rebuild # Force rebuild
"""

import subprocess
import sys
import webbrowser
from pathlib import Path
import time

VIEWER_DIR = Path(__file__).parent / "viewer"
DIST_DIR = VIEWER_DIR / "dist"


def run_npm_build():
    """Build the viewer with Vite."""
    print("[viewer] Building...")
    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=VIEWER_DIR,
        shell=True  # Needed on Windows
    )
    if result.returncode != 0:
        print("[viewer] Build failed!")
        sys.exit(1)
    print("[viewer] Build complete.")


def check_npm_installed():
    """Check if npm is available."""
    try:
        subprocess.run(
            ["npm", "--version"],
            capture_output=True,
            shell=True
        )
        return True
    except FileNotFoundError:
        return False


def main():
    args = sys.argv[1:]
    dev_mode = "--dev" in args
    force_rebuild = "--rebuild" in args

    if not check_npm_installed():
        print("[viewer] Error: npm not found. Install Node.js first.")
        sys.exit(1)

    # Check if node_modules exists
    if not (VIEWER_DIR / "node_modules").exists():
        print("[viewer] Installing dependencies...")
        subprocess.run(["npm", "install"], cwd=VIEWER_DIR, shell=True)

    if dev_mode:
        # Dev mode: run Vite dev server + FastAPI in parallel
        print("[viewer] Starting in development mode...")
        print("[viewer] Vite dev server: http://localhost:5173")
        print("[viewer] FastAPI server:  http://localhost:5000")
        print("[viewer] Use http://localhost:5173 for hot reload")
        print()

        # Start FastAPI in background
        import threading

        def run_fastapi():
            subprocess.run(
                [sys.executable, "-m", "uvicorn", "viewer.server:app",
                 "--port", "5000", "--reload"],
                cwd=Path(__file__).parent
            )

        api_thread = threading.Thread(target=run_fastapi, daemon=True)
        api_thread.start()

        # Give FastAPI a moment to start
        time.sleep(1)

        # Open browser
        webbrowser.open("http://localhost:5173")

        # Run Vite in foreground
        subprocess.run(["npm", "run", "dev"], cwd=VIEWER_DIR, shell=True)

    else:
        # Production mode: build then serve
        if force_rebuild or not DIST_DIR.exists():
            run_npm_build()
        else:
            # Check if source is newer than build
            src_dir = VIEWER_DIR / "src"
            if src_dir.exists():
                src_mtime = max(f.stat().st_mtime for f in src_dir.rglob("*") if f.is_file())
                dist_mtime = DIST_DIR.stat().st_mtime
                if src_mtime > dist_mtime:
                    print("[viewer] Source changed, rebuilding...")
                    run_npm_build()

        print("[viewer] Starting server...")
        print("[viewer] Open http://localhost:5000")
        print("[viewer] Click on the map to bless the colony!")
        print()

        # Open browser after a short delay
        def open_browser():
            time.sleep(1.5)
            webbrowser.open("http://localhost:5000")

        import threading
        threading.Thread(target=open_browser, daemon=True).start()

        # Run FastAPI server
        subprocess.run(
            [sys.executable, "-m", "uvicorn", "viewer.server:app",
             "--host", "0.0.0.0", "--port", "5000"],
            cwd=Path(__file__).parent
        )


if __name__ == "__main__":
    main()
