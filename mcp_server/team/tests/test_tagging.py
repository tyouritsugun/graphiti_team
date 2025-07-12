import pytest
from graphiti_core.driver.driver import GraphDriver
from graphiti_core.llm_client import LLMClient
from graphiti_core.embedder import EmbedderClient
from graphiti_core.cross_encoder.client import CrossEncoderClient
from graphiti_core.graphiti_types import GraphitiClients
from mcp_server.team.graphiti_team import TeamGraphiti

@pytest.fixture
def graphiti_clients(mocker):
    return GraphitiClients(
        driver=mocker.create_autospec(GraphDriver),
        llm_client=mocker.create_autospec(LLMClient),
        embedder=mocker.create_autospec(EmbedderClient),
        cross_encoder=mocker.create_autospec(CrossEncoderClient),
    )

@pytest.fixture
def team_graphiti(graphiti_clients):
    return TeamGraphiti(
        user_email="test@example.com",
        project_id="test_project",
        graph_driver=graphiti_clients.driver,
        llm_client=graphiti_clients.llm_client,
        embedder=graphiti_clients.embedder,
        cross_encoder=graphiti_clients.cross_encoder,
    )

@pytest.mark.asyncio
async def test_add_memory_with_tags(team_graphiti, mocker):
    # Mock the necessary methods
    mocker.patch.object(team_graphiti, "retrieve_episodes", return_value=[])
    mocker.patch("mcp_server.team.graphiti_team.extract_nodes", return_value=[])
    mocker.patch("mcp_server.team.graphiti_team.resolve_extracted_nodes", return_value=([], {}, []))
    mocker.patch("mcp_server.team.graphiti_team.extract_edges", return_value=[])
    mocker.patch("mcp_server.team.graphiti_team.resolve_extracted_edges", return_value=([], []))
    mocker.patch("mcp_server.team.graphiti_team.extract_attributes_from_nodes", return_value=[])
    add_nodes_and_edges_bulk_mock = mocker.patch("mcp_server.team.graphiti_team.add_nodes_and_edges_bulk")

    await team_graphiti.add_episode(
        name="test_episode",
        episode_body="test body",
        source_description="test source",
        reference_time=mocker.MagicMock(),
        knowledge_domain="project_specific",
        project_id="test_project_2",
    )

    # Get the call arguments for add_nodes_and_edges_bulk
    call_args = add_nodes_and_edges_bulk_mock.call_args.kwargs
    hydrated_nodes = call_args.get("entity_nodes", [])
    entity_edges = call_args.get("entity_edges", [])

    if hydrated_nodes:
        for node in hydrated_nodes:
            assert node.attributes["user_email"] == "test@example.com"
            assert node.attributes["project_id"] == "test_project_2"
            assert node.attributes["knowledge_domain"] == "project_specific"
            assert "created_at" in node.attributes
            assert "updated_at" in node.attributes

    if entity_edges:
        for edge in entity_edges:
            assert edge.attributes["user_email"] == "test@example.com"
            assert edge.attributes["project_id"] == "test_project_2"
            assert edge.attributes["knowledge_domain"] == "project_specific"
            assert "created_at" in edge.attributes
            assert "updated_at" in edge.attributes

@pytest.mark.asyncio
async def test_search_memory_nodes_filtering(team_graphiti, mocker):
    mocker.patch.object(team_graphiti, "search_")

    await team_graphiti.search_memory_nodes(
        query="test query",
        user_email="test@example.com",
        knowledge_domain="coding_conventions",
        project_id="test_project",
    )

    call_args = team_graphiti.search_.call_args.kwargs
    search_filter = call_args["search_filter"]

    assert search_filter.node_attributes["user_email"] == "test@example.com"
    assert search_filter.node_attributes["knowledge_domain"] == "coding_conventions"
    assert search_filter.node_attributes["project_id"] == "test_project"

@pytest.mark.asyncio
async def test_remove_by_tags(team_graphiti, mocker):
    team_graphiti.driver.execute_query = mocker.AsyncMock()
    await team_graphiti.remove_by_tags({"project_id": "test_project"})

    team_graphiti.driver.execute_query.assert_called_once_with(
        mocker.ANY, value0="test_project"
    )
    # Get the query from the call arguments
    query = team_graphiti.driver.execute_query.call_args[0][0]
    assert "MATCH (n)" in query
    assert "WHERE n.project_id = $value0" in query
    assert "DETACH DELETE n" in query

@pytest.mark.asyncio
async def test_backward_compatibility_search(team_graphiti, mocker):
    mocker.patch.object(team_graphiti, "search_")

    await team_graphiti.search_memory_nodes(query="test query")

    call_args = team_graphiti.search_.call_args.kwargs
    search_filter = call_args["search_filter"]

    assert not search_filter.node_labels
    assert not search_filter.edge_types
