# Design: API Refactor and Sync Fix

## Architecture Overview

Split the monolithic `api.py` (1222 lines) into a modular `api/` package while fixing the sync bug. The daemon-client architecture remains unchanged.

```
Before:                          After:
webtap/                          webtap/
├── api.py (1222 lines)          ├── api/
├── ...                          │   ├── __init__.py      (~20 lines)
                                 │   ├── app.py           (~50 lines)
                                 │   ├── models.py        (~60 lines)
                                 │   ├── state.py         (~80 lines)
                                 │   ├── sse.py           (~120 lines)
                                 │   ├── server.py        (~150 lines)
                                 │   └── routes/
                                 │       ├── __init__.py  (~30 lines)
                                 │       ├── events.py    (~100 lines)
                                 │       ├── data.py      (~120 lines)
                                 │       ├── fetch.py     (~100 lines)
                                 │       ├── connection.py (~120 lines)
                                 │       ├── filters.py   (~100 lines)
                                 │       └── browser.py   (~60 lines)
```

## Component Design

### `api/__init__.py` - Public Exports

```python
"""WebTap API package.

PUBLIC API:
  - run_daemon_server: Run daemon server (blocking)
"""

from webtap.api.server import run_daemon_server

__all__ = ["run_daemon_server"]
```

Note: `start_api_server` removed - daemon-only architecture.

### `api/app.py` - FastAPI Application

```python
"""FastAPI application and shared state."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

api = FastAPI(title="WebTap API", version="0.1.0")

api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state - set by server.py on startup
app_state: "Any | None" = None
```

### `api/models.py` - Pydantic Request Models

All request models in one place:
- `ConnectRequest`
- `FetchRequest`
- `ClearRequest`
- `QueryRequest`
- `CDPRequest`
- `ResumeRequest`
- `FailRequest`
- `FulfillRequest`
- `PrepareBodyRequest`

### `api/state.py` - State Helpers

```python
"""State management for SSE broadcasting."""

import hashlib
from webtap.api.app import app_state

def _stable_hash(data: str) -> str:
    """MD5 hash for frontend change detection."""
    return hashlib.md5(data.encode()).hexdigest()[:16]

def get_full_state() -> dict:
    """Get complete state for SSE/response.

    Returns immutable snapshot - thread-safe, no locks.
    """
    if not app_state:
        return {
            "connected": False,
            "events": {"total": 0},
            "fetch": {"enabled": False, "paused_count": 0},
            "filters": {"enabled": [], "disabled": []},
            "browser": {"inspect_active": False, "selections": {}, "prompt": "", "pending_count": 0},
            "error": None,
        }

    snapshot = app_state.service.get_state_snapshot()
    # ... build state dict with hashes ...
```

### `api/sse.py` - Server-Sent Events

```python
"""SSE streaming and broadcast management."""

import asyncio
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter()

# SSE client management
_sse_clients: set[asyncio.Queue] = set()
_sse_clients_lock = asyncio.Lock()
_broadcast_queue: asyncio.Queue | None = None

@router.get("/events/stream")
async def stream_events():
    """SSE endpoint for real-time state updates."""
    # ... implementation ...

async def broadcast_state():
    """Send state to all SSE clients."""
    # ... implementation ...

async def broadcast_processor():
    """Background task processing broadcast queue."""
    global _broadcast_queue
    _broadcast_queue = asyncio.Queue()
    # ... implementation ...

def get_broadcast_queue() -> asyncio.Queue | None:
    """Get broadcast queue for wiring to service."""
    return _broadcast_queue
```

### `api/server.py` - Server Lifecycle

```python
"""Daemon server lifecycle management."""

import asyncio
import uvicorn
from webtap.api.app import api, app_state
from webtap.api.sse import broadcast_processor, get_broadcast_queue
from webtap.api.routes import include_routes
from webtap.daemon_state import DaemonState

def run_daemon_server(host: str = "127.0.0.1", port: int = 8765):
    """Run daemon server in foreground (blocking).

    Called by daemon.py for --daemon mode.
    """
    global app_state

    # Include all routes
    include_routes(api)

    # Initialize daemon state
    app_state = DaemonState()

    async def run():
        config = uvicorn.Config(api, host=host, port=port, log_level="warning", access_log=False)
        server = uvicorn.Server(config)

        # Start broadcast processor
        broadcast_task = asyncio.create_task(broadcast_processor())

        # SYNC FIX: Wire broadcast queue to service
        await asyncio.sleep(0.1)  # Let processor create queue
        queue = get_broadcast_queue()
        if queue and app_state:
            app_state.service.set_broadcast_queue(queue)

        try:
            await server.serve()
        finally:
            broadcast_task.cancel()
            # ... cleanup ...

    asyncio.run(run())
```

### `api/routes/__init__.py` - Router Registration

```python
"""Route registration."""

from fastapi import FastAPI

def include_routes(app: FastAPI):
    """Include all route modules."""
    from webtap.api.routes import events, data, fetch, connection, filters, browser
    from webtap.api.sse import router as sse_router

    app.include_router(events.router)
    app.include_router(data.router)
    app.include_router(fetch.router)
    app.include_router(connection.router)
    app.include_router(filters.router)
    app.include_router(browser.router)
    app.include_router(sse_router)
```

### `api/routes/connection.py` - Connection Endpoints

**SYNC FIX: All action endpoints return state**

```python
"""Connection and status endpoints."""

from fastapi import APIRouter
from webtap.api.app import app_state
from webtap.api.state import get_full_state
from webtap.api.models import ConnectRequest, ClearRequest

router = APIRouter()

@router.post("/connect")
async def connect(request: ConnectRequest) -> dict:
    if not app_state:
        return {"error": "WebTap not initialized", "state": get_full_state()}

    result = await asyncio.to_thread(app_state.service.connect_to_page, page_id=request.page_id)
    return {**result, "state": get_full_state()}  # SYNC FIX

@router.post("/disconnect")
async def disconnect() -> dict:
    if not app_state:
        return {"error": "WebTap not initialized", "state": get_full_state()}

    result = await asyncio.to_thread(app_state.service.disconnect)
    return {**result, "state": get_full_state()}  # SYNC FIX

@router.post("/clear")
async def clear_data(request: ClearRequest) -> dict:
    # ... implementation ...
    return {"cleared": cleared, "state": get_full_state()}  # SYNC FIX

@router.get("/health")
async def health_check() -> dict:
    return {"status": "ok", "pid": os.getpid()}

@router.get("/status")
async def get_status() -> dict:
    # ... implementation ...

@router.get("/info")
async def get_info() -> dict:
    # ... implementation ...

@router.get("/pages")
async def get_pages() -> dict:
    # ... implementation ...
```

### Route Module Breakdown

| Module | Endpoints | Lines |
|--------|-----------|-------|
| `events.py` | `/events`, `/event/{rowid}`, `/query`, `/cdp` | ~100 |
| `data.py` | `/network`, `/body/{rowid}`, `/body/{rowid}/prepare`, `/console` | ~120 |
| `fetch.py` | `/fetch`, `/paused`, `/resume`, `/fail`, `/fulfill` | ~100 |
| `connection.py` | `/connect`, `/disconnect`, `/clear`, `/health`, `/status`, `/info`, `/pages` | ~120 |
| `filters.py` | `/filters/status`, `/filters/toggle/{category}`, `/filters/enable-all`, `/filters/disable-all`, `/filters/reload` | ~100 |
| `browser.py` | `/browser/start-inspect`, `/browser/stop-inspect`, `/browser/clear`, `/errors/dismiss` | ~60 |

## Extension Changes

### `sidepanel.js` - Immediate State Updates

**New helper function:**

```javascript
function updateFromState(newState) {
  state = newState;
  updateConnectionStatus(newState);
  updateEventCount(newState.events.total);
  updateButtons(newState.connected);
  updateErrorBanner(newState.error);
  updateFetchStatus(newState.fetch.enabled, newState.fetch.paused_count);
  updateFiltersUI(newState.filters);
  updateSelectionUI(newState.browser);

  // Update hashes to prevent SSE double-render
  previousHashes = {
    selections: newState.selections_hash,
    filters: newState.filters_hash,
    fetch: newState.fetch_hash,
    page: newState.page_hash,
    error: newState.error_hash,
  };
}
```

**Updated action handlers:**

```javascript
// Connect
const result = await api("/connect", "POST", { page_id: selectedPageId });
if (result.state) updateFromState(result.state);
if (result.error) showError(result.error);

// Disconnect
const result = await api("/disconnect", "POST");
if (result.state) updateFromState(result.state);

// Clear
const result = await api("/clear", "POST", { events: true });
if (result.state) updateFromState(result.state);

// Fetch toggle
const result = await api("/fetch", "POST", { enabled: !currentState });
if (result.state) updateFromState(result.state);
```

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     Action Response Flow                         │
├─────────────────────────────────────────────────────────────────┤
│  1. User clicks "Connect" in extension                          │
│  2. POST /connect {page_id}                                     │
│  3. Server executes connect, gets full state                    │
│  4. Response: {connected: true, title, url, state: {...}}       │
│  5. Extension calls updateFromState(response.state)             │
│  6. UI updates IMMEDIATELY                                      │
│  7. SSE also broadcasts (for other clients)                     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                     Background Update Flow                       │
├─────────────────────────────────────────────────────────────────┤
│  1. CDP event arrives at daemon                                 │
│  2. WebTapService._trigger_broadcast() queues update            │
│  3. broadcast_processor() receives signal                       │
│  4. broadcast_state() sends to all SSE clients                  │
│  5. Extension receives SSE, checks hashes                       │
│  6. If changed, updates relevant UI section                     │
└─────────────────────────────────────────────────────────────────┘
```

## Error Handling

All endpoints follow consistent pattern:

```python
@router.post("/endpoint")
async def endpoint(request: Request) -> dict:
    if not app_state:
        return {"error": "WebTap not initialized", "state": get_full_state()}

    try:
        result = await asyncio.to_thread(service_method, ...)
        return {**result, "state": get_full_state()}
    except Exception as e:
        return {"error": str(e), "state": get_full_state()}
```

**Key principle:** Always return state, even on error.

## Import Updates Required

After refactor, update imports in:

| File | Old Import | New Import |
|------|------------|------------|
| `daemon.py` | `from webtap.api import run_daemon_server` | `from webtap.api import run_daemon_server` (unchanged) |
| `__init__.py` | `from webtap.api import start_api_server` | Remove (daemon-only) |

## File Deletion

After successful refactor:
- Delete `webtap/api.py` (replaced by `webtap/api/` package)

## Security Considerations

- No new attack surface (same endpoints)
- State contains no secrets (connection status, counts, hashes)
- All requests localhost-only (127.0.0.1:8765)
