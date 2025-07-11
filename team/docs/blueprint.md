# Graphiti Fork Blueprint - Team Knowledge Management

## Overview

This blueprint outlines the development of an enhanced version of [Graphiti](https://github.com/getzep/graphiti) with team‑oriented knowledge management features. The fork will add tagging, user identification, **cross‑database merge**, and database management capabilities to enable collaborative AI memory across development teams.

## Project Goals

### Primary Objectives

- Enable team‑wide knowledge sharing through tagged memories
- Implement user identification for knowledge attribution
- Provide database management tools for project lifecycle management **including safe cross‑team database merge utilities**
- Maintain compatibility with existing Graphiti MCP protocol
- Follow official Graphiti embedding integration for vector storage and retrieval with custom tags

### Use Cases

- **Project Transitions**: Transfer conventions and regulations to new projects
- **Team Changes**: Remove departing members' personal preferences
- **Knowledge Organization**: Categorize information by domain and ownership
- **Collaborative Memory**: Share institutional knowledge across team members
- **Database Consolidation**: Merge knowledge from multiple teams (e.g., Team A & Team B) while excluding project‑specific context to create a shared institutional repository


## Technical Requirements

### 1. User Identification System

#### 1.1 MCP Configuration Enhancement

- **File**: `mcp_server/graphiti_mcp_server.py`
- **Changes**:
  - Add `user_email` parameter to MCP server configuration
  - Add `project_id` parameter to MCP server configuration
  - Auto-extract email and project\_id from MCP settings.json
  - Pass user email and project\_id to all memory operations

#### 1.2 Configuration Schema

```json
{
  "mcpServers": {
    "graphiti-memory": {
      "transport": "stdio",
      "command": "/path/to/uv",
      "args": ["run", "graphiti_mcp_server.py", "--transport", "stdio"],
      "env": {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "password",
        "OPENAI_API_KEY": "sk-XXXXXXXX",
        "MODEL_NAME": "gpt-4.1-mini",
        "USER_EMAIL": "developer@company.com",
        "PROJECT_ID": "project_alpha"
      }
    }
  }
}
```

### 2. Tagging System

#### 2.1 Tag Structure

- **Tag 1**: `user_email` (string) - Auto-extracted from MCP config
- **Tag 2**: `knowledge_domain` (enum) - Categorizes the type of knowledge
  - `personal_preference`
  - `project_specific`
  - `coding_conventions`
  - `legal_regulations`
- **Tag 3**: `project_id` (string) - Project identifier for scoping

#### 2.2 Database Schema Updates

```cypher
// Enhanced Entity node properties
CREATE (n:Entity {
  name: "Entity Name",
  summary: "Entity description",
  user_email: "developer@company.com",
  knowledge_domain: "coding_conventions",
  project_id: "project_alpha",
  created_at: datetime(),
  updated_at: datetime()
})

// Enhanced Relationship properties
CREATE (n1)-[r:RELATES_TO {
  name: "relationship_name",
  fact: "relationship description",
  user_email: "developer@company.com",
  knowledge_domain: "project_specific",
  project_id: "project_alpha",
  created_at: datetime()
}]->(n2)
```

##### Indexing Strategy for Tag Filtering

To maintain the performance goal (no more than 10 % overhead) when applying tag filters, create a composite index on `(project_id, knowledge_domain)`:

```cypher
CREATE INDEX entity_project_domain IF NOT EXISTS
FOR (e:Entity)
ON (e.project_id, e.knowledge_domain);
```

#### 2.3 API Changes

##### Enhanced add\_memory Function

```python
async def add_memory(
    name: str,
    episode_body: str,
    knowledge_domain: str,  # Required tag
    project_id: str = None,  # Optional project scope
    group_id: str = None,
    source: str = 'text',
    source_description: str = '',
    uuid: str = None,
) -> SuccessResponse | ErrorResponse:
```

##### Enhanced Search Functions

```python
async def search_memory_nodes(
    query: str,
    group_ids: List[str] = None,
    max_nodes: int = 10,
    center_node_uuid: str = None,
    user_email: str = None,
    knowledge_domain: str = None,
    project_id: str = None,
) -> dict:
```

### 2.4 Vector Embedding Support with Official Graphiti API

Graphiti natively supports vector embedding via the MCP protocol. We will maintain compatibility by using the official memory interface while extending it to support custom tags.

#### Adding Embedding with Tags

```python
await add_memory(
    name="Meeting with Client",
    episode_body="We discussed legal compliance for project Alpha...",
    knowledge_domain="legal_regulations",
    project_id="project_alpha",
    user_email="developer@company.com",
    source="text"
)
```

The embedding is automatically generated and stored with the node, ready for semantic search.

#### Vector Search with Tag Filters

```python
await search_memory_nodes(
    query="data handling for client projects",
    project_id="project_alpha",
    knowledge_domain="legal_regulations",
    max_nodes=10
)
```

#### Remove Vector Nodes by Tags

```python
await remove_by_tags(
    project_id="project_alpha",
    knowledge_domain="project_specific"
)
```

This safely removes tagged vector data without affecting shared nodes.

### 3. Cursor Rules Enhancement

#### 3.1 Updated Instructions
- **File**: `mcp_server/cursor_rules.md`
- **Changes**:
  - Add tagging instructions for LLM
  - Define when to use each knowledge domain
  - Specify project identification strategies

#### 3.2 Sample Cursor Rules
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
```

### 4. Database Management Tools

#### 4.1 New Management Functions

##### Duplicate Database

```python
async def duplicate_database(
    source_db: str,
    target_db: str,
    include_domains: List[str] = None
) -> SuccessResponse | ErrorResponse:
```

##### Remove Records by Tags

```python
async def remove_by_tags(
    user_email: str = None,
    knowledge_domain: str = None,
    project_id: str = None,
    group_id: str = None
) -> SuccessResponse | ErrorResponse:
```

##### **Merge Databases (NEW)**

```python
async def merge_databases(
    source_dbs: List[str],            # e.g. ["team_a_db", "team_b_db"]
    target_db: str,                  # e.g. "consolidated_db"
    exclude_domains: List[str] = ["project_specific"],
    conflict_resolution: Literal["keep_first", "keep_latest", "raise_error"] = "keep_latest",
    dry_run: bool = False
) -> SuccessResponse | ErrorResponse:
```

**Purpose:** Consolidate multiple team databases into a single target database while automatically filtering out nodes and edges tagged with any `knowledge_domain` values found in `exclude_domains` (defaults to `project_specific`).

**Implementation Notes**

- Iterate through `source_dbs`, stream‑copying records into `target_db`.
- For each record, **skip** if `knowledge_domain` ∈ `exclude_domains`.
- Detect UUID collisions; resolve according to `conflict_resolution`.
  - **Definition of "latest"**: The record whose `updated_at` timestamp is more recent is considered latest. If `updated_at` is absent, compare `created_at`. If both are missing, fall back to lexical UUID order as a deterministic tie-breaker.
- Provide `dry_run` option to output an OP‑log without persisting changes.
- Return a summary: counts of copied, skipped, overwritten, and conflicted records.

##### Project Transition Management

```python
async def transition_project(
    old_project: str,
    new_project: str,
    remaining_users: List[str],
    departing_users: List[str],
    transfer_domains: List[str] = ["coding_conventions", "legal_regulations"]
) -> SuccessResponse | ErrorResponse:
```

#### 4.2 Management Scripts

- **File**: `scripts/db_management.py`
  - Backup database before operations
  - Validate operations with dry‑run mode
  - Bulk operations with progress tracking
  - Rollback capabilities
  - **New CLI command:** `merge`
    ```bash
    python db_management.py merge --sources team_a_db team_b_db \
                                   --target consolidated_db \
                                   --exclude project_specific --keep latest
    ```

---

## File Structure

```
graphiti-fork/
├── mcp_server/
│   ├── graphiti_mcp_server.py          # Enhanced MCP server
│   ├── cursor_rules.md                 # Updated AI instructions
│   └── management_functions.py         # New database management functions (incl. merge)
├── team/
│   ├── scripts/
│   │   ├── db_management.py            # Database management CLI (merge added)
│   │   ├── migrate_schema.py           # Schema migration tools
│   │   └── backup_restore.py           # Backup/restore utilities
│   ├── tests/
│   │   ├── test_tagging.py             # Tag system tests
│   │   ├── test_management.py          # Management function tests (merge added)
│   │   └── test_integration.py         # MCP integration tests
│   └── docs/
│       ├── TAGGING_GUIDE.md            # Tagging system documentation
│       ├── MANAGEMENT_API.md           # Management API reference (merge documented)
│       └── MIGRATION_GUIDE.md          # Migration from original Graphiti
└── README.md                           # Updated project README
```

## Success Metrics

### Technical Metrics
- **Compatibility**: 100% backward compatibility with existing Graphiti MCP clients
- **Performance**: No more than 10% performance degradation with tagging overhead
- **Reliability**: 99.9% uptime for database operations
- **Data Integrity**: Zero data loss during management operations

### User Experience Metrics
- **Adoption**: 80% of team members actively using tagged memories
- **Efficiency**: 50% reduction in context re-establishment time
- **Satisfaction**: 90% positive feedback on knowledge sharing capabilities

## Risk Mitigation

### Technical Risks

- **Database Corruption**: Implement comprehensive backup/restore system **with merge transaction rollback**
- **Performance Degradation**: Optimize queries and add proper indexing
- **Compatibility Issues**: Maintain extensive test suite for MCP clients

### Organizational Risks
- **Privacy Concerns**: Implement clear data ownership and access controls
- **Adoption Resistance**: Provide clear documentation and training materials
- **Data Governance**: Establish clear policies for knowledge management

## References

- **Original Project**: https://github.com/getzep/graphiti
- **MCP Protocol**: https://modelcontextprotocol.io/
- **Neo4j Documentation**: https://neo4j.com/docs/
- **Graphiti Research Paper**: [Zep: A Temporal Knowledge Graph Architecture for Agent Memory](https://arxiv.org/abs/2410.13735)

## Legal Compliance & Attribution

### **License: Apache 2.0**
This fork is based on [Graphiti by Zep Software, Inc.](https://github.com/getzep/graphiti) and is licensed under Apache 2.0. All developers must follow these requirements:

### **✅ REQUIRED Legal Compliance:**

#### **1. License Attribution**
- **NEVER remove** the original `LICENSE` file
- **ALWAYS keep** copyright notices from Zep Software, Inc.
- **MUST include** attribution in derivative works

#### **2. Change Documentation**
- **Mark all modified files** with change notices:
  ```python
  # Modified by [Your Name/Company] - Added tagging functionality
  # Original copyright: Copyright 2024, Zep Software, Inc.
  ```
- **Document changes** in commit messages and changelog

#### **3. Repository Setup**
- **Keep original LICENSE** file in repository root
- **Credit original project** in README
- **Use different project name** (not "Graphiti") to avoid confusion

### **❌ PROHIBITED Actions:**
- ❌ Removing original license or copyright notices
- ❌ Claiming original authorship of base Graphiti code
- ❌ Using "Graphiti" as your project name without clear attribution
- ❌ Removing attribution notices from source files

### **✅ RECOMMENDED Best Practices:**
- ✅ Choose distinctive project name (e.g., "GraphitiTeam", "TeamKnowledge")
- ✅ Update package names in `setup.py`/`pyproject.toml`
- ✅ Maintain clear changelog of modifications
- ✅ Consider adding your own CLA if accepting external contributions

### **Compliance Checklist:**
Before any release or deployment:
- [ ] Original LICENSE file present and unmodified
- [ ] All modified files have change notices
- [ ] README credits original Graphiti project
- [ ] Project uses different name than "Graphiti"
- [ ] Copyright notices from Zep Software, Inc. preserved
- [ ] Package names updated to avoid conflicts

**⚠️ VIOLATION CONSEQUENCES:** Failure to follow these requirements could result in license violation and legal issues. When in doubt, over-attribute rather than under-attribute.

---

*This blueprint serves as a comprehensive guide for implementing team-oriented knowledge management features in Graphiti. Regular updates and refinements will be made based on development progress and user feedback.*