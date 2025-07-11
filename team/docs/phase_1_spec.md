# Phase 1 Implementation Specification: User Identification & Tagging System

This document provides a detailed technical specification for the tasks outlined in Phase 1.

## 1. MCP Server Enhancements

**Target File**: `mcp_server/graphiti_mcp_server.py`

### 1.1. Configuration Loading
- Modify the script to load `USER_EMAIL` and `PROJECT_ID` from environment variables. These will be passed from the MCP `settings.json`.
- If either `USER_EMAIL` or `PROJECT_ID` is not found in the environment, the script must raise a `ValueError` to terminate the MCP server startup. This ensures that all knowledge is properly attributed.

```python
# Example of reading env vars in graphiti_mcp_server.py
import os
import sys

USER_EMAIL = os.getenv("USER_EMAIL")
PROJECT_ID = os.getenv("PROJECT_ID")

if not USER_EMAIL or not PROJECT_ID:
    print("Error: USER_EMAIL and PROJECT_ID environment variables must be set.", file=sys.stderr)
    sys.exit(1)
```

### 1.2. Pass Configuration to Graphiti Instance
- Locate the instantiation of the `Graphiti` class within `graphiti_mcp_server.py`.
- Pass the `user_email` and `project_id` values to the `Graphiti` constructor. This will require modifying the `Graphiti` class `__init__` method first (see section 3).

```python
# Example modification
graphiti = Graphiti(
    # ... existing arguments
    user_email=USER_EMAIL,
    project_id=PROJECT_ID,
)
```

## 2. Database Schema Migration

**Conclusion from Investigation**: The project already handles idempotent schema creation in `graphiti_core/graph_queries.py`. A separate migration script is **not** needed for Phase 1. The required changes will be made directly to the existing files.

### 2.1. Add New Properties at Write Time
- The new properties (`user_email`, `knowledge_domain`, `project_id`, `created_at`, `updated_at`) will be added to nodes and relationships when they are created or updated by the `add_memory` function.
- **No backfill script**: We will not write a script to add these properties to existing data in this phase. New data will have the tags, and old data will not.

### 2.2. Add New Index
- **Target File**: `graphiti_core/graph_queries.py`
- **Action**: Add the new composite index to the list of indexes that are created on startup. The `IF NOT EXISTS` clause ensures this operation is idempotent.

```python
# In graphiti_core/graph_queries.py

# Add this to the appropriate list of index creation queries
'CREATE INDEX entity_project_domain IF NOT EXISTS FOR (e:Entity) ON (e.project_id, e.knowledge_domain)',
```
- This single line is the only schema migration action required for Phase 1.

## 3. API & Functionality Changes (Inheritance Model)

**Strategy**: To minimize direct modification of the core library and ease future merges from the upstream repository, we will use inheritance. We will create a new `TeamGraphiti` class that extends the base `Graphiti` class.

**New File**: `team/graphiti_team.py`

### 3.1. Create `TeamGraphiti` Class
- Create a new class `TeamGraphiti` that inherits from `graphiti_core.graphiti.Graphiti`.

```python
# In team/graphiti_team.py
from graphiti_core.graphiti import Graphiti

class TeamGraphiti(Graphiti):
    def __init__(self, user_email: str, project_id: str, **kwargs):
        super().__init__(**kwargs)
        self.user_email = user_email
        self.project_id = project_id
```

### 3.2. Override `add_memory`
- Re-implement the `add_memory` method in the `TeamGraphiti` class.
- The new implementation will be based on the original method but will add the `user_email`, `knowledge_domain`, `project_id`, `created_at`, and `updated_at` properties to the Cypher queries that create nodes and relationships.
- The `user_email` will come from `self.user_email`.
- The `project_id` will be taken from the method argument, falling back to `self.project_id`.

### 3.3. Override `search_memory_nodes`
- Re-implement the `search_memory_nodes` method in `TeamGraphiti`.
- The new implementation will modify the query generation logic to include `WHERE` clauses for `user_email`, `knowledge_domain`, and `project_id` when those arguments are provided.

### 3.4. Implement `remove_by_tags`
- Add the new `remove_by_tags` method to the `TeamGraphiti` class.
- This method will construct a Cypher `MATCH` query based on the provided tags and use `DETACH DELETE` to remove the matching nodes and their relationships.

### 3.5. Update MCP Server to Use `TeamGraphiti`
- **Target File**: `mcp_server/graphiti_mcp_server.py`
- **Action**: Modify the server file to import and instantiate `TeamGraphiti` instead of `Graphiti`.

```python
# In mcp_server/graphiti_mcp_server.py

# Remove the old import
# from graphiti_core.graphiti import Graphiti

# Add the new import
from team.graphiti_team import TeamGraphiti

# ... later in the file, change the instantiation
graphiti = TeamGraphiti(
    # ... existing arguments
    user_email=USER_EMAIL,
    project_id=PROJECT_ID,
)
```

## 4. Cursor Rules Update

**Target File**: `mcp_server/cursor_rules.md`

### 4.1. Content Update
- Prepend the existing content with the new rules for tagging knowledge.
- The new content should be exactly as specified in the blueprint to guide the LLM's behavior.

```markdown
## Graphiti Memory Management Rules

### Always Tag Knowledge
When adding memories to Graphiti, always include appropriate tags:

1. **Personal Preferences**: Use `knowledge_domain: "personal_preference"`
   - Code formatting preferences
   - Tool preferences
   - Working style preferences

2. **Project Specific**: Use `knowledge_domain: "project_specific"`
   - Project requirements
   - Project-specific decisions
   - Temporary project contexts

3. **Coding Conventions**: Use `knowledge_domain: "coding_conventions"`
   - Team coding standards
   - Architecture patterns
   - Best practices

4. **Legal Regulations**: Use `knowledge_domain: "legal_regulations"`
   - Compliance requirements
   - Security policies
   - Data handling rules

### Retrieval Before Action
Always search existing memories before adding new ones to avoid duplicates.

---
(Existing content follows)
```

## 5. Testing

**New File**: `team/tests/test_tagging.py`

### 5.1. Test Cases
- **Test `add_memory` with Tags**:
  - Call `add_memory` with `knowledge_domain` and `project_id`.
  - Query the database directly to verify that the created nodes and relationships have the correct `user_email`, `knowledge_domain`, and `project_id` properties.
- **Test `search_memory_nodes` Filtering**:
  - Add several nodes with different tags.
  - Call `search_memory_nodes` filtering by `project_id` and verify only nodes from that project are returned.
  - Call `search_memory_nodes` filtering by `knowledge_domain` and verify correctness.
  - Call `search_memory_nodes` filtering by a combination of tags.
- **Test `remove_by_tags`**:
  - Add a node with a specific `project_id`.
  - Call `remove_by_tags` with that `project_id`.
  - Verify the node has been deleted from the database.
- **Test Backward Compatibility**:
  - Call `search_memory_nodes` without any new tag filters to ensure it still works as before.
