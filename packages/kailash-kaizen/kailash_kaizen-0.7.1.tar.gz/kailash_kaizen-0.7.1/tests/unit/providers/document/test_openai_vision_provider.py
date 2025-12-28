"""
Unit tests for OpenAI Vision provider.

Tests:
- Provider initialization and configuration
- Cost estimation logic
- Availability checking
- Capability reporting
- Mock extraction (real API tested in Tier 2)
"""

import os
from unittest.mock import patch

import pytest
from kaizen.providers.document.base_provider import ExtractionResult
from kaizen.providers.document.openai_vision_provider import OpenAIVisionProvider


class TestOpenAIVisionProviderInit:
    """Tests for OpenAI Vision provider initialization."""

    def test_init_with_api_key(self):
        """Test initialization with explicit API key."""
        provider = OpenAIVisionProvider(api_key="test-openai-key")

        assert provider.provider_name == "openai_vision"
        assert provider.api_key == "test-openai-key"
        assert provider.model == "gpt-4o-mini"

    def test_init_with_env_var(self, monkeypatch):
        """Test initialization with environment variable."""
        monkeypatch.setenv("OPENAI_API_KEY", "env-openai-key")

        provider = OpenAIVisionProvider()

        assert provider.api_key == "env-openai-key"

    def test_init_without_api_key(self):
        """Test initialization without API key."""
        with patch.dict(os.environ, {}, clear=True):
            provider = OpenAIVisionProvider()

            assert provider.api_key is None

    def test_init_with_custom_model(self):
        """Test initialization with custom model."""
        provider = OpenAIVisionProvider(
            api_key="test-key",
            model="gpt-4-vision-preview",
        )

        assert provider.model == "gpt-4-vision-preview"

    def test_cost_per_page_constant(self):
        """Test COST_PER_PAGE constant."""
        assert OpenAIVisionProvider.COST_PER_PAGE == 0.068


class TestOpenAIVisionProviderAvailability:
    """Tests for OpenAI Vision provider availability checking."""

    def test_is_available_with_api_key(self):
        """Test availability when API key is set."""
        provider = OpenAIVisionProvider(api_key="test-key")

        assert provider.is_available() is True

    def test_is_available_without_api_key(self, monkeypatch):
        """Test availability when API key is missing."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        provider = OpenAIVisionProvider(api_key=None)

        assert provider.is_available() is False

    def test_is_available_with_empty_api_key(self, monkeypatch):
        """Test availability with empty string API key."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        provider = OpenAIVisionProvider(api_key="")

        assert provider.is_available() is False


class TestOpenAIVisionProviderCostEstimation:
    """Tests for cost estimation logic."""

    @pytest.mark.asyncio
    async def test_estimate_cost_10_page_pdf(self):
        """Test cost estimation for 10-page PDF."""
        provider = OpenAIVisionProvider(api_key="test-key")

        with patch.object(provider, "_get_page_count", return_value=10):
            cost = await provider.estimate_cost("test.pdf")

        expected_cost = 10 * 0.068  # $0.68
        assert cost == expected_cost

    @pytest.mark.asyncio
    async def test_estimate_cost_1_page_pdf(self):
        """Test cost estimation for 1-page PDF."""
        provider = OpenAIVisionProvider(api_key="test-key")

        with patch.object(provider, "_get_page_count", return_value=1):
            cost = await provider.estimate_cost("test.pdf")

        assert cost == 0.068

    @pytest.mark.asyncio
    async def test_estimate_cost_100_page_pdf(self):
        """Test cost estimation for large document."""
        provider = OpenAIVisionProvider(api_key="test-key")

        with patch.object(provider, "_get_page_count", return_value=100):
            cost = await provider.estimate_cost("test.pdf")

        expected_cost = 100 * 0.068  # $6.80
        assert cost == expected_cost


class TestOpenAIVisionProviderCapabilities:
    """Tests for provider capabilities reporting."""

    def test_get_capabilities_structure(self):
        """Test capabilities dictionary structure."""
        provider = OpenAIVisionProvider(api_key="test-key")

        caps = provider.get_capabilities()

        assert isinstance(caps, dict)
        assert "provider" in caps
        assert "accuracy" in caps
        assert "table_accuracy" in caps
        assert "cost_per_page" in caps
        assert "supports_bounding_boxes" in caps

    def test_get_capabilities_values(self):
        """Test capabilities values."""
        provider = OpenAIVisionProvider(api_key="test-key")

        caps = provider.get_capabilities()

        assert caps["provider"] == "openai_vision"
        assert caps["accuracy"] == 0.95  # 95% accuracy
        assert caps["table_accuracy"] == 0.90  # 90% table accuracy
        assert caps["cost_per_page"] == 0.068
        assert caps["supports_bounding_boxes"] is False  # OpenAI doesn't provide bboxes
        assert caps["supports_tables"] is True
        assert caps["avg_speed_seconds"] == 0.8  # Fastest provider

    def test_get_capabilities_use_cases(self):
        """Test use cases in capabilities."""
        provider = OpenAIVisionProvider(api_key="test-key")

        caps = provider.get_capabilities()

        assert "use_cases" in caps
        assert isinstance(caps["use_cases"], list)


class TestOpenAIVisionProviderExtraction:
    """Tests for extraction method (mock implementation)."""

    @pytest.mark.asyncio
    async def test_extract_basic(self, tmp_path):
        """Test basic extraction without tables or RAG."""
        provider = OpenAIVisionProvider(api_key="test-key")

        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("Mock PDF")

        with patch.object(provider, "_get_page_count", return_value=1):
            result = await provider.extract(
                str(pdf_file),
                "pdf",
                extract_tables=False,
                chunk_for_rag=False,
            )

        assert isinstance(result, ExtractionResult)
        assert result.provider == "openai_vision"
        assert result.cost == 0.068  # 1 page * $0.068
        assert len(result.text) > 0

    @pytest.mark.asyncio
    async def test_extract_with_tables(self, tmp_path):
        """Test extraction with table extraction enabled."""
        provider = OpenAIVisionProvider(api_key="test-key")

        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("Mock PDF")

        with patch.object(provider, "_get_page_count", return_value=1):
            result = await provider.extract(
                str(pdf_file),
                "pdf",
                extract_tables=True,
            )

        assert len(result.tables) > 0

    @pytest.mark.asyncio
    async def test_extract_with_rag_chunks(self, tmp_path):
        """Test extraction with RAG chunking."""
        provider = OpenAIVisionProvider(api_key="test-key")

        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("Mock PDF")

        with patch.object(provider, "_get_page_count", return_value=1):
            result = await provider.extract(
                str(pdf_file),
                "pdf",
                chunk_for_rag=True,
                chunk_size=512,
            )

        assert len(result.chunks) > 0
        assert "chunk_id" in result.chunks[0]
        assert "text" in result.chunks[0]
        assert "page" in result.chunks[0]

    @pytest.mark.asyncio
    async def test_extract_no_bounding_boxes(self, tmp_path):
        """Test that OpenAI Vision does not provide bounding boxes."""
        provider = OpenAIVisionProvider(api_key="test-key")

        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("Mock PDF")

        with patch.object(provider, "_get_page_count", return_value=1):
            result = await provider.extract(
                str(pdf_file),
                "pdf",
                chunk_for_rag=True,
            )

        # OpenAI chunks should not have bounding boxes
        assert len(result.chunks) > 0
        for chunk in result.chunks:
            assert chunk.get("bbox") is None

    @pytest.mark.asyncio
    async def test_extract_invalid_file_type(self, tmp_path):
        """Test extraction with invalid file type."""
        provider = OpenAIVisionProvider(api_key="test-key")

        xlsx_file = tmp_path / "test.xlsx"
        xlsx_file.write_text("Mock Excel")

        with pytest.raises(ValueError, match="Unsupported file type"):
            await provider.extract(str(xlsx_file), "xlsx")

    @pytest.mark.asyncio
    async def test_extract_nonexistent_file(self):
        """Test extraction with nonexistent file."""
        provider = OpenAIVisionProvider(api_key="test-key")

        with pytest.raises(FileNotFoundError):
            await provider.extract("/nonexistent/file.pdf", "pdf")

    @pytest.mark.asyncio
    async def test_extract_cost_calculation(self, tmp_path):
        """Test cost calculation for multi-page document."""
        provider = OpenAIVisionProvider(api_key="test-key")

        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("Mock PDF")

        with patch.object(provider, "_get_page_count", return_value=10):
            result = await provider.extract(str(pdf_file), "pdf")

        expected_cost = 10 * 0.068  # $0.68
        assert result.cost == expected_cost

    @pytest.mark.asyncio
    async def test_extract_metadata(self, tmp_path):
        """Test metadata in extraction result."""
        provider = OpenAIVisionProvider(api_key="test-key")

        pdf_file = tmp_path / "invoice.pdf"
        pdf_file.write_text("Mock PDF")

        with patch.object(provider, "_get_page_count", return_value=3):
            result = await provider.extract(str(pdf_file), "pdf")

        assert "file_name" in result.metadata
        assert result.metadata["file_name"] == "invoice.pdf"
        assert result.metadata["file_type"] == "pdf"
        assert result.metadata["page_count"] == 3
        assert result.metadata["model"] == "gpt-4o-mini"

    @pytest.mark.asyncio
    async def test_extract_processing_time_recorded(self, tmp_path):
        """Test that processing time is recorded."""
        provider = OpenAIVisionProvider(api_key="test-key")

        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("Mock PDF")

        with patch.object(provider, "_get_page_count", return_value=1):
            result = await provider.extract(str(pdf_file), "pdf")

        assert result.processing_time > 0

    @pytest.mark.asyncio
    async def test_extract_markdown_output(self, tmp_path):
        """Test markdown output generation."""
        provider = OpenAIVisionProvider(api_key="test-key")

        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("Mock PDF")

        with patch.object(provider, "_get_page_count", return_value=1):
            result = await provider.extract(str(pdf_file), "pdf")

        assert len(result.markdown) > 0
        assert result.markdown.startswith("#")

    @pytest.mark.asyncio
    async def test_extract_custom_model(self, tmp_path):
        """Test extraction with custom OpenAI model."""
        provider = OpenAIVisionProvider(
            api_key="test-key",
            model="gpt-4-vision-preview",
        )

        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("Mock PDF")

        with patch.object(provider, "_get_page_count", return_value=1):
            result = await provider.extract(str(pdf_file), "pdf")

        assert result.metadata["model"] == "gpt-4-vision-preview"
