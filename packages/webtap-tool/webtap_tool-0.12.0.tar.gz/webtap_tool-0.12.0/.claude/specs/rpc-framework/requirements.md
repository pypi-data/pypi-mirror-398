# Feature: WebTap RPC Framework

## Overview

Replace the current ad-hoc HTTP REST API with a unified JSON-RPC 2.0 framework backed by a `transitions` state machine. This is a **clean-break, big-bang refactor** on a new branch with **no backward compatibility constraints**.

### Goals
- Eliminate race conditions through state machine validation
- Reduce boilerplate in both Python handlers and JavaScript client code
- Provide a single mental model for extension↔daemon communication
- Enable automatic epoch tracking for stale request detection

### Non-Goals
- Maintaining backward compatibility with existing REST endpoints
- Supporting multiple concurrent browser connections (future work)
- Changing the underlying CDP session or threading model

## User Stories

### Story 1: Extension Developer Experience
**As a** WebTap extension developer
**I want** a simple client API with automatic state/epoch handling
**So that** I can focus on UI logic instead of error handling boilerplate

**Acceptance Criteria (EARS notation):**
- WHEN I call `client.call("method", params)`, THE SYSTEM SHALL automatically include the current epoch in the request
- WHEN a request completes successfully, THE SYSTEM SHALL return the result directly (no unwrapping needed)
- WHEN a request fails with an error, THE SYSTEM SHALL throw an Error with `.code`, `.message`, and `.data` properties
- WHEN the connection epoch changes during a request, THE SYSTEM SHALL update `client.state.epoch` from the response
- WHEN `client.debug = true`, THE SYSTEM SHALL log all RPC traffic with correlation IDs

### Story 2: Connection State Machine
**As a** WebTap daemon
**I want** explicit connection state tracking via a state machine
**So that** invalid operations are rejected before execution

**Acceptance Criteria (EARS notation):**
- WHEN in `disconnected` state, THE SYSTEM SHALL only allow `connect` method calls
- WHEN in `connecting` state, THE SYSTEM SHALL reject all method calls with INVALID_STATE error
- WHEN in `connected` state, THE SYSTEM SHALL allow all methods except `connect`
- WHEN in `inspecting` state, THE SYSTEM SHALL allow `browser.stopInspect`, `disconnect`, and query methods
- WHEN transitioning to `connected`, THE SYSTEM SHALL increment the epoch counter
- WHEN an RPC request has mismatched epoch, THE SYSTEM SHALL reject with STALE_EPOCH error
- WHEN a transition fails, THE SYSTEM SHALL remain in the original state (no partial transitions)

### Story 3: RPC Handler Definition
**As a** WebTap backend developer
**I want** declarative RPC method registration
**So that** I can define handlers with minimal boilerplate

**Acceptance Criteria (EARS notation):**
- WHEN I decorate a function with `@rpc.method("name", requires_state=[...])`, THE SYSTEM SHALL register it as an RPC handler
- WHEN an RPC request arrives, THE SYSTEM SHALL validate state requirements before invoking the handler
- WHEN a handler raises `RPCError`, THE SYSTEM SHALL return a structured error response
- WHEN a handler raises any other exception, THE SYSTEM SHALL return INTERNAL_ERROR with the exception message
- WHEN a handler returns a value, THE SYSTEM SHALL wrap it in a JSON-RPC 2.0 success response

### Story 4: SSE State Synchronization
**As a** WebTap extension
**I want** to receive state updates via SSE including connection state and epoch
**So that** my UI stays synchronized and can validate local state

**Acceptance Criteria (EARS notation):**
- WHEN the connection state changes, THE SYSTEM SHALL broadcast the new state via SSE
- WHEN the epoch changes, THE SYSTEM SHALL include the new epoch in SSE broadcasts
- WHEN connecting to SSE stream, THE SYSTEM SHALL immediately receive current full state
- WHEN SSE connection is lost, THE CLIENT SHALL emit an `error` event

### Story 5: Thread Safety
**As a** WebTap daemon handling concurrent requests
**I want** thread-safe state transitions
**So that** race conditions don't corrupt connection state

**Acceptance Criteria (EARS notation):**
- WHEN multiple threads attempt concurrent state transitions, THE SYSTEM SHALL serialize them via LockedMachine
- WHEN a state transition is queued while another is in progress, THE SYSTEM SHALL process them sequentially
- WHEN reading the current state, THE SYSTEM SHALL return a consistent snapshot

## Non-Functional Requirements

### Performance
- RPC handler overhead: < 1ms added latency vs direct function call
- State machine transition: < 0.1ms
- SSE broadcast coalescing: unchanged from current behavior

### Reliability
- All state transitions must be atomic (no partial state)
- LockedMachine must prevent all race conditions in state changes
- Epoch validation must catch 100% of stale requests

### Maintainability
- RPC module: ~150 lines of Python
- JS client: ~100 lines of JavaScript
- Each RPC handler: ~3-5 lines (vs current ~15-20 lines per route)

## Constraints

### Technical Constraints
- Must use `transitions` library with `LockedMachine` for thread safety
- Must maintain current sync-with-asyncio.to_thread() execution model
- Must preserve existing SSE broadcast mechanism (coalescing, queue-based)
- Must work with existing CDPSession threading (WebSocket thread, DB worker)

### Clean Break Constraints
- All existing REST routes will be **deleted** (not deprecated)
- Extension must be fully migrated to RPC client
- No hybrid mode supporting both REST and RPC

## Out of Scope

- Multi-tab browser connections (separate feature)
- WebSocket transport (current HTTP+SSE is sufficient)
- Request batching (JSON-RPC 2.0 batch format)
- Bidirectional RPC (server-to-client calls)
- Authentication/authorization (local daemon only)
- Rate limiting (single client expected)

## Assumptions

1. **Single client**: Only one Chrome extension connects at a time
2. **Localhost only**: Daemon runs on localhost, no network security needed
3. **Trusted input**: Extension sends well-formed requests (no adversarial input)
4. **Sync service layer**: All WebTapService methods remain synchronous, wrapped with asyncio.to_thread()
5. **State machine covers connection lifecycle only**: Fetch interception, filter state, etc. are not state machine states

## State Machine Definition

```
States: disconnected, connecting, connected, inspecting, disconnecting

Transitions:
  disconnected -> connecting    [start_connect]
  connecting   -> connected     [connect_success] (epoch++)
  connecting   -> disconnected  [connect_failed]
  connected    -> inspecting    [start_inspect]
  inspecting   -> connected     [stop_inspect]
  connected    -> disconnecting [start_disconnect]
  inspecting   -> disconnecting [start_disconnect]
  disconnecting-> disconnected  [disconnect_complete]
  *            -> disconnected  [force_disconnect] (emergency reset)
```

## RPC Methods to Implement

| Method | Required State | Triggers Transition | Description |
|--------|----------------|---------------------|-------------|
| `connect` | disconnected | disconnected→connecting→connected | Connect to Chrome page |
| `disconnect` | connected, inspecting | →disconnecting→disconnected | Disconnect from page |
| `pages` | * | - | List available Chrome pages |
| `status` | * | - | Get current daemon status |
| `clear` | connected, inspecting | - | Clear events/console |
| `browser.startInspect` | connected | connected→inspecting | Enable element selection |
| `browser.stopInspect` | inspecting | inspecting→connected | Disable element selection |
| `browser.clear` | connected, inspecting | - | Clear selections |
| `fetch.enable` | connected, inspecting | - | Enable request interception |
| `fetch.disable` | connected, inspecting | - | Disable request interception |
| `fetch.resume` | connected, inspecting | - | Resume paused request |
| `fetch.fail` | connected, inspecting | - | Fail paused request |
| `fetch.fulfill` | connected, inspecting | - | Fulfill with custom response |
| `network` | connected, inspecting | - | Query network requests |
| `request` | connected, inspecting | - | Get request details |
| `console` | connected, inspecting | - | Get console messages |
| `filters.status` | * | - | Get filter groups |
| `filters.enable` | connected, inspecting | - | Enable filter group |
| `filters.disable` | connected, inspecting | - | Disable filter group |
| `filters.enableAll` | connected, inspecting | - | Enable all filters |
| `filters.disableAll` | connected, inspecting | - | Disable all filters |
| `cdp` | connected, inspecting | - | Execute raw CDP command |
| `errors.dismiss` | * | - | Dismiss error banner |

## Error Codes

| Code | HTTP Equivalent | Description |
|------|-----------------|-------------|
| `METHOD_NOT_FOUND` | 404 | Unknown RPC method |
| `INVALID_STATE` | 409 | Method not allowed in current state |
| `STALE_EPOCH` | 409 | Request epoch doesn't match current |
| `INVALID_PARAMS` | 400 | Missing or invalid parameters |
| `INTERNAL_ERROR` | 500 | Unexpected server error |
| `NOT_CONNECTED` | 503 | CDP session not connected |
