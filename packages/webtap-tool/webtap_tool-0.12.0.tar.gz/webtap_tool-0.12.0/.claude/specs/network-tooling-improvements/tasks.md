# Implementation Tasks: Network Tooling Improvements

**Status:** Ready to implement
**Spec:** [requirements.md](./requirements.md) | [design.md](./design.md)

## Task Breakdown

### Task 1: Create HAR views in DuckDB
**Completed:** 2025-12-16

**Acceptance:**
- [x] `har_entries` view created with HTTP + WebSocket aggregation
- [x] `har_summary` view created for list display
- [x] Views query correctly via `session.query()`
- [x] Incomplete requests show with NULL fields

**Notes:**
- Created separate `cdp/har.py` module for cleaner separation (CDPSession stays focused on CDP storage)
- SQL views use proper type casting for DuckDB compatibility
- Views are created on CDPSession init via `create_har_views()`

**Dependencies:** None
**Complexity:** Medium

---

### Task 2: Rewrite FilterManager
**Completed:** 2025-12-16

**Acceptance:**
- [x] Groups stored in `.webtap/filters.json` (definitions only)
- [x] Enabled state in memory only
- [x] `get_active_filters()` returns deduplicated hide config
- [x] Old filter format ignored (no migration)

**Notes:**
- Added `build_filter_sql()` method for SQL generation (used by network command)
- Accepts both Path and str for filter_path

**Dependencies:** None
**Complexity:** Medium

---

### Task 3: Update network service to use HAR view
**Completed:** 2025-12-16

**Acceptance:**
- [x] `get_requests()` uses har_summary view (renamed from get_recent_requests)
- [x] Filter SQL applied correctly via FilterManager.build_filter_sql()
- [x] WebSocket entries included in results
- [x] Added `get_request_details()` for HAR entry lookup
- [x] Wired filters to network service in main.py

**Notes:**
- Also updated main.py to use new filter API (groups/enabled instead of filters/enabled_categories)

**Dependencies:** Task 1, Task 2
**Complexity:** Low

---

### Task 4: Add inline filters to network() command
**Completed:** 2025-12-16

**Acceptance:**
- [x] `network(status=404)` filters by status
- [x] `network(method="POST")` filters by method
- [x] `network(type="xhr")` filters by type
- [x] `network(url="*api*")` filters by URL pattern
- [x] `network(all=True)` bypasses filter groups
- [x] Added "State" column to output

**Dependencies:** Task 3
**Complexity:** Low

---

### Task 5: Create request() command
**Completed:** 2025-12-16

**Acceptance:**
- [x] `request(123)` returns minimal default fields
- [x] `request(123, ["*"])` returns all fields
- [x] `request(123, ["request.headers.*"])` returns all request headers
- [x] `request(123, ["body"])` fetches and includes body
- [x] Case-insensitive header lookup
- [x] Error for non-existent ID
- [x] Added to app.py imports

**Dependencies:** Task 1
**Complexity:** Medium

---

### Task 6: Rewrite filters() command
**Completed:** 2025-12-16

**Acceptance:**
- [x] `filters()` shows all groups with status
- [x] `filters(add="x", hide={...})` creates group
- [x] `filters(enable="x")` enables group
- [x] `filters(disable="x")` disables group
- [x] `filters(remove="x")` deletes group

**Notes:**
- Removed complex action/config pattern, now uses named parameters
- Calls client methods (to be implemented in Task 9)

**Dependencies:** Task 2
**Complexity:** Low

---

### Task 7: Update API endpoints
**Completed:** 2025-12-16

**Acceptance:**
- [x] `GET /network?status=404` works
- [x] `GET /request/{row_id}` returns HAR-nested structure
- [x] `GET /body/by-request-id/{request_id}` new endpoint
- [x] Filter group endpoints updated (add, remove, enable, disable)

**Dependencies:** Task 4, Task 5
**Complexity:** Medium

---

### Task 8: Update extension filter UI
**Description:** Add filter group toggles to extension sidepanel

**Files:**
- `packages/webtap/extension/sidepanel.js` - Add filter group toggles

**Changes:**
- Display filter groups from state
- Toggle buttons call `POST /filters/toggle/{name}`
- Update UI on SSE state changes

**Acceptance:**
- [ ] Filter groups displayed with enabled/disabled status
- [ ] Toggle updates daemon state
- [ ] UI reflects state changes

**Dependencies:** Task 2, Task 7
**Complexity:** Medium

---

### Task 9: Update client wrapper
**Completed:** 2025-12-16

**Acceptance:**
- [x] `client.network()` updated with inline filter params
- [x] `client.request_details(123)` returns HAR entry
- [x] `client.fetch_body(request_id)` fetches body
- [x] `client.filters_*()` methods for group management

**Notes:**
- Kept events() for backwards compat (can remove in Task 10)

**Dependencies:** Task 7
**Complexity:** Low

---

### Task 10: Delete obsolete files
**Completed:** 2025-12-16

**Deleted:**
- `commands/events.py` - replaced by HAR views
- `cdp/query.py` - dynamic query builder no longer needed
- `api/routes/events.py` - events API endpoints

**Updated:**
- `app.py` - removed events import
- `cdp/__init__.py` - removed build_query export
- `api/routes/__init__.py` - removed events router
- `client.py` - removed events() and query() methods

**Acceptance:**
- [x] `events()` command removed
- [x] No broken imports
- [x] Type check passes

**Dependencies:** Task 5, Task 9
**Complexity:** Low

---

### Task 11: Integration testing
**Description:** Verify full flow works end-to-end

**Test scenarios:**
1. Start daemon, connect to page
2. `network()` shows requests from har_summary
3. `network(status=404)` filters correctly
4. `request(123)` returns HAR structure
5. `request(123, ["body"])` fetches body
6. `filters(add="x", hide={...})` creates group
7. `filters(enable="x")` hides matching requests
8. Extension can toggle filter groups
9. WebSocket connections appear in network()

**Acceptance:**
- [ ] All scenarios pass
- [ ] No regressions in existing functionality

**Dependencies:** All previous tasks
**Complexity:** Medium

---

## Task Dependencies

```
Task 1 (HAR views)     Task 2 (FilterManager)
       │                      │
       ▼                      ▼
Task 3 (network service) ◄────┘
       │
       ▼
Task 4 (network cmd)    Task 5 (request cmd)    Task 6 (filters cmd)
       │                      │                       │
       └──────────┬───────────┘                       │
                  ▼                                   │
           Task 7 (API endpoints) ◄───────────────────┘
                  │
       ┌──────────┼──────────┐
       ▼          ▼          ▼
Task 8 (ext)  Task 9 (client)  Task 10 (delete)
       │          │              │
       └──────────┴──────────────┘
                  │
                  ▼
           Task 11 (testing)
```

## Parallel Tracks

**Track A (Data Layer):** Tasks 1 → 3 → 4 → 7
**Track B (Filters):** Tasks 2 → 6 → 7
**Track C (Request):** Tasks 1 → 5 → 7

Tasks 1 and 2 can run in parallel.
Tasks 4, 5, 6 can run in parallel after their dependencies.
Tasks 8, 9, 10 can run in parallel after Task 7.

## Execution Strategy

1. **Foundation (parallel):** Task 1 + Task 2
2. **Service layer:** Task 3
3. **Commands (parallel):** Task 4 + Task 5 + Task 6
4. **API:** Task 7
5. **Integration (parallel):** Task 8 + Task 9 + Task 10
6. **Verification:** Task 11
