# Feature: Layer Architecture Cleanup

## Overview

WebTap's architecture consists of four layers: Commands → RPC Handlers → Services → CDP/DuckDB. During the multi-target refactor, several RPC handlers began directly accessing daemon state and CDP sessions, bypassing the service layer. This creates race conditions, missing state broadcasts, and bugs (e.g., `ports()` showing 0 pages).

This cleanup enforces proper layer separation by moving all state management into the service layer.

## Problem Statement

### Current Violations

| Issue | Location | Impact |
|-------|----------|--------|
| Direct state mutation | `handlers.py:497,785,826` | Race conditions, no locking, missing broadcasts |
| Direct CDP queries | `handlers.py:299,489,593` | Schema coupling, bypasses service filtering |
| Port sessions unmanaged | `handlers.py:785-868` | Calls non-existent method `get_pages()`, broken `ports()` |
| Error state unprotected | `handlers.py:497` | No locking for `error_state` mutations |
| Broadcast inconsistency | various | Double broadcasts or missing broadcasts |

### Root Cause Example

`ports_list` handler directly accesses `ctx.service.state.cdp_sessions` and calls `session.get_pages()` which doesn't exist. Should use `ctx.service.list_ports()`.

## User Stories

### Story 1: Port Management Through Service Layer
**As a** WebTap developer
**I want** port registration/unregistration to go through the service layer
**So that** state changes are properly locked and broadcast to SSE clients

**Acceptance Criteria (EARS notation):**
- WHEN `ports.add` RPC is called, THE SYSTEM SHALL delegate to `WebTapService.register_port()`
- WHEN `ports.remove` RPC is called, THE SYSTEM SHALL delegate to `WebTapService.unregister_port()`
- WHEN `ports.list` RPC is called, THE SYSTEM SHALL delegate to `WebTapService.list_ports()`
- WHEN a port is registered, THE SYSTEM SHALL validate port range (1024-65535)
- WHEN a port is registered, THE SYSTEM SHALL check if Chrome is listening
- WHEN a port is unregistered, THE SYSTEM SHALL disconnect all connections on that port
- WHEN port 9222 unregister is attempted, THE SYSTEM SHALL reject with error (protected port)

### Story 2: Error State Through Service Layer
**As a** WebTap developer
**I want** error state mutations to go through the service layer with locking
**So that** race conditions are prevented and broadcasts are consistent

**Acceptance Criteria (EARS notation):**
- WHEN `errors.dismiss` RPC is called, THE SYSTEM SHALL delegate to `WebTapService.clear_error()`
- WHEN error state is set, THE SYSTEM SHALL acquire `_state_lock` before mutation
- WHEN error state is cleared, THE SYSTEM SHALL acquire `_state_lock` before mutation
- WHEN error state changes, THE SYSTEM SHALL trigger broadcast to SSE clients
- WHEN unexpected disconnect occurs, THE SYSTEM SHALL use `set_error()` instead of direct assignment

### Story 3: Consistent Broadcast Pattern
**As a** WebTap developer
**I want** a single consistent pattern for state broadcasts
**So that** there are no double-broadcasts or missing broadcasts

**Acceptance Criteria (EARS notation):**
- WHEN service methods mutate state, THE SYSTEM SHALL call `_trigger_broadcast()`
- WHEN handlers delegate to service, THE SYSTEM SHALL set `broadcasts=False` in registration
- WHEN `_trigger_broadcast()` is called, THE SYSTEM SHALL coalesce multiple calls within 50ms

### Story 4: Thread-Safe Disconnect
**As a** WebTap developer
**I want** disconnect operations to be properly synchronized
**So that** there are no race conditions when reading connection state

**Acceptance Criteria (EARS notation):**
- WHEN `disconnect_target()` is called, THE SYSTEM SHALL disconnect CDP outside lock (I/O)
- WHEN `disconnect_target()` is called, THE SYSTEM SHALL update `self.connections` inside lock
- WHEN `disconnect_target()` is called, THE SYSTEM SHALL update `self.cdp` inside lock
- WHEN primary CDP is disconnected, THE SYSTEM SHALL reset dependent services inside lock

## Non-Functional Requirements

### Thread Safety
- All state mutations MUST acquire `_state_lock` before modification
- CDP disconnect (network I/O) MUST happen outside lock to prevent deadlock
- State snapshot reads MUST NOT require locks (immutable snapshot pattern)

### Performance
- Broadcast coalescing: multiple state changes within 50ms = single broadcast
- Port listing MUST reuse existing `list_pages()` and aggregate (no duplicate HTTP calls)

### Maintainability
- Handlers MUST be thin delegators (single-line service calls where possible)
- Service layer MUST own all state mutation logic
- No direct access to `ctx.service.state.*` in handlers

## Constraints

- Python 3.12+ required
- Must maintain backward compatibility with existing RPC clients
- Must not break SSE broadcast protocol
- Port 9222 is always protected (default desktop port)

## Out of Scope

- Refactoring other handlers that directly query CDP (e.g., `history()`, `page()`) - future work
- Adding new port management features (auto-discovery, health checks) - future work
- Changing the RPC protocol or response formats

## Assumptions

- `_state_lock` is a `threading.Lock` that is already used elsewhere in the service
- `_trigger_broadcast()` already handles coalescing and SSE notification
- `CDPSession.cleanup()` is idempotent and safe to call multiple times
- Existing `list_pages()` method returns `chrome_port` in each page dict
