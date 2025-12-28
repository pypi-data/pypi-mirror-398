# GTM Knowledge Taxonomy

This document maps the complete landscape of GTM Engineering knowledge. It serves as the blueprint for what GTM Wizard covers and guides content development.

## How to Read This Taxonomy

Each domain contains:
- **Sub-topics**: Specific areas of knowledge
- **MCP Components**: What we'll build (Tools, Prompts, Resources)
- **Expertise Level**: Author's depth (Expert/Advanced/Learning)
- **Priority**: Build order (P1 = first, P2 = second, etc.)

---

## Domain Overview

| # | Domain | Sub-topics | Priority | Status |
|---|--------|------------|----------|--------|
| 0 | Foundations | 4 | P0 | Complete |
| 1 | Lead Qualification & Scoring | 6 | P1 | Next |
| 2 | Infrastructure & Architecture | 5 | P1 | Planned |
| 3 | Signal Source Aggregation | 4 | P2 | Planned |
| 4 | Integration Patterns | 5 | P2 | Planned |
| 5 | Email Infrastructure | 4 | P3 | Planned |
| 6 | Multi-Channel Orchestration | 4 | P3 | Planned |
| 7 | RevOps & Analytics | 5 | P4 | Learning |
| 8 | PLG & Product Signals | 4 | P4 | Learning |

---

## Domain 0: Foundations (Complete)

**Purpose:** Core knowledge every GTM Engineer needs before diving into specifics.

| Sub-topic | MCP Component | Type | Status |
|-----------|---------------|------|--------|
| What is GTM Engineering | `gtm://foundations/what-is-gtm-engineering` | Resource | Complete |
| GTM Archetypes | `gtm://foundations/gtm-archetypes` | Resource | Complete |
| Context Factors | `gtm://foundations/context-factors` | Resource | Complete |
| Principles vs Recipes | `gtm://foundations/principles-not-recipes` | Resource | Complete |

---

## Domain 1: Lead Qualification & Scoring (P1 - Next)

**Purpose:** How to evaluate, score, and prioritize leads for sales engagement.

**Expertise Level:** Expert (Rwazi production systems)

### Sub-topics

| Sub-topic | Description | Expertise |
|-----------|-------------|-----------|
| Qualification Logic | Deciding if a lead is worth pursuing | Expert |
| Scoring Models | Assigning numeric values to lead attributes | Expert |
| Role Classification | Mapping titles to decision-making tiers | Expert |
| Industry Classification | Categorizing companies by fit | Expert |
| Routing Rules | Directing leads to appropriate tracks | Expert |
| Disqualification | Identifying leads to reject (competitors, bad fit) | Expert |

### Planned MCP Components

| Component | Type | Description | Priority |
|-----------|------|-------------|----------|
| `score_lead` | Tool | Calculate lead score with breakdown | P1 |
| `classify_role` | Tool | Map job title to tier (C-level, VP, etc.) | P1 |
| `classify_industry` | Tool | Determine industry fit tier | P1 |
| `determine_routing` | Tool | Recommend routing track | P1 |
| `check_disqualification` | Tool | Check for disqualifying factors | P1 |
| `design_scoring_model` | Prompt | Guide building a custom scoring model | P1 |
| `design_qualification_gates` | Prompt | Design multi-gate qualification | P1 |
| `gtm://qualification/scoring-principles` | Resource | Principles of lead scoring | P1 |
| `gtm://qualification/role-hierarchy` | Resource | Standard role classifications | P1 |
| `gtm://qualification/industry-tiers` | Resource | Industry fit framework | P1 |

### Key Principles (from Rwazi experience)

1. **Fail-fast design**: Put high-rejection gates first to save processing cost
2. **Context-dependent scoring**: Weights should reflect YOUR conversion data
3. **Clear pass/fail criteria**: Ambiguity slows down automation
4. **Capacity-matched thresholds**: Strict when volume > capacity
5. **Model decay**: Scoring models need recalibration over time

---

## Domain 2: Infrastructure & Architecture (P1)

**Purpose:** Building reliable, scalable systems for GTM operations.

**Expertise Level:** Expert (Railway/n8n production systems)

### Sub-topics

| Sub-topic | Description | Expertise |
|-----------|-------------|-----------|
| Queue-Based Processing | Handling high-volume lead flows | Expert |
| Rate Limiting | Managing API constraints | Expert |
| Error Handling | Recovering from failures gracefully | Expert |
| Guaranteed Delivery | Ensuring no data loss | Expert |
| Scaling Patterns | When/how to add capacity | Advanced |

### Planned MCP Components

| Component | Type | Description | Priority |
|-----------|------|-------------|----------|
| `diagnose_rate_limiting` | Tool | Debug rate limit issues | Complete |
| `calculate_capacity` | Tool | Estimate system capacity needs | P1 |
| `design_queue_architecture` | Prompt | Design queue-based processing | P1 |
| `diagnose_data_loss` | Prompt | Find where leads are dropping | P1 |
| `gtm://infrastructure/queue-patterns` | Resource | Queue architecture patterns | P1 |
| `gtm://infrastructure/rate-limits` | Resource | Common API rate limits | P1 |
| `gtm://infrastructure/error-handling` | Resource | Error recovery patterns | P2 |

### Key Principles

1. **Immediate acknowledgment**: Accept webhooks instantly, process async
2. **Idempotency**: Handle duplicate events gracefully
3. **Dead letter queues**: Capture failures for retry/investigation
4. **Backpressure handling**: Don't overwhelm downstream systems
5. **Observability**: Log enough to debug without overwhelming storage

---

## Domain 3: Signal Source Aggregation (P2)

**Purpose:** Capturing and unifying leads from multiple sources.

**Expertise Level:** Expert (7 signal sources at Rwazi)

### Sub-topics

| Sub-topic | Description | Expertise |
|-----------|-------------|-----------|
| Intent Signals | Website visitors, product usage | Expert |
| Social Signals | LinkedIn engagement, content interaction | Expert |
| Direct Outreach | Cold prospecting lists | Expert |
| Inbound Signals | Form fills, demo requests | Advanced |

### Planned MCP Components

| Component | Type | Description | Priority |
|-----------|------|-------------|----------|
| `evaluate_signal_quality` | Tool | Assess signal source value | P2 |
| `design_signal_stack` | Prompt | Plan multi-source capture | P2 |
| `gtm://signals/source-types` | Resource | Overview of signal sources | P2 |
| `gtm://signals/intent-scoring` | Resource | Intent signal weighting | P2 |

### Key Principles

1. **Source attribution**: Always know where leads came from
2. **Deduplication**: Same person from multiple sources = one lead
3. **Signal decay**: Recent signals > old signals
4. **Source quality tracking**: Measure conversion by source

---

## Domain 4: Integration Patterns (P2)

**Purpose:** Connecting GTM tools into cohesive workflows.

**Expertise Level:** Expert (Clay → n8n → HubSpot at Rwazi)

### Sub-topics

| Sub-topic | Description | Expertise |
|-----------|-------------|-----------|
| CRM Integration | Syncing with Salesforce/HubSpot | Expert |
| Enrichment Pipelines | Data enrichment workflows | Expert |
| Outreach Integration | Connecting to email/LinkedIn tools | Expert |
| Webhook Design | Reliable webhook handling | Expert |
| Data Transformation | Mapping between systems | Advanced |

### Planned MCP Components

| Component | Type | Description | Priority |
|-----------|------|-------------|----------|
| `validate_integration` | Tool | Check integration configuration | P2 |
| `design_enrichment_pipeline` | Prompt | Plan data enrichment flow | P2 |
| `design_crm_sync` | Prompt | Plan CRM integration | P2 |
| `gtm://integrations/clay-patterns` | Resource | Clay integration patterns | P2 |
| `gtm://integrations/webhook-best-practices` | Resource | Webhook design patterns | P2 |

### Key Principles

1. **Single source of truth**: One system owns each data type
2. **Bi-directional sync**: Both systems stay updated
3. **Conflict resolution**: Rules for handling mismatches
4. **Audit trails**: Track what changed and when

---

## Domain 5: Email Infrastructure (P3)

**Purpose:** Building and maintaining email sending capability at scale.

**Expertise Level:** Advanced (200 inbox architecture at Rwazi)

### Sub-topics

| Sub-topic | Description | Expertise |
|-----------|-------------|-----------|
| Inbox Architecture | Multi-domain, multi-inbox setup | Advanced |
| Warmup Protocols | Preparing domains for sending | Advanced |
| Deliverability | Getting to inbox, not spam | Advanced |
| Domain Health | Monitoring and maintenance | Advanced |

### Planned MCP Components

| Component | Type | Description | Priority |
|-----------|------|-------------|----------|
| `calculate_inbox_capacity` | Tool | Estimate sending capacity | P3 |
| `design_email_infrastructure` | Prompt | Plan inbox architecture | P3 |
| `diagnose_deliverability` | Prompt | Debug deliverability issues | P3 |
| `gtm://email/infrastructure-patterns` | Resource | Email architecture guide | P3 |
| `gtm://email/warmup-protocols` | Resource | Domain warmup guide | P3 |

### Key Principles

1. **Domain diversity**: Spread risk across multiple domains
2. **Gradual warmup**: Don't rush new domain sending
3. **Monitor reputation**: Track bounce rates, spam complaints
4. **Replace, don't heal**: Burn a domain? Start fresh

---

## Domain 6: Multi-Channel Orchestration (P3)

**Purpose:** Coordinating outreach across email, LinkedIn, phone, etc.

**Expertise Level:** Advanced (LinkedIn + Email at Rwazi)

### Sub-topics

| Sub-topic | Description | Expertise |
|-----------|-------------|-----------|
| Sequence Design | Multi-touch, multi-channel flows | Advanced |
| Channel Selection | Which channel for which persona | Advanced |
| Timing & Cadence | When to send, how often | Advanced |
| Reply Handling | Processing and routing responses | Expert |

### Planned MCP Components

| Component | Type | Description | Priority |
|-----------|------|-------------|----------|
| `design_sequence` | Prompt | Plan multi-channel sequence | P3 |
| `recommend_channel` | Tool | Suggest best channel for lead | P3 |
| `gtm://orchestration/sequence-patterns` | Resource | Sequence design patterns | P3 |
| `gtm://orchestration/channel-selection` | Resource | Channel selection guide | P3 |

### Key Principles

1. **Channel preference**: Respect how people want to be contacted
2. **Coordinated timing**: Don't spam across channels simultaneously
3. **Response priority**: Reply handling trumps new outreach
4. **Graceful escalation**: Move up channels (email → LinkedIn → phone)

---

## Domain 7: RevOps & Analytics (P4 - Learning)

**Purpose:** Measuring, forecasting, and optimizing revenue operations.

**Expertise Level:** Learning (opportunity for growth)

### Sub-topics

| Sub-topic | Description | Expertise |
|-----------|-------------|-----------|
| Pipeline Analytics | Measuring funnel health | Learning |
| Forecasting | Predicting revenue outcomes | Learning |
| Attribution | Crediting conversion sources | Learning |
| Revenue Metrics | CAC, LTV, NRR calculations | Learning |
| Process Optimization | Improving operational efficiency | Advanced |

### Planned MCP Components (Future)

| Component | Type | Description | Priority |
|-----------|------|-------------|----------|
| `calculate_pipeline_metrics` | Tool | Compute pipeline health metrics | P4 |
| `design_attribution_model` | Prompt | Plan attribution approach | P4 |
| `gtm://revops/metrics-guide` | Resource | Revenue metrics explained | P4 |
| `gtm://revops/forecasting-methods` | Resource | Forecasting approaches | P4 |

### Learning Notes

This domain represents a growth area. Content will be added as expertise develops through:
- Studying RevOps frameworks
- Learning from community contributions
- Applying concepts in practice

---

## Domain 8: PLG & Product Signals (P4 - Learning)

**Purpose:** Product-led growth motions and product usage signals.

**Expertise Level:** Learning (opportunity for growth)

### Sub-topics

| Sub-topic | Description | Expertise |
|-----------|-------------|-----------|
| PQL Identification | Finding product-qualified leads | Learning |
| Activation Tracking | Measuring time-to-value | Learning |
| Usage Scoring | Scoring based on product behavior | Learning |
| Expansion Triggers | Identifying upsell opportunities | Learning |

### Planned MCP Components (Future)

| Component | Type | Description | Priority |
|-----------|------|-------------|----------|
| `identify_pql_signals` | Tool | Define PQL criteria | P4 |
| `design_activation_funnel` | Prompt | Plan activation tracking | P4 |
| `gtm://plg/pql-framework` | Resource | PQL identification guide | P4 |
| `gtm://plg/activation-metrics` | Resource | Activation measurement guide | P4 |

### Learning Notes

PLG is a distinct motion from sales-led. Content will be developed through:
- Studying PLG frameworks (ProductLed, OpenView)
- Learning from PLG practitioners
- Understanding product analytics tools

---

## Summary Statistics

### By Component Type

| Type | Planned | Complete | Remaining |
|------|---------|----------|-----------|
| Tools | 15+ | 1 | 14+ |
| Prompts | 12+ | 0 | 12+ |
| Resources | 20+ | 4 | 16+ |

### By Priority

| Priority | Domains | Focus |
|----------|---------|-------|
| P0 | Foundations | Complete |
| P1 | Qualification, Infrastructure | Expert areas, build first |
| P2 | Signals, Integrations | Strong areas, build second |
| P3 | Email, Orchestration | Advanced areas, build third |
| P4 | RevOps, PLG | Learning areas, build as expertise grows |

### By Expertise Level

| Level | Domains | Approach |
|-------|---------|----------|
| Expert | 1, 2, 3, 4 | Build from experience |
| Advanced | 5, 6 | Build with research |
| Learning | 7, 8 | Build as learning progresses |

---

## Usage Guidelines

### For Content Development

1. **Start with P1 domains** - Build where expertise is strongest
2. **Capture principles first** - Document the "why" before the "how"
3. **Test with real scenarios** - Validate tools against actual use cases
4. **Iterate based on feedback** - Improve based on usage

### For AI Agents Using This MCP

1. **Check context first** - Use foundations to understand user's situation
2. **Match expertise to need** - Don't recommend PLG tools for sales-led motions
3. **Acknowledge limitations** - Be honest about learning domains
4. **Reference principles** - Explain the "why" behind recommendations

---

*This taxonomy guides GTM Wizard development. It evolves as expertise grows and community feedback arrives.*
