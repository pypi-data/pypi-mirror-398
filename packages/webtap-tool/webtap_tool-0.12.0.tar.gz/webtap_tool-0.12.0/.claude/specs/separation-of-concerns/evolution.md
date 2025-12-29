# Evolution: Separation of Concerns → State Architecture Refactor

## What Was Completed

The separation-of-concerns spec successfully:
- Extracted 4 extension controllers (theme, notices, header, tabs)
- Reduced main.js from 430 to 246 lines (43%)
- Added navigation handler state requirements
- Fixed filter handler broadcast flags
- Implemented per-target errors
- Added STALE_EPOCH retry logic
- Added client tracking headers

## What Remains Valid

These patterns from the original spec continue:
- Controller extraction pattern
- RPC `requires_state` decorator pattern
- SSE broadcast coalescing
- Immutable StateSnapshot pattern
- Client tracking headers

## Issues Identified for Evolution

During implementation, these framework-level issues were identified:

1. **ResizeObserver loop** - DataTable dynamic truncation triggers loop
2. **Pages connected state** - Extension overwrites server's `connected` field with local computation
3. **Startup race** - "Failed to fetch" when daemon not ready
4. **State inconsistency** - Global state machine blocks operations on all targets

## Evolution Approach

The new spec (`state-architecture-refactor`) takes a **big bang atomic** approach:
- All changes deployed together
- No intermediate broken states
- Breaking change: `state.page` removed
- New feature: per-target connection state

## Lessons Learned

1. **Trust server state** - Extension should be "dumb", just render what server provides
2. **Multi-target needs per-target state** - Global state machine insufficient
3. **Debounce browser APIs** - ResizeObserver needs RAF debouncing
4. **Retry with backoff** - Network operations need retry logic
