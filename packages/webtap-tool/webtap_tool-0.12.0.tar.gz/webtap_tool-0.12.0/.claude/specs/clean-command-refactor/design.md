# Clean Command Refactor Design

## Principle

**RPC handlers own all CDP interaction. Commands are pure presentation wrappers.**

## New RPC Methods to Add

### Navigation
```python
rpc.method("navigate", requires_state=["connected", "inspecting"])(navigate)
rpc.method("reload", requires_state=["connected", "inspecting"])(reload)
rpc.method("back", requires_state=["connected", "inspecting"])(back)
rpc.method("forward", requires_state=["connected", "inspecting"])(forward)
rpc.method("history", requires_state=["connected", "inspecting"])(history)
rpc.method("page", requires_state=["connected", "inspecting"])(page)
```

### JavaScript Execution
```python
rpc.method("js", requires_state=["connected", "inspecting"])(js)
```

The `js` handler will:
- Handle IIFE wrapping for fresh scope
- Handle selection integration (get jsPath from DOM service)
- Handle persist mode for global scope
- Call Runtime.evaluate via CDP

## Command Layer Changes

### Pattern: Thin Wrapper
```python
@app.command(display="markdown")
def js(state, code: str, selection: int = None, persist: bool = False, ...):
    """Execute JavaScript in browser."""
    try:
        result = state.client.call("js", code=code, selection=selection, persist=persist, ...)
        return format_js_result(result)
    except RPCError as e:
        return error_response(e.message)
```

### What Stays in Commands
1. **Display formatting** - Building markdown responses
2. **Expression evaluation** - `request(id, fields, expr=...)` - REPL/MCP feature
3. **Code generation** - `to_model()`, `quicktype()` - Uses external CLI tools
4. **Mode-aware behavior** - Truncation differences between REPL/MCP

### What Moves to RPC Handlers
1. **CDP calls** - All `state.client.call("cdp", ...)`
2. **Connection state checks** - Trust `requires_state`
3. **Business logic** - IIFE wrapping, selection resolution

## Files to Modify

### rpc/handlers.py - Add handlers
- `navigate(ctx, url)` - Page.navigate
- `reload(ctx, ignore_cache)` - Page.reload
- `back(ctx)` - Page.navigateToHistoryEntry
- `forward(ctx)` - Page.navigateToHistoryEntry
- `history(ctx)` - Page.getNavigationHistory
- `page(ctx)` - Returns current page with title from Runtime.evaluate
- `js(ctx, code, selection, persist, await_promise, return_value)` - Runtime.evaluate

### commands/navigation.py - Simplify
- Remove all `state.client.call("cdp", ...)` calls
- Just call RPC and format results

### commands/javascript.py - Simplify
- Remove IIFE wrapping logic
- Remove selection handling
- Just call `state.client.call("js", ...)` and format

### commands/request.py - Keep expr evaluation
- Expression eval is REPL/MCP feature, stays here
- RPC provides data, command transforms it

### commands/to_model.py, quicktype.py - Keep code generation
- These use external CLI tools
- Body fetch via RPC, generation locally

## Benefits

1. **Single source of truth** for CDP interaction
2. **Testable handlers** independent of presentation
3. **Commands become predictable** - just format and display
4. **No more duplicate connection checks**
5. **Extension can use same RPC methods directly**
