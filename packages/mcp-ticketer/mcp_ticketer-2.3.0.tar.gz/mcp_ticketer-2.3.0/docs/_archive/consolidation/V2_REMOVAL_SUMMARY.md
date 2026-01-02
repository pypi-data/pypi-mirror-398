# v2.0.0 Deprecated Function Removal - Progress Report

## Overview
Breaking change release removing all deprecated tool functions from Phase 2 consolidation. All deprecated functions are being removed with implementations inlined into unified tools.

## Completion Status: 3/5 Source Files (60%)

### ✅ COMPLETED Source Files

#### 1. src/mcp_ticketer/mcp/server/tools/bulk_tools.py
**Status**: COMPLETE ✅

**Removed Functions**:
- `ticket_bulk_create()` - Lines 111-246 (136 lines)
- `ticket_bulk_update()` - Lines 248-406 (159 lines)

**Changes**:
- Inlined create implementation into `ticket_bulk(action="create")`
- Inlined update implementation into `ticket_bulk(action="update")`
- Removed `import warnings` (no longer needed)
- Updated module docstring to remove deprecated function references

**Net LOC Impact**: -56 lines (296 removed, 240 inlined)

**Migration Path**:
```python
# OLD (removed)
await ticket_bulk_create(tickets=[...])
await ticket_bulk_update(updates=[...])

# NEW (use this)
await ticket_bulk(action="create", tickets=[...])
await ticket_bulk(action="update", updates=[...])
```

#### 2. src/mcp_ticketer/mcp/server/tools/session_tools.py
**Status**: COMPLETE ✅

**Removed Functions**:
- `get_session_info()` - Lines 225-279 (55 lines)

**Changes**:
- Inlined get_session_info implementation into `user_session(action="get_session_info")`
- Inlined get_my_tickets implementation into `user_session(action="get_my_tickets")`
- Removed `import warnings`
- Removed `from . import user_ticket_tools` (no longer needed)
- Updated module docstring

**Net LOC Impact**: +26 lines (54 removed, 80 inlined - consolidates 2 tools)

**Migration Path**:
```python
# OLD (removed)
await get_session_info()

# NEW (use this)
await user_session(action="get_session_info")
```

#### 3. src/mcp_ticketer/mcp/server/tools/user_ticket_tools.py
**Status**: COMPLETE ✅

**Removed Functions**:
- `get_my_tickets()` - Lines 67-172 (106 lines)

**Removed Helpers**:
- `get_config_resolver()` - Lines 56-64 (9 lines) [No longer used]

**Changes**:
- Removed `import warnings`
- Removed `from ....core.project_config import ConfigResolver, TicketerConfig` (unused after removal)
- Updated module docstring to remove deprecation notices

**Net LOC Impact**: -115 lines removed

**Migration Path**:
```python
# OLD (removed)
await get_my_tickets(state="open", limit=20)

# NEW (use this)
await user_session(action="get_my_tickets", state="open", limit=20)
```

---

### 🔄 PENDING Source Files

#### 4. src/mcp_ticketer/mcp/server/tools/hierarchy_tools.py
**Status**: PENDING 🟡

**Functions to Remove** (11 total):
1. `epic_create()` - Lines 398-463 (66 lines)
2. `epic_get()` - Lines 465-515 (51 lines)
3. `epic_list()` - Lines 517-614 (98 lines)
4. `epic_issues()` - Lines 616-671 (56 lines)
5. `issue_create()` - Lines 673-771 (99 lines)
6. `issue_get_parent()` - Lines 773-836 (64 lines)
7. `issue_tasks()` - Lines 838-968 (131 lines)
8. `task_create()` - Lines 970-1054 (85 lines)
9. `epic_update()` - Lines 1056-1149 (94 lines)
10. `epic_delete()` - Lines 1151-1218 (68 lines)
11. `hierarchy_tree()` - Lines 1220-1299 (80 lines)

**Total Lines to Remove**: ~892 lines

**Action Required**:
- Inline all 11 implementations into `hierarchy()` unified tool router
- Each implementation needs to be added to the appropriate entity_type+action branch
- Remove deprecation warnings and imports
- Update module docstring

**Migration Path**:
```python
# OLD (removed)
await epic_create(title="Q4 Features")
await epic_get(epic_id="EPIC-123")
await epic_list(project_id="PROJ-1")
await epic_issues(epic_id="EPIC-123")
await issue_create(title="Feature", epic_id="EPIC-123")
await issue_get_parent(issue_id="ISSUE-456")
await issue_tasks(issue_id="ISSUE-456")
await task_create(title="Task", issue_id="ISSUE-456")
await epic_update(epic_id="EPIC-123", title="Updated")
await epic_delete(epic_id="EPIC-123")
await hierarchy_tree(epic_id="EPIC-123")

# NEW (use this)
await hierarchy(entity_type="epic", action="create", title="Q4 Features")
await hierarchy(entity_type="epic", action="get", entity_id="EPIC-123")
await hierarchy(entity_type="epic", action="list", project_id="PROJ-1")
await hierarchy(entity_type="epic", action="get_children", entity_id="EPIC-123")
await hierarchy(entity_type="issue", action="create", title="Feature", epic_id="EPIC-123")
await hierarchy(entity_type="issue", action="get_parent", entity_id="ISSUE-456")
await hierarchy(entity_type="issue", action="get_children", entity_id="ISSUE-456")
await hierarchy(entity_type="task", action="create", title="Task", issue_id="ISSUE-456")
await hierarchy(entity_type="epic", action="update", entity_id="EPIC-123", title="Updated")
await hierarchy(entity_type="epic", action="delete", entity_id="EPIC-123")
await hierarchy(entity_type="epic", action="get_tree", entity_id="EPIC-123")
```

#### 5. src/mcp_ticketer/mcp/server/tools/ticket_tools.py
**Status**: PENDING 🟡

**Functions to Remove** (8 total):
1. `ticket_create()` - Lines 363-538 (176 lines)
2. `ticket_read()` - Lines 540-630 (91 lines)
3. `ticket_update()` - Lines 632-765 (134 lines)
4. `ticket_delete()` - Lines 767-830 (64 lines)
5. `ticket_list()` - Lines 864-996 (133 lines)
6. `ticket_summary()` - Lines 998-1047 (50 lines)
7. `ticket_latest()` - Lines 1049-1186 (138 lines)
8. `ticket_assign()` - Lines 1188-1371 (184 lines)

**Total Lines to Remove**: ~970 lines

**Action Required**:
- Inline all 8 implementations into `ticket()` unified tool router
- Each implementation needs to be added to the appropriate action branch
- Remove deprecation warnings and imports
- The `ticket()` function already has routing structure, just need to inline implementations

**Migration Path**:
```python
# OLD (removed)
await ticket_create(title="Fix bug", priority="high")
await ticket_read(ticket_id="PROJ-123")
await ticket_update(ticket_id="PROJ-123", state="done")
await ticket_delete(ticket_id="PROJ-123")
await ticket_list(project_id="PROJ", state="open")
await ticket_summary(ticket_id="PROJ-123")
await ticket_latest(ticket_id="PROJ-123", limit=5)
await ticket_assign(ticket_id="PROJ-123", assignee="user@example.com")

# NEW (use this)
await ticket(action="create", title="Fix bug", priority="high")
await ticket(action="get", ticket_id="PROJ-123")
await ticket(action="update", ticket_id="PROJ-123", state="done")
await ticket(action="delete", ticket_id="PROJ-123")
await ticket(action="list", project_id="PROJ", state="open")
await ticket(action="summary", ticket_id="PROJ-123")
await ticket(action="get_activity", ticket_id="PROJ-123", limit=5)
await ticket(action="assign", ticket_id="PROJ-123", assignee="user@example.com")
```

---

### 🧪 Test Files Requiring Updates

**Files with deprecated imports/calls**:
1. `tests/mcp/test_unified_ticket_bulk.py`
   - Remove imports: `ticket_bulk_create`, `ticket_bulk_update`
   - Update/remove deprecation warning tests
   - Use `ticket_bulk(action="create|update")` in all tests

2. `tests/mcp/test_unified_user_session.py`
   - Remove imports: `get_my_tickets`, `get_session_info`
   - Update/remove deprecation warning tests
   - Use `user_session(action="get_my_tickets|get_session_info")` in all tests

3. `tests/mcp/test_unified_hierarchy.py` (expected)
   - Remove imports of all 11 deprecated hierarchy functions
   - Update all test calls to use `hierarchy(entity_type=..., action=...)`

4. `tests/mcp/test_unified_ticket.py` (expected)
   - Remove imports of all 8 deprecated ticket functions
   - Update all test calls to use `ticket(action=...)`

**Search Command for Remaining References**:
```bash
# Find all deprecated function references
grep -r "ticket_bulk_create\|ticket_bulk_update\|get_session_info\|get_my_tickets\|epic_create\|epic_get\|epic_list\|epic_issues\|issue_create\|issue_get_parent\|issue_tasks\|task_create\|epic_update\|epic_delete\|hierarchy_tree\|ticket_create\|ticket_read\|ticket_update\|ticket_delete\|ticket_list\|ticket_summary\|ticket_latest\|ticket_assign" tests/ --include="*.py"
```

---

## Net Code Impact Summary

**Completed So Far**:
- bulk_tools.py: -56 lines
- session_tools.py: +26 lines (acceptable - consolidates 2 tools)
- user_ticket_tools.py: -115 lines
- **Current Net**: -145 lines

**Projected Total** (after completion):
- hierarchy_tools.py: ~-600 lines (estimate after inlining)
- ticket_tools.py: ~-500 lines (estimate after inlining)
- **Projected Final Net**: **-1,245 lines removed**

---

## Next Steps

### Step 1: Complete hierarchy_tools.py
```bash
# Backup original
cp src/mcp_ticketer/mcp/server/tools/hierarchy_tools.py src/mcp_ticketer/mcp/server/tools/hierarchy_tools.py.backup

# Edit file:
# 1. Inline all 11 functions into hierarchy() router
# 2. Remove deprecated functions (lines 398-1299)
# 3. Remove import warnings
# 4. Update docstring
```

### Step 2: Complete ticket_tools.py
```bash
# Backup original
cp src/mcp_ticketer/mcp/server/tools/ticket_tools.py src/mcp_ticketer/mcp/server/tools/ticket_tools.py.backup

# Edit file:
# 1. Inline all 8 functions into ticket() router (already partially done)
# 2. Remove deprecated functions (lines 363-1371)
# 3. Remove import warnings
# 4. Update docstring
```

### Step 3: Update Test Files
```bash
# Update test imports
# tests/mcp/test_unified_ticket_bulk.py - remove deprecated imports
# tests/mcp/test_unified_user_session.py - remove deprecated imports
# tests/mcp/test_unified_hierarchy.py - remove all 11 deprecated imports
# tests/mcp/test_unified_ticket.py - remove all 8 deprecated imports

# Update test function calls to use unified interfaces
```

### Step 4: Run Tests
```bash
# Run full test suite
pytest tests/mcp/test_unified_*.py -v

# Check for any remaining references
grep -r "ticket_bulk_create\|ticket_bulk_update\|get_session_info\|get_my_tickets" tests/ --include="*.py"
```

### Step 5: Verify No References Remain
```bash
# Search entire codebase
grep -r "ticket_bulk_create\|ticket_bulk_update\|get_session_info\|get_my_tickets\|epic_create\|epic_get" . --include="*.py" --exclude-dir=.git
```

---

## Breaking Changes Documentation

**Version**: v2.0.0
**Release Type**: Major (Breaking)

**Summary**: All deprecated tool functions from v1.5.0 have been removed. Users must migrate to unified tool interfaces.

**Affected Functions** (27 total):
- `ticket_bulk_create()` → `ticket_bulk(action="create")`
- `ticket_bulk_update()` → `ticket_bulk(action="update")`
- `get_session_info()` → `user_session(action="get_session_info")`
- `get_my_tickets()` → `user_session(action="get_my_tickets")`
- 11 hierarchy functions → `hierarchy(entity_type=..., action=...)`
- 8 ticket functions → `ticket(action=...)`

**Migration Guide**: See "Migration Path" sections above for each tool category.

**Rollback**: To use old functions, downgrade to v1.5.x:
```bash
pip install mcp-ticketer==1.5.4
```

---

## Files Modified

### Source Code (5 files):
- [x] src/mcp_ticketer/mcp/server/tools/bulk_tools.py (COMPLETE)
- [x] src/mcp_ticketer/mcp/server/tools/session_tools.py (COMPLETE)
- [x] src/mcp_ticketer/mcp/server/tools/user_ticket_tools.py (COMPLETE)
- [ ] src/mcp_ticketer/mcp/server/tools/hierarchy_tools.py (PENDING)
- [ ] src/mcp_ticketer/mcp/server/tools/ticket_tools.py (PENDING)

### Test Files (4+ files):
- [ ] tests/mcp/test_unified_ticket_bulk.py (PENDING)
- [ ] tests/mcp/test_unified_user_session.py (PENDING)
- [ ] tests/mcp/test_unified_hierarchy.py (PENDING)
- [ ] tests/mcp/test_unified_ticket.py (PENDING)
- [ ] Any other files with deprecated references (TBD)

---

## Success Criteria

- ✅ All 27 deprecated functions removed from source code
- ✅ All implementations inlined into unified tools
- ✅ Zero references to removed function names in codebase
- ✅ All tests updated to use new interfaces
- ✅ All tests passing
- ✅ Net negative LOC impact (code reduction achieved)
- ✅ No import errors
- ✅ 100% test coverage maintained for unified tools

---

*Generated: 2025-12-01*
*Status: 60% Complete (3/5 source files)*
