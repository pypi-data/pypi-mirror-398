"""GTM Wizard MCP Server - Go-To-Market Engineering expertise for AI agents."""

from pathlib import Path
from typing import Any, TypedDict

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    GetPromptResult,
    Prompt,
    PromptArgument,
    PromptMessage,
    Resource,
    TextContent,
    TextResourceContents,
    Tool,
)
from pydantic import AnyUrl

from gtm_wizard.tools.qualification import (
    check_disqualification,
    classify_industry,
    classify_role,
    determine_routing,
    score_lead,
)

# Create the MCP server instance
server = Server("gtm-wizard")

# Path to resources directory
RESOURCES_DIR = Path(__file__).parent / "resources"

# Define available resources with metadata
FOUNDATION_RESOURCES = {
    "what-is-gtm-engineering": {
        "name": "What is GTM Engineering?",
        "description": "Core definition, history, responsibilities, and skills of GTM Engineers",
        "file": "foundations/what-is-gtm-engineering.md",
    },
    "gtm-archetypes": {
        "name": "GTM Engineer Archetypes",
        "description": "The 6 different specializations: Outbound, RevOps, PLG, AI, Data, Full-Stack",
        "file": "foundations/gtm-archetypes.md",
    },
    "context-factors": {
        "name": "Context Factors",
        "description": "The 8 factors that determine how to approach any GTM problem",
        "file": "foundations/context-factors.md",
    },
    "principles-not-recipes": {
        "name": "Principles, Not Recipes",
        "description": "GTM Wizard philosophy: teaching thinking, not templates",
        "file": "foundations/principles-not-recipes.md",
    },
    "knowledge-taxonomy": {
        "name": "GTM Knowledge Taxonomy",
        "description": "Complete map of GTM domains, sub-topics, and planned MCP components",
        "file": "GTM_KNOWLEDGE_TAXONOMY.md",
    },
}


class PromptArgumentData(TypedDict):
    """Type definition for prompt argument data."""

    name: str
    description: str
    required: bool


class PromptData(TypedDict):
    """Type definition for prompt data."""

    name: str
    description: str
    arguments: list[PromptArgumentData]


# Define available prompts for GTM workflows
GTM_PROMPTS: dict[str, PromptData] = {
    "lead-qualification-workflow": {
        "name": "Qualify Lead",
        "description": "Run a lead through the full qualification pipeline: "
        "disqualification check, role/industry classification, scoring, and routing decision.",
        "arguments": [
            {
                "name": "lead_email",
                "description": "Email address of the lead to qualify",
                "required": False,
            },
            {
                "name": "lead_title",
                "description": "Job title of the lead",
                "required": False,
            },
            {
                "name": "company_name",
                "description": "Name of the lead's company",
                "required": False,
            },
        ],
    },
    "icp-definition": {
        "name": "Build ICP Config",
        "description": "Build a structured ICP (Ideal Customer Profile) configuration "
        "that feeds into lead scoring and qualification tools.",
        "arguments": [
            {
                "name": "product_description",
                "description": "Brief description of your product/service",
                "required": False,
            },
            {
                "name": "current_customers",
                "description": "Description of your best current customers",
                "required": False,
            },
        ],
    },
    "outbound-campaign-design": {
        "name": "Design Campaign",
        "description": "Design a complete outbound campaign blueprint with targeting, "
        "sequence, messaging framework, and success metrics.",
        "arguments": [
            {
                "name": "campaign_goal",
                "description": "What you want to achieve (meetings, demos, signups)",
                "required": False,
            },
            {
                "name": "target_persona",
                "description": "Who you're trying to reach",
                "required": False,
            },
        ],
    },
    "lead-scoring-calibration": {
        "name": "Calibrate Scoring",
        "description": "Analyze scoring model performance and produce updated "
        "weight/threshold recommendations based on conversion data.",
        "arguments": [
            {
                "name": "current_conversion_rate",
                "description": "Your current overall conversion rate (e.g., '5%')",
                "required": False,
            },
            {
                "name": "pain_points",
                "description": "What's not working with current scoring",
                "required": False,
            },
        ],
    },
}


@server.list_prompts()  # type: ignore[no-untyped-call, untyped-decorator]
async def list_prompts() -> list[Prompt]:
    """List available GTM workflow prompts."""
    prompts = []
    for prompt_id, metadata in GTM_PROMPTS.items():
        prompts.append(
            Prompt(
                name=prompt_id,
                description=metadata["description"],
                arguments=[
                    PromptArgument(
                        name=arg["name"],
                        description=arg["description"],
                        required=arg["required"],
                    )
                    for arg in metadata["arguments"]
                ],
            )
        )
    return prompts


@server.get_prompt()  # type: ignore[no-untyped-call, untyped-decorator]
async def get_prompt(name: str, arguments: dict[str, str] | None) -> GetPromptResult:
    """Get a specific GTM workflow prompt."""
    if name not in GTM_PROMPTS:
        raise ValueError(f"Unknown prompt: {name}")

    args = arguments or {}

    if name == "lead-qualification-workflow":
        lead_info = []
        if args.get("lead_email"):
            lead_info.append(f"- **Email:** {args['lead_email']}")
        if args.get("lead_title"):
            lead_info.append(f"- **Title:** {args['lead_title']}")
        if args.get("company_name"):
            lead_info.append(f"- **Company:** {args['company_name']}")

        lead_context = "\n".join(lead_info) if lead_info else "(Gather lead information to begin)"

        content = f"""# Qualify This Lead

## Lead Data
{lead_context}

## Task
Run this lead through the full qualification pipeline and provide a routing decision.

## Execution Steps

**Step 1: Disqualification Check**
→ Use `check_disqualification` tool with the lead's email, company, and title
→ If disqualified, STOP and report the reason

**Step 2: Role Classification**
→ Use `classify_role` tool with the job title
→ Capture the tier and decision-making authority level

**Step 3: Industry Classification**
→ Use `classify_industry` tool
→ If user has defined industry tiers, apply them; otherwise note this needs configuration

**Step 4: Lead Scoring**
→ Use `score_lead` tool with all gathered information
→ Capture total score, tier (A/B/C/D), and score breakdown

**Step 5: Routing Decision**
→ Use `determine_routing` tool with the score and tier
→ Output the recommended engagement track

## Required Output

Provide a structured qualification result:

```
QUALIFICATION RESULT
====================
Lead: [name/email]
Status: [QUALIFIED / DISQUALIFIED]
Score: [X]/[Y] ([Z]%)
Tier: [A/B/C/D]
Routing: [high_touch / medium_touch / low_touch / nurture_only]

Key Factors:
- Role: [tier] - [X points]
- Industry: [tier] - [X points]
- Company Size: [X points]

Recommended Action: [specific next step]
Flags: [any concerns or notes]
```

If any information is missing, ask for it before proceeding.
"""
        return GetPromptResult(
            description="Qualify a lead through the full pipeline",
            messages=[PromptMessage(role="user", content=TextContent(type="text", text=content))],
        )

    if name == "icp-definition":
        product_ctx = args.get("product_description", "(not provided)")
        customer_ctx = args.get("current_customers", "(not provided)")

        content = f"""# Build ICP Configuration

## Context
- **Product:** {product_ctx}
- **Current Best Customers:** {customer_ctx}

## Task
Build a structured ICP (Ideal Customer Profile) configuration that can be used by lead scoring and qualification tools.

## Information Gathering

Collect the following from the user (ask if not provided):

**1. Industry Tiers**
- Tier 1 (primary target): Which industries have highest win rates and fastest cycles?
- Tier 2 (secondary): Which industries work but aren't ideal?
- Tier 3 (opportunistic): Which industries you'll take but won't prioritize?

**2. Role Priorities**
- Economic Buyer roles: Who signs contracts?
- Champion roles: Who drives deals internally?
- User roles: Who uses the product daily?
- Blocker roles: Who might veto?

**3. Company Size**
- Sweet spot: What employee count / revenue range converts best?
- Minimum viable: Below what size doesn't work?
- Enterprise threshold: At what size do you need enterprise motion?

**4. Disqualification Rules**
- Competitor domains to exclude
- Industries to exclude
- Roles to deprioritize
- Geographic restrictions

## Required Output

Produce a structured ICP configuration:

```yaml
ICP_CONFIG:
  industries:
    tier_1: [list]
    tier_2: [list]
    tier_3: [list]
    exclude: [list]

  roles:
    decision_makers: [list]
    champions: [list]
    users: [list]
    deprioritize: [list]

  company_size:
    sweet_spot: "X-Y employees"
    minimum: "X employees"
    enterprise_threshold: "Y employees"

  disqualifiers:
    competitor_domains: [list]
    excluded_industries: [list]
    excluded_roles: [list]
    other: [list]

  signals:
    high_intent: [list of behaviors]
    medium_intent: [list of behaviors]
```

This configuration will feed into `classify_industry`, `classify_role`, and `check_disqualification` tools.

If information is incomplete, note what's missing and provide a partial configuration.
"""
        return GetPromptResult(
            description="Build ICP configuration for lead tools",
            messages=[PromptMessage(role="user", content=TextContent(type="text", text=content))],
        )

    if name == "outbound-campaign-design":
        goal_ctx = args.get("campaign_goal", "(not specified)")
        persona_ctx = args.get("target_persona", "(not specified)")

        content = f"""# Design Outbound Campaign

## Parameters
- **Goal:** {goal_ctx}
- **Target Persona:** {persona_ctx}

## Task
Design a complete outbound campaign blueprint ready for execution.

## Information Needed

Gather from user if not provided:

**Targeting**
- Target persona (title, seniority, function)
- Target industries (use ICP if available)
- Company size range
- Geographic focus
- List source (LinkedIn, database, intent data, etc.)

**Campaign Parameters**
- Campaign goal (meetings, demos, signups, replies)
- Volume (how many prospects per week)
- Timeline (campaign duration)
- Available channels (email, LinkedIn, phone)
- Sending capacity / tool constraints

**Context**
- Product/offer being promoted
- Key value proposition
- Any existing messaging to build on
- Competitor landscape

## Required Output

Produce a campaign blueprint:

```yaml
CAMPAIGN_BLUEPRINT:
  name: "[Campaign Name]"
  goal: "[Primary metric]"
  duration: "[X weeks]"

  targeting:
    persona: "[Title + Function]"
    industries: [list]
    company_size: "[range]"
    geography: "[regions]"
    estimated_list_size: [number]

  sequence:
    - day: 1
      channel: email
      type: initial_outreach
      angle: "[hook/angle]"

    - day: 3
      channel: linkedin
      type: connection_request
      note: "[personalized note approach]"

    - day: 5
      channel: email
      type: follow_up
      angle: "[different angle]"

    - day: 8
      channel: linkedin
      type: message
      angle: "[value-add]"

    - day: 12
      channel: email
      type: breakup
      angle: "[final value or close loop]"

  messaging_framework:
    hook_options:
      - "[Option 1]"
      - "[Option 2]"
    value_prop: "[Core value statement]"
    cta: "[Low-friction ask]"
    proof_points:
      - "[Social proof 1]"
      - "[Social proof 2]"

  response_handling:
    positive: "→ Use `score_lead` → Route via `determine_routing`"
    objection: "[Handle with...]"
    not_now: "[Add to nurture]"

  success_metrics:
    open_rate_target: "[X%]"
    reply_rate_target: "[X%]"
    meeting_rate_target: "[X%]"
```

Validate targeting using `classify_role` and `classify_industry` tools.
"""
        return GetPromptResult(
            description="Design outbound campaign blueprint",
            messages=[PromptMessage(role="user", content=TextContent(type="text", text=content))],
        )

    if name == "lead-scoring-calibration":
        conv_rate = args.get("current_conversion_rate", "(not provided)")
        pain_points = args.get("pain_points", "(not specified)")

        content = f"""# Calibrate Lead Scoring Model

## Current State
- **Conversion Rate:** {conv_rate}
- **Issues:** {pain_points}

## Task
Analyze scoring performance and produce updated scoring configuration.

## Data Required

Ask user for conversion data by tier (if available):

```
Current Performance:
- Tier A: [X]% conversion, [Y] leads/month
- Tier B: [X]% conversion, [Y] leads/month
- Tier C: [X]% conversion, [Y] leads/month
- Tier D: [X]% conversion, [Y] leads/month

By Factor:
- Top converting roles: [list]
- Top converting industries: [list]
- Best company size segment: [range]
- Strongest intent signals: [list]

Capacity:
- Sales team size: [X reps]
- Leads per rep capacity: [Y/month]
```

## Analysis Steps

**1. Tier Predictiveness Check**
- Do higher tiers convert better? (If not, model is broken)
- Is there tier compression? (All tiers similar = model not differentiating)

**2. Factor Analysis**
- Which factors correlate with conversion?
- Any factors that don't predict anything?
- Any missing factors that should be added?

**3. Capacity Alignment**
- How many Tier A leads vs. rep capacity?
- Are you over/under-routing to sales?

## Required Output

Produce calibration recommendations:

```yaml
SCORING_CALIBRATION:
  analysis:
    tier_predictiveness: "[good/broken/needs_work]"
    key_finding: "[main insight]"

  weight_adjustments:
    role:
      current: 30
      recommended: [X]
      reason: "[why]"
    industry:
      current: 25
      recommended: [X]
      reason: "[why]"
    company_size:
      current: 20
      recommended: [X]
      reason: "[why]"
    intent_signals:
      current: 20
      recommended: [X]
      reason: "[why]"

  threshold_adjustments:
    tier_a:
      current: "70%+"
      recommended: "[X%]+"
      reason: "[capacity/conversion based]"
    tier_b:
      current: "50-69%"
      recommended: "[X-Y%]"
    tier_c:
      current: "30-49%"
      recommended: "[X-Y%]"

  new_factors_to_add:
    - factor: "[name]"
      weight: [X]
      reason: "[why]"

  factors_to_remove:
    - factor: "[name]"
      reason: "[not predictive]"

  routing_impact:
    high_touch_volume_change: "[+/-X%]"
    automation_volume_change: "[+/-X%]"
```

Use `score_lead` with custom_factors to test new weights.
Use `determine_routing` to validate routing changes.

If no data is available, provide a framework for collecting it.
"""
        return GetPromptResult(
            description="Calibrate lead scoring model",
            messages=[PromptMessage(role="user", content=TextContent(type="text", text=content))],
        )

    raise ValueError(f"Unknown prompt: {name}")


@server.list_tools()  # type: ignore[no-untyped-call, untyped-decorator]
async def list_tools() -> list[Tool]:
    """List available GTM engineering tools."""
    return [
        Tool(
            name="diagnose_rate_limiting",
            description="Diagnose API rate limiting issues in your GTM infrastructure. "
            "Provide the API name and symptoms to get actionable recommendations.",
            inputSchema={
                "type": "object",
                "properties": {
                    "api_name": {
                        "type": "string",
                        "description": "Name of the API (e.g., HubSpot, Clay, Instantly)",
                    },
                    "symptoms": {
                        "type": "string",
                        "description": "Describe what's happening (e.g., '429 errors', 'slow responses')",
                    },
                },
                "required": ["api_name", "symptoms"],
            },
        ),
        Tool(
            name="score_lead",
            description="Calculate a lead score with transparent breakdown. "
            "Returns score, tier, and reasoning - not just a number. "
            "Use this as a STARTING FRAMEWORK and adapt based on your conversion data.",
            inputSchema={
                "type": "object",
                "properties": {
                    "role_title": {
                        "type": "string",
                        "description": "Job title of the lead (e.g., 'VP of Marketing')",
                    },
                    "industry": {
                        "type": "string",
                        "description": "Industry of the company",
                    },
                    "company_size": {
                        "type": "string",
                        "description": "Company size category (enterprise/mid-market/smb/startup)",
                    },
                    "intent_signals": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of intent signals (e.g., ['visited pricing page', 'downloaded whitepaper'])",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="classify_role",
            description="Classify a job title into decision-making tiers. "
            "Helps prioritize based on likely authority. "
            "Role importance varies by product - adapt accordingly.",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_title": {
                        "type": "string",
                        "description": "The job title to classify",
                    },
                },
                "required": ["job_title"],
            },
        ),
        Tool(
            name="classify_industry",
            description="Classify an industry into fit tiers (Tier 1/2/3). "
            "REQUIRES your tier definitions - industry fit is product-specific. "
            "Provide your target industries to get meaningful results.",
            inputSchema={
                "type": "object",
                "properties": {
                    "industry": {
                        "type": "string",
                        "description": "The industry to classify",
                    },
                    "tier_1_industries": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Your primary target industries (best fit)",
                    },
                    "tier_2_industries": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Your secondary target industries (good fit)",
                    },
                    "tier_3_industries": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Your tertiary target industries (some fit)",
                    },
                },
                "required": ["industry"],
            },
        ),
        Tool(
            name="determine_routing",
            description="Determine the appropriate routing track for a lead "
            "(high-touch, medium-touch, low-touch, nurture-only). "
            "Match lead quality to your sales capacity.",
            inputSchema={
                "type": "object",
                "properties": {
                    "score": {
                        "type": "integer",
                        "description": "Lead score (from score_lead tool)",
                    },
                    "tier": {
                        "type": "string",
                        "description": "Lead tier (A/B/C/D from score_lead tool)",
                    },
                    "company_size": {
                        "type": "string",
                        "description": "Company size for potential override",
                    },
                    "has_intent_signals": {
                        "type": "boolean",
                        "description": "Whether the lead has shown intent signals",
                    },
                },
                "required": ["score", "tier"],
            },
        ),
        Tool(
            name="check_disqualification",
            description="Check for disqualifying factors (competitors, personal emails, etc.). "
            "Returns flags with severity - not all flags require disqualification. "
            "Provide your competitor list for accurate detection.",
            inputSchema={
                "type": "object",
                "properties": {
                    "email": {
                        "type": "string",
                        "description": "Lead's email address",
                    },
                    "company_name": {
                        "type": "string",
                        "description": "Company name to check against competitors",
                    },
                    "job_title": {
                        "type": "string",
                        "description": "Job title to check for red flags",
                    },
                    "competitors": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of your competitor names",
                    },
                    "excluded_domains": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Additional domains to exclude",
                    },
                },
                "required": [],
            },
        ),
    ]


@server.call_tool()  # type: ignore[no-untyped-call, untyped-decorator]
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    if name == "diagnose_rate_limiting":
        api_name = arguments.get("api_name", "Unknown API")
        symptoms = arguments.get("symptoms", "No symptoms provided")

        # GTM Engineering expertise for rate limiting
        diagnosis = f"""## Rate Limiting Diagnosis: {api_name}

**Symptoms reported:** {symptoms}

### Common Causes
1. **Exceeding API limits** - Check the API's rate limit headers
2. **Burst traffic** - Too many requests in a short window
3. **Missing backoff logic** - No exponential retry strategy

### Recommended Actions
1. **Check rate limit headers** in API responses (X-RateLimit-Remaining)
2. **Implement exponential backoff** - Start with 1s delay, double on each retry
3. **Add request queuing** - Use a queue (Redis/BullMQ) to throttle requests
4. **Monitor with logging** - Track 429 responses to identify patterns

### GTM-Specific Tips for {api_name}
- Consider batch endpoints if available
- Spread requests across time windows
- Cache responses where possible to reduce API calls

*This diagnosis is powered by GTM Wizard - real-world GTM engineering expertise.*
"""
        return [TextContent(type="text", text=diagnosis)]

    if name == "score_lead":
        result = score_lead(
            role_title=arguments.get("role_title"),
            industry=arguments.get("industry"),
            company_size=arguments.get("company_size"),
            intent_signals=arguments.get("intent_signals"),
            custom_factors=arguments.get("custom_factors"),
        )
        output = f"""## Lead Score Results

**Score:** {result["total_score"]}/{result["max_possible"]} ({result["percentage"]}%)
**Tier:** {result["tier"]} - {result["tier_description"]}

### Score Breakdown

"""
        for item in result["breakdown"]:
            output += f"**{item['factor']}:** {item['points']}/{item['max_points']} points\n"
            output += f"  - Value: {item['value']}\n"
            output += f"  - Reasoning: {item['reasoning']}\n"
            if "action_required" in item:
                output += f"  - **Action Required:** {item['action_required']}\n"
            output += "\n"

        output += f"""### Calibration Note
{result["calibration_note"]}

### Next Steps
"""
        for step in result["next_steps"]:
            output += f"- {step}\n"

        return [TextContent(type="text", text=output)]

    if name == "classify_role":
        job_title = arguments.get("job_title", "")
        result = classify_role(job_title)

        output = f"""## Role Classification

**Title:** {result.get("original_title", job_title)}
**Tier:** {result["tier"]} - {result["label"]}
**Points:** {result.get("points", "N/A")}
**Confidence:** {result["confidence"]}

**Reasoning:** {result["reasoning"]}
"""
        if "customization_note" in result:
            output += f"\n**Note:** {result['customization_note']}"
        if "action" in result:
            output += f"\n**Action:** {result['action']}"

        return [TextContent(type="text", text=output)]

    if name == "classify_industry":
        result = classify_industry(
            industry=arguments.get("industry", ""),
            tier_1_industries=arguments.get("tier_1_industries"),
            tier_2_industries=arguments.get("tier_2_industries"),
            tier_3_industries=arguments.get("tier_3_industries"),
        )

        output = f"""## Industry Classification

**Industry:** {result.get("original_industry", arguments.get("industry", "Unknown"))}
**Tier:** {result["tier"]} - {result["label"]}
**Points:** {result.get("points", "N/A")}

**Reasoning:** {result["reasoning"]}
"""
        if "action_required" in result:
            output += f"\n**Action Required:** {result['action_required']}"
        if "questions_to_answer" in result:
            output += "\n\n**Questions to Answer:**\n"
            for q in result["questions_to_answer"]:
                output += f"- {q}\n"

        return [TextContent(type="text", text=output)]

    if name == "determine_routing":
        result = determine_routing(
            score=arguments.get("score", 0),
            tier=arguments.get("tier", "D"),
            company_size=arguments.get("company_size"),
            has_intent_signals=arguments.get("has_intent_signals", False),
        )

        output = f"""## Routing Recommendation

**Track:** {result["recommended_track"]}
**Description:** {result["track_description"]}

### Suggested Actions
"""
        for action in result["suggested_actions"]:
            output += f"- {action}\n"

        if result["size_override_note"]:
            output += f"\n**Size Override:** {result['size_override_note']}"

        output += f"""

### Customization Note
{result["customization_note"]}

### Questions to Consider
"""
        for q in result["questions_to_consider"]:
            output += f"- {q}\n"

        return [TextContent(type="text", text=output)]

    if name == "check_disqualification":
        result = check_disqualification(
            email=arguments.get("email"),
            company_name=arguments.get("company_name"),
            job_title=arguments.get("job_title"),
            competitors=arguments.get("competitors"),
            excluded_domains=arguments.get("excluded_domains"),
        )

        status = "DISQUALIFIED" if result["is_disqualified"] else "QUALIFIED"
        output = f"""## Disqualification Check

**Status:** {status}
"""
        if result["disqualification_reason"]:
            output += f"**Reason:** {result['disqualification_reason']}\n"

        output += f"**Flags Found:** {result['flag_count']}\n\n"

        if result["flags"]:
            output += "### Flags\n\n"
            for flag in result["flags"]:
                output += f"**{flag['type']}** (Severity: {flag['severity']})\n"
                output += f"  - Value: {flag['value']}\n"
                output += f"  - Recommendation: {flag['recommendation']}\n\n"

        output += f"""### Recommendation
{result["recommendation"]}

### Customization Note
{result["customization_note"]}
"""
        return [TextContent(type="text", text=output)]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


@server.list_resources()  # type: ignore[no-untyped-call, untyped-decorator]
async def list_resources() -> list[Resource]:
    """List available GTM knowledge resources."""
    resources = []
    for resource_id, metadata in FOUNDATION_RESOURCES.items():
        resources.append(
            Resource(
                uri=AnyUrl(f"gtm://foundations/{resource_id}"),
                name=metadata["name"],
                description=metadata["description"],
                mimeType="text/markdown",
            )
        )
    return resources


@server.read_resource()  # type: ignore[no-untyped-call, untyped-decorator]
async def read_resource(uri: str) -> TextResourceContents:
    """Read a GTM knowledge resource by URI."""
    # Parse the URI to get the resource path
    if not uri.startswith("gtm://"):
        raise ValueError(f"Invalid URI scheme: {uri}")

    # Extract resource type and ID from URI (e.g., "gtm://foundations/what-is-gtm-engineering")
    path_part = uri[6:]  # Remove "gtm://"
    parts = path_part.split("/", 1)

    if len(parts) != 2:
        raise ValueError(f"Invalid URI format: {uri}")

    resource_type, resource_id = parts

    if resource_type == "foundations" and resource_id in FOUNDATION_RESOURCES:
        file_path = RESOURCES_DIR / FOUNDATION_RESOURCES[resource_id]["file"]
        if file_path.exists():
            content = file_path.read_text(encoding="utf-8")
            return TextResourceContents(
                uri=AnyUrl(uri),
                mimeType="text/markdown",
                text=content,
            )
        raise ValueError(f"Resource file not found: {file_path}")

    raise ValueError(f"Unknown resource: {uri}")


async def main() -> None:
    """Run the GTM Wizard MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
