# Adding New Tools to GTM Wizard

This guide explains how to add new MCP tools to GTM Wizard.

## Quick Start

1. Define the tool in `list_tools()`
2. Handle the tool in `call_tool()`
3. Write tests
4. Update documentation

## Step 1: Define the Tool

Add a new `Tool` object to the `list_tools()` function in `src/gtm_wizard/server.py`:

```python
@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        # Existing tools...
        Tool(
            name="your_new_tool",
            description="Clear description of what this tool does. "
            "Include when to use it and what value it provides.",
            inputSchema={
                "type": "object",
                "properties": {
                    "param1": {
                        "type": "string",
                        "description": "Description of param1",
                    },
                    "param2": {
                        "type": "integer",
                        "description": "Description of param2",
                    },
                },
                "required": ["param1"],  # List required parameters
            },
        ),
    ]
```

### Tool Naming Convention

- Use `snake_case` for tool names
- Start with a verb: `diagnose_`, `calculate_`, `classify_`, `generate_`
- Be specific: `score_lead` not `score`

### Input Schema Best Practices

- Always include `"type": "object"` at the root
- Provide clear descriptions for every property
- Mark required parameters in the `required` array
- Use appropriate types: `string`, `integer`, `number`, `boolean`, `array`

## Step 2: Handle the Tool

Add a handler in the `call_tool()` function:

```python
@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    if name == "diagnose_rate_limiting":
        # Existing handler...
        pass

    elif name == "your_new_tool":
        # Extract parameters with defaults
        param1 = arguments.get("param1", "default_value")
        param2 = arguments.get("param2", 0)

        # Implement your tool logic
        result = process_something(param1, param2)

        # Return formatted response
        response = f"""## Your Tool Output

**Input:** {param1}

### Results
{result}

*Powered by GTM Wizard*
"""
        return [TextContent(type="text", text=response)]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]
```

### Response Format Guidelines

- Use Markdown for formatting
- Include headers for structure
- Echo back key inputs for context
- Provide actionable recommendations
- Keep responses concise but complete

## Step 3: Write Tests

Add tests in `tests/test_tools.py`:

```python
class TestYourNewTool:
    """Tests for your_new_tool."""

    @pytest.mark.asyncio
    async def test_tool_exists(self, list_tools_handler):
        """Tool appears in list_tools."""
        tools = await list_tools_handler()
        tool_names = [t.name for t in tools]
        assert "your_new_tool" in tool_names

    @pytest.mark.asyncio
    async def test_has_correct_schema(self, list_tools_handler):
        """Tool has correct input schema."""
        tools = await list_tools_handler()
        tool = next(t for t in tools if t.name == "your_new_tool")

        schema = tool.inputSchema
        assert schema["type"] == "object"
        assert "param1" in schema["properties"]
        assert "param1" in schema["required"]

    @pytest.mark.asyncio
    async def test_returns_valid_response(self, call_tool_handler):
        """Tool returns proper TextContent."""
        result = await call_tool_handler(
            "your_new_tool",
            {"param1": "test_value"},
        )

        assert len(result) > 0
        assert result[0].type == "text"
        assert "test_value" in result[0].text

    @pytest.mark.asyncio
    async def test_handles_missing_optional_params(self, call_tool_handler):
        """Tool handles missing optional parameters."""
        result = await call_tool_handler(
            "your_new_tool",
            {"param1": "test"},  # param2 is optional
        )

        assert len(result) > 0
```

### Test Checklist

- [ ] Tool exists in `list_tools()`
- [ ] Schema is correct
- [ ] Returns valid TextContent
- [ ] Handles all required parameters
- [ ] Handles missing optional parameters
- [ ] Output contains expected content

## Step 4: Update Documentation

1. **README.md** - Add tool to "Available Tools" section
2. **CHANGELOG.md** - Add entry under "Unreleased"

### README Entry Template

```markdown
### `your_new_tool`

Brief description of what the tool does.

**Parameters:**
- `param1` (string, required): Description
- `param2` (integer, optional): Description

**Example prompt:**
```
Your example prompt here
```
```

## Full Example: Adding `calculate_lead_score`

### 1. Tool Definition

```python
Tool(
    name="calculate_lead_score",
    description="Calculate a lead score based on engagement signals and firmographic data. "
    "Returns a score from 0-100 with breakdown by category.",
    inputSchema={
        "type": "object",
        "properties": {
            "company_size": {
                "type": "string",
                "enum": ["startup", "smb", "mid-market", "enterprise"],
                "description": "Company size tier",
            },
            "engagement_signals": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of engagement signals (e.g., 'visited_pricing', 'downloaded_whitepaper')",
            },
            "days_since_last_activity": {
                "type": "integer",
                "description": "Days since last engagement activity",
            },
        },
        "required": ["company_size", "engagement_signals"],
    },
),
```

### 2. Tool Handler

```python
elif name == "calculate_lead_score":
    company_size = arguments.get("company_size", "unknown")
    signals = arguments.get("engagement_signals", [])
    days_inactive = arguments.get("days_since_last_activity", 0)

    # Scoring logic
    size_scores = {"startup": 20, "smb": 40, "mid-market": 70, "enterprise": 100}
    base_score = size_scores.get(company_size, 30)

    signal_score = len(signals) * 10
    recency_penalty = min(days_inactive * 2, 30)

    total_score = min(100, max(0, base_score + signal_score - recency_penalty))

    response = f"""## Lead Score: {total_score}/100

**Company Size:** {company_size} (+{size_scores.get(company_size, 30)} points)
**Engagement Signals:** {len(signals)} signals (+{signal_score} points)
**Recency Penalty:** {days_inactive} days inactive (-{recency_penalty} points)

### Breakdown
- Base score (firmographic): {base_score}
- Signal bonus: +{signal_score}
- Recency penalty: -{recency_penalty}

### Recommendation
{"High priority - engage immediately" if total_score >= 70 else "Medium priority - nurture sequence" if total_score >= 40 else "Low priority - continue monitoring"}

*Calculated by GTM Wizard*
"""
    return [TextContent(type="text", text=response)]
```

## Running Tests

```bash
# Run all tests
make test

# Run specific test class
python3 -m pytest tests/test_tools.py::TestYourNewTool -v

# Run with coverage
make test-cov
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Missing `required` array | Always specify required parameters |
| Vague descriptions | Be specific about what the tool does |
| No input validation | Use `.get()` with defaults |
| Inconsistent response format | Follow Markdown template |
| Missing tests | Every tool needs at least 4 tests |

## Questions?

Open an issue on GitHub if you need help adding a new tool.
