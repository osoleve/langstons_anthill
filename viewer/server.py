"""Viewer server. Renders game state as a living map."""

import json
import time
from pathlib import Path
from flask import Flask, Response, send_from_directory

app = Flask(__name__, static_folder='static')

STATE_FILE = Path(__file__).parent.parent / "state" / "game.json"


def load_state():
    """Load current game state."""
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return None


@app.route('/')
def index():
    """Serve the main viewer page."""
    return send_from_directory('static', 'index.html')


@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files."""
    return send_from_directory('static', filename)


@app.route('/state')
def state():
    """Return current state as JSON."""
    state = load_state()
    if state:
        return json.dumps(state)
    return json.dumps({"error": "no state"})


@app.route('/events')
def events():
    """SSE endpoint for live updates."""
    def generate():
        last_tick = -1
        while True:
            state = load_state()
            if state and state.get("tick", 0) != last_tick:
                last_tick = state.get("tick", 0)
                yield f"data: {json.dumps(state)}\n\n"
            time.sleep(0.5)

    return Response(generate(), mimetype='text/event-stream')


if __name__ == '__main__':
    print("[viewer] starting on http://localhost:5000")
    app.run(debug=True, threaded=True, port=5000)
