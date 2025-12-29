# Design: WebTap Separation of Concerns

## Architecture Overview

This refactor touches two layers:
1. **Extension (JS):** Extract 4 controllers from `main.js`
2. **Daemon (Python):** Fix handler consistency + add per-target errors

```
Extension                                    Daemon
┌─────────────────────────────────┐         ┌─────────────────────────────┐
│ main.js (orchestrator only)     │         │ rpc/handlers.py             │
│  ├── controllers/theme.js       │   SSE   │  └── requires_state fixes   │
│  ├── controllers/header.js      │◄────────│                             │
│  ├── controllers/tabs.js        │         │ api/state.py                │
│  ├── controllers/notices.js     │   RPC   │  └── per-target errors      │
│  └── client.js (+ headers)      │────────►│                             │
└─────────────────────────────────┘         └─────────────────────────────┘
```

---

## Part 1: Extension Controllers

### Component Analysis

#### Existing Components to Modify

| File | Changes |
|------|---------|
| `extension/main.js` | Remove extracted functions, add imports, wire controllers |
| `extension/client.js` | Add `x-webtap-*` headers, add STALE_EPOCH retry |

#### New Components to Create

| File | Purpose |
|------|---------|
| `extension/controllers/theme.js` | Theme toggle (auto/light/dark) |
| `extension/controllers/notices.js` | Notice banner rendering |
| `extension/controllers/header.js` | Status, error banner, event count |
| `extension/controllers/tabs.js` | Tab switching with network callback |

---

### Controller Interfaces

#### theme.js

```javascript
/**
 * Theme Controller
 * Manages theme toggle: auto → light → dark → auto
 */

// No init params needed - reads from localStorage
export function init();

// Cycle to next theme
export function toggle();
```

**DOM Elements:** `#themeToggle`
**Storage:** `localStorage["webtap-theme"]`

---

#### notices.js

```javascript
/**
 * Notices Controller
 * Renders notice banners with dismiss functionality
 */
import { icons, ui } from "../lib/ui.js";

const TYPE_CLASSES = {
  extension_installed: "notice--info",
  extension_updated: "notice--warning",
  extension_manifest_changed: "notice--warning",
  client_stale: "notice--stale",
};

// Render notices to banner
export function render(notices, clients);
```

**DOM Elements:** `#noticesBanner`
**Dependencies:** `ui.el()`, `icons.close`

---

#### header.js

```javascript
/**
 * Header Controller
 * Manages status indicator, error banner, event count
 */

// Update header status text and state class
export function updateStatus(text, state = "disconnected");

// Update from SSE connection state
export function updateConnection(state);

// Update event count display
export function updateEventCount(count);

// Show/hide error banner
export function updateError(error);

// Convenience: show error message
export function showError(message);
```

**DOM Elements:** `#status`, `.status-text`, `#errorBanner`, `#errorMessage`

---

#### tabs.js

```javascript
/**
 * Tabs Controller
 * Manages tab switching with network fetch callback
 */

let activeTab = localStorage.getItem("webtap-tab") || "pages";
let onNetworkTabActive = null;

// Initialize with callbacks
export function init(callbacks = {});

// Switch to tab, trigger callback if network
export function switchTo(tabName);

// Get current active tab
export function getActive();
```

**DOM Elements:** `.tab-button`, `.tab-content`
**Storage:** `localStorage["webtap-tab"]`
**Callback:** `onNetworkTabActive()` when switching to network tab

---

### Updated main.js Structure

After refactoring, main.js contains only:

```javascript
// Imports
import * as theme from "./controllers/theme.js";
import * as tabs from "./controllers/tabs.js";
import * as header from "./controllers/header.js";
import * as notices from "./controllers/notices.js";
// ... existing controllers

// Global state (minimal)
let client = null;
let webtapAvailable = false;

// Callbacks for existing controllers
const callbacks = {
  onError: header.showError,
  getWebtapAvailable: () => webtapAvailable,
  withButtonLock,
};

// Helper functions
async function withButtonLock(buttonId, asyncFn) { ... }
function setupEventHandlers() { ... }
function setupUIBindings() { ... }
async function discoverAndConnect() { ... }

// Initialize
theme.init();
tabs.init({ onNetworkTabActive: () => { ... } });
discoverAndConnect();
```

**Target:** ~150 lines (down from ~430)

---

## Part 2: Daemon Handler Fixes

### handlers.py Changes

#### Navigation Handlers - Add State Requirements

```python
# Before
@rpc.method("navigate")
def navigate(ctx, url, target=None): ...

# After
@rpc.method("navigate", requires_state=CONNECTED_STATES)
def navigate(ctx, url, target=None): ...
```

**Handlers to update:** `navigate`, `reload`, `back`, `forward`

#### Filter Handlers - Fix Broadcast Flags

```python
# Before (implicit broadcasts=True)
@rpc.method("filters.add")
def filters_add(ctx, name, config): ...

# After
@rpc.method("filters.add", broadcasts=False)
def filters_add(ctx, name, config): ...
```

**Handlers to update:** `filters.add`, `filters.remove`

---

## Part 3: Per-Target Errors

### Data Model Change

```python
# Before (api/state.py, services/main.py)
error_state: dict | None = None  # {"message": str, "timestamp": float}

# After
error_state: dict[str, dict] = {}  # {target_id: {"message": str, "timestamp": float}}
```

### SSE State Shape

```python
# Before
"error": {"message": "...", "timestamp": 1.0} | None

# After
"errors": {
  "9222:abc123": {"message": "Connection lost", "timestamp": 1.0},
  "9224:def456": {"message": "CDP timeout", "timestamp": 2.0}
}
```

### Extension Compatibility

Extension's `updateError()` needs to handle both shapes during transition, or we update atomically.

---

## Part 4: STALE_EPOCH Retry

### client.js Changes

```javascript
async call(method, params = {}, options = {}) {
  // ... existing code ...

  if (data.error?.code === "STALE_EPOCH" && !options._isRetry) {
    // Wait for next SSE state update
    await this._waitForStateUpdate();
    // Retry once
    return this.call(method, params, { ...options, _isRetry: true });
  }

  // ... rest of error handling ...
}

async _waitForStateUpdate(timeout = 2000) {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error("State update timeout")), timeout);
    const handler = () => {
      clearTimeout(timer);
      this.off("state", handler);
      resolve();
    };
    this.on("state", handler);
  });
}
```

---

## Error Handling Strategy

| Error Type | Handling |
|------------|----------|
| STALE_EPOCH | Auto-retry once after SSE update |
| INVALID_STATE | Surface to user via header.showError() |
| Network errors | Trigger reconnection flow |
| Per-target errors | Store in errors dict, display in UI |

---

## Migration Strategy

1. **Extension controllers:** Pure addition, no migration needed
2. **Handler fixes:** Additive (decorators), backward compatible
3. **Per-target errors:** Breaking change to SSE shape
   - Option A: Version the SSE format
   - Option B: Update extension and daemon atomically
   - **Recommended:** Option B (single PR, test together)
