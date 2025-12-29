# Feature: WebTap Separation of Concerns

## Overview

Refactor the WebTap extension and daemon to improve separation of concerns. The extension's `main.js` (~430 lines) will be split into dedicated controllers, and the daemon will receive fixes for handler consistency and improved error handling.

## User Stories

### Story 1: Extension Code Organization
**As a** developer maintaining WebTap
**I want** the extension code organized into focused controllers
**So that** I can find, understand, and modify specific functionality without navigating a monolithic file

**Acceptance Criteria (EARS notation):**
- WHEN the extension loads, THE SYSTEM SHALL initialize all controllers (theme, tabs, header, notices) independently
- WHEN theme toggle is clicked, THE SYSTEM SHALL cycle through auto → light → dark → auto
- WHEN tab is switched, THE SYSTEM SHALL update UI and trigger appropriate data fetches via callback
- WHEN SSE state arrives, THE SYSTEM SHALL dispatch updates to each controller
- WHEN an error occurs, THE SYSTEM SHALL display it via header controller

### Story 2: Daemon Handler Consistency
**As a** developer using the RPC API
**I want** consistent handler behavior for state requirements and broadcasts
**So that** operations fail predictably when preconditions aren't met

**Acceptance Criteria (EARS notation):**
- WHEN navigation methods (navigate/reload/back/forward) are called without connection, THE SYSTEM SHALL return INVALID_STATE error
- WHEN filter management methods (add/remove) complete, THE SYSTEM SHALL NOT broadcast state (read-only operations)
- WHEN extension makes RPC calls, THE SYSTEM SHALL include client tracking headers

### Story 3: Per-Target Error Tracking
**As a** user with multiple browser targets connected
**I want** to see which specific target had an error
**So that** I can troubleshoot the correct connection

**Acceptance Criteria (EARS notation):**
- WHEN a target-specific error occurs, THE SYSTEM SHALL store error with target ID
- WHEN SSE state is broadcast, THE SYSTEM SHALL include errors keyed by target ID
- WHEN error is dismissed, THE SYSTEM SHALL clear only that target's error

### Story 4: STALE_EPOCH Recovery
**As a** extension user
**I want** RPC calls to recover from epoch mismatches automatically
**So that** I don't see spurious errors during connection transitions

**Acceptance Criteria (EARS notation):**
- WHEN RPC call fails with STALE_EPOCH, THE SYSTEM SHALL wait for next SSE state update
- WHEN SSE state arrives after STALE_EPOCH, THE SYSTEM SHALL retry the original call once
- WHEN retry also fails, THE SYSTEM SHALL surface the error to user

## Non-Functional Requirements

- **Maintainability:** Each controller should be < 100 lines
- **Testability:** Controllers should have minimal cross-dependencies
- **Backward Compatibility:** No changes to RPC method signatures or SSE state shape (only additions)
- **Performance:** No additional network round-trips for normal operations

## Constraints

- Must follow existing controller pattern (`init()`, module-level state, callback injection)
- Must maintain existing localStorage keys for theme and tab persistence
- Daemon changes must not break existing REPL client

## Out of Scope

- UI/UX redesign of the extension
- New RPC methods
- Changes to CDP session management
- Auto-promote primary connection (explicit targets required in multi-target mode)

## Assumptions

- Extension always connects via SSE before making RPC calls
- Epoch increments only on successful page connection
- Existing controller pattern is correct and should be followed
- localStorage is available in extension context
