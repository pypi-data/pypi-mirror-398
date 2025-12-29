# Implementation Tasks: WebTap Client-Daemon Sync

**Status:** EVOLVED - See: [daemon-client-architecture](../daemon-client-architecture/)
**Spec:** [requirements.md](./requirements.md) | [design.md](./design.md)

## Task Breakdown

### Task 1: Wire broadcast queue in daemon mode
**Description:** Fix the root cause - `_broadcast_queue` is never wired in `run_daemon_server()`

**Files:**
- `packages/webtap/src/webtap/api.py` - Add queue wiring after `broadcast_processor()` starts (around line 1193)

**Changes:**
```python
# After: broadcast_task = asyncio.create_task(broadcast_processor())
await asyncio.sleep(0.1)  # Let broadcast_processor create queue
if _broadcast_queue and app_state:
    app_state.service.set_broadcast_queue(_broadcast_queue)
    logger.debug("Broadcast queue wired to WebTapService")
```

**Acceptance:**
- [ ] Daemon mode wires broadcast queue on startup
- [ ] SSE broadcasts work in daemon mode
- [ ] `_trigger_broadcast()` no longer exits early

**Dependencies:** None
**Complexity:** Low

---

### Task 2: Update /connect endpoint to return state
**Description:** Add full state to connect response

**Files:**
- `packages/webtap/src/webtap/api.py` - Modify `/connect` endpoint (lines 586-595)

**Changes:**
```python
@api.post("/connect")
async def connect(request: ConnectRequest) -> Dict[str, Any]:
    if not app_state:
        return {"error": "WebTap not initialized", "state": get_full_state()}

    result = await asyncio.to_thread(app_state.service.connect_to_page, page_id=request.page_id)
    return {**result, "state": get_full_state()}
```

**Acceptance:**
- [ ] Response includes `state` field with full WebTapState
- [ ] Error responses also include state

**Dependencies:** Task 1
**Complexity:** Low

---

### Task 3: Update /disconnect endpoint to return state
**Description:** Add full state to disconnect response

**Files:**
- `packages/webtap/src/webtap/api.py` - Modify `/disconnect` endpoint (lines 598-607)

**Acceptance:**
- [ ] Response includes `state` field with full WebTapState

**Dependencies:** Task 1
**Complexity:** Low

---

### Task 4: Update /fetch endpoint to return state
**Description:** Add full state to fetch toggle response

**Files:**
- `packages/webtap/src/webtap/api.py` - Modify `/fetch` endpoint (lines 658-676)

**Acceptance:**
- [ ] Response includes `state` field with full WebTapState

**Dependencies:** Task 1
**Complexity:** Low

---

### Task 5: Update /clear endpoint to return state
**Description:** Add full state to clear response

**Files:**
- `packages/webtap/src/webtap/api.py` - Modify `/clear` endpoint (lines 618-656)

**Acceptance:**
- [ ] Response includes `state` field with full WebTapState

**Dependencies:** Task 1
**Complexity:** Low

---

### Task 6: Add updateFromState() to extension
**Description:** Create helper function to update all UI from a state object

**Files:**
- `packages/webtap/extension/sidepanel.js` - Add new function

**Changes:**
```javascript
/**
 * Update all UI from a full state object.
 * Used for immediate updates from action responses.
 */
function updateFromState(newState) {
  state = newState;
  updateConnectionStatus(newState);
  updateEventCount(newState.events.total);
  updateButtons(newState.connected);
  updateErrorBanner(newState.error);
  updateFetchStatus(newState.fetch.enabled, newState.fetch.paused_count);
  updateFiltersUI(newState.filters);
  updateSelectionUI(newState.browser);

  // Update hashes so SSE doesn't re-render
  previousHashes = {
    selections: newState.selections_hash,
    filters: newState.filters_hash,
    fetch: newState.fetch_hash,
    page: newState.page_hash,
    error: newState.error_hash,
  };
}
```

**Acceptance:**
- [ ] Function updates all UI sections
- [ ] Function updates hash cache to prevent SSE double-render

**Dependencies:** None
**Complexity:** Low

---

### Task 7: Update extension action handlers
**Description:** Modify connect/disconnect/fetch/clear handlers to use response state

**Files:**
- `packages/webtap/extension/sidepanel.js` - Update action handlers (lines 484-581)

**Changes for each action:**
```javascript
// Example: connect handler
const result = await api("/connect", "POST", { page_id: selectedPageId });
if (result.error) {
  showError(result.error);
}
if (result.state) {
  updateFromState(result.state);
}
```

**Actions to update:**
- Connect button handler (line ~486)
- Disconnect button handler (line ~496)
- Clear button handler (line ~506)
- Fetch toggle handler (line ~534)

**Acceptance:**
- [ ] All action handlers check for `result.state`
- [ ] UI updates immediately on action completion
- [ ] Error handling preserved

**Dependencies:** Task 6, Tasks 2-5
**Complexity:** Medium

---

### Task 8: Test full sync flow
**Description:** Verify the complete extension ↔ daemon sync works

**Test scenarios:**
1. Start daemon, open extension → shows "Not connected"
2. Click Connect → UI immediately shows "Connected"
3. Click Disconnect → UI immediately shows "Not connected"
4. Toggle Fetch → UI immediately reflects new state
5. Click Clear → Event count resets immediately
6. Background CDP events → SSE updates event count

**Acceptance:**
- [ ] All test scenarios pass
- [ ] No "click but nothing happens" issues
- [ ] SSE still works for background updates

**Dependencies:** Tasks 1-7
**Complexity:** Low (manual testing)

---

## Task Dependencies

```
Task 1 (wire queue)
    ↓
Tasks 2-5 (API endpoints) ←── can run in parallel
    ↓
Task 6 (updateFromState) ←── can run in parallel with 2-5
    ↓
Task 7 (extension handlers)
    ↓
Task 8 (testing)
```

## Parallel Tracks

**Track A (Backend):** Tasks 1 → 2, 3, 4, 5 (parallel)
**Track B (Frontend):** Task 6
**Merge:** Task 7 (needs both tracks)
**Final:** Task 8
