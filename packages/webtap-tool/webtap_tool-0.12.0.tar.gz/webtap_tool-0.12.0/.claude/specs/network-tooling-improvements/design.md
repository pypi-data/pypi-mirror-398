# Design: Network Tooling Improvements

## Architecture Overview

Replace raw CDP event queries with HAR-based aggregation views in DuckDB. Simplify filter system to named groups with in-memory toggle state.

```
┌─────────────────────────────────────────────────────────────────┐
│                         CDP Events                               │
│  Network.requestWillBeSent, responseReceived, loadingFinished   │
│  Network.webSocketCreated, webSocketFrame*, webSocketClosed     │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DuckDB events table                          │
│              (raw CDP events stored as-is)                      │
└─────────────────────────────┬───────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌─────────────────────────┐     ┌─────────────────────────┐
│   har_entries VIEW      │     │   har_summary VIEW      │
│   (full HAR structure)  │     │   (lightweight list)    │
└─────────────────────────┘     └─────────────────────────┘
              │                               │
              ▼                               ▼
┌─────────────────────────┐     ┌─────────────────────────┐
│   request(id, fields)   │     │   network(filters...)   │
│   + body fetching       │     │   + inline filters      │
└─────────────────────────┘     └─────────────────────────┘
```

## Component Design

### 1. HAR Views in DuckDB

#### `har_entries` - Full HAR Aggregation

Aggregates CDP events by `requestId` into HAR-like structure.

```sql
CREATE VIEW har_entries AS
WITH
-- HTTP Request: extract from requestWillBeSent
http_requests AS (
    SELECT
        json_extract_string(event, '$.params.requestId') as request_id,
        MIN(rowid) as first_rowid,
        'http' as protocol,
        json_extract_string(event, '$.params.wallTime') as started_datetime,
        json_extract_string(event, '$.params.timestamp') as started_timestamp,
        MAX(json_extract_string(event, '$.params.request.method')) as method,
        MAX(json_extract_string(event, '$.params.request.url')) as url,
        MAX(json_extract(event, '$.params.request.headers')) as request_headers,
        MAX(json_extract_string(event, '$.params.request.postData')) as post_data,
        MAX(json_extract_string(event, '$.params.type')) as resource_type
    FROM events
    WHERE method = 'Network.requestWillBeSent'
    GROUP BY json_extract_string(event, '$.params.requestId')
),

-- HTTP Response: extract from responseReceived
http_responses AS (
    SELECT
        json_extract_string(event, '$.params.requestId') as request_id,
        MAX(json_extract_string(event, '$.params.response.status')) as status,
        MAX(json_extract_string(event, '$.params.response.statusText')) as status_text,
        MAX(json_extract(event, '$.params.response.headers')) as response_headers,
        MAX(json_extract_string(event, '$.params.response.mimeType')) as mime_type,
        MAX(json_extract(event, '$.params.response.timing')) as timing
    FROM events
    WHERE method = 'Network.responseReceived'
    GROUP BY json_extract_string(event, '$.params.requestId')
),

-- HTTP Finished: timing and size
http_finished AS (
    SELECT
        json_extract_string(event, '$.params.requestId') as request_id,
        MAX(json_extract_string(event, '$.params.timestamp')) as finished_timestamp,
        MAX(json_extract_string(event, '$.params.encodedDataLength')) as final_size
    FROM events
    WHERE method = 'Network.loadingFinished'
    GROUP BY json_extract_string(event, '$.params.requestId')
),

-- HTTP Failed: error info
http_failed AS (
    SELECT
        json_extract_string(event, '$.params.requestId') as request_id,
        MAX(json_extract_string(event, '$.params.errorText')) as error_text
    FROM events
    WHERE method = 'Network.loadingFailed'
    GROUP BY json_extract_string(event, '$.params.requestId')
),

-- WebSocket Created
ws_created AS (
    SELECT
        json_extract_string(event, '$.params.requestId') as request_id,
        MIN(rowid) as first_rowid,
        'websocket' as protocol,
        json_extract_string(event, '$.params.url') as url
    FROM events
    WHERE method = 'Network.webSocketCreated'
    GROUP BY json_extract_string(event, '$.params.requestId')
),

-- WebSocket Handshake
ws_handshake AS (
    SELECT
        json_extract_string(event, '$.params.requestId') as request_id,
        MAX(json_extract_string(event, '$.params.wallTime')) as started_datetime,
        MAX(json_extract_string(event, '$.params.timestamp')) as started_timestamp,
        MAX(json_extract(event, '$.params.request.headers')) as request_headers,
        MAX(json_extract_string(event, '$.params.response.status')) as status,
        MAX(json_extract(event, '$.params.response.headers')) as response_headers
    FROM events
    WHERE method IN ('Network.webSocketWillSendHandshakeRequest', 'Network.webSocketHandshakeResponseReceived')
    GROUP BY json_extract_string(event, '$.params.requestId')
),

-- WebSocket Frame Stats (aggregated, not individual)
ws_frames AS (
    SELECT
        json_extract_string(event, '$.params.requestId') as request_id,
        SUM(CASE WHEN method = 'Network.webSocketFrameSent' THEN 1 ELSE 0 END) as frames_sent,
        SUM(CASE WHEN method = 'Network.webSocketFrameReceived' THEN 1 ELSE 0 END) as frames_received,
        SUM(LENGTH(COALESCE(json_extract_string(event, '$.params.response.payloadData'), ''))) as total_bytes
    FROM events
    WHERE method IN ('Network.webSocketFrameSent', 'Network.webSocketFrameReceived')
    GROUP BY json_extract_string(event, '$.params.requestId')
),

-- WebSocket Closed
ws_closed AS (
    SELECT
        json_extract_string(event, '$.params.requestId') as request_id,
        MAX(json_extract_string(event, '$.params.timestamp')) as closed_timestamp
    FROM events
    WHERE method = 'Network.webSocketClosed'
    GROUP BY json_extract_string(event, '$.params.requestId')
),

-- Combine HTTP
http_entries AS (
    SELECT
        req.first_rowid as id,
        req.request_id,
        req.protocol,
        req.method,
        req.url,
        CAST(COALESCE(resp.status, 0) AS INTEGER) as status,
        resp.status_text,
        req.resource_type as type,
        CAST(COALESCE(fin.final_size, 0) AS INTEGER) as size,
        CASE
            WHEN fin.finished_timestamp IS NOT NULL
            THEN CAST((CAST(fin.finished_timestamp AS DOUBLE) - CAST(req.started_timestamp AS DOUBLE)) * 1000 AS INTEGER)
            ELSE NULL
        END as time_ms,
        CASE
            WHEN fail.error_text IS NOT NULL THEN 'failed'
            WHEN fin.finished_timestamp IS NOT NULL THEN 'complete'
            WHEN resp.status IS NOT NULL THEN 'loading'
            ELSE 'pending'
        END as state,
        req.request_headers,
        req.post_data,
        resp.response_headers,
        resp.mime_type,
        resp.timing,
        fail.error_text,
        NULL as frames_sent,
        NULL as frames_received,
        NULL as total_bytes
    FROM http_requests req
    LEFT JOIN http_responses resp ON req.request_id = resp.request_id
    LEFT JOIN http_finished fin ON req.request_id = fin.request_id
    LEFT JOIN http_failed fail ON req.request_id = fail.request_id
),

-- Combine WebSocket
websocket_entries AS (
    SELECT
        ws.first_rowid as id,
        ws.request_id,
        ws.protocol,
        'WS' as method,
        ws.url,
        COALESCE(hs.status, 101) as status,
        NULL as status_text,
        'WebSocket' as type,
        COALESCE(wf.total_bytes, 0) as size,
        CASE
            WHEN wc.closed_timestamp IS NOT NULL
            THEN CAST((CAST(wc.closed_timestamp AS DOUBLE) - CAST(hs.started_timestamp AS DOUBLE)) * 1000 AS INTEGER)
            ELSE NULL
        END as time_ms,
        CASE
            WHEN wc.closed_timestamp IS NOT NULL THEN 'closed'
            WHEN hs.status IS NOT NULL THEN 'open'
            ELSE 'connecting'
        END as state,
        hs.request_headers,
        NULL as post_data,
        hs.response_headers,
        'websocket' as mime_type,
        NULL as timing,
        NULL as error_text,
        wf.frames_sent,
        wf.frames_received,
        wf.total_bytes
    FROM ws_created ws
    LEFT JOIN ws_handshake hs ON ws.request_id = hs.request_id
    LEFT JOIN ws_frames wf ON ws.request_id = wf.request_id
    LEFT JOIN ws_closed wc ON ws.request_id = wc.request_id
)

SELECT * FROM http_entries
UNION ALL
SELECT * FROM websocket_entries
ORDER BY id DESC;
```

#### `har_summary` - Lightweight List View

For `network()` command table display:

```sql
CREATE VIEW har_summary AS
SELECT
    id,
    request_id,
    protocol,
    method,
    status,
    url,
    type,
    size,
    time_ms,
    state,
    frames_sent,
    frames_received
FROM har_entries;
```

### 2. Enhanced `network()` Command

**File:** `commands/network.py`

```python
def network(
    state,
    status: int = None,
    method: str = None,
    type: str = None,
    url: str = None,
    all: bool = False,
    limit: int = 20,
) -> dict:
    """List network requests with inline filters.

    Args:
        status: Filter by HTTP status code (e.g., 404, 500)
        method: Filter by HTTP method (e.g., "POST", "GET")
        type: Filter by resource type (e.g., "xhr", "fetch", "websocket")
        url: Filter by URL pattern (supports * wildcard)
        all: Bypass noise filter groups
        limit: Max results (default 20)

    Examples:
        network()                    # Default with noise filter
        network(status=404)          # Only 404s
        network(method="POST")       # Only POST requests
        network(type="websocket")    # Only WebSocket
        network(url="*api*")         # URLs containing "api"
        network(all=True)            # Show everything
    """
```

**Filter SQL generation:**

```python
def _build_filter_sql(
    status: int = None,
    method: str = None,
    type: str = None,
    url: str = None,
    filter_groups: dict = None,  # From daemon memory
) -> str:
    conditions = []

    # Inline filters
    if status:
        conditions.append(f"status = {status}")
    if method:
        conditions.append(f"UPPER(method) = '{method.upper()}'")
    if type:
        conditions.append(f"LOWER(type) = '{type.lower()}'")
    if url:
        sql_pattern = url.replace("*", "%")
        conditions.append(f"url LIKE '{sql_pattern}'")

    # Filter groups (from enabled groups in daemon memory)
    if filter_groups:
        hide_types = set()
        hide_urls = []
        for group in filter_groups.values():
            if group.get("enabled"):
                hide_types.update(group["hide"].get("types", []))
                hide_urls.extend(group["hide"].get("urls", []))

        if hide_types:
            type_list = ", ".join(f"'{t}'" for t in hide_types)
            conditions.append(f"type NOT IN ({type_list})")

        for pattern in hide_urls:
            sql_pattern = pattern.replace("*", "%")
            conditions.append(f"url NOT LIKE '{sql_pattern}'")

    return " AND ".join(conditions) if conditions else ""
```

### 3. New `request()` Command

**File:** `commands/request.py` (NEW)

```python
def request(
    state,
    id: int,
    fields: list[str] = None,
) -> dict:
    """Get HAR-like request details with field selection.

    Args:
        id: Row ID from network() output
        fields: ES-style field patterns
            - None: minimal default (url, method, status, size, state)
            - ["*"]: all fields
            - ["request.headers.*"]: all request headers
            - ["response.headers.content-type"]: specific header
            - ["body"]: fetch response body on-demand

    Examples:
        request(123)                              # Minimal
        request(123, ["*"])                       # Everything
        request(123, ["request.headers.*"])       # All request headers
        request(123, ["body"])                    # Include body
        request(123, ["response.status", "body"]) # Status + body
    """
```

**Field selection implementation:**

```python
MINIMAL_FIELDS = ["url", "method", "status", "size", "state", "time_ms"]

def _select_fields(har_entry: dict, patterns: list[str] | None) -> dict:
    """Apply ES-style field selection."""
    if patterns is None:
        # Minimal default
        return {k: har_entry.get(k) for k in MINIMAL_FIELDS}

    if patterns == ["*"]:
        return har_entry

    result = {}
    for pattern in patterns:
        if pattern == "*":
            return har_entry
        elif pattern == "body":
            # Fetch on-demand via CDP
            result["body"] = _fetch_body(har_entry["id"])
        elif pattern.endswith(".*"):
            # Wildcard: "request.headers.*"
            prefix = pattern[:-2]  # "request.headers"
            obj = _get_nested(har_entry, prefix.split("."))
            _set_nested(result, prefix.split("."), obj)
        else:
            # Specific path: "response.headers.content-type"
            parts = pattern.split(".")
            value = _get_nested(har_entry, parts)
            _set_nested(result, parts, value)

    return result

def _get_nested(obj: dict, path: list[str]):
    """Get nested value by path, case-insensitive for headers."""
    for key in path:
        if obj is None:
            return None
        if isinstance(obj, dict):
            # Case-insensitive header lookup
            if key.lower() in [k.lower() for k in obj.keys()]:
                key = next(k for k in obj.keys() if k.lower() == key.lower())
            obj = obj.get(key)
        else:
            return None
    return obj
```

### 4. Simplified Filter System

**File:** `filters.py` (rewrite)

```python
@dataclass
class FilterGroup:
    """A named filter group."""
    hide: dict  # {"types": [...], "urls": [...]}

class FilterManager:
    """Manages filter groups with file persistence and memory toggle state."""

    def __init__(self, filter_path: Path | None = None):
        self.filter_path = filter_path or (Path.cwd() / ".webtap" / "filters.json")
        self.groups: dict[str, FilterGroup] = {}  # Definitions from file
        self.enabled: set[str] = set()  # In-memory toggle state

    def load(self) -> bool:
        """Load group definitions from file. All disabled by default."""
        if self.filter_path.exists():
            with open(self.filter_path) as f:
                data = json.load(f)
            self.groups = {
                name: FilterGroup(hide=cfg["hide"])
                for name, cfg in data.get("groups", {}).items()
            }
            self.enabled = set()  # All disabled on load
            return True
        return False

    def save(self) -> bool:
        """Save group definitions to file (not enabled state)."""
        self.filter_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "groups": {
                name: {"hide": group.hide}
                for name, group in self.groups.items()
            }
        }
        with open(self.filter_path, "w") as f:
            json.dump(data, f, indent=2)
        return True

    def add(self, name: str, hide: dict) -> None:
        """Add a group definition and persist to file."""
        self.groups[name] = FilterGroup(hide=hide)
        self.save()

    def remove(self, name: str) -> bool:
        """Remove a group and persist to file."""
        if name in self.groups:
            del self.groups[name]
            self.enabled.discard(name)
            self.save()
            return True
        return False

    def enable(self, name: str) -> bool:
        """Enable a group (in-memory only)."""
        if name in self.groups:
            self.enabled.add(name)
            return True
        return False

    def disable(self, name: str) -> bool:
        """Disable a group (in-memory only)."""
        if name in self.groups:
            self.enabled.discard(name)
            return True
        return False

    def get_active_filters(self) -> dict:
        """Get consolidated filters from enabled groups (deduplicated)."""
        hide_types = set()
        hide_urls = set()
        for name in self.enabled:
            if name in self.groups:
                hide_types.update(self.groups[name].hide.get("types", []))
                hide_urls.update(self.groups[name].hide.get("urls", []))
        return {"types": list(hide_types), "urls": list(hide_urls)}

    def get_status(self) -> dict:
        """Get all groups with enabled status."""
        return {
            name: {
                "enabled": name in self.enabled,
                "hide": group.hide,
            }
            for name, group in self.groups.items()
        }
```

### 5. Updated `filters()` Command

**File:** `commands/filters.py` (rewrite)

```python
def filters(
    state,
    add: str = None,
    remove: str = None,
    enable: str = None,
    disable: str = None,
    hide: dict = None,
) -> dict:
    """Manage filter groups.

    Args:
        add: Create new group with this name (requires hide=)
        remove: Delete group by name
        enable: Enable group by name
        disable: Disable group by name
        hide: Filter config for add ({"types": [...], "urls": [...]})

    Examples:
        filters()                                           # Show all groups
        filters(add="assets", hide={"types": ["Image"]})   # Create group
        filters(enable="assets")                            # Enable group
        filters(disable="assets")                           # Disable group
        filters(remove="assets")                            # Delete group
    """
```

### 6. API Endpoints

**File:** `api/routes/data.py`

Update `/network` to use HAR view:

```python
@router.get("/network")
async def get_network(
    status: int = None,
    method: str = None,
    type: str = None,
    url: str = None,
    all: bool = False,
    limit: int = 20,
) -> dict:
    """Get network requests from har_summary view."""
    filter_sql = _build_filter_sql(
        status=status,
        method=method,
        type=type,
        url=url,
        filter_groups=None if all else app_state.filters.get_status(),
    )
    # Query har_summary view
    ...
```

**File:** `api/routes/data.py`

Add `/request/{id}` endpoint:

```python
@router.get("/request/{id}")
async def get_request(
    id: int,
    fields: str = None,  # Comma-separated field patterns
) -> dict:
    """Get HAR entry with field selection."""
    field_list = fields.split(",") if fields else None
    # Query har_entries view, apply field selection
    ...
```

### 7. Files to Delete

- `commands/events.py` - Replaced by `request(id, ["*"])`
- `cdp/query.py` - Dynamic query builder no longer needed

### 8. Files to Update

| File | Changes |
|------|---------|
| `cdp/session.py` | Add HAR view creation in `__init__` |
| `services/network.py` | Use `har_summary` view |
| `commands/network.py` | Add inline filters |
| `filters.py` | Rewrite with simplified group model |
| `commands/filters.py` | Rewrite with new API |
| `api/routes/data.py` | Update `/network`, add `/request/{id}` |
| `api/routes/events.py` | Remove `/query` endpoint |
| `client.py` | Add `request()`, update `filters()` |

## Data Flow

### Network List Flow
```
network(status=404)
    │
    ▼
DaemonClient.network(status=404)
    │
    ▼
GET /network?status=404
    │
    ▼
Query har_summary + filter SQL
    │
    ▼
Return list of request summaries
```

### Request Detail Flow
```
request(123, ["body", "request.headers.*"])
    │
    ▼
DaemonClient.request(123, fields=["body", "request.headers.*"])
    │
    ▼
GET /request/123?fields=body,request.headers.*
    │
    ▼
Query har_entries WHERE id=123
    │
    ├─── body requested? ──► CDP Network.getResponseBody
    │
    ▼
Apply field selection, return HAR dict
```

### Filter Toggle Flow
```
filters(enable="assets")  OR  Extension toggle
    │
    ▼
POST /filters/toggle/assets
    │
    ▼
FilterManager.enable("assets")  (in-memory)
    │
    ▼
Broadcast state update via SSE
```

## Security Considerations

- Filter patterns use SQL LIKE with proper escaping
- Body fetching is on-demand (no automatic storage of sensitive data)
- Filter config stored in project directory (not global)
