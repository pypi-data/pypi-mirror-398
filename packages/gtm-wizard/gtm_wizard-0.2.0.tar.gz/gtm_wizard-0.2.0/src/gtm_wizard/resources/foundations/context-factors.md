# Context Factors: How to Adapt GTM Approaches

## The Core Principle

> **There is no universal "best practice" in GTM Engineering. There is only "best for this context."**

A 4-gate qualification system that works for a $25M ARR enterprise company would be overkill for a bootstrapped startup. A simple lead scoring model that works for SMB sales would fail for Fortune 500 targeting.

This document helps you identify the context factors that should shape your approach.

## The 8 Context Factors

### 1. Company Stage

| Stage | Characteristics | GTM Implications |
|-------|-----------------|------------------|
| **Pre-revenue** | No customers yet, validating product | Manual processes OK, learning > efficiency |
| **Early ($0-1M ARR)** | First customers, finding PMF | Simple systems, fast iteration, founder-led sales |
| **Growth ($1-10M ARR)** | Scaling what works | Automation becomes critical, hire specialists |
| **Scale ($10-50M ARR)** | Optimizing efficiency | Sophisticated systems, dedicated GTM team |
| **Enterprise ($50M+ ARR)** | Maximizing performance | Complex architecture, multiple specialists |

**How to adapt:**
- Early stage: Favor simplicity, don't over-engineer
- Growth stage: Build for scale, but stay flexible
- Scale/Enterprise: Invest in robustness, handle edge cases

---

### 2. GTM Motion

| Motion | Definition | System Needs |
|--------|------------|--------------|
| **Sales-Led** | Humans drive the sale, product supports | Outbound automation, CRM, pipeline management |
| **Product-Led (PLG)** | Product drives adoption, sales assists | Product analytics, PQL identification, usage triggers |
| **Marketing-Led** | Inbound content drives leads | Attribution, nurturing, lead scoring |
| **Channel/Partner** | Partners sell for you | Partner enablement, deal registration |
| **Hybrid** | Multiple motions combined | Integration between systems, segment routing |

**How to adapt:**
- Sales-led: Focus on prospecting, qualification, pipeline systems
- Product-led: Focus on activation, engagement, conversion triggers
- Marketing-led: Focus on attribution, nurturing, scoring
- Hybrid: Build routing logic to direct leads to right motion

---

### 3. Average Deal Size (ACV)

| ACV Range | Sales Approach | System Complexity |
|-----------|----------------|-------------------|
| **< $1K** | Self-serve, no-touch | High automation, low personalization |
| **$1K - $10K** | Low-touch, transactional | Balanced automation + human touch |
| **$10K - $50K** | Mid-touch, consultative | More qualification, some personalization |
| **$50K - $250K** | High-touch, enterprise | Deep qualification, high personalization |
| **$250K+** | Strategic, multi-stakeholder | Account-based, highly customized |

**How to adapt:**
- Low ACV: Automate everything possible, volume matters
- High ACV: Invest in personalization, quality over quantity
- The higher the ACV, the more qualification gates make sense

---

### 4. Sales Cycle Length

| Cycle Length | Characteristics | System Needs |
|--------------|-----------------|--------------|
| **< 14 days** | Fast, transactional | Speed optimization, instant response |
| **14-30 days** | Standard B2B | Sequencing, follow-up automation |
| **30-90 days** | Consultative | Multi-touch nurturing, stakeholder mapping |
| **90+ days** | Enterprise | Long-term engagement, relationship tracking |

**How to adapt:**
- Short cycles: Optimize for speed, reduce friction
- Long cycles: Build nurturing, multi-stakeholder awareness
- Match follow-up cadences to cycle length

---

### 5. Target Market Segment

| Segment | Characteristics | Approach |
|---------|-----------------|----------|
| **SMB** | High volume, low complexity | Scale-focused, automated |
| **Mid-Market** | Balanced volume/complexity | Efficient processes, some customization |
| **Enterprise** | Low volume, high complexity | Highly customized, account-based |
| **Mixed** | Multiple segments | Routing logic, segment-specific tracks |

**How to adapt:**
- SMB: Optimize for throughput
- Enterprise: Optimize for fit and personalization
- Mixed: Build routing to different tracks

---

### 6. Industry/Vertical

Some industries have specific requirements:

| Factor | Examples | Implications |
|--------|----------|--------------|
| **Regulation** | Healthcare (HIPAA), Finance (SOX), EU (GDPR) | Compliance in data handling, messaging |
| **Buying patterns** | Government (RFP), Education (budget cycles) | Timing, process alignment |
| **Technical sophistication** | Tech companies vs traditional industries | Messaging complexity, channel preferences |

**How to adapt:**
- Know the vertical's constraints
- Align with buying cycles
- Adjust messaging sophistication

---

### 7. Team Size & Resources

| Team Size | Who Does GTM | System Needs |
|-----------|--------------|--------------|
| **Solo founder** | Founder does everything | Maximum automation, minimum maintenance |
| **Small team (2-5)** | Shared responsibilities | Clear handoffs, simple workflows |
| **Dedicated GTM (5-15)** | Specialists emerging | Role-specific tools, integration |
| **Large GTM (15+)** | Full specialization | Complex orchestration, governance |

**How to adapt:**
- Small teams: Favor simplicity, avoid tool sprawl
- Large teams: Invest in governance, documentation
- Match system complexity to team capacity to maintain it

---

### 8. Current Maturity

| Maturity Level | Characteristics | Priority |
|----------------|-----------------|----------|
| **None** | No systems, all manual | Build foundations, quick wins |
| **Basic** | CRM exists, some automation | Fill gaps, improve reliability |
| **Established** | Working systems, some issues | Optimize, scale, fix leaks |
| **Advanced** | Sophisticated, well-maintained | Innovate, experiment, edge cases |

**How to adapt:**
- Low maturity: Start with foundations, don't skip steps
- High maturity: Look for marginal gains, innovation opportunities

---

## Context Discovery Questions

When approaching any GTM problem, ask:

### Business Context
1. What's your company stage? (ARR range)
2. What's your primary GTM motion? (Sales-led, PLG, etc.)
3. What's your average deal size?
4. How long is your typical sales cycle?
5. Who's your target customer? (SMB, Mid-market, Enterprise)

### Technical Context
6. What CRM do you use?
7. What automation tools are in your stack?
8. What's your team's technical capability?
9. How many people touch these systems?

### Current State
10. What systems exist today?
11. What's working? What's broken?
12. What's the biggest bottleneck?
13. What have you tried that didn't work?

### Constraints
14. What's your budget for tools?
15. What's your timeline?
16. Any compliance or regulatory constraints?
17. What's non-negotiable?

---

## The Adaptation Framework

When designing any GTM system, use this framework:

```
1. IDENTIFY CONTEXT
   - Stage, motion, ACV, cycle, segment, resources

2. SELECT APPROPRIATE COMPLEXITY
   - Simple (low ACV, early stage, small team)
   - Moderate (mid-market, growth stage)
   - Complex (enterprise, scale stage, large team)

3. CHOOSE PATTERNS THAT FIT
   - Don't copy someone else's system
   - Adapt principles to your context
   - Start simpler than you think you need

4. BUILD WITH EVOLUTION IN MIND
   - What will change as you grow?
   - Where are the extension points?
   - What should you NOT build yet?

5. VALIDATE AND ITERATE
   - Does it actually work for this context?
   - What feedback are you getting?
   - What needs to change?
```

---

## Common Mistakes

### 1. Over-Engineering Too Early
**Mistake:** Building a 4-gate qualification system when you have 50 leads/month
**Fix:** Match system complexity to volume

### 2. Copying Without Context
**Mistake:** Implementing exactly what a $100M company does when you're at $1M
**Fix:** Understand WHY they do it, then adapt to your context

### 3. Ignoring Maintenance Burden
**Mistake:** Building complex systems a small team can't maintain
**Fix:** Factor in ongoing maintenance, not just initial build

### 4. Not Evolving
**Mistake:** Keeping the same systems as you 10x in size
**Fix:** Plan for evolution, rebuild when context changes significantly

---

## Key Insight

> **The best GTM Engineers don't apply templates. They understand principles and adapt them to context.**

The same problem (lead qualification) might need:
- A simple threshold for a $10K ACV SMB business
- A multi-gate AI system for a $500K ACV enterprise business
- A product-usage model for a PLG company

Context determines everything.

---

*This content is part of the GTM Wizard knowledge base - teaching AI agents to adapt to user context rather than apply universal templates.*
