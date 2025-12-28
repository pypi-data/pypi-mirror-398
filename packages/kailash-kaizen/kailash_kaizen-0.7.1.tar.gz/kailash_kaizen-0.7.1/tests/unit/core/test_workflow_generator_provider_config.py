"""
Test WorkflowGenerator provider_config preservation.

Verifies that provider_config is passed as nested dict to LLMAgentNode,
not flattened into top-level node_config.

References:
- Bug report: workflow_generator.py was flattening provider_config
- Fix: Preserve provider_config as nested dict for LLMAgentNode
"""

import pytest
from kaizen.core.config import BaseAgentConfig
from kaizen.core.workflow_generator import WorkflowGenerator
from kaizen.signatures import InputField, OutputField, Signature


class SimpleSignature(Signature):
    """Simple test signature."""

    question: str = InputField(desc="Question")
    answer: str = OutputField(desc="Answer")


class TestWorkflowGeneratorProviderConfig:
    """Test provider_config preservation in WorkflowGenerator."""

    def test_provider_config_preserved_as_nested_dict_signature_workflow(self):
        """Test provider_config is preserved as nested dict in signature workflow."""
        # Create config with provider_config
        provider_config = {
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "test",
                    "strict": True,
                    "schema": {"type": "object"},
                },
            }
        }

        config = BaseAgentConfig(
            llm_provider="openai",
            model="gpt-4o-2024-08-06",
            provider_config=provider_config,
        )

        # Generate workflow
        generator = WorkflowGenerator(config=config, signature=SimpleSignature())
        workflow = generator.generate_signature_workflow()

        # Verify workflow structure
        assert workflow.nodes
        assert len(workflow.nodes) == 1

        # Get the LLMAgentNode config
        node_id = list(workflow.nodes.keys())[0]
        node = workflow.nodes[node_id]
        assert node["type"] == "LLMAgentNode"

        # CRITICAL: Verify provider_config is nested, not flattened
        assert "provider_config" in node["config"]
        assert node["config"]["provider_config"] == provider_config

        # Verify response_format is NOT a top-level key (was the bug)
        assert "response_format" not in node["config"]

    def test_provider_config_preserved_as_nested_dict_fallback_workflow(self):
        """Test provider_config is preserved as nested dict in fallback workflow."""
        # Create config with provider_config
        provider_config = {
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "test",
                    "strict": True,
                    "schema": {"type": "object"},
                },
            }
        }

        config = BaseAgentConfig(
            llm_provider="openai",
            model="gpt-4o-2024-08-06",
            provider_config=provider_config,
        )

        # Generate fallback workflow (no signature)
        generator = WorkflowGenerator(config=config)
        workflow = generator.generate_fallback_workflow()

        # Verify workflow structure
        assert workflow.nodes
        assert len(workflow.nodes) == 1

        # Get the LLMAgentNode config
        node_id = list(workflow.nodes.keys())[0]
        node = workflow.nodes[node_id]
        assert node["type"] == "LLMAgentNode"

        # CRITICAL: Verify provider_config is nested, not flattened
        assert "provider_config" in node["config"]
        assert node["config"]["provider_config"] == provider_config

        # Verify response_format is NOT a top-level key (was the bug)
        assert "response_format" not in node["config"]

    def test_empty_provider_config_does_not_add_key(self):
        """Test that empty provider_config doesn't add the key."""
        config = BaseAgentConfig(
            llm_provider="openai",
            model="gpt-4",
            provider_config=None,  # No provider config
        )

        generator = WorkflowGenerator(config=config, signature=SimpleSignature())
        workflow = generator.generate_signature_workflow()

        # Get the node config
        node_id = list(workflow.nodes.keys())[0]
        node = workflow.nodes[node_id]

        # Should not have provider_config key if not provided
        assert "provider_config" not in node["config"]
