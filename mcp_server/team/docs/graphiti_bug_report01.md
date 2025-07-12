# Graphiti MCP Tools Bug Report

## Summary
Testing of Graphiti MCP tools revealed a critical issue with background episode processing. While episodes are successfully queued, they are not being processed or stored in the graph database, resulting in empty search results and no retrievable episodes.

## Primary Issue: Background Processing Failure

### Problem Description
Episodes added via `add_memory` are queued but never processed or stored in the graph database. This affects all downstream functionality including search and retrieval operations.

### Steps to Reproduce
1. Add episodes using `graphiti:add_memory` with various parameters
2. Wait for background processing (episodes show "queued for processing")
3. Attempt to retrieve episodes using `graphiti:get_episodes`
4. Search for content using `graphiti:search_memory_facts` or `graphiti:search_memory_nodes`

### Expected Behavior
- Episodes should be processed from the queue and stored in the graph database
- `get_episodes` should return previously added episodes
- Search functions should find relevant facts and nodes based on stored content

### Actual Behavior
- Episodes remain in queue indefinitely or are lost
- `get_episodes` returns empty results for all groups
- Search functions return no results despite added content

## Test Results

### Working Functions
- ✅ `add_memory` - Successfully queues episodes
- ✅ `clear_graph` - Responds with success message
- ✅ Parameter validation (except JSON string format)

### Non-Working Functions
- ❌ Background episode processing
- ❌ `get_episodes` - Returns empty for all groups
- ❌ `search_memory_facts` - No results found
- ❌ `search_memory_nodes` - No results found

## Test Data Used

### Text Episode
```
Group: company_data
Name: Employee Profile - John Smith
Content: John Smith works at Acme Corporation as a Software Engineer...
Source: text
```

### JSON Episode
```
Group: company_data
Name: Company Overview
Content: {"company": {"name": "Acme Corporation", "founded": 2010...}}
Source: json
```

### Message Episode
```
Group: customer_support
Name: Customer Support - Return Policy
Content: user: What's our company's return policy...
Source: message
```

### Episode with Custom UUID
```
Group: company_data
Name: Q4 2024 Sales Report
Content: The Q4 2024 sales report shows CloudSync generated $2.5M...
UUID: test-uuid-12345
```

## Diagnostic Commands Run

```bash
# Check default group
graphiti:get_episodes(last_n=10)
# Result: "No episodes found for group default"

# Check specific groups
graphiti:get_episodes(group_id="company_data", last_n=10)
# Result: "No episodes found for group company_data"

# Search attempts
graphiti:search_memory_facts(query="Acme Corporation", max_facts=5)
# Result: "No relevant facts found"

graphiti:search_memory_nodes(query="John Smith", max_nodes=5)
# Result: "No relevant nodes found"
```

## Potential Root Causes

1. **Background Worker Not Running**: The background processing system may not be active or configured properly
2. **Database Connection Issues**: Episodes may be queued but not persisted due to database connectivity problems
3. **Queue Processing Logic**: The queue processing mechanism may have bugs or be misconfigured
4. **Index Building**: Search indices may not be built or updated after episode processing
5. **Group Management**: Episodes may be processed but stored in unexpected locations

## Recommended Investigation Areas

1. **Check Background Worker Status**
   - Verify if background processing threads/workers are running
   - Check worker logs for processing errors
   - Confirm queue processing configuration

2. **Database Connectivity**
   - Verify database connection and health
   - Check if episodes are being written to database tables
   - Confirm transaction handling and commits

3. **Queue Implementation**
   - Review queue management logic
   - Check for deadlocks or blocking operations
   - Verify queue persistence and recovery

4. **Search Index Management**
   - Confirm search indices are built after episode processing
   - Check index update mechanisms
   - Verify search query implementation

## Environment Information
- **Testing Date**: July 12, 2025
- **Tool Interface**: Claude Desktop MCP integration
- **Episode Queue Position**: All episodes queued at position 1
- **Groups Tested**: default, company_data, customer_support

## Next Steps
1. Enable detailed logging for background processing
2. Check database state and episode storage
3. Verify queue processing mechanisms
4. Test with simplified episode content
5. Review MCP server configuration and initialization