# Graphiti Fork Task List

This task list is derived from the `blueprint.md` and outlines the development work required to implement the team-oriented knowledge management features.

## Phase 1: User Identification & Tagging System

- [ ] **MCP Server Enhancements (`mcp_server/graphiti_mcp_server.py`)**:
    - [ ] Add `user_email` to the MCP server configuration.
    - [ ] Add `project_id` to the MCP server configuration.
    - [ ] Implement logic to auto-extract `user_email` and `project_id` from MCP `settings.json`.
    - [ ] Pass `user_email` and `project_id` to all memory operations.
- [ ] **Database Schema Migration**:
    - [ ] Create `team/scripts/migrate_schema.py` for schema updates.
    - [ ] Add `user_email`, `knowledge_domain`, `project_id`, `created_at`, and `updated_at` to the `Entity` node properties.
    - [ ] Add `user_email`, `knowledge_domain`, `project_id`, and `created_at` to relationship properties.
    - [ ] Create a composite index on `(e.project_id, e.knowledge_domain)` for `Entity` nodes to optimize filtering.
- [ ] **API & Functionality Changes**:
    - [ ] Enhance `add_memory` to require `knowledge_domain` and accept `project_id`.
    - [ ] Enhance `search_memory_nodes` to allow filtering by `user_email`, `knowledge_domain`, and `project_id`.
    - [ ] Implement `remove_by_tags` to safely remove nodes and vectors based on tags.
- [ ] **Cursor Rules Update (`mcp_server/cursor_rules.md`)**:
    - [ ] Add instructions for the LLM on how to apply tags.
    - [ ] Define the use cases for each `knowledge_domain`.
    - [ ] Provide strategies for project identification.
- [ ] **Testing**:
    - [ ] Write `test_tagging.py` to validate the tagging system.

## Phase 2: Database Management Tools

- [ ] **Create Management Functions (`mcp_server/management_functions.py`)**:
    - [ ] Implement `duplicate_database` function.
    - [ ] Implement `remove_by_tags` function for broader data removal.
    - [ ] Implement `merge_databases` function:
        - [ ] Handle `source_dbs` and `target_db` parameters.
        - [ ] Filter records based on `exclude_domains`.
        - [ ] Implement conflict resolution (`keep_first`, `keep_latest`, `raise_error`).
        - [ ] Ensure `updated_at` / `created_at` logic for "latest" is correct.
        - [ ] Add a `dry_run` mode to preview changes.
        - [ ] Return a summary of the merge operation.
    - [ ] Implement `transition_project` function for managing project handovers.
- [ ] **Create Management CLI (`team/scripts/db_management.py`)**:
    - [ ] Build a CLI to expose the new management functions.
    - [ ] Implement the `merge` command with all specified options.
    - [ ] Integrate robust pre-operation backups.
    - [ ] Add progress tracking for bulk operations.
    - [ ] Investigate and implement rollback capabilities for failed operations.
- [ ] **Backup and Restore Scripts (`team/scripts/backup_restore.py`)**:
    - [ ] Develop and test reliable backup and restore utilities.
- [ ] **Testing**:
    - [ ] Write `test_management.py` to test all database management functions, with a focus on the `merge` command.

## Phase 3: Integration and Validation

- [ ] **Integration Testing**:
    - [ ] Write `test_integration.py` to ensure full MCP compatibility is maintained.
- [ ] **Performance Testing**:
    - [ ] Benchmark the system to ensure tagging adds no more than 10% performance overhead.
- [ ] **Data Integrity Testing**:
    - [ ] Run simulations of management operations (especially merge and remove) to ensure zero data loss.

## Phase 4: Documentation & Finalization

- [ ] **Create User and Developer Documentation (`team/docs/`)**:
    - [ ] Write `TAGGING_GUIDE.md` explaining the new tagging system.
    - [ ] Write `MANAGEMENT_API.md` to document the new database management functions and CLI.
    - [ ] Write `MIGRATION_GUIDE.md` for users transitioning from the original Graphiti.
- [ ] **Compliance Checklist**:
    - [ ] Before release, verify every item in the "Legal Compliance & Attribution" section of the blueprint.
      - [ ] Original LICENSE file present.
      - [ ] All modified files have change notices.
      - [ ] README credits original Graphiti project.
      - [ ] Project uses a different name.
      - [ ] Copyright notices from Zep Software, Inc. are preserved.
      - [ ] Package names are updated.
- [ ] **Project Naming**: Decide on a distinctive name for the fork to avoid confusion with the original Graphiti.
- [ ] **Repository Setup**:
    - [ ] Confirm the original `LICENSE` file is present.
    - [ ] Update the `README.md` to credit the original Graphiti project.
    - [ ] Update package names in `pyproject.toml` to reflect the new project name.
- [ ] **Changelog**: Create and maintain a `CHANGELOG.md` to document modifications.
