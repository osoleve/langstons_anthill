"""
Viewer server - FastAPI with SSE and static file serving.

Run with: python viewer/server.py
Or: uvicorn viewer.server:app --reload --port 5000
"""

import asyncio
import json
import time
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse

# Paths
VIEWER_DIR = Path(__file__).parent
PROJECT_DIR = VIEWER_DIR.parent
STATE_FILE = PROJECT_DIR / "state" / "game.json"
DECISIONS_FILE = PROJECT_DIR / "logs" / "decisions.jsonl"
BLESSINGS_FILE = PROJECT_DIR / "state" / "blessings.json"
DIST_DIR = VIEWER_DIR / "dist"


def load_state() -> dict | None:
    """Load current game state."""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return None


def load_decisions(limit: int = 10) -> list:
    """Load recent decisions from the JSONL log."""
    if not DECISIONS_FILE.exists():
        return []

    decisions = []
    with open(DECISIONS_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    decisions.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    return decisions[-limit:]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown events."""
    # Check if dist exists, warn if not
    if not DIST_DIR.exists():
        print("[viewer] Warning: dist/ not found. Run 'npm run build' first.")
        print("[viewer] Or use 'npm run dev' for development with hot reload.")
    else:
        print(f"[viewer] Serving built files from {DIST_DIR}")

    print("[viewer] Starting on http://localhost:5000")
    print("[viewer] Observers can click on the map to bless the colony")
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/state")
async def get_state():
    """Return current game state as JSON."""
    state = load_state()
    if state:
        return JSONResponse(content=state)
    return JSONResponse(content={"error": "no state"})


@app.get("/decisions")
async def get_decisions():
    """Return recent decisions as JSON array."""
    decisions = load_decisions(limit=10)
    return JSONResponse(content=decisions)


@app.get("/events")
async def events(request: Request):
    """SSE endpoint for live state updates."""
    async def event_generator():
        last_tick = -1
        while True:
            if await request.is_disconnected():
                break

            state = load_state()
            if state and state.get("tick", 0) != last_tick:
                last_tick = state.get("tick", 0)
                yield {
                    "event": "message",
                    "data": json.dumps(state)
                }

            await asyncio.sleep(0.5)

    return EventSourceResponse(event_generator())


@app.post("/bless")
async def bless(request: Request):
    """
    Accept blessings from observers.
    Blessings are accumulated and applied to game state by the tick engine.
    """
    try:
        data = await request.json()
        blessings = data.get('blessings', [])

        if not blessings:
            return JSONResponse(content={"status": "no_blessings"})

        # Load existing blessings or create new
        pending = {"blessings": [], "total_influence": 0}
        if BLESSINGS_FILE.exists():
            try:
                with open(BLESSINGS_FILE, 'r') as f:
                    pending = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass

        # Add new blessings
        for b in blessings:
            pending["blessings"].append({
                "type": b.get("type", "touch"),
                "tile_id": b.get("tileId"),
                "amount": b.get("amount", 0.1),
                "timestamp": time.time()
            })
            pending["total_influence"] += b.get("amount", 0.1)

        # Save
        with open(BLESSINGS_FILE, 'w') as f:
            json.dump(pending, f)

        return JSONResponse(content={
            "status": "blessed",
            "count": len(blessings),
            "total_pending": pending["total_influence"]
        })

    except Exception as e:
        return JSONResponse(
            content={"status": "error", "message": str(e)},
            status_code=500
        )


@app.get("/blessings")
async def get_blessings():
    """Get pending blessings (for tick engine to consume)."""
    if BLESSINGS_FILE.exists():
        try:
            with open(BLESSINGS_FILE, 'r') as f:
                return JSONResponse(content=json.load(f))
        except (json.JSONDecodeError, IOError):
            pass
    return JSONResponse(content={"blessings": [], "total_influence": 0})


@app.post("/blessings/clear")
async def clear_blessings():
    """Clear pending blessings after they've been applied."""
    with open(BLESSINGS_FILE, 'w') as f:
        json.dump({"blessings": [], "total_influence": 0}, f)
    return JSONResponse(content={"status": "cleared"})


# Mount static files LAST so API routes take precedence
# This serves the built Vite output
if DIST_DIR.exists():
    app.mount("/assets", StaticFiles(directory=DIST_DIR / "assets"), name="assets")

    @app.get("/", response_class=HTMLResponse)
    async def serve_index():
        """Serve the main HTML page."""
        index_path = DIST_DIR / "index.html"
        if index_path.exists():
            return HTMLResponse(content=index_path.read_text())
        return HTMLResponse(content="<h1>Build not found. Run: cd viewer && npm run build</h1>")


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(
        "viewer.server:app",
        host="0.0.0.0",
        port=5000,
        reload=True,
        reload_dirs=[str(PROJECT_DIR)]
    )
