# Debugging Summary: `add_memory` Background Processing Failure

## 1. Summary of the Bug

As detailed in the [initial bug report](./graphiti_bug_report01.md), the `add_memory` tool successfully queues episodes for background processing, but the processing fails silently. This results in no new data being added to the knowledge graph, causing subsequent search and retrieval operations to return empty.

The root of the problem appears to be an unhandled exception within the background worker task, which causes it to terminate prematurely.

## 2. Implementation Goal

Our goal is to correctly implement the tagging feature as specified in the [Phase 1 Spec](./phase_1_spec.md). This involves:
1.  Creating a `TeamGraphiti` class that inherits from `graphiti_core.graphiti.Graphiti`.
2.  Overriding the `add_episode` method to inject new attributes (`user_email`, `project_id`, `knowledge_domain`, `created_at`, `updated_at`) onto the nodes and edges before they are saved to the database.
3.  The new attributes must be added just before the call to `add_nodes_and_edges_bulk` at the end of the method.

## 3. The Core Problem

When we implement the overridden `add_episode` method in `TeamGraphiti` and add the new attributes, the `add_nodes_and_edges_bulk` function fails with the following error:

**`TypeError: Object of type DateTime is not JSON serializable`**

This error occurs because the underlying Neo4j driver used by `add_nodes_and_edges_bulk` does not automatically serialize `datetime` objects when they are part of the `attributes` dictionary on a node or edge.

## 4. The Debugging Journey: What We've Tried

Our path to identifying this core problem was iterative:

1.  **Initial State**: The bug was opaque, only manifesting as a silent failure of the background worker.
2.  **Logging**: We added extensive logging to `graphiti_mcp_server.py`. This was crucial as it revealed the first concrete error message from the background task.
3.  **Reverting to Isolate**: Following a suggestion, we reverted `TeamGraphiti` to a minimal class that inherited directly from `Graphiti` without any overrides. **This worked perfectly.** This test proved that the `graphiti-core` library is stable and the issue lies entirely within our modifications.
4.  **Incremental Re-implementation**:
    *   We restored the overridden `add_episode` method in `TeamGraphiti` but with our new tagging logic commented out. The process failed again.
    *   This was a key finding: the simple act of overriding the method, even with identical code, was causing a failure. This pointed towards a subtle issue with inheritance or how arguments were being passed.
5.  **Wrapper Approach**: We attempted to avoid overriding by creating a new method (`add_tagged_episode`) that called `super().add_episode()` and then tried to modify the results. This failed because the data was already committed to the database by the `super()` call, and we were trying to re-save it.
6.  **Final Approach & Current Error**: We returned to the full override model, as it's the only one that allows us to modify data *before* it's saved. We correctly identified that all logic must happen before the single `add_nodes_and_edges_bulk` call. When we added our tagging logic at this point, we encountered the `DateTime is not JSON serializable` error.

## 5. Request for Help

We have a clear understanding of the error, but we're struggling with the correct way to solve it within the existing `graphiti-core` framework.

- **What is the canonical way to handle `datetime` objects in node/edge attributes before they are passed to `add_nodes_and_edges_bulk`?**
- Our latest attempt involved converting the `datetime` objects to ISO 8601 strings (`now.isoformat()`), but this still resulted in the same serialization error.
- Is there a specific serialization utility function within `graphiti-core` that we are meant to use? We found a `convert_datetimes_to_strings` function in the FalkorDB driver, but it's not clear if that's intended for general use with the Neo4j driver.

Any insight into the expected data format for the `attributes` dictionary would be greatly appreciated. The relevant code is in `mcp_server/team/graphiti_team.py`.
