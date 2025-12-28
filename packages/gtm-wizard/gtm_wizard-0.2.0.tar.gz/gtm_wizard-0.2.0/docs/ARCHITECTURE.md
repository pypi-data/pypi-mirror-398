# GTM Wizard Architecture

This document describes the architecture of GTM Wizard, an MCP (Model Context Protocol) server that packages Go-To-Market Engineering expertise for AI agents.

## Overview

GTM Wizard follows the MCP specification to expose GTM engineering knowledge through three primitives:

- **Tools** - Executable functions that perform calculations or diagnostics
- **Resources** - Static or dynamic data (architecture patterns, runbooks)
- **Prompts** - Reusable prompt templates for common GTM tasks

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    AGENTIC GTM ARCHITECTURE                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  SIGNAL SOURCES                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ RB2B │ AppCues │ Trigify │ Clay │ HubSpot │ Cal.com    │   │
│  └─────────────────────────────────────────────────────────┘   │
│       ↓                                                         │
│  GTM WIZARD MCP (Knowledge + Tools)                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Tools: diagnose_rate_limiting, score_lead, classify_role│   │
│  │ Resources: architecture patterns, runbooks, frameworks  │   │
│  │ Prompts: diagnose_infrastructure, design_pipeline       │   │
│  └─────────────────────────────────────────────────────────┘   │
│       ↓                                                         │
│  AI AGENT (Claude Desktop / Cursor / Agent SDK)                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Autonomous execution with human-in-the-loop             │   │
│  │ Confidence-based routing: >95% auto, <70% escalate      │   │
│  └─────────────────────────────────────────────────────────┘   │
│       ↓                                                         │
│  EXECUTION LAYER                                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ HubSpot │ Instantly │ HeyReach │ n8n │ Pipedrive       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Transport Protocol

GTM Wizard currently uses **STDIO transport** for local execution:

```
┌──────────────┐     stdin/stdout      ┌──────────────┐
│    Client    │ ◄──────────────────► │  GTM Wizard  │
│ (Claude/etc) │    JSON-RPC 2.0       │  MCP Server  │
└──────────────┘                       └──────────────┘
```

Future versions will support HTTP/SSE for remote deployment.

## Project Structure

```
gtm-wizard/
├── src/
│   └── gtm_wizard/
│       ├── __init__.py      # Package initialization
│       ├── server.py        # MCP server entry point
│       └── py.typed         # PEP 561 typed package marker
├── tests/
│   ├── conftest.py          # Test fixtures
│   └── test_tools.py        # Tool tests
├── docs/
│   ├── ARCHITECTURE.md      # This file
│   └── ADDING_TOOLS.md      # Tool development guide
├── examples/
│   └── claude_desktop_config.md
├── pyproject.toml           # Package configuration
└── Makefile                 # Development commands
```

## Server Implementation

The MCP server is implemented in `src/gtm_wizard/server.py`:

```python
from mcp.server import Server
from mcp.server.stdio import stdio_server

server = Server("gtm-wizard")

@server.list_tools()
async def list_tools() -> list[Tool]:
    # Return available tools
    ...

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    # Handle tool execution
    ...
```

## Tool Categories

GTM Wizard organizes tools into knowledge domains:

| Domain | Description | Example Tools |
|--------|-------------|---------------|
| **Infrastructure** | Queue-based processing, scaling | `diagnose_rate_limiting` |
| **Signal Aggregation** | Multi-source data collection | `aggregate_signals` |
| **Integration** | CRM sync, enrichment flows | `design_integration` |
| **Lead Processing** | Qualification, scoring, routing | `score_lead`, `classify_role` |
| **Email Operations** | Deliverability, compliance | `check_deliverability` |
| **Orchestration** | Multi-channel campaigns | `design_campaign` |

## Integration Phases

GTM Wizard follows a phased integration approach:

| Phase | Model | Capability |
|-------|-------|------------|
| **Phase 1** | Knowledge-Only | Provides expertise, user applies manually |
| **Phase 2** | Calculation Tools | Score leads, estimate capacity, validate configs |
| **Phase 3** | MCP Composition | Orchestrates other MCPs (HubSpot, Clay) |
| **Phase 4** | Direct API | Makes API calls to services directly |
| **Phase 5** | Agent SDK | Full autonomous operations with HITL |

## Client Compatibility

GTM Wizard works with any MCP-compatible client:

- **Claude Desktop** - Native MCP support via config file
- **Cursor** - Native STDIO + SSE support
- **VS Code** - Via MCP extensions
- **Claude Code CLI** - `claude mcp add` command
- **Claude Agent SDK** - For autonomous operations

## Security Considerations

- All tool inputs are validated before processing
- No credentials are stored in the server
- API keys should be passed via environment variables
- Rate limiting is recommended for production deployments

## Performance

- Async/await throughout for non-blocking execution
- Stateless design enables horizontal scaling
- Session reuse provides 10x performance improvement

## Future Architecture

Remote deployment will use HTTP/SSE transport:

```
┌──────────────┐       HTTPS          ┌──────────────┐
│    Client    │ ◄──────────────────► │  GTM Wizard  │
│ (Claude/etc) │    Server-Sent       │  (Fly.io)    │
└──────────────┘      Events          └──────────────┘
```
