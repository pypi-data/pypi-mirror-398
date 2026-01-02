# v2.0.0 Test Fixes - Comprehensive Summary

## Overview
All deprecated functions have been removed from the public API for v2.0.0. Tests need updating to work with unified interfaces.

## Progress Report

### ✅ test_unified_hierarchy.py (PARTIALLY COMPLETE)

**Completed:**
- ✅ Removed all 11 deprecation warning tests (lines 746-994)
- ✅ Updated file docstring for v2.0.0
- ✅ Removed `warnings` import
- ✅ Cleaned up imports (removed deprecated function imports)
- ✅ Reduced file from ~994 lines to 756 lines

**Test Status:**
- **Passing**: 7/29 tests (24%)
- **Failing**: 22/29 tests (76%)

**Remaining Work:**

1. **Fix AsyncMock Issues** (affects ~15 tests):
   - Problem: When `adapter = AsyncMock()`, ALL attributes become AsyncMock
   - Solution: Use `adapter = MagicMock()` for base, then `adapter.method = AsyncMock(...)` for async methods
   - For `adapter.read` operations, must `del adapter.get_epic` to force fallback to `.read()`

   Example fix:
   ```python
   # OLD (doesn't work):
   adapter = AsyncMock()
   adapter.adapter_type = "test"
   adapter.read.return_value = Epic(...)

   # NEW (works):
   adapter = MagicMock()
   adapter.adapter_type = "test"
   adapter.read = AsyncMock(return_value=Epic(...))
   del adapter.get_epic  # Force fallback to read()
   ```

2. **Add get_adapter Mocking** (affects ~10 tests):
   - Problem: Tests for validation errors don't mock `get_adapter()`
   - Issue: `hierarchy()` calls `get_adapter()` on line 243, BEFORE validation
   - Solution: All tests must mock `get_adapter()`, even validation tests

   Tests needing this fix:
   - test_hierarchy_epic_invalid_action
   - test_hierarchy_epic_missing_entity_id
   - test_hierarchy_issue_invalid_action
   - test_hierarchy_issue_missing_entity_id
   - test_hierarchy_task_invalid_action
   - test_hierarchy_task_only_supports_create
   - test_hierarchy_invalid_entity_type
   - test_hierarchy_missing_required_parameters
   - test_hierarchy_adapter_not_available

   Example fix:
   ```python
   # OLD:
   async def test_hierarchy_invalid_entity_type():
       result = await hierarchy(entity_type="invalid", action="create", title="Test")
       assert result["status"] == "error"

   # NEW:
   async def test_hierarchy_invalid_entity_type():
       with patch('mcp_ticketer.mcp.server.tools.hierarchy_tools.get_adapter') as mock_get_adapter:
           adapter = MagicMock()
           adapter.adapter_type = "test"
           adapter.adapter_display_name = "Test Adapter"
           mock_get_adapter.return_value = adapter

           result = await hierarchy(entity_type="invalid", action="create", title="Test")
           assert result["status"] == "error"
   ```

### ❌ test_unified_ticket.py (NOT STARTED)

**Required Changes:**
1. Remove 8 deprecation warning tests:
   - test_ticket_create_deprecation_warning
   - test_ticket_read_deprecation_warning
   - test_ticket_update_deprecation_warning
   - test_ticket_delete_deprecation_warning
   - test_ticket_list_deprecation_warning
   - test_ticket_summary_deprecation_warning
   - test_ticket_latest_deprecation_warning
   - test_ticket_assign_deprecation_warning

2. Update remaining tests to use `ticket(action=...)` interface
3. Apply same AsyncMock fixes as hierarchy tests
4. Mock `get_adapter()` for all tests

**Current Status:**
- Tests try to patch `ticket_create`, `ticket_read`, etc. which no longer have @mcp.tool() decorators
- All deprecation warning tests are invalid (functions removed, not deprecated)

### ❌ test_unified_ticket_bulk.py (NOT STARTED)

**Required Changes:**
1. Remove deprecation tests for `ticket_bulk_create`, `ticket_bulk_update` (if any)
2. Verify all tests use `ticket_bulk(action=...)` interface
3. Apply AsyncMock fixes if needed

**Likely Status:** Mostly correct already, just needs verification

### ❌ test_unified_user_session.py (NOT STARTED)

**Required Changes:**
1. Remove deprecation tests for `get_my_tickets`, `get_session_info` (if any)
2. Verify all tests use `user_session(action=...)` interface
3. Apply AsyncMock fixes if needed

**Likely Status:** Mostly correct already, just needs verification

## Key Patterns to Fix

### Pattern 1: AsyncMock → MagicMock for Adapters

```python
# BEFORE:
adapter = AsyncMock()
adapter.adapter_type = "test"
adapter.adapter_display_name = "Test Adapter"
adapter.read.return_value = Epic(id="EPIC-1", title="Test")

# AFTER:
adapter = MagicMock()
adapter.adapter_type = "test"
adapter.adapter_display_name = "Test Adapter"
adapter.read = AsyncMock(return_value=Epic(id="EPIC-1", title="Test"))
del adapter.get_epic  # For read operations only
```

### Pattern 2: Always Mock get_adapter

```python
# BEFORE:
async def test_something():
    result = await hierarchy(...)
    assert result["status"] == "error"

# AFTER:
async def test_something():
    with patch('mcp_ticketer.mcp.server.tools.hierarchy_tools.get_adapter') as mock_get_adapter:
        adapter = MagicMock()
        adapter.adapter_type = "test"
        adapter.adapter_display_name = "Test Adapter"
        mock_get_adapter.return_value = adapter

        result = await hierarchy(...)
        assert result["status"] == "error"
```

### Pattern 3: Remove Deprecation Tests

```python
# DELETE THESE ENTIRELY:
@pytest.mark.asyncio
async def test_epic_create_deprecation_warning():
    """Test epic_create emits deprecation warning."""
    with warnings.catch_warnings(record=True) as w:
        ...
```

## Automated Fix Script

A partial fix script has been created at `fix_hierarchy_tests.py` that:
- ✅ Removes deprecation tests
- ✅ Updates docstrings
- ✅ Cleans imports
- ⚠️ Partially fixes AsyncMock patterns (needs manual review)

## Estimated Test Count Changes

**Before** (with deprecation tests):
- test_unified_hierarchy.py: 40 tests
- test_unified_ticket.py: 30 tests
- test_unified_ticket_bulk.py: 22 tests
- test_unified_user_session.py: 14 tests
- **Total**: 106 tests

**After** (v2.0.0 without deprecation tests):
- test_unified_hierarchy.py: 29 tests (removed 11)
- test_unified_ticket.py: ~22 tests (remove 8)
- test_unified_ticket_bulk.py: ~20 tests (remove 2)
- test_unified_user_session.py: ~12 tests (remove 2)
- **Target Total**: ~83 tests

## Next Steps

1. **Complete test_unified_hierarchy.py**:
   - Apply AsyncMock → MagicMock pattern to all 22 failing tests
   - Add get_adapter mocking to validation tests
   - Run tests until all 29 pass

2. **Fix test_unified_ticket.py**:
   - Remove 8 deprecation tests
   - Update mocking patterns
   - Apply same fixes as hierarchy tests

3. **Verify test_unified_ticket_bulk.py**:
   - Check for any remaining deprecated references
   - Run tests

4. **Verify test_unified_user_session.py**:
   - Check for any remaining deprecated references
   - Run tests

5. **Final Verification**:
   ```bash
   pytest tests/mcp/test_unified*.py -v --tb=short
   ```

## Files Modified

- `/Users/masa/Projects/mcp-ticketer/tests/mcp/test_unified_hierarchy.py` (in progress)
- `/Users/masa/Projects/mcp-ticketer/fix_hierarchy_tests.py` (helper script created)
- `/Users/masa/Projects/mcp-ticketer/TEST_FIX_SUMMARY.md` (this file)

## Critical Insights

1. **AsyncMock Has All Attributes**: When you create `AsyncMock()`, accessing ANY attribute returns another AsyncMock. This causes `hasattr(adapter, "get_epic")` to return True even when you haven't defined it.

2. **get_adapter Called Early**: The `hierarchy()` function calls `get_adapter()` on line 243, BEFORE any validation. This means ALL tests must mock it, even tests checking validation errors.

3. **model_dump() Returns Coroutine**: When an Epic returned from `adapter.read.return_value` (on AsyncMock) has its `.model_dump()` called, it becomes a coroutine because attribute access on AsyncMock return values creates new AsyncMock objects.

## Solution: MagicMock + Selective AsyncMock

The solution is to use `MagicMock()` for the base adapter, then selectively make specific methods async:

```python
adapter = MagicMock()  # Base is NOT async
adapter.read = AsyncMock(return_value=real_epic_object)  # Method IS async
del adapter.get_epic  # Remove auto-created attribute
```

This prevents the cascade of AsyncMock objects while still allowing async method mocking.
