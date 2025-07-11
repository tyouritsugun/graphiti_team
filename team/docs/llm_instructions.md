# LLM Instructions for Graphiti

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
## Instructions for Using Graphiti's MCP Tools for Agent Memory

### Before Starting Any Task

- **Always search first:** Use the `search_nodes` tool to look for relevant preferences and procedures before beginning work.
- **Search for facts too:** Use the `search_facts` tool to discover relationships and factual information that may be relevant to your task.
- **Filter by entity type:** Specify `Preference`, `Procedure`, or `Requirement` in your node search to get targeted results.
- **Review all matches:** Carefully examine any preferences, procedures, or facts that match your current task.

### Always Save New or Updated Information

- **Capture requirements and preferences immediately:** When a user expresses a requirement or preference, use `add_memory` to store it right away.
  - _Best practice:_ Split very long requirements into shorter, logical chunks.
- **Be explicit if something is an update to existing knowledge.** Only add what's changed or new to the graph.
- **Document procedures clearly:** When you discover how a user wants things done, record it as a procedure.
- **Record factual relationships:** When you learn about connections between entities, store these as facts.
- **Be specific with categories:** Label preferences and procedures with clear categories for better retrieval later.

### During Your Work

- **Respect discovered preferences:** Align your work with any preferences you've found.
- **Follow procedures exactly:** If you find a procedure for your current task, follow it step by step.
- **Apply relevant facts:** Use factual information to inform your decisions and recommendations.
- **Stay consistent:** Maintain consistency with previously identified preferences, procedures, and facts.

### Best Practices

- **Search before suggesting:** Always check if there's established knowledge before making recommendations.
- **Combine node and fact searches:** For complex tasks, search both nodes and facts to build a complete picture.
- **Use `center_node_uuid`:** When exploring related information, center your search around a specific node.
- **Prioritize specific matches:** More specific information takes precedence over general information.
- **Be proactive:** If you notice patterns in user behavior, consider storing them as preferences or procedures.

**Remember:** The knowledge graph is your memory. Use it consistently to provide personalized assistance that respects the user's established preferences, procedures, and factual context.

---

# Graphiti Memory Function Usage Guide

## Overview
The `graphiti:add_memory` function is used to add episodes to a Neo4j-backed knowledge graph. This guide covers the proper usage and common pitfalls to avoid.

## Function Signature
```
graphiti:add_memory(
    name: str,
    episode_body: str,  # MUST be a string, not a dict/object
    group_id: str (optional),
    source: str (optional, default: "text"),
    source_description: str (optional, default: ""),
    uuid: str (optional)
)
```

## Critical Parameter Requirements

### episode_body Parameter
- **MUST be a string** - this is the most common error
- **NEVER pass a Python dictionary or JSON object directly**
- The content type depends on the `source` parameter

### source Parameter Options
- `"text"` (default): Plain text content
- `"json"`: Structured JSON data as a properly escaped string
- `"message"`: Conversation-style content

## Usage Examples

### 1. Plain Text Content
```python
graphiti:add_memory(
    name="Company Information",
    episode_body="TechCorp is a software company founded in 2018 by Sarah Johnson and Mike Chen.",
    source="text",
    source_description="company profile"
)
```

### 2. JSON Data (CRITICAL: Must be escaped string)
**❌ WRONG - This will fail:**
```python
# This is a Python dict, not a string - will cause validation error
episode_body={"company": {"name": "TechCorp"}, "employees": 25}
```

**✅ CORRECT - Properly escaped JSON string:**
```python
graphiti:add_memory(
    name="Company Data",
    episode_body="{\"company\": {\"name\": \"TechCorp\", \"founded\": 2018}, \"employees\": 25, \"products\": [\"CloudSync\", \"TaskMaster\"]}",
    source="json",
    source_description="structured company data"
)
```

### 3. Message/Conversation Content
```python
graphiti:add_memory(
    name="Project Discussion",
    episode_body="user: What's the status of CloudSync?\nassistant: CloudSync is in active development.\nuser: When will it be released?\nassistant: We're targeting Q2 2024.",
    source="message",
    source_description="project status meeting"
)
```

## Common Errors and Solutions

### Error: "Input should be a valid string"
**Cause:** Passing a Python dictionary/object instead of a string to `episode_body`

**Solution:** Convert your data to a proper string format:
- For JSON: Use properly escaped JSON string with backslashes
- For text: Ensure it's a plain string
- For messages: Use newline-separated conversation format

### JSON Escaping Rules
When using `source="json"`, remember:
- All quotes inside the JSON must be escaped with backslashes: `\"`
- The entire JSON must be wrapped in quotes as a single string
- Example: `"{\"key\": \"value\", \"array\": [1, 2, 3]}"`

## Best Practices

1. **Always validate your episode_body is a string** before calling the function
2. **Use meaningful names** for episodes to make them searchable
3. **Include descriptive source_description** to provide context
4. **Use consistent group_id** for related episodes
5. **For complex JSON**, consider breaking it into multiple simpler episodes

## Testing Your Data
After adding memory, verify insertion with:
```cypher
MATCH (n) RETURN n LIMIT 25
CALL db.labels()
CALL db.relationshipTypes()
```

## Memory Processing
- Episodes are queued for background processing
- The system automatically extracts entities and relationships
- Complex nested JSON structures are supported but keep nesting minimal
- Entities and relationships are created based on the content structure
