# Feature: State Architecture Refactor

## Specification Heritage

**Evolves from:** `.claude/specs/separation-of-concerns/` (Completed 2025-12-25)

The separation-of-concerns spec extracted extension controllers and added per-target errors, but identified remaining framework-level issues that require deeper architectural changes:
- ResizeObserver loop errors from dynamic truncation
- Pages not showing connected state (extension overwrites server's `connected` field)
- Startup race condition ("Failed to fetch" before daemon ready)
- State inconsistency (`pages()` vs `targets()` show different states)

This spec addresses all of these as a **big bang atomic refactor**.

---

## Overview

Refactor WebTap's state management architecture to:
1. Make the extension "dumber" - trust server state instead of local computation
2. Deprecate the legacy `page` field in favor of `connections` array
3. Add per-target connection state to support concurrent multi-target operations
4. Fix ResizeObserver loop and startup race condition

**Approach:** Atomic refactor - all changes deployed together to avoid intermediate broken states.

---

## User Stories

### Story 1: Accurate Connection Status Display

**As a** WebTap user
**I want** the extension to show accurate connection status for all pages
**So that** I can see which Chrome tabs are connected to the daemon

**Acceptance Criteria (EARS notation):**
- WHEN a page is connected via daemon, THE SYSTEM SHALL display the connected indicator (green dot) next to that page in the pages list
- WHEN multiple pages are connected, THE SYSTEM SHALL display connected indicators for ALL connected pages, not just the first
- WHEN the daemon reports a page as connected, THE SYSTEM SHALL use the server's `connected` field directly without local recomputation
- WHEN a page is disconnected, THE SYSTEM SHALL immediately remove the connected indicator

---

### Story 2: Concurrent Multi-Target Operations

**As a** WebTap user with multiple Chrome tabs connected
**I want** to perform operations on one target while another is connecting
**So that** I don't have to wait for all connections to complete before working

**Acceptance Criteria (EARS notation):**
- WHEN target A is in "connecting" state, THE SYSTEM SHALL allow RPC operations on target B if B is in "connected" state
- WHEN target A disconnects, THE SYSTEM SHALL preserve target B's connected state and allow operations to continue
- WHEN an RPC method specifies a target parameter, THE SYSTEM SHALL validate state requirements against that target's individual state, not global state
- WHEN no target is specified, THE SYSTEM SHALL fall back to global state validation for backward compatibility

---

### Story 3: Reliable Extension Startup

**As a** WebTap user
**I want** the extension to connect to the daemon reliably on startup
**So that** I don't see "Failed to fetch" errors when opening the extension

**Acceptance Criteria (EARS notation):**
- WHEN the daemon is not immediately available, THE SYSTEM SHALL retry discovery with exponential backoff (500ms, 1s, 2s)
- WHEN all retry attempts fail, THE SYSTEM SHALL display a user-friendly "Daemon not running" message
- WHEN a cached port is stale, THE SYSTEM SHALL fallback to port scanning
- WHEN the daemon becomes available during retry, THE SYSTEM SHALL connect successfully

---

### Story 4: Responsive DataTable Rendering

**As a** WebTap user resizing the sidepanel
**I want** the DataTable to resize smoothly without console errors
**So that** I have a polished user experience

**Acceptance Criteria (EARS notation):**
- WHEN the DataTable container is resized, THE SYSTEM SHALL debounce truncation updates using requestAnimationFrame
- WHEN rapid resize events occur, THE SYSTEM SHALL coalesce updates to prevent ResizeObserver loop errors
- WHEN the DataTable is destroyed, THE SYSTEM SHALL properly clean up the ResizeObserver

---

## Non-Functional Requirements

### Performance
- SSE state broadcasts SHALL complete within 50ms
- Extension state updates SHALL render within 16ms (one frame)
- ResizeObserver callbacks SHALL be debounced to max 60fps

### Reliability
- Daemon discovery SHALL succeed within 5 seconds if daemon is running
- Per-target state SHALL be thread-safe and consistent with global state

### Backward Compatibility
- RPC methods without `target` parameter SHALL continue using global state validation
- Extension SHALL handle both old and new SSE state formats during rollout (if needed)

---

## Constraints

### Technical Constraints
- Must work with existing `transitions` library for state machine
- Must preserve immutable `StateSnapshot` pattern for thread-safe SSE
- Must work with Chrome extension manifest v3

### Breaking Changes (Intentional)
- `state.page` field WILL be removed from SSE state
- Extension WILL require update to work with new state shape

---

## Out of Scope

- WebSocket replacement for SSE (future consideration)
- Per-target inspect mode (inspect is global)
- Multi-client conflict resolution
- Undo/redo for connection operations

---

## Assumptions

1. **Single extension instance** - Only one sidepanel instance connects to daemon at a time
2. **Target format stable** - Target ID format (`port:page_id`) won't change
3. **Connections dict thread-safe** - Python dict operations are atomic for our use case
4. **RAF availability** - `requestAnimationFrame` is available in Chrome extension context
5. **Daemon restarts clear state** - All connections reset when daemon restarts
