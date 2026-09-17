# Demo UI

A single self-contained `index.html` (no build step, no npm install) that talks directly to the API for live demos.

## Features

- **Ask mode**: instant Q&A against the repository, no file edits, no tool calls.
- **Agent mode**: full autonomous edit/test loop with live SSE event stream and rendered diff.
- Apply/Reject/Cancel actions wired directly to the API.
- Live metrics panel (`/metrics`).

## Run it

No server needed — just open the file directly in a browser:

```bash
# from your local machine or the EC2 instance with a browser/X11, or just download the file locally
open ui/index.html      # macOS
start ui\index.html     # Windows
```

Or serve it over HTTP (useful if opening `file://` causes fetch/CORS quirks in your browser):

```bash
cd ui
python3 -m http.server 8090
```

Then visit `http://<host>:8090` (use the EC2 public/private IP if running remotely).

## Usage

1. Set **API base URL** (e.g. `http://127.0.0.1:8080` or the EC2 instance's reachable address) and **API key** (`dev-local-key` by default).
2. Set **workspace path** to a path *inside the API container* (e.g. `/workspace/coding-agent/examples/sample-repository`).
3. Click **New Session**.
4. Use **Ask mode** for quick Q&A, or **Agent mode** to run the full edit/test loop, watch live events, and review/apply the diff.

## Notes

- The API must have `REQUIRE_API_KEY` matching what you enter here (default: `dev-local-key`).
- CORS is already open (`allow_origins=["*"]`) in [services/api/src/enterprise_agent/api/app.py](../services/api/src/enterprise_agent/api/app.py), so no backend changes are needed to use this from any origin.
- Sessions are in-memory; if the API container restarts, click **New Session** again.
