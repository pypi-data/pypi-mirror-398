# GTM Wizard Roadmap

> "The Senior GTM Engineer in Your Pocket"

This roadmap outlines the development milestones for GTM Wizard, an MCP server that brings world-class GTM Engineering expertise into AI-powered workflows.

## Vision: Agentic GTM Foundation

GTM Wizard is the **foundation layer for Agentic GTM** - AI agents that can build and operate GTM machines.

**What GTM Wizard IS:**
- An expertise layer that AI agents use to make GTM decisions
- Action-oriented tools that produce structured, usable outputs
- Flexible components that adapt to different contexts and integrations
- The "GTM brain" that powers autonomous go-to-market operations

**What GTM Wizard is NOT:**
- A tutorial or teaching tool
- A collection of templates to copy
- A replacement for human judgment on strategy

**Future State:**
- Access to project folders for context-aware recommendations
- Integration with CRMs (HubSpot, Salesforce) via MCP
- Connection to email/outreach tools for campaign execution
- Real-time data analysis from connected systems

## Current Status

| Component | Status | Coverage |
|-----------|--------|----------|
| Infrastructure | Complete | CI, tests, types |
| Foundation Resources | Complete | 5 resources |
| Lead Qualification Tools | Complete | 6 tools |
| GTM Prompts | Complete | 4 prompts |
| Test Coverage | 85% | 50 tests |

---

## Milestones

### v0.1 - Foundation (Complete)

Infrastructure and foundational knowledge layer.

- [x] Project setup (pyproject.toml, CI, testing)
- [x] MCP server skeleton with tool/resource/prompt handlers
- [x] Foundation resources:
  - What is GTM Engineering?
  - GTM Engineer Archetypes
  - Context Factors
  - Principles, Not Recipes
  - GTM Knowledge Taxonomy
- [x] Basic rate limiting diagnosis tool
- [x] UV + MCP Inspector setup
- [x] 80%+ test coverage

### v0.2 - Lead Intelligence (Complete)

Lead qualification and scoring capabilities - the first operational layer.

- [x] Lead scoring tool with transparent breakdown
- [x] Role classification tool
- [x] Industry classification tool
- [x] Routing determination tool
- [x] Disqualification check tool
- [x] **Qualify Lead** prompt - Full qualification pipeline
- [x] **Build ICP Config** prompt - Structured ICP output
- [x] **Design Campaign** prompt - Campaign blueprint generator
- [x] **Calibrate Scoring** prompt - Model calibration workflow

### v0.3 - Outbound Automation (Planned)

Tools for outbound campaign execution.

- [ ] Email sequence design tool
- [ ] Subject line analyzer tool
- [ ] CTA effectiveness checker
- [ ] Personalization variable generator
- [ ] A/B test planner tool
- [ ] Sequence timing optimizer
- [ ] Resources: Email copywriting principles, multi-channel strategy

### v0.4 - Data & Analytics (Planned)

Data pipeline and reporting capabilities.

- [ ] Funnel analysis tool
- [ ] Conversion rate calculator
- [ ] Cohort analysis helper
- [ ] Attribution model explainer
- [ ] Dashboard recommendation tool
- [ ] Resources: GTM metrics guide, reporting best practices

### v0.5 - Integration Patterns (Planned)

Common integration patterns and troubleshooting.

- [ ] API error diagnosis (expanded)
- [ ] Webhook debugger tool
- [ ] Data sync validator
- [ ] CRM integration health check
- [ ] Resources: Integration architecture patterns, data hygiene guide

### v0.6 - Advanced GTM (Future)

Advanced GTM Engineering patterns.

- [ ] PLG motion analyzer
- [ ] Sales-assist vs self-serve router
- [ ] Pricing page optimizer
- [ ] Trial-to-paid conversion analyzer
- [ ] Resources: PLG foundations, hybrid motion design

### v0.7+ - Agentic Integrations (Future)

Connect GTM Wizard to external systems for autonomous operation.

- [ ] **Context Awareness** - Read project folder for automatic ICP inference
- [ ] **HubSpot MCP Integration** - Read/write contacts, deals, companies
- [ ] **CRM Sync** - Push qualification results to CRM records
- [ ] **Email Tool Integration** - Execute campaigns via connected tools
- [ ] **Analytics Connection** - Pull conversion data for auto-calibration

---

## Domain Coverage

Based on the [GTM Knowledge Taxonomy](src/gtm_wizard/resources/GTM_KNOWLEDGE_TAXONOMY.md):

| Domain | Status | Components |
|--------|--------|------------|
| 1. Lead Intelligence | Complete | 5 tools, 2 prompts |
| 2. Outbound Automation | Planned | v0.3 |
| 3. Data & Analytics | Planned | v0.4 |
| 4. Infrastructure | Partial | 1 tool |
| 5. CRM & RevOps | Planned | v0.5+ |
| 6. PLG Mechanics | Planned | v0.6 |
| 7. AI-Augmented GTM | Future | TBD |
| 8. Process & Operations | Future | TBD |

---

## Contributing

GTM Wizard is an open-source project. Contributions welcome!

### How to Contribute

1. **New tools**: Follow the tool design pattern in `src/gtm_wizard/tools/`
2. **New resources**: Add markdown files to `src/gtm_wizard/resources/`
3. **New prompts**: Add to `GTM_PROMPTS` in `server.py`

### Development Setup

```bash
cd /path/to/gtm-wizard
uv sync --all-extras
make all  # format, lint, type-check, test
```

### Content Guidelines

All content must follow the **Agentic GTM** philosophy:

- **Action-oriented** - Tools DO things, they don't explain things
- **Structured outputs** - Produce configs, blueprints, decisions that can be used downstream
- **Context-flexible** - Adapt to different scenarios without rigid templates
- **Integration-ready** - Design with future tool connections in mind
- **Expert application** - Apply GTM expertise, don't lecture about it

---

## Links

- **Repository**: https://github.com/MathewJoseph1993/gtm-wizard
- **Domain**: gtmwizard.io
- **MCP Protocol**: https://modelcontextprotocol.io
