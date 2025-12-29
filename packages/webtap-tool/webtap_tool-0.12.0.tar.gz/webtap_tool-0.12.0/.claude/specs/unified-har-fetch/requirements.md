# Feature: Unified HAR/Fetch View

## Overview

Unify the HAR (HTTP Archive) view with Fetch interception events to provide a seamless experience where paused requests appear naturally in the network table with proper state indicators. Users interact with a single ID system (HAR IDs) and commands automatically handle the Fetch event correlation internally.

This is a **clean break refactor** - after implementation, the separate `requests()` paused-only view and separate paused ID system are eliminated.

## Specification Heritage

**Evolves from:** `rpc-framework` spec (RPC migration complete)
**Builds on:** Current HAR views in `cdp/har.py` and FetchService in `services/fetch.py`
**Replaces:** Separate paused request tracking with distinct IDs

## User Stories

### Story 1: See Paused Requests in Network Table
**As a** developer debugging HTTP traffic
**I want** to see paused requests in the network table with clear status
**So that** I can identify which requests are paused without using a separate command

**Acceptance Criteria (EARS notation):**
- WHEN a request is paused at Request stage, THE SYSTEM SHALL show `state: paused` and `pause: Request` in network()
- WHEN a request is paused at Response stage, THE SYSTEM SHALL show `state: paused` and `pause: Response` in network()
- WHEN a request is paused at Response stage, THE SYSTEM SHALL show the response status code from Fetch event
- WHEN a paused request is resumed, THE SYSTEM SHALL update state to reflect Network event state (pending/complete/failed)
- WHEN fetch interception is disabled, THE SYSTEM SHALL show `pause: -` for all requests

### Story 2: View Complete Request Details Including Fetch Data
**As a** developer inspecting a paused request
**I want** request() to show all available data including response headers from Fetch events
**So that** I can see response headers at Response stage without needing a separate inspect command

**Acceptance Criteria (EARS notation):**
- WHEN request(id) is called on a paused Response stage request, THE SYSTEM SHALL merge Fetch event response headers into the HAR response
- WHEN request(id) is called on a paused Request stage request, THE SYSTEM SHALL show available request data with state: paused
- WHEN request(id) is called on a completed request, THE SYSTEM SHALL show standard HAR data

### Story 3: Resume/Fail Using HAR IDs
**As a** developer controlling paused requests
**I want** to use HAR IDs with resume() and fail()
**So that** I don't need to track separate paused IDs

**Acceptance Criteria (EARS notation):**
- WHEN resume(har_id) is called, THE SYSTEM SHALL lookup the paused Fetch event by networkId and resume it
- WHEN fail(har_id) is called, THE SYSTEM SHALL lookup the paused Fetch event by networkId and fail it
- WHEN resume(har_id) is called on a non-paused request, THE SYSTEM SHALL return an error indicating request is not paused
- WHEN multiple Fetch events exist for same networkId (redirect chain), THE SYSTEM SHALL use the most recent unresolved event

### Story 4: Filter Network by Paused State
**As a** developer focusing on paused requests
**I want** to filter network() by state
**So that** I can see only paused requests when needed

**Acceptance Criteria (EARS notation):**
- WHEN network(state="paused") is called, THE SYSTEM SHALL show only paused requests
- WHEN requests() is called, THE SYSTEM SHALL return network(state="paused") with fetch-specific tips
- WHEN no requests are paused, THE SYSTEM SHALL show empty table with appropriate message

## Non-Functional Requirements

- **Performance:** HAR view query should complete in <100ms for 1000 events
- **Consistency:** State transitions must be atomic - no stale paused indicators after resume
- **Backwards Compatibility:** None required - this is a clean break refactor

## Constraints

- DuckDB is the storage engine - all queries must be valid DuckDB SQL
- HAR views are recreated on connection - changes take effect on reconnect
- Fetch events use `networkId` to correlate with Network events (may be NULL)

## Out of Scope

- Response body interception/modification (Fetch can modify but we don't expose body in inspect)
- WebSocket frame-level interception
- Multiple simultaneous Chrome connections
- Persistent paused state across daemon restarts

## Assumptions

1. A paused Fetch event always has a corresponding `Network.requestWillBeSent` event with matching networkId
2. `networkId` in Fetch events is unique per request (not reused)
3. Only one Fetch.requestPaused event per networkId is unresolved at a time (except redirect chains)
4. Users prefer a single unified ID system over understanding HAR vs Fetch IDs
