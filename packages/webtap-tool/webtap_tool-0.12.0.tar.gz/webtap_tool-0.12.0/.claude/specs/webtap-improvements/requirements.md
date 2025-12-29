# Feature: WebTap Improvements

## Overview

Three interconnected improvements to WebTap's architecture and usability:
1. **Target Architecture Redesign** - Decouple actions from connection state
2. **Console Entry Drill-Down** - Add `entry(id)` command for console inspection
3. **Extension DataTable Component** - Reusable table UI component

Breaking changes accepted. No migration path required.

## User Stories

### Story 1: Fire-and-Forget Actions on Any Page

**As a** developer debugging multiple browser tabs
**I want** to execute JavaScript or navigate on any page without connecting first
**So that** I can quickly interact with pages without managing connection state

**Acceptance Criteria (EARS notation):**

- WHEN user calls `js(code, target="9222:abc")` and target page exists, THE SYSTEM SHALL execute the code on that page and return the result
- WHEN user calls `js(code, target="9224:def")` and port 9224 is not registered, THE SYSTEM SHALL auto-register the port, execute the code, and disconnect
- WHEN user calls `navigate(url, target="9222:abc")`, THE SYSTEM SHALL navigate without requiring prior `connect()`
- WHEN user calls `reload(target="9222:abc")`, THE SYSTEM SHALL reload without requiring connection state
- WHEN user calls `js(code)` without target and no connection exists, THE SYSTEM SHALL return an error with suggestion: "Specify target or connect first"
- WHEN target page is already connected, THE SYSTEM SHALL reuse the existing connection for actions
- WHEN ephemeral action completes, THE SYSTEM SHALL disconnect cleanly without affecting other connections

### Story 2: Target Filtering for Queries

**As a** developer with multiple pages connected
**I want** to filter network/console queries by target
**So that** I can see events from specific pages without noise from others

**Acceptance Criteria (EARS notation):**

- WHEN user calls `network(target="9222:abc")`, THE SYSTEM SHALL return only requests from that target
- WHEN user calls `network(target=["9222:abc", "9224:def"])`, THE SYSTEM SHALL return requests from both targets
- WHEN user calls `console(target="9222:abc")`, THE SYSTEM SHALL return only console messages from that target
- WHEN user calls `network()` without target filter, THE SYSTEM SHALL return requests from all connected targets (current behavior)
- WHEN specified target has no stored events, THE SYSTEM SHALL return empty results (not an error)

### Story 3: Console Entry Drill-Down

**As a** developer investigating console errors
**I want** to inspect full console entry details including stack traces
**So that** I can debug issues without switching to Chrome DevTools

**Acceptance Criteria (EARS notation):**

- WHEN user calls `entry(5)`, THE SYSTEM SHALL return minimal fields: level, message, source
- WHEN user calls `entry(5, ["*"])`, THE SYSTEM SHALL return the full CDP event
- WHEN user calls `entry(5, ["stackTrace"])`, THE SYSTEM SHALL return only the stack trace
- WHEN user calls `entry(5, ["args.*"])`, THE SYSTEM SHALL return all console arguments
- WHEN user calls `entry(5, expr="len(data['args'])")`, THE SYSTEM SHALL evaluate the expression against selected data
- WHEN user calls `entry(5, output="error.json")`, THE SYSTEM SHALL export the entry to file
- WHEN entry has stack trace, THE SYSTEM SHALL format call frames as: `at functionName (file:line:col)`
- WHEN entry ID does not exist, THE SYSTEM SHALL return error: "Console entry {id} not found"

### Story 4: Extension DataTable Component

**As a** WebTap extension user
**I want** a consistent table display for network, console, and pages
**So that** I can efficiently browse and select data in the side panel

**Acceptance Criteria (EARS notation):**

- WHEN DataTable is created with columns config, THE SYSTEM SHALL render header row with column headers
- WHEN `table.update(data)` is called, THE SYSTEM SHALL efficiently update rows (reuse DOM elements)
- WHEN user clicks a row in selectable table, THE SYSTEM SHALL highlight the row and call `onRowClick`
- WHEN column has `truncate: true`, THE SYSTEM SHALL truncate text with ellipsis and show full text on hover
- WHEN column has `formatter` function, THE SYSTEM SHALL use it to render cell content
- WHEN table body overflows, THE SYSTEM SHALL enable vertical scroll with fixed header
- WHEN status code is 2xx, THE SYSTEM SHALL display green badge
- WHEN status code is 4xx/5xx, THE SYSTEM SHALL display red badge
- WHEN request is paused, THE SYSTEM SHALL display yellow badge with pause indicator

## Non-Functional Requirements

- **Performance:** Ephemeral connections must complete within 500ms for local Chrome
- **Performance:** DataTable must handle 500+ rows without lag (efficient DOM reuse)
- **Compatibility:** Actions work on any Chrome debug port (9222-9299 typical range)
- **Compatibility:** DataTable works in Chrome side panel (narrow viewport)
- **Maintainability:** DataTable follows existing extension patterns (vanilla JS, CSS variables)

## Constraints

- No external dependencies for extension (vanilla JS only)
- Python 3.10+ for type hints
- Must pass `ruff check`, `ruff format`, `basedpyright`
- Breaking changes to existing APIs are acceptable

## Out of Scope

- Object resolution via CDP `Runtime.getProperties` (v2 feature)
- Virtual scrolling for very large tables
- Column resizing/reordering in DataTable
- Persistent target filter state across sessions
- WebSocket connection pooling for ephemeral actions

## Assumptions

- Chrome DevTools Protocol is available on specified ports
- Console events are stored in DuckDB with full CDP structure
- Existing `request()` command pattern is stable and proven
- Extension side panel has minimum width of 300px
- Users typically have 1-5 pages connected simultaneously
