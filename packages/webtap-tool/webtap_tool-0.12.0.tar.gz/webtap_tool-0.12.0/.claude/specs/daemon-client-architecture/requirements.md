# Feature: API Refactor and Sync Fix

## Overview

Fix the WebTap extension sync bug and refactor the monolithic api.py (1200+ lines) into a modular package structure. The daemon-client architecture already exists (`client.py`, `daemon.py`), but the sync bug causes stale UI state and the large api.py file hurts maintainability.

## Specification Heritage

**Evolves from:** `.claude/specs/client-daemon-sync/`

The original spec identified the sync bug (broadcast queue not wired, action endpoints don't return state). This spec supersedes it by:
1. Adding API code organization (split api.py into modules)
2. Providing cleaner implementation after understanding existing architecture

**Discovery:** Daemon-client architecture already exists:
- `client.py`: `DaemonClient` HTTP wrapper
- `daemon.py`: `ensure_daemon()`, pidfile at `~/.local/state/webtap/daemon.pid`
- Commands already use `state.client` for HTTP calls
- No architectural changes needed, just bug fixes and refactoring

**Preserved from original:**
- Action endpoints return full state for immediate UI updates
- SSE for background state broadcasts
- Error responses include current state

## User Stories

### Story 1: Reliable Connection Status
**As a** developer using the WebTap extension
**I want** the extension to always show the correct connection status
**So that** I know whether the daemon is connected to a Chrome page

**Acceptance Criteria (EARS notation):**
- WHEN the user clicks "Connect" in the extension, THE SYSTEM SHALL return the new state in the HTTP response AND the extension SHALL update immediately
- WHEN the daemon connects to a Chrome page, THE SYSTEM SHALL broadcast the updated state via SSE within 100ms
- WHEN the SSE connection is established, THE SYSTEM SHALL send the current accurate state immediately
- WHEN the broadcast queue is created, THE SYSTEM SHALL wire it to WebTapService automatically

### Story 2: Immediate UI Feedback on Actions
**As a** developer using the WebTap extension
**I want** UI updates to happen immediately when I perform actions
**So that** I don't experience "click but nothing happens" scenarios

**Acceptance Criteria (EARS notation):**
- WHEN the user performs any action (connect, disconnect, fetch toggle, clear), THE SYSTEM SHALL return the full current state in the response
- WHEN the extension receives a response with state, THE SYSTEM SHALL update the UI immediately without waiting for SSE
- WHEN an action fails, THE SYSTEM SHALL return an error with the current state so the UI remains consistent

### Story 3: Background State Updates
**As a** developer using the WebTap extension
**I want** to see real-time updates for background events (CDP events, console messages)
**So that** I can monitor browser activity

**Acceptance Criteria (EARS notation):**
- WHEN CDP events are received by the daemon, THE SYSTEM SHALL update the event count in the next SSE broadcast
- WHEN multiple CDP events arrive rapidly, THE SYSTEM SHALL coalesce broadcasts to prevent flooding (max 10/sec)
- WHEN the SSE connection drops, THE SYSTEM SHALL allow the browser's EventSource to auto-reconnect

### Story 4: Maintainable API Code Structure
**As a** developer maintaining WebTap
**I want** the API code organized into logical modules
**So that** I can easily find and modify specific functionality

**Acceptance Criteria (EARS notation):**
- WHEN looking for route handlers, THE SYSTEM SHALL have them organized in `api/routes/` by domain
- WHEN looking for server lifecycle code, THE SYSTEM SHALL have it in `api/server.py`
- WHEN looking for SSE/broadcast logic, THE SYSTEM SHALL have it in `api/sse.py`
- WHEN looking for state helpers, THE SYSTEM SHALL have them in `api/state.py`
- WHEN importing public API, THE SYSTEM SHALL export from `api/__init__.py`

## Non-Functional Requirements

- **Performance:** Action endpoints SHALL respond within 100ms (excluding CDP latency)
- **Performance:** SSE broadcasts SHALL be coalesced to max 10/second during high-frequency CDP events
- **Reliability:** State returned in action responses SHALL always reflect post-action state
- **Maintainability:** No single file in api/ SHALL exceed 300 lines
- **Maintainability:** Each route module SHALL handle a single domain

## Constraints

- SSE protocol preserved (no WebSocket migration - unnecessary complexity)
- Must work with existing Chrome DevTools Protocol patterns
- Design for tomorrow - no backward compatibility shims or re-exports

## Out of Scope

- Architectural changes to daemon-client model (already works)
- WebSocket-based communication (SSE is sufficient)
- Extension UI redesign
- New CDP features
- Authentication/authorization

## Assumptions

- The extension's EventSource auto-reconnect is reliable
- Action response latency is acceptable for UI updates (no optimistic UI needed)
- CDP event coalescing at 10/sec is sufficient for UI responsiveness
- Breaking changes to imports are acceptable (update all callers)
