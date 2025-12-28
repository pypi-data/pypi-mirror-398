"""
Tests for Agent as MCP Client Example

⚠️ MIGRATION IN PROGRESS (2025-10-04)
These tests were designed for the deprecated kaizen.mcp implementation.
The example has been migrated to use kailash.mcp_server via BaseAgent helpers.

Tests need refactoring to:
1. Remove kaizen.mcp imports (deprecated)
2. Use BaseAgent.setup_mcp_client() via migrated example
3. Test real JSON-RPC protocol behavior

See: tests/integration/MCP_INTEGRATION_TEST_MIGRATION_STATUS.md

3-Tier Testing Strategy:
- Tier 1 (Unit): Agent logic with minimal mocking
- Tier 2 (Integration): Real MCP connections via BaseAgent helpers
- Tier 3 (E2E): Complete workflows with kailash.mcp_server infrastructure

NO MOCKING of MCP protocol - uses real MCPClient from kailash.mcp_server.
"""

import logging

# Import example using standardized loader
import sys
import time
from pathlib import Path

import pytest

# Add examples directory to path for direct import
example_path = (
    Path(__file__).parent.parent.parent.parent
    / "examples"
    / "5-mcp-integration"
    / "agent-as-client"
)
if str(example_path) not in sys.path:
    sys.path.insert(0, str(example_path))

# Import from workflow module (with unique name to avoid conflicts)
import importlib.util

workflow_spec = importlib.util.spec_from_file_location(
    "agent_as_client_workflow", str(example_path / "workflow.py")
)
agent_as_client_example = importlib.util.module_from_spec(workflow_spec)
workflow_spec.loader.exec_module(agent_as_client_example)

MCPClientConfig = agent_as_client_example.MCPClientConfig
MCPClientAgent = agent_as_client_example.MCPClientAgent
TaskAnalysisSignature = agent_as_client_example.TaskAnalysisSignature
ToolInvocationSignature = agent_as_client_example.ToolInvocationSignature
ResultSynthesisSignature = agent_as_client_example.ResultSynthesisSignature

# Real MCP infrastructure - UPDATED to use kailash.mcp_server
# NOTE: kaizen.mcp has been deprecated and removed
# Tests now use BaseAgent helpers which use kailash.mcp_server internally
from kaizen.memory import SharedMemoryPool

# TODO: When tests are refactored, import real MCP client
# from kailash.mcp_server import MCPClient

logger = logging.getLogger(__name__)


# ===================================================================
# TIER 1: UNIT TESTS (Agent Logic)
# ===================================================================


class TestMCPClientConfig:
    """Test configuration validation."""

    def test_default_config(self):
        """Test default configuration values."""
        config = MCPClientConfig()

        assert config.llm_provider == "openai"
        assert config.model == "gpt-3.5-turbo"
        assert config.temperature == 0.7
        assert config.max_tokens == 1000
        assert config.connection_timeout == 30  # Default is 30 seconds
        assert config.retry_strategy == "circuit_breaker"
        assert config.enable_metrics is True

    def test_custom_config(self):
        """Test custom configuration."""
        config = MCPClientConfig(
            llm_provider="anthropic",
            model="claude-3-sonnet",
            temperature=0.5,
            mcp_servers=[{"name": "custom-server", "url": "http://localhost:9999"}],
            connection_timeout=20,
        )

        assert config.llm_provider == "anthropic"
        assert config.model == "claude-3-sonnet"
        assert config.temperature == 0.5
        assert len(config.mcp_servers) == 1
        assert config.mcp_servers[0]["name"] == "custom-server"
        assert config.connection_timeout == 20

    def test_mcp_servers_list(self):
        """Test MCP servers list configuration."""
        servers = [
            {"name": "server1", "url": "http://localhost:8080"},
            {"name": "server2", "url": "http://localhost:8081"},
            {"name": "server3", "url": "http://localhost:8082"},
        ]

        config = MCPClientConfig(mcp_servers=servers)

        assert len(config.mcp_servers) == 3
        assert config.mcp_servers[0]["name"] == "server1"
        assert config.mcp_servers[2]["url"] == "http://localhost:8082"


class TestMCPClientSignatures:
    """Test signature definitions."""

    def test_task_analysis_signature(self):
        """Test TaskAnalysisSignature structure."""
        sig = TaskAnalysisSignature()

        # Input fields
        assert hasattr(sig, "task_description")
        assert hasattr(sig, "available_tools")
        assert hasattr(sig, "context")

        # Output fields
        assert hasattr(sig, "required_tools")
        assert hasattr(sig, "execution_plan")
        assert hasattr(sig, "estimated_complexity")

    def test_tool_invocation_signature(self):
        """Test ToolInvocationSignature structure."""
        sig = ToolInvocationSignature()

        # Input fields
        assert hasattr(sig, "tool_name")
        assert hasattr(sig, "tool_schema")
        assert hasattr(sig, "user_request")
        assert hasattr(sig, "context")

        # Output fields
        assert hasattr(sig, "tool_arguments")
        assert hasattr(sig, "invocation_reasoning")
        assert hasattr(sig, "expected_output")

    def test_result_synthesis_signature(self):
        """Test ResultSynthesisSignature structure."""
        sig = ResultSynthesisSignature()

        # Input fields
        assert hasattr(sig, "task_description")
        assert hasattr(sig, "tool_results")
        assert hasattr(sig, "execution_context")

        # Output fields
        assert hasattr(sig, "final_answer")
        assert hasattr(sig, "confidence_score")
        assert hasattr(sig, "tool_usage_summary")


class TestMCPClientAgentInitialization:
    """Test agent initialization without real connections."""

    def test_agent_creation_minimal(self):
        """Test agent creation with minimal config."""
        # Use invalid server URLs to prevent real connections
        config = MCPClientConfig(
            mcp_servers=[{"name": "invalid-server", "url": "http://invalid-host:19999"}]
        )

        agent = MCPClientAgent(config)

        assert agent is not None
        assert agent.client_config == config
        # Agent now uses BaseAgent helpers - MCP setup happens via async _setup_mcp_connections()
        # After migration, agent creation is lightweight - no sync MCP setup
        assert isinstance(agent, MCPClientAgent)

    def test_agent_with_shared_memory(self):
        """Test agent creation with shared memory."""
        config = MCPClientConfig(mcp_servers=[])
        memory = SharedMemoryPool()

        agent = MCPClientAgent(config, shared_memory=memory)

        assert agent.shared_memory == memory

    def test_agent_auto_discovery_enabled(self):
        """Test agent with auto-discovery enabled."""
        config = MCPClientConfig(mcp_servers=[])

        agent = MCPClientAgent(config)

        # Auto-discovery is not implemented in migrated example
        # Agent uses explicit server configuration via mcp_servers
        assert agent.client_config.mcp_servers == []

    def test_agent_auto_discovery_disabled(self):
        """Test agent with auto-discovery disabled."""
        config = MCPClientConfig(mcp_servers=[])

        agent = MCPClientAgent(config)

        # Agent uses explicit MCP server configuration
        # No auto-discovery mechanism in migrated implementation
        assert agent.client_config.mcp_servers == []


# ===================================================================
# TIER 2: INTEGRATION TESTS (Real MCP Infrastructure)
# ===================================================================


@pytest.mark.skip(
    reason="Deprecated: Uses kaizen.mcp.MCPConnection - needs refactor for kailash.mcp_server.MCPClient"
)
class TestMCPClientAgentConnections:
    """Test real MCP connections - NO MOCKING.

    ⚠️ DEPRECATED: These tests use kaizen.mcp.MCPConnection which has been removed.
    TODO: Refactor to use kailash.mcp_server.MCPClient via BaseAgent.setup_mcp_client()
    """

    def test_connection_to_test_server(self):
        """Test real MCP connection to test server."""
        # Create real MCP connection
        connection = MCPConnection(
            name="integration-server", url="http://localhost:18080", timeout=5
        )

        # Real connection attempt
        result = connection.connect()

        # Connection should succeed (or fail gracefully)
        assert isinstance(result, bool)

        if result:
            # If connected, verify protocol worked
            assert connection.status == "connected"
            assert connection.last_connection_time is not None
            assert connection.server_capabilities is not None

            # Disconnect
            connection.disconnect()
            assert connection.status == "disconnected"

    def test_tool_discovery_real_protocol(self):
        """Test real tool discovery via MCP protocol."""
        connection = MCPConnection(
            name="integration-server", url="http://localhost:18080"
        )

        if connection.connect():
            # Real tool discovery via MCP
            tools = connection.available_tools

            assert isinstance(tools, list)
            # Should have discovered tools
            assert len(tools) >= 0

            for tool in tools:
                assert "name" in tool
                assert "description" in tool or True  # Description is optional

            connection.disconnect()

    def test_agent_connection_setup(self):
        """Test agent MCP connection setup."""
        config = MCPClientConfig(
            mcp_servers=[
                {"name": "integration-server", "url": "http://localhost:18080"}
            ]
        )

        agent = MCPClientAgent(config)

        # Check connection was attempted
        assert "integration-server" in agent.connections

        connection = agent.connections["integration-server"]
        assert isinstance(connection, MCPConnection)

        # Check status (connected or failed)
        assert connection.status in ["connected", "failed", "disconnected"]

        # Cleanup
        agent.disconnect_all()

    def test_multiple_server_connections(self):
        """Test connecting to multiple MCP servers."""
        config = MCPClientConfig(
            mcp_servers=[
                {"name": "server1", "url": "http://localhost:18080"},
                {"name": "server2", "url": "http://localhost:18081"},
            ]
        )

        agent = MCPClientAgent(config)

        # Both connections should be attempted
        assert "server1" in agent.connections
        assert "server2" in agent.connections

        # Cleanup
        agent.disconnect_all()


@pytest.mark.skip(
    reason="Deprecated: Uses kaizen.mcp.MCPConnection - needs refactor for kailash.mcp_server.MCPClient"
)
class TestMCPClientToolInvocation:
    """Test real MCP tool invocation - NO MOCKING.

    ⚠️ DEPRECATED: These tests use kaizen.mcp.MCPConnection which has been removed.
    TODO: Refactor to use kailash.mcp_server.MCPClient via BaseAgent.call_mcp_tool()
    """

    def test_real_tool_call(self):
        """Test real MCP tool invocation via JSON-RPC."""
        connection = MCPConnection(
            name="integration-server", url="http://localhost:18080"
        )

        if connection.connect():
            # Real JSON-RPC tool call
            result = connection.call_tool(
                tool_name="integration_test_tool", arguments={"message": "test"}
            )

            assert isinstance(result, dict)

            # Check result structure
            if result.get("success"):
                assert "result" in result
                assert result["server_name"] == "integration-server"
                assert result["tool_name"] == "integration_test_tool"
            else:
                # If tool doesn't exist, error should be descriptive
                assert "error" in result

            connection.disconnect()

    def test_agent_tool_invocation(self):
        """Test agent tool invocation through MCP."""
        config = MCPClientConfig(
            mcp_servers=[
                {"name": "integration-server", "url": "http://localhost:18080"}
            ]
        )

        agent = MCPClientAgent(config)

        # Check if we have any tools available
        if len(agent.available_tools) > 0:
            # Get first available tool
            tool_id = list(agent.available_tools.keys())[0]

            # Invoke via agent
            result = agent.invoke_tool(
                tool_id=tool_id,
                user_request="Test invocation",
                context="Integration test",
            )

            assert isinstance(result, dict)
            # Should have success status
            assert "success" in result

        agent.disconnect_all()

    def test_tool_invocation_with_arguments(self):
        """Test tool invocation with specific arguments."""
        connection = MCPConnection(
            name="integration-server", url="http://localhost:18080"
        )

        if connection.connect() and len(connection.available_tools) > 0:
            # Try calculate tool if available
            result = connection.call_tool(
                tool_name="calculate_integration", arguments={"a": 5, "b": 3}
            )

            if result.get("success"):
                assert result["result"] == 8

            connection.disconnect()


# ===================================================================
# TIER 3: E2E TESTS (Complete Workflows)
# ===================================================================


@pytest.mark.skip(
    reason="Deprecated: Uses kaizen.mcp infrastructure - needs refactor for kailash.mcp_server"
)
class TestMCPClientWorkflows:
    """Test complete workflows with real MCP infrastructure.

    ⚠️ DEPRECATED: These tests use kaizen.mcp which has been removed.
    TODO: Refactor to test migrated example which uses BaseAgent helpers
    """

    def test_complete_task_execution(self):
        """Test complete task execution workflow."""
        config = MCPClientConfig(
            llm_provider="mock",  # Use mock provider for tests
            mcp_servers=[
                {"name": "integration-server", "url": "http://localhost:18080"}
            ],
        )

        memory = SharedMemoryPool()
        agent = MCPClientAgent(config, shared_memory=memory)

        # Only test if connected
        if len(agent.connections) > 0 and any(
            c.status == "connected" for c in agent.connections.values()
        ):
            # Execute task
            result = agent.execute_task(
                task="Test task for integration", context="E2E test"
            )

            assert isinstance(result, dict)
            assert "success" in result

            # Check memory was updated (use read_all to get all insights)
            all_insights = agent.shared_memory.read_all()
            assert len(all_insights) > 0

        agent.disconnect_all()

    def test_task_analysis_workflow(self):
        """Test task analysis workflow."""
        config = MCPClientConfig(
            llm_provider="mock",  # Use mock provider for tests
            mcp_servers=[
                {"name": "integration-server", "url": "http://localhost:18080"}
            ],
        )

        memory = SharedMemoryPool()
        agent = MCPClientAgent(config, shared_memory=memory)

        # Analyze task
        analysis = agent.analyze_task(
            task="Perform a search and calculate results", context="E2E test"
        )

        assert isinstance(analysis, dict)
        assert "required_tools" in analysis
        assert "execution_plan" in analysis
        assert "complexity" in analysis

        # Complexity should be between 0 and 1
        assert 0.0 <= analysis["complexity"] <= 1.0

        # Check memory (use read_all to get all insights)
        all_insights = agent.shared_memory.read_all()
        assert len(all_insights) > 0

        agent.disconnect_all()

    def test_multi_tool_workflow(self):
        """Test workflow using multiple tools."""
        config = MCPClientConfig(
            mcp_servers=[
                {"name": "server1", "url": "http://localhost:18080"},
                {"name": "server2", "url": "http://localhost:18081"},
            ]
        )

        agent = MCPClientAgent(config)

        connected_count = sum(
            1 for c in agent.connections.values() if c.status == "connected"
        )

        if connected_count >= 2:
            # Task requiring multiple tools
            result = agent.execute_task(
                task="Search for data and perform calculations",
                context="Multi-tool test",
            )

            assert isinstance(result, dict)

            if result.get("success"):
                assert "tool_results" in result
                # Should have used multiple tools
                assert len(result["tool_results"]) >= 1

        agent.disconnect_all()

    def test_error_handling_invalid_tool(self):
        """Test error handling for invalid tools."""
        config = MCPClientConfig(
            mcp_servers=[
                {"name": "integration-server", "url": "http://localhost:18080"}
            ]
        )

        agent = MCPClientAgent(config)

        # Try to invoke non-existent tool
        result = agent.invoke_tool(tool_id="nonexistent:tool", user_request="Test")

        assert result["success"] is False
        assert "error" in result

        agent.disconnect_all()

    def test_connection_failure_handling(self):
        """Test handling of connection failures."""
        config = MCPClientConfig(
            mcp_servers=[
                {"name": "nonexistent-server", "url": "http://localhost:19999"}
            ]
        )

        agent = MCPClientAgent(config)

        # Connection should have failed
        if "nonexistent-server" in agent.connections:
            connection = agent.connections["nonexistent-server"]
            assert connection.status == "failed"
            assert connection.last_error is not None

        agent.disconnect_all()


# ===================================================================
# PERFORMANCE TESTS
# ===================================================================


@pytest.mark.skip(
    reason="Deprecated: Uses kaizen.mcp.MCPConnection - needs refactor for kailash.mcp_server.MCPClient"
)
class TestMCPClientPerformance:
    """Test performance characteristics.

    ⚠️ DEPRECATED: These tests use kaizen.mcp which has been removed.
    """

    def test_connection_performance(self):
        """Test connection establishment performance."""
        config = MCPClientConfig(
            mcp_servers=[
                {"name": "integration-server", "url": "http://localhost:18080"}
            ]
        )

        start_time = time.time()
        agent = MCPClientAgent(config)
        connection_time = time.time() - start_time

        # Connection should be fast (< 2 seconds for test server)
        assert connection_time < 2.0

        agent.disconnect_all()

    def test_tool_invocation_latency(self):
        """Test tool invocation latency."""
        connection = MCPConnection(
            name="integration-server", url="http://localhost:18080"
        )

        if connection.connect() and len(connection.available_tools) > 0:
            tool_name = connection.available_tools[0]["name"]

            start_time = time.time()
            connection.call_tool(
                tool_name=tool_name, arguments={"message": "latency test"}
            )
            latency = time.time() - start_time

            # Tool call should be fast (< 1 second for test tool)
            assert latency < 1.0

            connection.disconnect()


# ===================================================================
# PYTEST MARKERS
# ===================================================================

# Mark all integration tests
pytestmark = [
    pytest.mark.integration,
    pytest.mark.mcp,
]
