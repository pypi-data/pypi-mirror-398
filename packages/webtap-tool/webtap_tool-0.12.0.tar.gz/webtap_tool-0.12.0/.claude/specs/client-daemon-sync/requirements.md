# Feature: WebTap Client-Daemon Sync Refactoring

## Overview

Refactor the WebTap extension ↔ daemon communication to ensure reliable state synchronization. The current architecture has a bug where the broadcast queue is not wired in daemon mode, causing the extension to show stale state (e.g., "Not connected" when actually connected). Additionally, the architecture relies solely on SSE broadcasts which can be missed due to coalescing or timing issues.

## Specification Heritage

This specification formalizes the plan from `~/.claude/plans/adaptive-doodling-gray.md`.

**Already Completed:**
- DaemonState extraction to separate module
- Clean daemon shutdown (no traceback on Ctrl+C)

## User Stories

### Story 1: Reliable Connection Status
**As a** developer using the WebTap extension
**I want** the extension to always show the correct connection status
**So that** I know whether the daemon is connected to a Chrome page

**Acceptance Criteria (EARS notation):**
- WHEN the user clicks "Connect" in the extension, THE SYSTEM SHALL return the new state in the HTTP response AND the extension SHALL update immediately
- WHEN the daemon connects to a Chrome page, THE SYSTEM SHALL broadcast the updated state via SSE within 100ms
- WHEN the SSE connection is established, THE SYSTEM SHALL send the current accurate state immediately
- WHEN the broadcast queue is not yet created, THE SYSTEM SHALL wait for it before accepting connections

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

### Story 4: Clean Error Handling
**As a** developer using the WebTap extension
**I want** consistent error responses across all endpoints
**So that** I can handle errors uniformly in the extension

**Acceptance Criteria (EARS notation):**
- WHEN any endpoint encounters an error, THE SYSTEM SHALL return `{"error": "message", "state": {...}}` format
- WHEN the daemon is not connected and a connection-required endpoint is called, THE SYSTEM SHALL return an error with current state
- WHEN an exception occurs, THE SYSTEM SHALL catch it and return a structured error response

## Non-Functional Requirements

- **Performance:** Action endpoints SHALL respond within 100ms (excluding CDP latency)
- **Performance:** SSE broadcasts SHALL be coalesced to max 10/second during high-frequency CDP events
- **Reliability:** State returned in action responses SHALL always reflect post-action state
- **Maintainability:** Services SHALL use constructor injection for dependencies

## Constraints

- Must maintain backward compatibility with existing extension code (gradual migration)
- SSE protocol must be preserved (no WebSocket migration)
- Must work with existing Chrome DevTools Protocol patterns

## Out of Scope

- WebSocket-based communication (SSE is sufficient)
- Extension UI redesign
- New CDP features
- Authentication/authorization

## Assumptions

- The extension's EventSource auto-reconnect is reliable
- Action response latency is acceptable for UI updates (no optimistic UI needed)
- CDP event coalescing at 10/sec is sufficient for UI responsiveness
- The broadcast queue will be created within 100ms of server start
