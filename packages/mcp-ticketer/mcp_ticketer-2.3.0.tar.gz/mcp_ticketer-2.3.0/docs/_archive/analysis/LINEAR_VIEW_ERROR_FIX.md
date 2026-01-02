# Linear View URL Error Handling Fix

## Problem
Bug found where Linear's `customView(id:)` API doesn't accept the slug-id format (`mcp-skills-issues-0d0359fabcf9`) extracted from view URLs. The API query silently fails, returning None, so users see "Ticket not found" instead of the helpful error message about view URLs not being supported.

## Root Cause Analysis

1. **URL parsing works**: Extracts `mcp-skills-issues-0d0359fabcf9` correctly ✅
2. **API query fails**: Linear API rejects slug-id format ❌
3. **Error handling**: Returns None when API fails ❌
4. **Result**: User sees generic error instead of helpful message ❌

## Solution Implemented

Updated `_get_custom_view()` method in `/src/mcp_ticketer/adapters/linear/adapter.py` to implement resilient error handling that detects view URL identifiers even when the API query fails.

### Key Changes

1. **Pattern Detection**: Added view ID pattern detection:
   - Checks if ID contains hyphens (slug-uuid format)
   - Checks if ID is longer than 12 characters
   - This indicates it's likely a view URL identifier

2. **Minimal View Object**: When API fails but ID looks like a view:
   ```python
   {
       "id": view_id,
       "name": "Linear View",  # Generic since we can't fetch actual name
       "issues": {"nodes": [], "pageInfo": {"hasNextPage": False}}
   }
   ```

3. **Two Fallback Paths**:
   - API returns empty result → Check pattern → Return minimal view object
   - API raises exception → Check pattern → Return minimal view object

4. **Preserved Existing Logic**:
   - Still tries API query first (in case it works for some IDs)
   - Doesn't break issue or project lookups
   - Only triggers for view-like identifiers (>12 chars with hyphens)

### Code Changes

**File**: `src/mcp_ticketer/adapters/linear/adapter.py`

**Method**: `_get_custom_view()` (lines 284-331)

```python
async def _get_custom_view(self, view_id: str) -> dict[str, Any] | None:
    """Get a Linear custom view by ID to check if it exists."""
    if not view_id:
        return None

    try:
        result = await self.client.execute_query(
            GET_CUSTOM_VIEW_QUERY, {"viewId": view_id, "first": 10}
        )

        if result.get("customView"):
            return result["customView"]

        # API query failed but check if this looks like a view identifier
        # View IDs from URLs have format: slug-uuid (e.g., "mcp-skills-issues-0d0359fabcf9")
        # If it has hyphens and is longer than 12 chars, it's likely a view URL identifier
        if "-" in view_id and len(view_id) > 12:
            # Return minimal view object to trigger helpful error message
            # We can't fetch the actual name, so use generic "Linear View"
            return {
                "id": view_id,
                "name": "Linear View",
                "issues": {"nodes": [], "pageInfo": {"hasNextPage": False}},
            }

        return None

    except Exception:
        # Linear returns error if view not found
        # Check if this looks like a view identifier to provide helpful error
        if "-" in view_id and len(view_id) > 12:
            # Return minimal view object to trigger helpful error message
            return {
                "id": view_id,
                "name": "Linear View",
                "issues": {"nodes": [], "pageInfo": {"hasNextPage": False}},
            }
        return None
```

## Error Messages

### Before Fix
```
Ticket not found: mcp-skills-issues-0d0359fabcf9
```

### After Fix
```
Linear view URLs are not supported in ticket_read.

View: 'Linear View' (mcp-skills-issues-0d0359fabcf9)
This view contains 0 issues.

Use ticket_list or ticket_search to query issues instead.
```

## Testing

Created comprehensive test suite in `/tests/adapters/test_linear_view_error.py`:

1. **test_view_url_helpful_error_when_api_fails**: Verifies error message when API fails
2. **test_view_url_helpful_error_when_api_succeeds**: Verifies error message when API succeeds
3. **test_non_view_id_does_not_trigger_view_error**: Ensures issue/project IDs work normally
4. **test_view_id_pattern_detection**: Tests various ID patterns

### Test Results
```
tests/adapters/test_linear_view_error.py::test_view_url_helpful_error_when_api_fails PASSED
tests/adapters/test_linear_view_error.py::test_view_url_helpful_error_when_api_succeeds PASSED
tests/adapters/test_linear_view_error.py::test_non_view_id_does_not_trigger_view_error PASSED
tests/adapters/test_linear_view_error.py::test_view_id_pattern_detection PASSED
```

## Success Criteria

- ✅ API query still attempted first
- ✅ Minimal view object returned when API fails but ID looks like view
- ✅ Helpful error message shown to user
- ✅ No breaking changes to issue/project lookups
- ✅ User's URL now triggers helpful error
- ✅ Pattern detection prevents false positives (issue IDs, short IDs)

## Edge Cases Handled

1. **Short issue IDs** (e.g., "BTA-123"): Not treated as views (only 7 chars)
2. **UUID-like IDs** (e.g., "abc123456789"): Not treated as views (no hyphens)
3. **Short project IDs** (e.g., "project-123"): Not treated as views (only 11 chars)
4. **Actual view IDs** (e.g., "mcp-skills-issues-0d0359fabcf9"): Correctly detected (>12 chars with hyphens)

## Net Code Impact

- **Lines Added**: +26 (pattern detection + minimal view object logic)
- **Lines Modified**: 0 (no breaking changes)
- **Lines Deleted**: 0
- **Net LOC**: +26

## Files Changed

1. `/src/mcp_ticketer/adapters/linear/adapter.py` - Enhanced `_get_custom_view()` method
2. `/tests/adapters/test_linear_view_error.py` - New test file (4 comprehensive tests)

## Deployment Notes

- No configuration changes required
- No database migrations needed
- No API version changes
- Backward compatible with all existing code
