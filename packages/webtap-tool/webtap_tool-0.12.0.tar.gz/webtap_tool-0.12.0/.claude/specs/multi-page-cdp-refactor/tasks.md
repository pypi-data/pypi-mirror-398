# Implementation Tasks: Multi-Page CDP Connection Refactor

**Status:** Ready to implement
**Spec:** [requirements.md](./requirements.md) | [design.md](./design.md)
**Type:** Clean break atomic refactor - all tasks deployed together

---

## Task Overview

| # | Task | Complexity | Files |
|---|------|------------|-------|
| 1 | Replace cdp_sessions with registered_ports | Low | `daemon_state.py` |
| 2 | Add tracked_targets and get_cdps() | Medium | `services/main.py` |
| 3 | Update list_pages() to use direct HTTP | Low | `services/main.py` |
| 4 | Refactor connect_to_page() | Medium | `services/main.py` |
| 5 | Refactor disconnect_target() | Low | `services/main.py` |
| 6 | Update NetworkService for aggregation | Medium | `services/network.py` |
| 7 | Update ConsoleService for aggregation | Medium | `services/console.py` |
| 8 | Update FetchService for all connections | Low | `services/fetch.py` |
| 9 | Update DOMService to require target | Medium | `services/dom.py` |
| 10 | Add targets() RPC handler | Low | `rpc/handlers.py` |
| 11 | Update browser() RPC handler | Low | `rpc/handlers.py` |
| 12 | Update StateSnapshot and SSE state | Low | `services/state_snapshot.py`, `api/state.py` |
| 13 | Update commands layer | Medium | `commands/network.py`, `commands/console.py` |
| 14 | Create targets.js controller | Medium | `extension/controllers/targets.js` |
| 15 | Update extension UI layout | Medium | `extension/main.js`, `extension/sidepanel.html` |

---

## Daemon Tasks

### Task 1: Replace cdp_sessions with registered_ports
**Started:** 2025-12-26
**Completed:** 2025-12-26

**Description:** Remove cdp_sessions dict, add registered_ports set.

**Files:**
- `src/webtap/daemon_state.py`

**Changes:**
```python
# REMOVE
self.cdp = CDPSession()
self.cdp_sessions: dict[int, "CDPSession"] = {9222: self.cdp}

# ADD
self.registered_ports: set[int] = {9222}

# UPDATE cleanup()
def cleanup(self):
    if self.service:
        self.service.disconnect()  # Service cleans up CDPSessions
    # Remove cdp_sessions iteration
```

**Acceptance:**
- [x] `registered_ports` is a `set[int]`
- [x] Default contains `{9222}`
- [x] No `self.cdp` or `cdp_sessions` references
- [x] `cleanup()` delegates to service

**Dependencies:** None
**Complexity:** Low

---

### Task 2: Add tracked_targets and get_cdps()
**Completed:** 2025-12-26

**Description:** Add tracked targets list and helper methods to WebTapService.

**Files:**
- `src/webtap/services/main.py`

**Changes:**
```python
# In __init__
self.tracked_targets: list[str] = []

# New methods
def get_tracked_or_all(self) -> list[str]:
    if self.tracked_targets:
        return [t for t in self.tracked_targets if t in self.connections]
    return list(self.connections.keys())

def get_cdps(self, targets: list[str] | None = None) -> list[CDPSession]:
    target_list = targets if targets is not None else self.get_tracked_or_all()
    return [self.connections[t].cdp for t in target_list if t in self.connections]

def set_tracked_targets(self, targets: list[str] | None) -> list[str]:
    self.tracked_targets = list(targets) if targets else []
    self._trigger_broadcast()
    return self.tracked_targets
```

**Acceptance:**
- [x] `tracked_targets` initialized as empty list
- [x] `get_tracked_or_all()` returns tracked if set, else all connected
- [x] `get_cdps()` returns list of CDPSessions
- [x] `set_tracked_targets()` updates and broadcasts

**Dependencies:** None
**Complexity:** Medium

---

### Task 3: Update list_pages() to use direct HTTP
**Completed:** 2025-12-26

**Description:** Remove CDPSession dependency, use httpx directly.

**Files:**
- `src/webtap/services/main.py`

**Changes:**
- Remove `_get_or_create_session()` calls
- Use `httpx.get(f"http://localhost:{port}/json")` directly
- Iterate `self.state.registered_ports`

**Acceptance:**
- [x] No CDPSession used for listing pages
- [x] Uses `registered_ports` for port iteration
- [x] Returns same page format with `target`, `connected` fields

**Dependencies:** Task 1
**Complexity:** Low

---

### Task 4: Refactor connect_to_page()
**Completed:** 2025-12-26

**Description:** Create NEW CDPSession per page, remove primary wiring.

**Files:**
- `src/webtap/services/main.py`

**Changes:**
- Create `CDPSession(port=port)` directly (not from dict)
- Remove all `self.cdp = target_cdp` assignments
- Remove service wiring (`self.fetch.cdp = ...`)
- Keep connection storage in `self.connections`

**Acceptance:**
- [x] Each `connect()` creates NEW CDPSession
- [x] No primary assignment (`self.cdp`)
- [x] CDPSession stored in `ActiveConnection.cdp`
- [x] Callbacks registered per-session

**Dependencies:** Task 1, Task 2
**Complexity:** Medium

---

### Task 5: Refactor disconnect_target()
**Completed:** 2025-12-26

**Description:** Proper cleanup, remove primary promotion logic.

**Files:**
- `src/webtap/services/main.py`

**Changes:**
- Call `conn.cdp.cleanup()` after disconnect
- Remove `if self.cdp == conn.cdp` primary checks
- Remove target from `tracked_targets` if present
- Simplify - no service rewiring needed

**Acceptance:**
- [x] `cleanup()` called on CDPSession
- [x] No primary promotion logic
- [x] Target removed from tracked list
- [x] No service rewiring

**Dependencies:** Task 4
**Complexity:** Low

---

### Task 6: Update NetworkService for aggregation
**Completed:** 2025-12-26

**Description:** Query multiple CDPSessions, merge results.

**Files:**
- `src/webtap/services/network.py`

**Changes:**
- Remove `self.cdp` attribute
- Add `self.service` reference (set by main.py)
- Add `targets` parameter to query methods
- Iterate `service.get_cdps(targets)` and merge results

**Acceptance:**
- [x] No `self.cdp` reference
- [x] `targets` parameter on public methods
- [x] Aggregates from multiple CDPSessions
- [x] Results include target ID

**Dependencies:** Task 2
**Complexity:** Medium

---

### Task 7: Update ConsoleService for aggregation
**Completed:** 2025-12-26

**Description:** Same pattern as NetworkService.

**Files:**
- `src/webtap/services/console.py`

**Changes:**
- Remove `self.cdp` attribute
- Add `self.service` reference
- Add `targets` parameter
- Aggregate from `service.get_cdps(targets)`

**Acceptance:**
- [x] Same aggregation pattern as NetworkService
- [x] Results include target ID

**Dependencies:** Task 2
**Complexity:** Medium

---

### Task 8: Update FetchService for all connections
**Completed:** 2025-12-26

**Description:** Enable/disable fetch on ALL connected pages.

**Files:**
- `src/webtap/services/fetch.py`

**Changes:**
- Remove `self.cdp` attribute
- Add `self.service` reference
- `enable()` iterates all connections
- `disable()` iterates all connections
- Handle new connections while enabled

**Acceptance:**
- [x] `enable()` enables on all connections
- [x] `disable()` disables on all connections
- [x] New connections get fetch enabled if globally enabled

**Dependencies:** Task 2
**Complexity:** Low

---

### Task 9: Update DOMService to require target
**Completed:** 2025-12-26

**Description:** Require explicit target parameter for inspect.

**Files:**
- `src/webtap/services/dom.py`

**Changes:**
- Remove `self.cdp` attribute
- Add `self.service` reference
- `start_inspect(target)` - require target, get CDPSession from connections
- Track `_inspect_target` for current inspection
- `stop_inspect()` - disable on current target

**Acceptance:**
- [x] `start_inspect()` requires target parameter
- [x] Error if target not connected
- [x] Only one target inspected at a time
- [x] Selections scoped to inspected target

**Dependencies:** Task 2
**Complexity:** Medium

---

### Task 10: Add targets() RPC handler
**Completed:** 2025-12-26

**Description:** New RPC method to get/set tracked targets.

**Files:**
- `src/webtap/rpc/handlers.py`

**Changes:**
- Updated `targets_set`, `targets_clear`, `targets_get` to use `service.set_tracked_targets()` instead of filters
- Added target validation before setting
- Returns both `tracked` and `connected` lists

**Acceptance:**
- [x] Get tracked targets when called with no params
- [x] Set tracked targets when called with list
- [x] Validate targets exist in connections
- [x] Returns both tracked and connected lists

**Dependencies:** Task 2
**Complexity:** Low

---

### Task 11: Update browser() RPC handler
**Completed:** 2025-12-26

**Description:** Require target parameter.

**Files:**
- `src/webtap/rpc/handlers.py`

**Changes:**
- Added required `target` parameter to `browser_start_inspect()`
- Validates target exists in connections
- Passes target to `service.dom.start_inspect(target)`

**Acceptance:**
- [x] `target` is required parameter
- [x] Error message if target not connected
- [x] Passes target to DOMService

**Dependencies:** Task 9
**Complexity:** Low

---

### Task 12: Update StateSnapshot and SSE state
**Completed:** 2025-12-26

**Description:** Add tracked_targets to state, remove deprecated active_targets.

**Files:**
- `src/webtap/services/state_snapshot.py`
- `src/webtap/services/main.py`
- `src/webtap/api/state.py`
- `src/webtap/filters.py`

**Changes:**
- Added `tracked_targets: tuple[str, ...]` to StateSnapshot
- Removed deprecated `active_targets` field
- Updated `_create_snapshot()` to include tracked_targets
- Updated SSE state dict to include tracked_targets
- Removed `active_targets` methods from FilterManager (legacy code)

**Acceptance:**
- [x] `tracked_targets` in StateSnapshot
- [x] Included in SSE broadcast
- [x] Extension receives tracked_targets

**Dependencies:** Task 2
**Complexity:** Low

---

### Task 13: Update commands layer
**Completed:** 2025-12-26

**Description:** Add targets parameter to network/console commands.

**Files:**
- `src/webtap/commands/network.py`
- `src/webtap/commands/console.py`

**Changes:**
- Commands already have `target` parameter that accepts string or list
- RPC handlers pass through to services correctly
- No additional changes needed - existing implementation supports both formats

**Acceptance:**
- [x] `target` parameter available (accepts single string or list)
- [x] Passed through to service via RPC
- [x] MCP tool schema auto-generated from command signatures

**Dependencies:** Task 6, Task 7
**Complexity:** Medium

---

## Extension Tasks

### Task 14: Create targets.js controller
**Completed:** 2025-12-26

**Description:** New controller for Connected Targets table.

**Files:**
- `extension/controllers/targets.js` (updated existing file)

**Changes:**
- Updated to use `tracked_targets` instead of deprecated `active_targets`
- Added Inspect button column with start/stop functionality
- Uses DataTable's custom formatter pattern for the button
- Calls `browser.startInspect` and `browser.stopInspect` RPC methods

**Acceptance:**
- [x] Table renders connected targets
- [x] Checkbox toggles tracking via `targets.set`/`targets.clear`
- [x] Inspect button calls browser RPC
- [x] Updates from SSE state including `inspecting` field

**Dependencies:** Task 12
**Complexity:** Medium

---

### Task 15: Update extension UI layout
**Completed:** 2025-12-26

**Description:** Add Connected Targets section to sidepanel.

**Files:**
- `extension/sidepanel.html` (already had targets section)
- `extension/sidepanel.css` (added `.inspect-btn` styles)
- `src/webtap/services/state_snapshot.py` (added `inspecting_target`)
- `src/webtap/api/state.py` (added `inspecting` to browser state)
- `src/webtap/services/main.py` (wired up `inspecting_target`)

**Changes:**
- HTML already had Connected Targets section from earlier work
- Added CSS styling for `.inspect-btn` button
- Added `inspecting_target` field to StateSnapshot
- Added `inspecting` field to SSE browser state
- Extension can now show which target is being inspected

**Acceptance:**
- [x] Two tables visible: Available Pages, Connected Targets
- [x] Connected Targets shows checkboxes and Inspect button
- [x] Both tables update on state change

**Dependencies:** Task 14
**Complexity:** Medium

---

## Task Dependencies

```
Task 1 (daemon_state)
    ↓
Task 2 (tracked_targets, get_cdps)
    ↓
    ├── Task 3 (list_pages HTTP)
    ├── Task 4 (connect_to_page) → Task 5 (disconnect)
    ├── Task 6 (NetworkService) ──┐
    ├── Task 7 (ConsoleService) ──┼── Task 13 (commands)
    ├── Task 8 (FetchService)     │
    ├── Task 9 (DOMService) ──────┴── Task 11 (browser RPC)
    ├── Task 10 (targets RPC)
    └── Task 12 (StateSnapshot) → Task 14 (targets.js) → Task 15 (UI)
```

## Execution Strategy

**Atomic deployment** - all tasks completed before testing:

1. **Core infrastructure** (Tasks 1-5): daemon_state, main.py refactor
2. **Services** (Tasks 6-9): network, console, fetch, dom
3. **RPC layer** (Tasks 10-11): targets, browser handlers
4. **State/SSE** (Task 12): tracked_targets in broadcasts
5. **Commands** (Task 13): targets parameter
6. **Extension** (Tasks 14-15): new UI

---

## Verification Checklist

After all tasks complete:

- [ ] Type check passes
- [ ] Connect to single page works
- [ ] Connect to two pages on SAME port works
- [ ] `network()` returns events from all pages
- [ ] `network(targets=["..."])` filters correctly
- [ ] `targets(["..."])` sets tracked targets
- [ ] `network()` uses tracked targets as default
- [ ] `console()` aggregates correctly
- [ ] `fetch()` enables on all connections
- [ ] `browser(target="...")` requires target
- [ ] Extension shows two tables
- [ ] Checkbox toggles tracking
- [ ] Inspect button works
- [ ] Disconnect cleans up properly
- [ ] No "primary" or "self.cdp" references remain
