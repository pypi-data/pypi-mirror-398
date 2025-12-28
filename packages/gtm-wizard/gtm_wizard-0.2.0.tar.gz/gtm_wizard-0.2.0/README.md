# GTM Wizard

[![CI](https://github.com/MathewJoseph1993/gtm-wizard/actions/workflows/ci.yml/badge.svg)](https://github.com/MathewJoseph1993/gtm-wizard/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%20|%203.11%20|%203.12-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

> **The Senior GTM Engineer in Your Pocket** - Go-To-Market Engineering expertise for AI agents via MCP.

An MCP (Model Context Protocol) server that brings world-class GTM Engineering expertise into AI-powered workflows. Built from real production systems handling high-velocity lead pipelines.

**Note:** GTM = Go-To-Market, not Google Tag Manager.

## What is GTM Wizard?

GTM Wizard is the **foundation layer for Agentic GTM** - AI agents that can build and operate GTM machines.

| GTM Wizard IS | GTM Wizard is NOT |
|---------------|-------------------|
| An expertise layer AI agents USE | A tutorial or teaching tool |
| Action-oriented tools with structured outputs | A collection of templates to copy |
| Flexible components for different contexts | Educational content explaining concepts |
| The "GTM brain" for autonomous operations | A replacement for strategic thinking |

## Features

### Tools (6 available)

| Tool | Purpose |
|------|---------|
| `score_lead` | Calculate lead scores with transparent breakdown |
| `classify_role` | Classify job titles into decision-making tiers |
| `classify_industry` | Determine industry fit based on your ICP |
| `determine_routing` | Route leads to appropriate engagement tracks |
| `check_disqualification` | Check for disqualifying factors |
| `diagnose_rate_limiting` | Debug API rate limit issues |

### Prompts (4 available)

| Prompt | Output |
|--------|--------|
| `lead-qualification-workflow` | Structured qualification result with routing decision |
| `icp-definition` | YAML ICP configuration for lead tools |
| `outbound-campaign-design` | Campaign blueprint with sequence and metrics |
| `lead-scoring-calibration` | Scoring model calibration recommendations |

### Resources (5 available)

GTM Engineering knowledge accessible via `gtm://foundations/{resource-id}`:
- `what-is-gtm-engineering` - Core definitions and skills
- `gtm-archetypes` - 6 specialization types
- `context-factors` - 8 factors that shape decisions
- `principles-not-recipes` - GTM Wizard philosophy
- `knowledge-taxonomy` - Full domain map

## Installation

### From Source (Recommended)

We use [UV](https://docs.astral.sh/uv/) for fast, reliable dependency management:

```bash
# Install UV (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup
git clone https://github.com/MathewJoseph1993/gtm-wizard.git
cd gtm-wizard
uv sync --all-extras
```

### From Source (pip)

```bash
git clone https://github.com/MathewJoseph1993/gtm-wizard.git
cd gtm-wizard
pip install -e ".[dev]"
```

## Quick Start

### Claude Desktop

Add to your config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "gtm-wizard": {
      "command": "python",
      "args": ["-m", "gtm_wizard.server"]
    }
  }
}
```

### Cursor

Add to Cursor MCP settings:

```json
{
  "mcpServers": {
    "gtm-wizard": {
      "command": "python",
      "args": ["-m", "gtm_wizard.server"]
    }
  }
}
```

### Claude Code CLI

```bash
claude mcp add gtm-wizard -- python -m gtm_wizard.server
```

## Example Usage

### Qualify a Lead

```
Qualify this lead: john@acmecorp.com, VP of Marketing at Acme Corp
```

GTM Wizard will run the full qualification pipeline and return:
```
QUALIFICATION RESULT
====================
Lead: john@acmecorp.com
Status: QUALIFIED
Score: 65/95 (68%)
Tier: B
Routing: medium_touch

Key Factors:
- Role: VP Level - 25 points
- Industry: Unclassified - 10 points
- Company Size: 20 points

Recommended Action: Enroll in nurture sequence with sales oversight
```

### Design a Campaign

```
Design an outbound campaign targeting VP of Sales at SaaS companies, goal is booking demos
```

Returns a complete `CAMPAIGN_BLUEPRINT` with targeting, sequence, messaging framework, and metrics.

### Build ICP Configuration

```
Help me build an ICP config for my B2B SaaS product
```

Returns a structured `ICP_CONFIG` in YAML that feeds into lead scoring tools.

## Development

```bash
# Sync dependencies (UV)
uv sync --all-extras

# Run all checks
make all

# Individual commands
make test        # Run tests (50 tests, 85% coverage)
make lint        # Lint code
make format      # Format code
make type-check  # Type checking (strict)
make serve       # Run the MCP server
make inspect     # Open MCP Inspector
```

### Testing with MCP Inspector

```bash
make inspect
```

Opens browser at `http://localhost:6274` for visual tool testing.

## Roadmap

See [ROADMAP.md](ROADMAP.md) for full details.

**Current:** v0.2 - Lead Intelligence (Complete)
**Next:** v0.3 - Outbound Automation

Future milestones include:
- Outbound campaign execution tools
- Data & analytics capabilities
- CRM integration patterns
- Agentic integrations (HubSpot MCP, email tools, context awareness)

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Content Guidelines:**
- Action-oriented - tools DO things, don't explain things
- Structured outputs - produce configs, blueprints, decisions
- Integration-ready - design for CRM/tool connections
- Expert application - apply GTM expertise, don't lecture

## License

MIT License - see [LICENSE](LICENSE) for details.

---

*Built by [Mathew Joseph](https://github.com/MathewJoseph1993) - GTM Engineer*
