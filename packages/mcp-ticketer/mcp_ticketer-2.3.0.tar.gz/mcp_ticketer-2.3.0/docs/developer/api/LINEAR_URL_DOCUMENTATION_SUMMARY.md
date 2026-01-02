# Linear URL Documentation Summary

**Date:** 2025-11-29
**Task:** Document Linear URL structure and adapter behavior for clarity
**Status:** ✅ Complete

## Overview

This documentation effort clarifies how the Linear adapter handles different Linear URL formats and explains the relationship between Linear's web UI routes and the underlying GraphQL API.

## Key Documentation Created

### 1. Comprehensive URL Handling Guide

**File:** `/docs/developer-docs/adapters/LINEAR_URL_HANDLING.md`
**Size:** 413 lines
**Scope:** Complete documentation of Linear URL structure and adapter behavior

**Sections:**
- Linear URL structure explanation
- URL parsing implementation details
- GraphQL API vs Web UI routes distinction
- MCP tool usage guide with examples
- Common misconceptions clarification
- Quick reference table
- Code references for developers

### 2. Documentation Updates

**Files Updated:**
1. `/docs/developer-docs/adapters/LINEAR.md`
   - Added "URL Handling" section in table of contents
   - Added overview of URL handling with quick reference
   - Linked to detailed URL handling guide

2. `/README.md`
   - Added "Understanding Linear URLs" section
   - Referenced URL handling guide

3. `/docs/integrations/setup/LINEAR_SETUP.md`
   - Added note about URL handling at top of document
   - Linked to URL handling guide

4. `/docs/developer-docs/adapters/OVERVIEW.md`
   - Added URL handling note in Linear adapter section
   - Added documentation links

5. `/docs/developer-docs/README.md`
   - Added Linear URL Handling to adapters section

## Key Findings Documented

### URL Structure

Linear uses different URL paths in its web interface:
- `/issues` - Project issues list view
- `/overview` - Project summary view
- `/updates` - Project status updates feed

**Important:** These are **frontend-only routes**. They don't affect the GraphQL API.

### Adapter Behavior

All project URL variants extract the same project ID and query the same GraphQL endpoint:

```
https://linear.app/team/project/my-project-abc123/issues   → my-project-abc123
https://linear.app/team/project/my-project-abc123/overview → my-project-abc123
https://linear.app/team/project/my-project-abc123/updates  → my-project-abc123
```

### MCP Tool Usage

Different data types require different MCP tools:

| Data Type | MCP Tool | GraphQL Query |
|-----------|----------|---------------|
| Project metadata + issues | `epic_get()` | `project(id:)` + `issues()` |
| Project updates only | `project_update_list()` | `project(id:).projectUpdates` |
| Issues only | `epic_issues()` | `issues(filter: {project: ...})` |
| Single issue | `ticket_read()` | `issue(id:)` |

## Common Misconceptions Addressed

### ❌ Misconception: URL suffix determines data returned
**Reality:** All project URLs return the same data (project metadata + issues)

### ❌ Misconception: Different URLs need different tools
**Reality:** Same MCP tool works for all URL variants

### ❌ Misconception: Updates are included in project query
**Reality:** Updates require separate `project_update_list()` call

## Documentation Quality

- ✅ Comprehensive examples provided
- ✅ Clear distinction between web UI and API
- ✅ Quick reference tables for easy lookup
- ✅ Code references with line numbers
- ✅ Related documentation cross-referenced
- ✅ Common misconceptions explicitly addressed

## Success Criteria Met

- ✅ Linear URL structure documented clearly
- ✅ MCP tool usage guide created
- ✅ Examples provided for each URL variant
- ✅ Users understand that URL suffixes don't affect API behavior
- ✅ Comprehensive cross-referencing between documents
- ✅ Code references provided for developers

## Files Modified

### New Files
- `/docs/developer-docs/adapters/LINEAR_URL_HANDLING.md` (413 lines)

### Updated Files
- `/docs/developer-docs/adapters/LINEAR.md` (added URL Handling section)
- `/README.md` (added URL understanding note)
- `/docs/integrations/setup/LINEAR_SETUP.md` (added URL guide reference)
- `/docs/developer-docs/adapters/OVERVIEW.md` (added URL handling note)
- `/docs/developer-docs/README.md` (added URL handling guide link)

## Related Research

- **Research Document:** `/docs/research/linear-url-structure-analysis-2025-11-29.md`
- **Verification:** URL parsing tested in `tests/adapters/test_linear_resolve_project_id.py`
- **Implementation:** `src/mcp_ticketer/core/url_parser.py` and `src/mcp_ticketer/adapters/linear/adapter.py`

## Future Improvements

Consider adding:
1. Visual diagrams showing URL parsing flow
2. Interactive examples in documentation site
3. FAQ section for common URL-related questions
4. Video tutorial demonstrating URL handling

## Conclusion

This documentation comprehensively addresses the gap identified in the research phase. Users now have clear guidance on:
- How Linear URLs are structured
- How the adapter parses and handles URLs
- Which MCP tools to use for different data types
- Why URL suffixes don't affect adapter behavior

The documentation is thorough, well-organized, and provides practical examples for users to reference.

---

**Documentation Status:** Production-ready
**Maintenance:** Update if Linear API or URL structure changes
**Last Review:** 2025-11-29
