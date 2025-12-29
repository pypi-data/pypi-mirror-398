# Feature: Network Tooling Improvements

## Overview

Improve WebTap's network request inspection by introducing a HAR-based data model, enhanced filtering, and ES-style field selection. This replaces the current raw CDP event querying with a structured, developer-friendly approach that supports both HTTP and WebSocket protocols.

## Specification Heritage

**Builds on:** `.claude/specs/daemon-client-architecture/` (completed)

The daemon-client architecture spec established the modular API structure. This spec extends the data layer with:
1. HAR-based aggregation view replacing raw event queries
2. Simplified filter system replacing category-based modes
3. New `request()` command replacing `events()`

## User Stories

### Story 1: View Network Requests with Inline Filtering
**As a** developer debugging network requests
**I want** to filter requests directly in the network command
**So that** I can quickly find specific requests without configuring filters

**Acceptance Criteria (EARS notation):**
- WHEN the user calls `network()`, THE SYSTEM SHALL return recent requests with noise filter applied
- WHEN the user calls `network(status=404)`, THE SYSTEM SHALL return only requests with status 404
- WHEN the user calls `network(method="POST")`, THE SYSTEM SHALL return only POST requests
- WHEN the user calls `network(type="xhr")`, THE SYSTEM SHALL return only XHR requests
- WHEN the user calls `network(all=True)`, THE SYSTEM SHALL bypass the noise filter
- WHEN multiple inline filters are provided, THE SYSTEM SHALL apply them with AND logic

### Story 2: Inspect Request Details with Field Selection
**As a** developer analyzing specific requests
**I want** to select which fields to include in the response
**So that** I can get exactly the information I need without noise

**Acceptance Criteria (EARS notation):**
- WHEN the user calls `request(id)`, THE SYSTEM SHALL return minimal default fields (url, method, status, size)
- WHEN the user calls `request(id, ["*"])`, THE SYSTEM SHALL return all available fields
- WHEN the user calls `request(id, ["request.headers.*"])`, THE SYSTEM SHALL return all request headers
- WHEN the user calls `request(id, ["response.headers.content-type"])`, THE SYSTEM SHALL return that specific header
- WHEN the user calls `request(id, ["body"])`, THE SYSTEM SHALL fetch and include the response body
- WHEN requesting body for a request without body, THE SYSTEM SHALL return null for the body field
- WHEN the ID does not exist, THE SYSTEM SHALL return an error with helpful message

### Story 3: View WebSocket Connections
**As a** developer debugging WebSocket communication
**I want** WebSocket connections to appear alongside HTTP requests
**So that** I can monitor all network activity in one place

**Acceptance Criteria (EARS notation):**
- WHEN a WebSocket connection is established, THE SYSTEM SHALL show it in network() with type "websocket"
- WHEN viewing a WebSocket in request(), THE SYSTEM SHALL show frame statistics (sent/received counts, total bytes)
- WHEN the WebSocket is still open, THE SYSTEM SHALL show state as "open"
- WHEN the WebSocket closes, THE SYSTEM SHALL show state as "closed"
- WHEN filtering by type, THE SYSTEM SHALL support `type="websocket"` filter

### Story 4: Filter Groups for Noise Reduction
**As a** developer who doesn't want to see tracking/asset requests
**I want** to create named filter groups that I can toggle on/off
**So that** I can quickly switch between different filtering contexts per project

**Acceptance Criteria (EARS notation):**
- WHEN `filters()` is called, THE SYSTEM SHALL show all groups with their enabled/disabled status
- WHEN `filters(add="assets", hide={"types": ["Image", "Font"], "urls": []})` is called, THE SYSTEM SHALL create a new group
- WHEN `filters(add="tracking", hide={"types": [], "urls": ["*analytics*"]})` is called, THE SYSTEM SHALL create a new group
- WHEN `filters(enable="assets")` is called, THE SYSTEM SHALL enable that group
- WHEN `filters(disable="tracking")` is called, THE SYSTEM SHALL disable that group
- WHEN `filters(remove="assets")` is called, THE SYSTEM SHALL delete that group
- WHEN multiple groups are enabled, THE SYSTEM SHALL combine all hide.types and hide.urls with OR logic (deduplicated)
- WHEN filter config file doesn't exist, THE SYSTEM SHALL start with no groups (empty config)
- WHEN `network(all=True)` is called, THE SYSTEM SHALL bypass all filter groups

**State Management:**
- Group definitions (name, hide config) are persisted to `.webtap/filters.json`
- Group enabled/disabled state is in daemon memory only (not persisted)
- WHEN daemon starts, THE SYSTEM SHALL load group definitions from file (all disabled by default)
- WHEN `filters(add=...)` is called, THE SYSTEM SHALL persist group definition to file
- WHEN `filters(enable=...)` or `filters(disable=...)` is called, THE SYSTEM SHALL update daemon memory only
- WHEN extension toggles a group, THE SYSTEM SHALL update daemon memory (same as REPL)

**Filter Config Structure (file - definitions only):**
```json
{
  "groups": {
    "assets": {"hide": {"types": ["Image", "Font", "Stylesheet"], "urls": []}},
    "tracking": {"hide": {"types": [], "urls": ["*analytics*", "*doubleclick*"]}}
  }
}
```

### Story 5: Request Lifecycle States
**As a** developer monitoring in-flight requests
**I want** to see the state of each request
**So that** I know which requests are pending, loading, or complete

**Acceptance Criteria (EARS notation):**
- WHEN a request is sent but no response received, THE SYSTEM SHALL show state "pending"
- WHEN a response is received but loading not finished, THE SYSTEM SHALL show state "loading"
- WHEN loading finishes successfully, THE SYSTEM SHALL show state "complete"
- WHEN loading fails, THE SYSTEM SHALL show state "failed" with error info
- WHEN a WebSocket is connecting, THE SYSTEM SHALL show state "connecting"

## Non-Functional Requirements

- **Performance:** `network()` queries SHALL complete within 50ms for 1000 events
- **Performance:** HAR view aggregation SHALL not block CDP event ingestion
- **Memory:** Body content SHALL only be fetched on-demand, not stored in HAR view
- **Compatibility:** Filter config SHALL use `.webtap/filters.json` path (no migration of old format)

## Constraints

- DuckDB views must be used (not materialized tables) to show incomplete requests
- Body fetching remains on-demand via CDP `Network.getResponseBody`
- Raw CDP events preserved for `inspect()` command (edge cases)
- WebSocket frame content not stored in HAR view (use `inspect()` for individual frames)

## Out of Scope

- HAR file export (future consideration)
- WebSocket frame-level inspection in `request()` (use `inspect()`)
- Filter migration from old category-based format
- Real-time streaming updates (SSE handles this separately)
- Request/response modification (handled by fetch interception)

## Assumptions

- Users prefer HAR-like structure over raw CDP event access
- Removing `events()` command won't break workflows (use `request(id, ["*"])` instead)
- WebSocket frame aggregation (counts/bytes) is sufficient for most debugging
- Default noise filter (Image, Font, Stylesheet, Media) matches common use cases
