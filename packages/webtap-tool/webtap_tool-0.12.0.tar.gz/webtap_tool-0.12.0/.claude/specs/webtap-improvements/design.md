# Design: WebTap Improvements

## Architecture Overview

Three interconnected improvements to WebTap:

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Command Layer                                 │
│  commands/navigation.py  commands/entry.py  extension/datatable.js │
└─────────────────────────────────────────────────────────────────────┘
                                    │
┌─────────────────────────────────────────────────────────────────────┐
│                        RPC Handlers                                  │
│  handlers.py: navigate, reload, js, entry (remove state reqs)      │
└─────────────────────────────────────────────────────────────────────┘
                                    │
┌─────────────────────────────────────────────────────────────────────┐
│                        Service Layer                                 │
│  main.py: execute_on_target()  console.py: get_entry_details()     │
└─────────────────────────────────────────────────────────────────────┘
                                    │
┌─────────────────────────────────────────────────────────────────────┐
│                        CDP / DuckDB                                  │
│  session.py: ephemeral connect/disconnect, event storage            │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Feature 1: Target Architecture Redesign

### Component Analysis

#### Existing Components to Modify

**`src/webtap/services/main.py`**
- Add `execute_on_target(target, callback)` for ephemeral execution
- Add `_get_or_create_session(port)` helper for auto-registration

**`src/webtap/rpc/handlers.py`**
- Remove `requires_state=CONNECTED_STATES` from: `navigate`, `reload`, `back`, `forward`, `js`
- Modify handlers to use ephemeral execution when target specified
- Add `target` parameter to `network`, `console` handlers

**`src/webtap/filters.py`**
- Extend `build_filter_sql()` to accept `target: str | list[str]`

**`src/webtap/services/network.py`**
- Add `target` parameter to `get_requests()`

**`src/webtap/services/console.py`**
- Add `target` parameter to `get_recent_messages()`

### Data Flow

**Fire-and-Forget Action (with target):**
```
js(code, target="9224:abc")
       │
       ▼
handlers.js() ─── target provided ───▶ service.execute_on_target()
                                              │
                         ┌────────────────────┴────────────────────┐
                         │                                         │
                    Connected?                              Not connected
                         │                                         │
                    Reuse conn                          Auto-register port
                         │                                    Connect
                         │                                    Execute
                         │                                    Disconnect
                         ▼                                         ▼
                     Return result ◀───────────────────────────────┘
```

**Query with Target Filter:**
```
network(target=["9222:abc", "9224:def"])
       │
       ▼
handlers.network(target=[...])
       │
       ▼
service.network.get_requests(target=[...])
       │
       ▼
filters.build_filter_sql(target=[...])
       │
       ▼
SQL: WHERE target IN ('9222:abc', '9224:def')
```

### API Changes

```python
# services/main.py - NEW
def execute_on_target(self, target: str, callback: Callable[[CDPSession], Any]) -> Any:
    """Execute callback on target, reusing or creating ephemeral connection."""
    # Check existing connection
    existing = self.get_connection(target)
    if existing:
        return callback(existing.cdp)

    # Parse and resolve target
    port, short_id = parse_target(target)
    cdp_session = self._get_or_create_session(port)

    # Resolve to full page
    pages = self.list_pages(chrome_port=port)
    page = resolve_target(target, pages["pages"])
    if not page:
        raise ValueError(f"Target '{target}' not found")

    # Ephemeral connection
    try:
        cdp_session.connect(page_id=page["id"])
        return callback(cdp_session)
    finally:
        cdp_session.disconnect()

def _get_or_create_session(self, port: int) -> CDPSession:
    """Get existing session or create new one (auto-register)."""
    if port not in self.state.cdp_sessions:
        self.register_port(port)
    return self.state.cdp_sessions[port]
```

```python
# rpc/handlers.py - MODIFIED
# Remove requires_state from registration:
rpc.method("navigate")(navigate)  # Was: requires_state=CONNECTED_STATES
rpc.method("js")(js)
rpc.method("reload")(reload)
rpc.method("back")(back)
rpc.method("forward")(forward)

def js(ctx: RPCContext, code: str, target: str | None = None, ...) -> dict:
    if target:
        def do_js(cdp):
            return cdp.execute("Runtime.evaluate", {"expression": code, ...})
        result = ctx.service.execute_on_target(target, do_js)
    else:
        if not ctx.service.connections:
            raise RPCError(ErrorCode.NOT_CONNECTED, "Specify target or connect first")
        cdp = _resolve_cdp_session(ctx, None)
        result = cdp.execute("Runtime.evaluate", {"expression": code, ...})
    return {...}
```

```python
# filters.py - MODIFIED
def build_filter_sql(
    self,
    ...,
    target: str | list[str] | None = None,
) -> str:
    conditions = []

    # Target filtering
    if target:
        if isinstance(target, str):
            conditions.append(f"target = '{target}'")
        else:
            escaped = [t.replace("'", "''") for t in target]
            targets_sql = ", ".join(f"'{t}'" for t in escaped)
            conditions.append(f"target IN ({targets_sql})")
    elif self.active_targets:
        # Fallback to session-level filter
        ...
```

---

## Feature 2: Console Entry Drill-Down

### Component Analysis

#### Existing Components to Modify

**`src/webtap/services/console.py`**
- Add `get_entry_details(row_id: int) -> dict | None`
- Add `select_fields(entry: dict, patterns: list[str] | None) -> dict`
- Add `format_stack_trace(stack: dict) -> list[str]`

**`src/webtap/rpc/handlers.py`**
- Add `entry()` handler
- Register with `rpc.method("entry", requires_state=CONNECTED_STATES, broadcasts=False)`

#### New Components

**`src/webtap/commands/entry.py`** (new file)
- Follow `request.py` pattern exactly
- Field selection, expression evaluation, output export

### Data Models

**Console Entry Structure:**
```python
# From Runtime.consoleAPICalled
{
    "id": 123,                          # rowid
    "method": "Runtime.consoleAPICalled",
    "type": "error",                    # error|warning|log|info|debug
    "source": "console",
    "message": "Error message text",
    "timestamp": 1704000000.0,
    "stackTrace": {
        "callFrames": [
            {
                "functionName": "handleClick",
                "url": "https://example.com/app.js",
                "lineNumber": 45,
                "columnNumber": 10
            }
        ]
    },
    "args": [
        {"type": "string", "value": "Error message"},
        {"type": "object", "objectId": "...", "className": "Error"}
    ],
    "executionContextId": 1
}

# From Log.entryAdded
{
    "id": 124,
    "method": "Log.entryAdded",
    "type": "warning",
    "source": "network",
    "message": "Failed to load resource",
    "timestamp": 1704000001.0,
    "entry": {
        "url": "https://api.example.com/data",
        "lineNumber": 0,
        "networkRequestId": "req-123"
    }
}
```

**Field Selection Patterns:**
| Pattern | Result |
|---------|--------|
| `None` | `{type, message, source, timestamp}` |
| `["*"]` | Full entry |
| `["stackTrace"]` | Stack trace object |
| `["stackTrace.callFrames"]` | Just call frames array |
| `["args.*"]` | All arguments |
| `["args.0"]` | First argument |

### API Design

```python
# services/console.py - NEW METHODS
def get_entry_details(self, row_id: int) -> dict | None:
    """Get full console entry by database row ID."""
    sql = "SELECT event FROM events WHERE rowid = ?"
    rows = self.cdp.query(sql, [row_id])
    if not rows:
        return None

    event = json.loads(rows[0][0])
    params = event.get("params", {})

    # Normalize both Runtime.consoleAPICalled and Log.entryAdded
    if event.get("method") == "Log.entryAdded":
        entry = params.get("entry", {})
        return {
            "id": row_id,
            "method": event["method"],
            "type": entry.get("level"),
            "source": entry.get("source"),
            "message": entry.get("text"),
            "timestamp": entry.get("timestamp"),
            "entry": entry,
            "stackTrace": entry.get("stackTrace"),
        }
    else:  # Runtime.consoleAPICalled
        return {
            "id": row_id,
            "method": event.get("method"),
            "type": params.get("type"),
            "source": "console",
            "message": self._extract_message(params.get("args", [])),
            "timestamp": params.get("timestamp"),
            "args": params.get("args"),
            "stackTrace": params.get("stackTrace"),
            "executionContextId": params.get("executionContextId"),
        }

def select_fields(self, entry: dict, patterns: list[str] | None) -> dict:
    """Apply field selection patterns to console entry."""
    if patterns is None:
        return {k: entry[k] for k in ["type", "message", "source", "timestamp"] if k in entry}

    if patterns == ["*"] or "*" in patterns:
        return entry

    result = {}
    for pattern in patterns:
        parts = pattern.split(".")
        if pattern.endswith(".*"):
            # Wildcard: args.* -> get all of args
            prefix = pattern[:-2].split(".")
            value = _get_nested(entry, prefix)
            if value is not None:
                _set_nested(result, prefix, value)
        else:
            value = _get_nested(entry, parts)
            if value is not None:
                _set_nested(result, parts, value)
    return result

def _extract_message(self, args: list) -> str:
    """Extract message from console args."""
    if not args:
        return ""
    first = args[0]
    return first.get("value") or first.get("description") or str(first)
```

```python
# rpc/handlers.py - NEW HANDLER
def entry(ctx: RPCContext, id: int, fields: list[str] | None = None) -> dict:
    """Get console entry details with field selection."""
    entry = ctx.service.console.get_entry_details(id)
    if not entry:
        raise RPCError(ErrorCode.INVALID_PARAMS, f"Console entry {id} not found")

    selected = ctx.service.console.select_fields(entry, fields)
    return {"entry": selected}

# Registration
rpc.method("entry", requires_state=CONNECTED_STATES, broadcasts=False)(entry)
```

```python
# commands/entry.py - NEW FILE (follows request.py pattern)
@app.command(display="markdown", fastmcp={"type": "tool", ...})
def entry(state, id: int, fields: list = None, expr: str = None, output: str = None):
    """Get console entry details with field selection and expressions."""
    result = state.client.call("entry", id=id, fields=fields)
    selected = result.get("entry")

    if expr:
        namespace = {"data": selected}
        eval_result, stdout = evaluate_expression(expr, namespace)
        # Return markdown with expression result
        ...

    if output:
        # Export to file
        ...

    # Default: markdown with formatted display
    elements = [{"type": "heading", "content": f"Console Entry {id}", "level": 2}]

    # Format stack trace if present
    if "stackTrace" in selected:
        frames = format_stack_frames(selected["stackTrace"])
        elements.append({"type": "code_block", "content": "\n".join(frames)})

    elements.append({"type": "code_block", "content": json.dumps(selected, indent=2), "language": "json"})
    return {"elements": elements}
```

---

## Feature 3: Extension DataTable Component

### Component Analysis

#### New Components

**`extension/datatable.js`** (new file)
- Reusable DataTable class following ListRenderer pattern
- Column configuration, row selection, sorting

#### Existing Components to Modify

**`extension/sidepanel.css`**
- Add `.data-table*` classes
- Add `.status-badge*` classes

**`extension/sidepanel.js`**
- Replace `updateNetworkTable()` with DataTable instance
- Remove manual DOM creation

**`extension/sidepanel.html`**
- Add `<script src="datatable.js">`

### Data Models

```javascript
// Column Definition
{
  key: "method",        // Data field name
  header: "Method",     // Column header
  width: "60px",        // CSS width (optional)
  truncate: true,       // Enable ellipsis (optional)
  monospace: true,      // Use mono font (optional)
  formatter: (value, row) => el  // Custom formatter (optional)
}

// DataTable Options
{
  columns: [...],
  selectable: true,
  sortable: false,
  onRowClick: (row, key) => {},
  getKey: (row, index) => row.id || index,
  emptyText: "No data"
}
```

### DOM Structure

```html
<!-- Generated by DataTable -->
<div class="data-table">
  <div class="data-table-header">
    <div class="data-table-row">
      <div class="data-table-cell" style="width: 60px">Method</div>
      <div class="data-table-cell" style="width: 50px">Status</div>
      <div class="data-table-cell data-table-cell--flex">URL</div>
    </div>
  </div>
  <div class="data-table-body">
    <div class="data-table-row" data-key="123">
      <div class="data-table-cell">GET</div>
      <div class="data-table-cell">
        <span class="status-badge status-badge--success">200</span>
      </div>
      <div class="data-table-cell data-table-cell--truncate" title="...">
        https://api.example.com/data
      </div>
    </div>
  </div>
</div>
```

### CSS Design

```css
/* Container */
.data-table {
  display: flex;
  flex-direction: column;
  height: 100%;
  font-size: var(--text-sm);
}

/* Header - fixed */
.data-table-header {
  flex-shrink: 0;
  border-bottom: var(--border-width) solid var(--color-border);
  background: var(--color-bg-subtle);
}

/* Body - scrollable */
.data-table-body {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}

/* Rows */
.data-table-row {
  display: flex;
  padding: var(--space-xs) var(--space-sm);
  border-bottom: 1px solid var(--color-border-subtle);
  cursor: pointer;
}

.data-table-row:hover {
  background: var(--color-bg-hover);
}

.data-table-row--selected {
  background: var(--color-bg-muted);
}

/* Cells */
.data-table-cell {
  flex-shrink: 0;
  padding-right: var(--space-sm);
}

.data-table-cell--flex {
  flex: 1;
  min-width: 0;
}

.data-table-cell--truncate {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.data-table-cell--mono {
  font-family: var(--font-mono);
}

/* Status badges */
.status-badge {
  display: inline-block;
  padding: 0 var(--space-xs);
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  font-weight: 500;
}

.status-badge--success {
  background: light-dark(#e6f4ea, #1e3a29);
  color: var(--color-success);
}

.status-badge--error {
  background: light-dark(#fce8e6, #3a1e1e);
  color: var(--color-error);
}

.status-badge--warning {
  background: light-dark(#fef7e0, #3a3320);
  color: var(--color-warning);
}
```

### Component Implementation

```javascript
// extension/datatable.js
class DataTable {
  constructor(selector, options = {}) {
    this.container = document.querySelector(selector);
    this.columns = options.columns || [];
    this.selectable = options.selectable || false;
    this.onRowClick = options.onRowClick || null;
    this.getKey = options.getKey || ((row, i) => i);
    this.emptyText = options.emptyText || "No data";

    this._data = [];
    this._selectedKey = null;
    this._elements = new Map();  // key -> row element

    this._render();
  }

  _render() {
    this.container.innerHTML = "";
    this.container.className = "data-table";

    // Header
    this._header = document.createElement("div");
    this._header.className = "data-table-header";
    const headerRow = this._createHeaderRow();
    this._header.appendChild(headerRow);
    this.container.appendChild(this._header);

    // Body
    this._body = document.createElement("div");
    this._body.className = "data-table-body";
    this.container.appendChild(this._body);
  }

  _createHeaderRow() {
    const row = document.createElement("div");
    row.className = "data-table-row";

    for (const col of this.columns) {
      const cell = document.createElement("div");
      cell.className = "data-table-cell" + (col.width ? "" : " data-table-cell--flex");
      if (col.width) cell.style.width = col.width;
      cell.textContent = col.header;
      row.appendChild(cell);
    }
    return row;
  }

  update(data) {
    this._data = data || [];
    const seen = new Set();

    // Update/create rows
    for (let i = 0; i < this._data.length; i++) {
      const item = this._data[i];
      const key = this.getKey(item, i);
      seen.add(key);

      let row = this._elements.get(key);
      if (!row) {
        row = this._createRow(item, key);
        this._elements.set(key, row);
      } else {
        this._updateRow(row, item);
      }
      this._body.appendChild(row);
    }

    // Remove stale rows
    for (const [key, el] of this._elements) {
      if (!seen.has(key)) {
        el.remove();
        this._elements.delete(key);
      }
    }

    // Empty state
    if (this._data.length === 0) {
      this._body.innerHTML = `<div class="data-table-empty">${this.emptyText}</div>`;
    }
  }

  _createRow(item, key) {
    const row = document.createElement("div");
    row.className = "data-table-row";
    row.dataset.key = key;

    if (this.selectable && key === this._selectedKey) {
      row.classList.add("data-table-row--selected");
    }

    for (const col of this.columns) {
      const cell = document.createElement("div");
      cell.className = "data-table-cell";
      if (!col.width) cell.classList.add("data-table-cell--flex");
      if (col.width) cell.style.width = col.width;
      if (col.truncate) cell.classList.add("data-table-cell--truncate");
      if (col.monospace) cell.classList.add("data-table-cell--mono");

      const value = item[col.key];
      if (col.formatter) {
        const content = col.formatter(value, item);
        if (typeof content === "string") {
          cell.textContent = content;
        } else {
          cell.appendChild(content);
        }
      } else {
        cell.textContent = value ?? "";
      }

      if (col.truncate) cell.title = value ?? "";
      row.appendChild(cell);
    }

    if (this.onRowClick) {
      row.onclick = () => {
        if (this.selectable) this.select(key);
        this.onRowClick(item, key);
      };
    }

    return row;
  }

  _updateRow(row, item) {
    const cells = row.querySelectorAll(".data-table-cell");
    for (let i = 0; i < this.columns.length; i++) {
      const col = this.columns[i];
      const cell = cells[i];
      const value = item[col.key];

      if (col.formatter) {
        cell.innerHTML = "";
        const content = col.formatter(value, item);
        if (typeof content === "string") {
          cell.textContent = content;
        } else {
          cell.appendChild(content);
        }
      } else {
        cell.textContent = value ?? "";
      }

      if (col.truncate) cell.title = value ?? "";
    }
  }

  select(key) {
    // Deselect previous
    if (this._selectedKey !== null) {
      const prev = this._elements.get(this._selectedKey);
      if (prev) prev.classList.remove("data-table-row--selected");
    }

    this._selectedKey = key;
    const row = this._elements.get(key);
    if (row) row.classList.add("data-table-row--selected");
  }

  clearSelection() {
    if (this._selectedKey !== null) {
      const row = this._elements.get(this._selectedKey);
      if (row) row.classList.remove("data-table-row--selected");
      this._selectedKey = null;
    }
  }
}

// Built-in formatters
const formatters = {
  status: (value, row) => {
    if (row.state === "paused") {
      const badge = document.createElement("span");
      badge.className = "status-badge status-badge--warning";
      badge.textContent = row.pause_stage === "Response" ? "Res" : "Req";
      return badge;
    }
    const type = value >= 400 ? "error" : value >= 300 ? "warning" : "success";
    const badge = document.createElement("span");
    badge.className = `status-badge status-badge--${type}`;
    badge.textContent = value || "-";
    return badge;
  }
};
```

### Integration

```javascript
// sidepanel.js - Replace updateNetworkTable()
const networkTable = new DataTable("#networkTable", {
  columns: [
    { key: "method", header: "Method", width: "55px" },
    { key: "status", header: "Status", width: "50px", formatter: formatters.status },
    { key: "url", header: "URL", truncate: true, monospace: true }
  ],
  selectable: true,
  onRowClick: (row) => showRequestDetails(row.id),
  getKey: (row) => row.id
});

// In fetchNetwork():
async function fetchNetwork() {
  const result = await client.call("network", { limit: 100 });
  document.getElementById("networkCount").textContent = `${result.requests.length} requests`;
  networkTable.update(result.requests);
}
```

---

## Error Handling Strategy

### Feature 1: Target Architecture

| Error | Handling |
|-------|----------|
| Target not found | `RPCError(INVALID_PARAMS, "Target 'x' not found")` |
| Port unreachable | `RPCError(INTERNAL_ERROR, "Port X not responding")` |
| No connection + no target | `RPCError(NOT_CONNECTED, "Specify target or connect first")` |

### Feature 2: Console Entry

| Error | Handling |
|-------|----------|
| Entry not found | `RPCError(INVALID_PARAMS, "Console entry X not found")` |
| Invalid field pattern | Silently ignore, return empty for that pattern |
| Expression error | Return error_response with traceback |

### Feature 3: DataTable

| Error | Handling |
|-------|----------|
| Invalid selector | Throw in constructor |
| Missing column key | Render empty cell |
| Formatter throws | Log error, render raw value |

---

## Security Considerations

- **Expression evaluation:** Uses existing sandboxed `evaluate_expression()` with pre-imported safe libraries
- **Target validation:** Targets validated against known pages before connection
- **SQL injection:** Target strings escaped in `build_filter_sql()`

---

## Files Modified Summary

| File | Changes |
|------|---------|
| `src/webtap/services/main.py` | +`execute_on_target()`, +`_get_or_create_session()` |
| `src/webtap/rpc/handlers.py` | Remove state reqs, +`entry()`, +target params |
| `src/webtap/services/network.py` | +target param to `get_requests()` |
| `src/webtap/services/console.py` | +`get_entry_details()`, +`select_fields()`, +target param |
| `src/webtap/filters.py` | Extend `build_filter_sql()` for list targets |
| `src/webtap/commands/navigation.py` | +target param to all commands |
| `src/webtap/commands/javascript.py` | +target param |
| `src/webtap/commands/network.py` | +target param |
| `src/webtap/commands/console.py` | +target param |
| `src/webtap/commands/entry.py` | **NEW** - console entry drill-down |
| `src/webtap/commands/TIPS.md` | +entry docs |
| `src/webtap/app.py` | +import entry |
| `extension/datatable.js` | **NEW** - DataTable component |
| `extension/sidepanel.css` | +data-table, +status-badge classes |
| `extension/sidepanel.js` | Replace network table |
| `extension/sidepanel.html` | +script tag |
