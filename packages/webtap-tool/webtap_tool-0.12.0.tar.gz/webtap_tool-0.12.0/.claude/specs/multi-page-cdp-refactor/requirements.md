# Feature: Multi-Page CDP Connection Refactor

## Overview

Remove the "primary" CDPSession concept and enable connecting to multiple pages on the same Chrome instance. Services aggregate data from all connections with optional target filtering.

**Type:** Clean break atomic refactor - all changes deployed together.

---

## User Stories

### Story 1: Connect to Multiple Pages on Same Chrome

**As a** WebTap user with multiple tabs open in Chrome
**I want** to connect to multiple pages simultaneously on the same Chrome instance
**So that** I can monitor network traffic and console logs across multiple tabs

**Acceptance Criteria (EARS notation):**
- WHEN connecting to page A on port 9222, THE SYSTEM SHALL create a dedicated CDPSession for that page
- WHEN connecting to page B on the same port 9222, THE SYSTEM SHALL create a separate CDPSession for page B
- WHEN both pages are connected, THE SYSTEM SHALL maintain independent WebSocket connections for each
- WHEN disconnecting page A, THE SYSTEM SHALL preserve page B's connection and data

---

### Story 2: Tracked Targets (Default Scope)

**As a** WebTap user with many pages connected
**I want** to set a list of "tracked targets" as my default scope
**So that** commands like `network()` and `console()` only show data from pages I care about

**Acceptance Criteria (EARS notation):**
- WHEN calling `targets()`, THE SYSTEM SHALL return the current tracked targets list
- WHEN calling `targets(["9222:abc", "9222:def"])`, THE SYSTEM SHALL set the tracked targets
- WHEN calling `targets([])` or `targets(None)`, THE SYSTEM SHALL clear tracked targets (meaning "all")
- WHEN tracked targets is set, THE SYSTEM SHALL use it as default for `network()`, `console()`, etc.
- WHEN tracked targets is empty/None, THE SYSTEM SHALL default to all connected pages
- WHEN explicit `targets` param provided to command, THE SYSTEM SHALL override tracked targets

**Example flow:**
```python
connect(target="9222:abc")      # Connect page A
connect(target="9222:def")      # Connect page B
connect(target="9222:ghi")      # Connect page C

network()                       # Returns events from A, B, C (all)

targets(["9222:abc", "9222:def"])  # Set tracked to A, B

network()                       # Returns events from A, B only
network(targets=["9222:ghi"])   # Explicit override - returns C only

targets([])                     # Clear tracked
network()                       # Returns A, B, C again
```

**Extension UI (Two Tables):**

```
Available Pages:              (from /json - what CAN be connected)
┌──────────────────────────────────────┐
│ ● 9222:abc  github.com               │  ● = connected
│   9222:def  google.com               │
│   9222:ghi  twitter.com              │
└──────────────────────────────────────┘
  Double-click to connect/disconnect

Connected Targets:            (from state.connections - what IS connected)
┌─────────────────────────────────────────────────┐
│ [x] 9222:abc  github.com         [Inspect]      │  [x] = tracked
│ [ ] 9222:def  google.com         [Inspect]      │
└─────────────────────────────────────────────────┘
  Checkbox = tracked for aggregation
  Inspect = activate inspect mode
```

- WHEN viewing extension, THE SYSTEM SHALL show "Available Pages" and "Connected Targets" as separate tables
- WHEN page is connected, THE SYSTEM SHALL show it in both tables (with indicator in Available Pages)
- WHEN user checks/unchecks in Connected Targets, THE SYSTEM SHALL update tracked targets
- WHEN user clicks Inspect, THE SYSTEM SHALL call `browser(target=...)` RPC

---

### Story 3: Aggregate Network Events

**As a** WebTap user with multiple pages connected
**I want** `network()` to show events from tracked pages (or all if none tracked)
**So that** I can see network activity scoped to my current focus

**Acceptance Criteria (EARS notation):**
- WHEN calling `network()`, THE SYSTEM SHALL return events from tracked targets (or all if none)
- WHEN calling `network(targets=["9222:abc"])`, THE SYSTEM SHALL override with explicit targets
- WHEN calling `network(type="fetch")`, THE SYSTEM SHALL apply type filter to tracked targets
- WHEN events are returned, THE SYSTEM SHALL include the target ID for each event

**Note:** All existing filters (type, status, url, etc.) remain unchanged. `targets` is additive.

---

### Story 4: Aggregate Console Logs

**As a** WebTap user debugging multiple pages
**I want** `console()` to show logs from tracked pages (or all if none tracked)
**So that** I can see console output scoped to my current focus

**Acceptance Criteria (EARS notation):**
- WHEN calling `console()`, THE SYSTEM SHALL return logs from tracked targets (or all if none)
- WHEN calling `console(targets=["9222:abc"])`, THE SYSTEM SHALL override with explicit targets
- WHEN logs are returned, THE SYSTEM SHALL include the target ID for each log entry

---

### Story 5: Fetch Interception Across All Pages

**As a** WebTap user intercepting requests
**I want** fetch interception to work on all connected pages
**So that** I can intercept and modify requests from any connected tab

**Acceptance Criteria (EARS notation):**
- WHEN enabling fetch interception, THE SYSTEM SHALL enable it on ALL connected pages
- WHEN a new page is connected while fetch is enabled, THE SYSTEM SHALL enable fetch on the new page
- WHEN disabling fetch, THE SYSTEM SHALL disable it on all pages

---

### Story 6: Target-Specific DOM Inspection

**As a** WebTap user inspecting DOM elements
**I want** to specify which page to inspect
**So that** I can interact with elements on a specific tab

**Acceptance Criteria (EARS notation):**
- WHEN calling `browser(target="9222:abc")`, THE SYSTEM SHALL activate inspect mode on that connected page
- WHEN target is not connected, THE SYSTEM SHALL return error "Target not connected"
- WHEN `target` parameter is omitted, THE SYSTEM SHALL return error "target parameter required"
- WHEN inspecting, THE SYSTEM SHALL only capture selections from the inspected page
- WHEN user clicks Inspect in extension, THE SYSTEM SHALL pass target to `browser()` RPC

**Note:** Inspect ALWAYS requires explicit `target` parameter. No implicit defaults.

---

## Non-Functional Requirements

### Performance
- Creating a new CDPSession SHALL complete within 500ms
- Aggregating events from N pages SHALL scale linearly with N
- Each CDPSession maintains its own DuckDB - no shared state contention

### Resource Management
- Each CDPSession has one DuckDB instance and one background thread
- Disconnect SHALL cleanup DuckDB thread within 1 second
- No resource leaks on repeated connect/disconnect cycles

### Backward Compatibility
- Single-page usage works identically to before
- Existing RPC API preserved (new `targets` parameter is optional)

---

## Constraints

### Technical Constraints
- Each CDPSession requires its own WebSocket connection (CDP limitation)
- Each CDPSession has isolated DuckDB storage (by design)
- Port registry separate from page connections (HTTP for discovery, WebSocket for connection)

### Breaking Changes
- Remove `self.cdp` "primary" concept from WebTapService
- Remove `cdp_sessions: dict[int, CDPSession]` (replaced by `registered_ports: set[int]`)
- Services no longer wired to single CDPSession

---

## Out of Scope

- Shared DuckDB across all connections (each page keeps own storage)
- Cross-page event correlation
- Automatic reconnection on page crash
- Load balancing across pages

---

## Assumptions

1. **Typical usage:** 1-5 simultaneous page connections
2. **Resource acceptable:** N pages = N DuckDB instances + N threads
3. **Target format stable:** `{port}:{short_id}` format unchanged
4. **HTTP discovery works:** `/json` endpoint available without WebSocket
5. **Events tagged:** CDPSession already tags events with `target` field
