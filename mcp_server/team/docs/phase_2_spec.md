# Phase 2 Implementation Specification: Database Management Tools

This document provides a detailed technical specification for the tasks outlined in Phase 2. The goal is to create a suite of tools for managing the knowledge graph's lifecycle, including merging, duplicating, and cleaning data.

## Proposed File Structure

To maintain consistency with the blueprint, all new management scripts and logic will be placed within the `mcp_server/scripts` directory.

```
mcp_server/
├── scripts/
│   ├── db_management.py      # Core logic for db operations (merge, duplicate, etc.)
│   ├── backup_restore.py     # Backup and restore utilities
│   ├── run_merge.py          # User-facing script to run the merge
│   └── merge_config.json     # Configuration for the merge script
└── tests/
    └── test_management.py    # Tests for all management functions
```
*(Other runner scripts and configs like `run_transition.py` will be added here as well)*

---

## 1. Core Management Functions

**Target File**: `mcp_server/scripts/db_management.py`

This file will contain the core business logic for all database management operations. Each function should accept a Neo4j driver instance to communicate with the database.

### 1.1. `merge_databases`

This is the most critical function of this phase. It will merge nodes and relationships from multiple source databases into a single target database.

```python
# In mcp_server/scripts/db_management.py
from neo4j import Driver
from typing import List, Literal

async def merge_databases(
    driver: Driver,
    source_dbs: List[str],
    target_db: str,
    exclude_domains: List[str] = ["project_specific"],
    conflict_resolution: Literal["keep_first", "keep_latest", "raise_error"] = "keep_latest",
    dry_run: bool = False
) -> dict:
    # ... implementation ...
```

**(Implementation steps remain the same)**

### 1.2. `duplicate_database`
**(Implementation remains the same)**

### 1.3. `remove_by_tags`
**(Implementation remains the same)**

### 1.4. `transition_project`
**(Implementation remains the same)**

---

## 2. Management Scripts (User-Friendly Approach)

**Strategy**: We will provide simple, single-purpose scripts in the `mcp_server/scripts` directory. Each script corresponds to a specific management task and is configured via an adjacent JSON file. This makes them easy to run for non-technical users.

### Example: Merging Databases

#### 1. The Configuration File (`mcp_server/scripts/merge_config.json`)
A user can easily edit this file to define the merge parameters.

```json
{
  "source_databases": ["team_a_db", "team_b_db"],
  "target_database": "consolidated_db",
  "exclude_domains": ["project_specific"],
  "conflict_resolution": "keep_latest",
  "dry_run": false
}
```

#### 2. The Script (`mcp_server/scripts/run_merge.py`)
This script is simple. It reads the config, calls the core function from `db_management.py`, and prints the status. The user just runs `python mcp_server/scripts/run_merge.py`.

**Implementation Steps**:
1.  **Import necessary modules**: `json`, `tqdm`, and the `merge_databases` function from `mcp_server.scripts.db_management`.
2.  **Load Configuration**: Open and read `merge_config.json`.
3.  **Initialize Driver**: Set up the connection to the Neo4j database.
4.  **Call Core Function**: Call `merge_databases` with the parameters from the loaded config.
5.  **Provide Feedback**: Print status updates and the final summary.
6.  **Backup Integration**: Before executing the merge, the script will first call a `create_backup` function from `mcp_server.scripts.backup_restore` to ensure safety.

This model will be applied to all other management tasks.

---

## 3. Backup and Restore Utilities

**Target File**: `mcp_server/scripts/backup_restore.py`

This script will handle database backups by calling the standard `neo4j-admin` tool.

**(Implementation steps remain the same)**

---

## 4. Testing

**Target File**: `mcp_server/tests/test_management.py`

**Setup**:
- Tests will require a live Neo4j instance. A testing framework like `pytest` should be used.
- Use fixtures to provide a clean driver instance for each test.
- The test setup should be able to create and populate temporary databases or use unique `group_id`s to isolate test data.

**Test Cases**:
- **`test_merge_no_conflict`**: Verify that all data is copied correctly when source and target are distinct.
- **`test_merge_exclude_domains`**: Verify that records with excluded `knowledge_domain`s are skipped.
- **`test_merge_conflict_keep_latest`**: Create a conflict and verify that the record with the more recent `updated_at` timestamp is kept.
- **`test_merge_dry_run`**: Verify that no changes are made to the target database when `dry_run` is `True`.
- **`test_remove_by_tags`**: Verify that only the targeted nodes/relationships are deleted.
- **`test_transition_project`**: Verify that project IDs are correctly updated and personal data is removed.