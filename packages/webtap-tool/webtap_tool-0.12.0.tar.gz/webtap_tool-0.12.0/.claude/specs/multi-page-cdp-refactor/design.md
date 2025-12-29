# Design: Multi-Page CDP Connection Refactor

## Architecture Overview

Remove "primary" CDPSession concept. Each page connection gets its own CDPSession. Services aggregate from all (or tracked) connections.

```
BEFORE:
  DaemonState.cdp_sessions: dict[int, CDPSession]  # ONE per port
  WebTapService.cdp = "primary" CDPSession         # Services wired to this
  WebTapService.connections: dict[str, ActiveConnection]

AFTER:
  DaemonState.registered_ports: set[int]           # Just port numbers
  WebTapService.connections: dict[str, ActiveConnection]  # Each has OWN CDPSession
  WebTapService.tracked_targets: list[str]         # Default scope for aggregation
  # NO primary - services query across connections
```

---

## Component Analysis

### Existing Components to Modify

#### `src/webtap/daemon_state.py`

**Current:**
```python
self.cdp = CDPSession()
self.cdp_sessions: dict[int, "CDPSession"] = {9222: self.cdp}
```

**Changes:**
```python
self.registered_ports: set[int] = {9222}
# Remove self.cdp entirely
```

- Remove `self.cdp` - no primary session
- Replace `cdp_sessions` dict with `registered_ports` set
- Update `cleanup()` - service owns CDPSession cleanup now

#### `src/webtap/services/main.py`

**Remove:**
- `self.cdp` assignment and all references (lines ~71, ~89-100)
- `_get_or_create_session()` method (lines ~676-694)
- All service wiring (`self.fetch.cdp = ...`, etc.)
- Primary promotion logic in `connect_to_page()` and `disconnect_target()`

**Add:**
```python
# Tracked targets for default aggregation scope
self.tracked_targets: list[str] = []

def get_tracked_or_all(self) -> list[str]:
    """Get tracked targets, or all connected if none tracked."""
    if self.tracked_targets:
        return [t for t in self.tracked_targets if t in self.connections]
    return list(self.connections.keys())

def get_cdps(self, targets: list[str] | None = None) -> list[CDPSession]:
    """Get CDPSessions for specified targets (or tracked/all)."""
    target_list = targets if targets is not None else self.get_tracked_or_all()
    return [self.connections[t].cdp for t in target_list if t in self.connections]

def set_tracked_targets(self, targets: list[str] | None) -> list[str]:
    """Set tracked targets. None or [] clears (meaning all)."""
    self.tracked_targets = list(targets) if targets else []
    self._trigger_broadcast()
    return self.tracked_targets
```

**Update `list_pages()`** - direct HTTP, no CDPSession needed:
```python
def list_pages(self, chrome_port: int | None = None) -> dict:
    import httpx
    ports = [chrome_port] if chrome_port else list(self.state.registered_ports)
    all_pages = []
    for port in ports:
        try:
            resp = httpx.get(f"http://localhost:{port}/json", timeout=2.0)
            pages = resp.json()
            for page in pages:
                if page.get("type") != "page":
                    continue
                target_id = make_target(port, page.get("id", ""))
                page["target"] = target_id
                page["chrome_port"] = port
                page["connected"] = target_id in self.connections
                all_pages.append(page)
        except Exception:
            pass
    return {"pages": all_pages}
```

**Update `connect_to_page()`**:
```python
def connect_to_page(self, target: str) -> dict:
    # Check already connected
    if target in self.connections:
        return {"already_connected": True, ...}

    # Parse target and resolve
    port, short_id = parse_target(target)
    pages = self.list_pages(chrome_port=port)
    page = resolve_target(target, pages["pages"])
    if not page:
        raise ValueError(f"Target {target} not found")

    # Create NEW CDPSession for this page
    cdp = CDPSession(port=port)
    cdp.connect(page_id=page["id"])

    # Enable domains
    for domain in _REQUIRED_DOMAINS:
        cdp.execute(f"{domain}.enable")

    # Store connection
    target_id = make_target(port, page["id"])
    cdp.target = target_id
    connection = ActiveConnection(
        target=target_id,
        cdp=cdp,
        page_info=page,
        connected_at=time.time(),
        state=TargetState.CONNECTED,
    )
    self.connections[target_id] = connection

    # Register callbacks
    cdp.set_disconnect_callback(lambda c, r: self._handle_disconnect(target_id, c, r))
    cdp.set_broadcast_callback(self._trigger_broadcast)

    self._trigger_broadcast()
    return {"target": target_id, "title": page.get("title"), "url": page.get("url")}
```

**Update `disconnect_target()`**:
```python
def disconnect_target(self, target: str) -> None:
    conn = self.connections.get(target)
    if not conn:
        return

    conn.state = TargetState.DISCONNECTING
    self._trigger_broadcast()

    conn.cdp.disconnect()
    conn.cdp.cleanup()  # Cleanup DuckDB thread

    del self.connections[target]

    # Remove from tracked if present
    if target in self.tracked_targets:
        self.tracked_targets.remove(target)

    self._trigger_broadcast()
```

#### `src/webtap/services/network.py`

**Current:** Uses `self.cdp` directly

**Changes:** Accept `targets` param, aggregate from multiple CDPSessions

```python
class NetworkService:
    def __init__(self):
        self.service = None  # Set by main.py
        self.filters = None

    def set_service(self, service):
        self.service = service

    def get_requests(self, targets: list[str] | None = None, **filters) -> list:
        """Get network requests from specified targets (or tracked/all)."""
        cdps = self.service.get_cdps(targets)
        all_requests = []
        for cdp in cdps:
            # Query this CDPSession's DuckDB
            requests = self._query_requests(cdp, **filters)
            all_requests.extend(requests)
        return all_requests

    def _query_requests(self, cdp: CDPSession, **filters) -> list:
        # Existing query logic, but on specific cdp
        sql = self._build_query(**filters)
        return cdp.query(sql)
```

#### `src/webtap/services/console.py`

**Same pattern as network:**
```python
def get_messages(self, targets: list[str] | None = None, **filters) -> list:
    cdps = self.service.get_cdps(targets)
    all_messages = []
    for cdp in cdps:
        messages = self._query_messages(cdp, **filters)
        all_messages.extend(messages)
    return all_messages
```

#### `src/webtap/services/fetch.py`

**Enable/disable on ALL connected pages:**
```python
def enable(self, patterns: list = None):
    for conn in self.service.connections.values():
        conn.cdp.execute("Fetch.enable", {"patterns": patterns or [{"urlPattern": "*"}]})
    self.enabled = True

def disable(self):
    for conn in self.service.connections.values():
        try:
            conn.cdp.execute("Fetch.disable")
        except Exception:
            pass  # Page may have disconnected
    self.enabled = False
```

#### `src/webtap/services/dom.py`

**Require explicit target:**
```python
def start_inspect(self, target: str) -> dict:
    conn = self.service.connections.get(target)
    if not conn:
        raise ValueError(f"Target {target} not connected")

    # Disable on previous target if any
    if self._inspect_target and self._inspect_target != target:
        self._disable_inspect(self._inspect_target)

    self._inspect_target = target
    conn.cdp.execute("Overlay.setInspectMode", {"mode": "searchForNode", ...})
    return {"inspecting": target}

def stop_inspect(self) -> dict:
    if self._inspect_target:
        self._disable_inspect(self._inspect_target)
        self._inspect_target = None
    return {"inspecting": None}
```

---

## New Components

### RPC Handler: `targets()`

**File:** `src/webtap/rpc/handlers.py`

```python
def targets(ctx: RPCContext, targets: list[str] | None = None) -> dict:
    """Get or set tracked targets.

    Args:
        targets: If provided, set tracked targets. None/[] clears (all).
                 If omitted, returns current tracked targets.

    Returns:
        {"tracked": [...], "connected": [...]}
    """
    if targets is not None:
        # Validate targets exist
        invalid = [t for t in targets if t not in ctx.service.connections]
        if invalid:
            raise RPCError(ErrorCode.INVALID_PARAMS, f"Unknown targets: {invalid}")
        ctx.service.set_tracked_targets(targets)

    return {
        "tracked": ctx.service.tracked_targets,
        "connected": list(ctx.service.connections.keys()),
    }
```

### Updated RPC Handler: `browser()`

```python
def browser(ctx: RPCContext, target: str, action: str = "start") -> dict:
    """Control DOM inspection on a specific target.

    Args:
        target: Required. Target ID to inspect.
        action: "start" or "stop"
    """
    if action == "start":
        return ctx.service.dom.start_inspect(target)
    elif action == "stop":
        return ctx.service.dom.stop_inspect()
    else:
        raise RPCError(ErrorCode.INVALID_PARAMS, f"Unknown action: {action}")
```

---

## Data Models

### Updated StateSnapshot

**File:** `src/webtap/services/state_snapshot.py`

Add `tracked_targets` field:
```python
@dataclass(frozen=True)
class StateSnapshot:
    # ... existing fields ...
    tracked_targets: tuple[str, ...]  # NEW
```

### Updated SSE State

**File:** `src/webtap/api/state.py`

Add to state dict:
```python
return {
    # ... existing fields ...
    "tracked_targets": list(snapshot.tracked_targets),  # NEW
    "connections": [
        {
            "target": conn["target"],
            "title": conn["title"],
            "url": conn["url"],
            "state": conn["state"],
        }
        for conn in snapshot.connections
    ],
}
```

---

## Extension Changes

### `extension/main.js`

Update to handle two-table UI and tracked targets.

### `extension/controllers/pages.js`

Split into Available Pages (existing) - connect/disconnect only.

### `extension/controllers/targets.js` (NEW)

Connected Targets table with:
- Checkbox for tracking
- Inspect button
- Sync with `state.connections` and `state.tracked_targets`

```javascript
export function render(state) {
  const connections = state.connections || [];
  const tracked = new Set(state.tracked_targets || []);

  const rows = connections.map(conn => ({
    target: conn.target,
    url: conn.url,
    tracked: tracked.has(conn.target),
    inspecting: state.browser?.inspecting === conn.target,
  }));

  targetTable.update(rows);
}

export async function toggleTracked(target, checked) {
  const current = client.state.tracked_targets || [];
  const updated = checked
    ? [...current, target]
    : current.filter(t => t !== target);
  await client.call("targets", { targets: updated });
}

export async function inspect(target) {
  await client.call("browser", { target, action: "start" });
}
```

---

## Data Flow

### Connection Flow
```
User double-clicks page in Available Pages
  → pages.js calls connect(target)
  → RPC handler calls service.connect_to_page(target)
  → Creates NEW CDPSession
  → Enables domains
  → Stores in connections dict
  → Triggers broadcast
  → Extension receives SSE update
  → targets.js renders new row in Connected Targets
```

### Aggregation Flow
```
User calls network()
  → command calls service.network.get_requests(targets=None)
  → service.get_cdps(None) returns tracked or all CDPSessions
  → NetworkService queries each CDPSession's DuckDB
  → Results merged and returned
```

### Inspect Flow
```
User clicks Inspect button in Connected Targets
  → targets.js calls browser(target, "start")
  → RPC handler calls service.dom.start_inspect(target)
  → Gets CDPSession from connections[target]
  → Executes Overlay.setInspectMode on that session
  → User clicks element in browser
  → CDPSession receives inspectNodeRequested event
  → dom.py stores selection
  → Triggers broadcast
  → Extension shows selection
```

---

## Error Handling

### Connection Errors
- Target not found: `ValueError("Target {target} not found")`
- Already connected: Return `{"already_connected": True}`
- Domain enable failure: Disconnect and raise `RuntimeError`

### Aggregation Errors
- Invalid target in list: Skip (target may have disconnected)
- Empty result: Return empty list (not error)

### Inspect Errors
- Target not connected: `ValueError("Target {target} not connected")`
- Missing target param: `RPCError(INVALID_PARAMS, "target parameter required")`

---

## Migration Notes

### Breaking Changes
- `self.cdp` removed from WebTapService
- `cdp_sessions` dict removed from DaemonState
- Services no longer have `.cdp` attribute
- `browser()` now requires `target` parameter

### Backward Compatibility
- Single-page usage unchanged (just connect to one page)
- `network()`, `console()` without params = all (same as before with one page)
- Extension auto-upgraded (new UI, same RPC calls)
