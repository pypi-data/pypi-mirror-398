"""Tests for GTM Wizard MCP tools."""

import pytest
from mcp.types import TextContent


class TestListTools:
    """Tests for tool listing functionality."""

    @pytest.mark.asyncio
    async def test_list_tools_returns_expected_tools(self, list_tools_handler):
        """Test that list_tools returns all expected tools."""
        tools = await list_tools_handler()

        tool_names = [t.name for t in tools]
        assert "diagnose_rate_limiting" in tool_names

    @pytest.mark.asyncio
    async def test_diagnose_rate_limiting_has_correct_schema(self, list_tools_handler):
        """Test that diagnose_rate_limiting tool has correct input schema."""
        tools = await list_tools_handler()
        tool = next(t for t in tools if t.name == "diagnose_rate_limiting")

        schema = tool.inputSchema
        assert schema["type"] == "object"
        assert "required" in schema
        assert "api_name" in schema["required"]
        assert "symptoms" in schema["required"]
        assert "api_name" in schema["properties"]
        assert "symptoms" in schema["properties"]


class TestDiagnoseRateLimiting:
    """Tests for diagnose_rate_limiting tool."""

    @pytest.mark.asyncio
    async def test_returns_valid_response(self, call_tool_handler, rate_limiting_input):
        """Test tool execution returns valid TextContent."""
        result = await call_tool_handler(
            "diagnose_rate_limiting",
            rate_limiting_input,
        )

        assert len(result) > 0
        assert isinstance(result[0], TextContent)
        assert result[0].type == "text"

    @pytest.mark.asyncio
    async def test_includes_api_name_in_response(self, call_tool_handler, rate_limiting_input):
        """Test that response includes the API name."""
        result = await call_tool_handler(
            "diagnose_rate_limiting",
            rate_limiting_input,
        )

        assert "HubSpot" in result[0].text

    @pytest.mark.asyncio
    async def test_includes_symptoms_in_response(self, call_tool_handler, rate_limiting_input):
        """Test that response includes the symptoms."""
        result = await call_tool_handler(
            "diagnose_rate_limiting",
            rate_limiting_input,
        )

        assert "429 errors" in result[0].text

    @pytest.mark.asyncio
    async def test_includes_actionable_recommendations(
        self, call_tool_handler, rate_limiting_input
    ):
        """Test that response includes actionable recommendations."""
        result = await call_tool_handler(
            "diagnose_rate_limiting",
            rate_limiting_input,
        )

        response_text = result[0].text
        assert "Recommended Actions" in response_text
        assert "exponential backoff" in response_text.lower()

    @pytest.mark.asyncio
    async def test_handles_various_api_names(self, call_tool_handler):
        """Test tool with various API names."""
        test_cases = [
            {"api_name": "Clay", "symptoms": "slow responses"},
            {"api_name": "Instantly", "symptoms": "rate limited"},
            {"api_name": "Custom API", "symptoms": "connection timeouts"},
        ]

        for inputs in test_cases:
            result = await call_tool_handler("diagnose_rate_limiting", inputs)
            assert result is not None
            assert len(result) > 0
            assert inputs["api_name"] in result[0].text

    @pytest.mark.asyncio
    async def test_handles_missing_params_gracefully(self, call_tool_handler):
        """Test tool handles missing parameters with defaults."""
        result = await call_tool_handler(
            "diagnose_rate_limiting",
            {},  # Missing required params
        )

        # Should still return a response (with default values)
        assert len(result) > 0
        assert result[0].type == "text"


class TestScoreLead:
    """Tests for score_lead tool."""

    @pytest.mark.asyncio
    async def test_returns_valid_score_breakdown(self, call_tool_handler):
        """Test tool returns score with breakdown."""
        result = await call_tool_handler(
            "score_lead",
            {"role_title": "VP of Marketing", "company_size": "enterprise"},
        )

        assert len(result) > 0
        response = result[0].text
        assert "Score:" in response
        assert "Tier:" in response
        assert "Breakdown" in response

    @pytest.mark.asyncio
    async def test_role_scoring_works(self, call_tool_handler):
        """Test that role titles affect scoring."""
        result = await call_tool_handler(
            "score_lead",
            {"role_title": "CEO"},
        )

        response = result[0].text
        assert "C-Level" in response or "CEO" in response

    @pytest.mark.asyncio
    async def test_handles_empty_input(self, call_tool_handler):
        """Test tool handles empty input gracefully."""
        result = await call_tool_handler("score_lead", {})

        assert len(result) > 0
        assert "Score:" in result[0].text

    @pytest.mark.asyncio
    async def test_includes_calibration_notes(self, call_tool_handler):
        """Test that response includes calibration guidance."""
        result = await call_tool_handler(
            "score_lead",
            {"role_title": "Manager"},
        )

        response = result[0].text
        assert "Calibration" in response or "calibrate" in response.lower()


class TestClassifyRole:
    """Tests for classify_role tool."""

    @pytest.mark.asyncio
    async def test_classifies_c_level(self, call_tool_handler):
        """Test C-level titles are classified correctly."""
        result = await call_tool_handler(
            "classify_role",
            {"job_title": "Chief Technology Officer"},
        )

        response = result[0].text
        assert "Tier: 1" in response or "C-Level" in response

    @pytest.mark.asyncio
    async def test_classifies_vp_level(self, call_tool_handler):
        """Test VP titles are classified correctly."""
        result = await call_tool_handler(
            "classify_role",
            {"job_title": "VP of Sales"},
        )

        response = result[0].text
        assert "Tier: 2" in response or "VP" in response

    @pytest.mark.asyncio
    async def test_handles_unrecognized_title(self, call_tool_handler):
        """Test unrecognized titles return unclassified."""
        result = await call_tool_handler(
            "classify_role",
            {"job_title": "Chief Happiness Officer"},
        )

        response = result[0].text
        # Should still return a classification (possibly unclassified or C-level due to "Chief")
        assert "Tier:" in response

    @pytest.mark.asyncio
    async def test_handles_empty_title(self, call_tool_handler):
        """Test empty title is handled gracefully."""
        result = await call_tool_handler(
            "classify_role",
            {"job_title": ""},
        )

        response = result[0].text
        assert "Unknown" in response or "Tier: 0" in response


class TestClassifyIndustry:
    """Tests for classify_industry tool."""

    @pytest.mark.asyncio
    async def test_classifies_tier_1_industry(self, call_tool_handler):
        """Test Tier 1 industries are classified correctly."""
        result = await call_tool_handler(
            "classify_industry",
            {
                "industry": "SaaS",
                "tier_1_industries": ["SaaS", "Technology"],
                "tier_2_industries": ["Finance"],
            },
        )

        response = result[0].text
        assert "Tier: 1" in response or "Primary Target" in response

    @pytest.mark.asyncio
    async def test_returns_unclassified_without_config(self, call_tool_handler):
        """Test industry without tier config returns action required."""
        result = await call_tool_handler(
            "classify_industry",
            {"industry": "Healthcare"},
        )

        response = result[0].text
        assert "Unclassified" in response or "Action Required" in response

    @pytest.mark.asyncio
    async def test_handles_empty_input(self, call_tool_handler):
        """Test empty industry is handled gracefully."""
        result = await call_tool_handler(
            "classify_industry",
            {"industry": ""},
        )

        response = result[0].text
        assert "Unknown" in response or "Tier: 0" in response


class TestDetermineRouting:
    """Tests for determine_routing tool."""

    @pytest.mark.asyncio
    async def test_high_touch_for_tier_a(self, call_tool_handler):
        """Test Tier A leads get high-touch routing."""
        result = await call_tool_handler(
            "determine_routing",
            {"score": 80, "tier": "A"},
        )

        response = result[0].text
        assert "high_touch" in response or "High" in response

    @pytest.mark.asyncio
    async def test_low_touch_for_tier_c(self, call_tool_handler):
        """Test Tier C leads get low-touch routing."""
        result = await call_tool_handler(
            "determine_routing",
            {"score": 35, "tier": "C"},
        )

        response = result[0].text
        assert "low_touch" in response or "Low" in response

    @pytest.mark.asyncio
    async def test_enterprise_override_note(self, call_tool_handler):
        """Test enterprise accounts get override consideration."""
        result = await call_tool_handler(
            "determine_routing",
            {"score": 40, "tier": "C", "company_size": "enterprise"},
        )

        response = result[0].text
        assert "enterprise" in response.lower() or "override" in response.lower()


class TestCheckDisqualification:
    """Tests for check_disqualification tool."""

    @pytest.mark.asyncio
    async def test_flags_personal_email(self, call_tool_handler):
        """Test personal emails are flagged."""
        result = await call_tool_handler(
            "check_disqualification",
            {"email": "john@gmail.com"},
        )

        response = result[0].text
        assert "personal_email" in response or "gmail" in response.lower()

    @pytest.mark.asyncio
    async def test_flags_competitor(self, call_tool_handler):
        """Test competitors are flagged and disqualified."""
        result = await call_tool_handler(
            "check_disqualification",
            {"company_name": "Acme Corp", "competitors": ["Acme"]},
        )

        response = result[0].text
        assert "DISQUALIFIED" in response or "competitor" in response.lower()

    @pytest.mark.asyncio
    async def test_disqualifies_on_excluded_domain(self, call_tool_handler):
        """Test excluded domains cause disqualification."""
        result = await call_tool_handler(
            "check_disqualification",
            {"email": "test@blocked.com", "excluded_domains": ["blocked.com"]},
        )

        response = result[0].text
        assert "DISQUALIFIED" in response

    @pytest.mark.asyncio
    async def test_handles_no_flags(self, call_tool_handler):
        """Test clean leads pass with no flags."""
        result = await call_tool_handler(
            "check_disqualification",
            {"email": "john@acmecorp.com"},
        )

        response = result[0].text
        assert "QUALIFIED" in response or "Flags Found: 0" in response


class TestUnknownTool:
    """Tests for unknown tool handling."""

    @pytest.mark.asyncio
    async def test_unknown_tool_returns_error(self, call_tool_handler):
        """Test that calling unknown tool returns appropriate message."""
        result = await call_tool_handler(
            "nonexistent_tool",
            {"param": "value"},
        )

        assert len(result) > 0
        assert "Unknown tool" in result[0].text
