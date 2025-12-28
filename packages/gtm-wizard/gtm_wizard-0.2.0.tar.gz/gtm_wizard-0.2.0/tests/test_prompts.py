"""Tests for GTM Wizard MCP prompts."""

import pytest
from mcp.types import GetPromptResult, Prompt


class TestListPrompts:
    """Tests for prompt listing functionality."""

    @pytest.mark.asyncio
    async def test_list_prompts_returns_all_prompts(self, list_prompts_handler):
        """Test that list_prompts returns all 4 GTM prompts."""
        prompts = await list_prompts_handler()

        assert len(prompts) == 4
        assert all(isinstance(p, Prompt) for p in prompts)

    @pytest.mark.asyncio
    async def test_prompts_have_required_metadata(self, list_prompts_handler):
        """Test that all prompts have name and description."""
        prompts = await list_prompts_handler()

        for prompt in prompts:
            assert prompt.name is not None
            assert prompt.description is not None
            assert len(prompt.description) > 0

    @pytest.mark.asyncio
    async def test_expected_prompts_exist(self, list_prompts_handler):
        """Test that expected prompts are listed."""
        prompts = await list_prompts_handler()
        names = [p.name for p in prompts]

        expected = [
            "lead-qualification-workflow",
            "icp-definition",
            "outbound-campaign-design",
            "lead-scoring-calibration",
        ]

        for expected_name in expected:
            assert expected_name in names

    @pytest.mark.asyncio
    async def test_prompts_have_arguments(self, list_prompts_handler):
        """Test that prompts have argument definitions."""
        prompts = await list_prompts_handler()

        for prompt in prompts:
            assert prompt.arguments is not None
            assert len(prompt.arguments) > 0


class TestGetPrompt:
    """Tests for prompt retrieval functionality."""

    @pytest.mark.asyncio
    async def test_get_lead_qualification_workflow(self, get_prompt_handler):
        """Test getting lead-qualification-workflow prompt."""
        result = await get_prompt_handler("lead-qualification-workflow", None)

        assert isinstance(result, GetPromptResult)
        assert len(result.messages) > 0
        content = result.messages[0].content.text
        assert "Qualify" in content
        assert "Disqualification" in content
        assert "QUALIFICATION RESULT" in content

    @pytest.mark.asyncio
    async def test_get_lead_qualification_with_args(self, get_prompt_handler):
        """Test lead-qualification-workflow with arguments."""
        result = await get_prompt_handler(
            "lead-qualification-workflow",
            {
                "lead_email": "test@example.com",
                "lead_title": "VP of Sales",
                "company_name": "Acme Corp",
            },
        )

        content = result.messages[0].content.text
        assert "test@example.com" in content
        assert "VP of Sales" in content
        assert "Acme Corp" in content

    @pytest.mark.asyncio
    async def test_get_icp_definition(self, get_prompt_handler):
        """Test getting icp-definition prompt."""
        result = await get_prompt_handler("icp-definition", None)

        assert isinstance(result, GetPromptResult)
        content = result.messages[0].content.text
        assert "ICP" in content
        assert "ICP_CONFIG" in content
        assert "industries" in content

    @pytest.mark.asyncio
    async def test_get_icp_definition_with_args(self, get_prompt_handler):
        """Test icp-definition with arguments."""
        result = await get_prompt_handler(
            "icp-definition",
            {
                "product_description": "CRM software",
                "current_customers": "SaaS companies",
            },
        )

        content = result.messages[0].content.text
        assert "CRM software" in content
        assert "SaaS companies" in content

    @pytest.mark.asyncio
    async def test_get_outbound_campaign_design(self, get_prompt_handler):
        """Test getting outbound-campaign-design prompt."""
        result = await get_prompt_handler("outbound-campaign-design", None)

        assert isinstance(result, GetPromptResult)
        content = result.messages[0].content.text
        assert "Campaign" in content
        assert "CAMPAIGN_BLUEPRINT" in content
        assert "sequence" in content

    @pytest.mark.asyncio
    async def test_get_outbound_campaign_with_args(self, get_prompt_handler):
        """Test outbound-campaign-design with arguments."""
        result = await get_prompt_handler(
            "outbound-campaign-design",
            {
                "campaign_goal": "Book demos",
                "target_persona": "Marketing managers",
            },
        )

        content = result.messages[0].content.text
        assert "Book demos" in content
        assert "Marketing managers" in content

    @pytest.mark.asyncio
    async def test_get_lead_scoring_calibration(self, get_prompt_handler):
        """Test getting lead-scoring-calibration prompt."""
        result = await get_prompt_handler("lead-scoring-calibration", None)

        assert isinstance(result, GetPromptResult)
        content = result.messages[0].content.text
        assert "Calibrate" in content
        assert "SCORING_CALIBRATION" in content
        assert "weight_adjustments" in content

    @pytest.mark.asyncio
    async def test_get_lead_scoring_with_args(self, get_prompt_handler):
        """Test lead-scoring-calibration with arguments."""
        result = await get_prompt_handler(
            "lead-scoring-calibration",
            {
                "current_conversion_rate": "5%",
                "pain_points": "Too many false positives",
            },
        )

        content = result.messages[0].content.text
        assert "5%" in content
        assert "Too many false positives" in content

    @pytest.mark.asyncio
    async def test_unknown_prompt_raises(self, get_prompt_handler):
        """Test that unknown prompt raises ValueError."""
        with pytest.raises(ValueError, match="Unknown prompt"):
            await get_prompt_handler("nonexistent-prompt", None)
