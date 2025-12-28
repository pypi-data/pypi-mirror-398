"""Tests for GTM Wizard MCP resources."""

import pytest
from mcp.types import Resource, TextResourceContents


class TestListResources:
    """Tests for resource listing functionality."""

    @pytest.mark.asyncio
    async def test_list_resources_returns_foundation_resources(self, list_resources_handler):
        """Test that list_resources returns all foundation resources."""
        resources = await list_resources_handler()

        assert len(resources) == 5
        assert all(isinstance(r, Resource) for r in resources)

    @pytest.mark.asyncio
    async def test_resources_have_gtm_uri_scheme(self, list_resources_handler):
        """Test that all resources use the gtm:// URI scheme."""
        resources = await list_resources_handler()

        for resource in resources:
            assert str(resource.uri).startswith("gtm://foundations/")

    @pytest.mark.asyncio
    async def test_resources_have_required_metadata(self, list_resources_handler):
        """Test that all resources have name, description, and mimeType."""
        resources = await list_resources_handler()

        for resource in resources:
            assert resource.name is not None
            assert resource.description is not None
            assert resource.mimeType == "text/markdown"

    @pytest.mark.asyncio
    async def test_expected_resources_exist(self, list_resources_handler):
        """Test that expected foundation resources are listed."""
        resources = await list_resources_handler()
        uris = [str(r.uri) for r in resources]

        expected = [
            "gtm://foundations/what-is-gtm-engineering",
            "gtm://foundations/gtm-archetypes",
            "gtm://foundations/context-factors",
            "gtm://foundations/principles-not-recipes",
            "gtm://foundations/knowledge-taxonomy",
        ]

        for expected_uri in expected:
            assert expected_uri in uris


class TestReadResource:
    """Tests for resource reading functionality."""

    @pytest.mark.asyncio
    async def test_read_valid_resource(self, read_resource_handler):
        """Test reading a valid foundation resource."""
        result = await read_resource_handler("gtm://foundations/what-is-gtm-engineering")

        assert isinstance(result, TextResourceContents)
        assert result.mimeType == "text/markdown"
        assert len(result.text) > 0
        assert "GTM Engineer" in result.text

    @pytest.mark.asyncio
    async def test_read_all_foundation_resources(self, read_resource_handler):
        """Test that all foundation resources can be read."""
        resource_ids = [
            "what-is-gtm-engineering",
            "gtm-archetypes",
            "context-factors",
            "principles-not-recipes",
            "knowledge-taxonomy",
        ]

        for resource_id in resource_ids:
            uri = f"gtm://foundations/{resource_id}"
            result = await read_resource_handler(uri)
            assert isinstance(result, TextResourceContents)
            assert len(result.text) > 100  # Should have meaningful content

    @pytest.mark.asyncio
    async def test_read_invalid_uri_scheme_raises(self, read_resource_handler):
        """Test that invalid URI scheme raises ValueError."""
        with pytest.raises(ValueError, match="Invalid URI scheme"):
            await read_resource_handler("http://example.com/resource")

    @pytest.mark.asyncio
    async def test_read_invalid_uri_format_raises(self, read_resource_handler):
        """Test that invalid URI format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid URI format"):
            await read_resource_handler("gtm://invalid")

    @pytest.mark.asyncio
    async def test_read_unknown_resource_raises(self, read_resource_handler):
        """Test that unknown resource URI raises ValueError."""
        with pytest.raises(ValueError, match="Unknown resource"):
            await read_resource_handler("gtm://foundations/nonexistent-resource")

    @pytest.mark.asyncio
    async def test_read_unknown_resource_type_raises(self, read_resource_handler):
        """Test that unknown resource type raises ValueError."""
        with pytest.raises(ValueError, match="Unknown resource"):
            await read_resource_handler("gtm://other/some-resource")
