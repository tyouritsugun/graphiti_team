# Fork Change Log

This document tracks all modifications made to the forked `graphiti-core` library.

## [Unreleased]

### Added
- **`graphiti_core.search.search_filters.SearchFilters`**:
  - Added `node_attributes: dict[str, Any] | None` to allow filtering nodes by their attributes.
- **`graphiti_core.search.search_filters.node_search_filter_query_constructor`**:
  - Added logic to construct Cypher `WHERE` clauses for the new `node_attributes` filter.
- **`mcp_server/pyproject.toml`**:
  - Added `debugpy` as a development dependency to support attaching a debugger to the running server.
