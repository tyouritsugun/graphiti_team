import logging
from datetime import datetime
from time import time
from typing import Any

from pydantic import BaseModel

from graphiti_core.graphiti import AddEpisodeResults, Graphiti
from graphiti_core.graphiti_types import GraphitiClients
from graphiti_core.helpers import (
    semaphore_gather,
    validate_excluded_entity_types,
    validate_group_id,
)
from graphiti_core.nodes import EpisodeType, EpisodicNode
from graphiti_core.search.search_config import SearchResults
from graphiti_core.search.search_filters import SearchFilters
from graphiti_core.utils.bulk_utils import (
    add_nodes_and_edges_bulk,
    resolve_edge_pointers,
)
from graphiti_core.utils.datetime_utils import utc_now
from graphiti_core.utils.maintenance.edge_operations import (
    build_duplicate_of_edges,
    build_episodic_edges,
    extract_edges,
    resolve_extracted_edge,
    resolve_extracted_edges,
)
from graphiti_core.search.search_config_recipes import (
    NODE_HYBRID_SEARCH_RRF,
)
from graphiti_core.search.search_utils import RELEVANT_SCHEMA_LIMIT
from graphiti_core.utils.maintenance.node_operations import (
    extract_attributes_from_nodes,
    extract_nodes,
    resolve_extracted_nodes,
)
from graphiti_core.utils.ontology_utils.entity_types_utils import validate_entity_types

logger = logging.getLogger(__name__)


class TeamGraphiti(Graphiti):
    def __init__(self, user_email: str, project_id: str, **kwargs):
        super().__init__(**kwargs)
        self.user_email = user_email
        self.project_id = project_id

    async def add_episode(
        self,
        name: str,
        episode_body: str,
        source_description: str,
        reference_time: datetime,
        source: EpisodeType = EpisodeType.message,
        group_id: str = "",
        uuid: str | None = None,
        update_communities: bool = False,
        entity_types: dict[str, BaseModel] | None = None,
        excluded_entity_types: list[str] | None = None,
        previous_episode_uuids: list[str] | None = None,
        edge_types: dict[str, BaseModel] | None = None,
        edge_type_map: dict[tuple[str, str], list[str]] | None = None,
        knowledge_domain: str | None = None,
        project_id: str | None = None,
    ) -> AddEpisodeResults:
        """
        Process an episode and update the graph.

        This method extracts information from the episode, creates nodes and edges,
        and updates the graph database accordingly.
        """
        try:
            start = time()
            now = utc_now()

            validate_entity_types(entity_types)
            validate_excluded_entity_types(excluded_entity_types, entity_types)
            validate_group_id(group_id)

            previous_episodes = (
                await self.retrieve_episodes(
                    reference_time,
                    last_n=RELEVANT_SCHEMA_LIMIT,
                    group_ids=[group_id],
                    source=source,
                )
                if previous_episode_uuids is None
                else await EpisodicNode.get_by_uuids(self.driver, previous_episode_uuids)
            )

            episode = (
                await EpisodicNode.get_by_uuid(self.driver, uuid)
                if uuid is not None
                else EpisodicNode(
                    name=name,
                    group_id=group_id,
                    labels=[],
                    source=source,
                    content=episode_body,
                    source_description=source_description,
                    created_at=now,
                    valid_at=reference_time,
                )
            )

            # Create default edge type map
            edge_type_map_default = (
                {("Entity", "Entity"): list(edge_types.keys())}
                if edge_types is not None
                else {("Entity", "Entity"): []}
            )

            # Extract entities as nodes

            extracted_nodes = await extract_nodes(
                self.clients, episode, previous_episodes, entity_types, excluded_entity_types
            )

            # Extract edges and resolve nodes
            (nodes, uuid_map, node_duplicates), extracted_edges = await semaphore_gather(
                resolve_extracted_nodes(
                    self.clients,
                    extracted_nodes,
                    episode,
                    previous_episodes,
                    entity_types,
                ),
                extract_edges(
                    self.clients,
                    episode,
                    extracted_nodes,
                    previous_episodes,
                    edge_type_map or edge_type_map_default,
                    group_id,
                    edge_types,
                ),
                max_coroutines=self.max_coroutines,
            )

            edges = resolve_edge_pointers(extracted_edges, uuid_map)

            (resolved_edges, invalidated_edges), hydrated_nodes = await semaphore_gather(
                resolve_extracted_edges(
                    self.clients,
                    edges,
                    episode,
                    nodes,
                    edge_types or {},
                    edge_type_map or edge_type_map_default,
                ),
                extract_attributes_from_nodes(
                    self.clients, nodes, episode, previous_episodes, entity_types
                ),
                max_coroutines=self.max_coroutines,
            )

            duplicate_of_edges = build_duplicate_of_edges(episode, now, node_duplicates)

            entity_edges = resolved_edges + invalidated_edges + duplicate_of_edges

            episodic_edges = build_episodic_edges(nodes, episode.uuid, now)

            episode.entity_edges = [edge.uuid for edge in entity_edges]

            if not self.store_raw_episode_content:
                episode.content = ""

            # Add tags to nodes and edges
            for node in hydrated_nodes:
                node.attributes["user_email"] = self.user_email
                node.attributes["project_id"] = project_id or self.project_id
                if knowledge_domain:
                    node.attributes["knowledge_domain"] = knowledge_domain
                node.attributes["created_at"] = now
                node.attributes["updated_at"] = now

            for edge in entity_edges:
                edge.attributes["user_email"] = self.user_email
                edge.attributes["project_id"] = project_id or self.project_id
                if knowledge_domain:
                    edge.attributes["knowledge_domain"] = knowledge_domain
                edge.attributes["created_at"] = now
                edge.attributes["updated_at"] = now

            await add_nodes_and_edges_bulk(
                self.driver, [episode], episodic_edges, hydrated_nodes, entity_edges, self.embedder
            )

            # Update any communities
            if update_communities:
                await semaphore_gather(
                    *[
                        update_community(self.driver, self.llm_client, self.embedder, node)
                        for node in nodes
                    ],
                    max_coroutines=self.max_coroutines,
                )
            end = time()
            logger.info(f"Completed add_episode in {(end - start) * 1000} ms")

            return AddEpisodeResults(episode=episode, nodes=nodes, edges=entity_edges)

        except Exception as e:
            raise e

    async def search_memory_nodes(
        self,
        query: str,
        group_ids: list[str] | None = None,
        max_nodes: int = 10,
        center_node_uuid: str | None = None,
        user_email: str | None = None,
        knowledge_domain: str | None = None,
        project_id: str | None = None,
    ) -> SearchResults:
        """Search the graph memory for relevant node summaries."""
        search_config = NODE_HYBRID_SEARCH_RRF.model_copy(deep=True)
        search_config.limit = max_nodes

        filters = SearchFilters()
        node_attributes = {}
        if user_email:
            node_attributes["user_email"] = user_email
        if knowledge_domain:
            node_attributes["knowledge_domain"] = knowledge_domain
        if project_id:
            node_attributes["project_id"] = project_id
        
        if node_attributes:
            filters.node_attributes = node_attributes

        return await self.search_(
            query=query,
            config=search_config,
            group_ids=group_ids,
            center_node_uuid=center_node_uuid,
            search_filter=filters,
        )

    async def remove_by_tags(self, tags: dict[str, Any]):
        """Remove nodes and edges by tags."""
        match_clauses = []
        params = {}
        for i, (key, value) in enumerate(tags.items()):
            param_name = f"value{i}"
            match_clauses.append(f"n.{key} = ${param_name}")
            params[param_name] = value

        query = f"""
        MATCH (n)
        WHERE {' AND '.join(match_clauses)}
        DETACH DELETE n
        """

        await self.driver.execute_query(query, **params)
