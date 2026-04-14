# AI Prompt Templates for Segment Workspace Analysis

These prompts are designed to be used with your exported Segment workspace markdown file. Copy the markdown export, then use one of these prompts to get targeted analysis.

---

## 🎯 Quick Start Prompts

### General Health Check
```
I'm attaching my Segment workspace audit. Please analyze it and provide:
1. Top 3 critical issues that need immediate attention
2. Top 3 quick wins for optimization
3. Overall health score with justification
4. Priority action items ranked by impact vs. effort
```

### Executive Summary
```
Please review this Segment workspace audit and create an executive summary for leadership covering:
- Current state assessment (3-5 bullets)
- Key risks and their business impact
- ROI opportunities from optimization
- Recommended budget/resource allocation for next quarter
- Comparison against industry best practices
```

---

## 🔍 Deep Dive Analysis Prompts

### Data Quality & Governance
```
Analyze this Segment workspace for data quality and governance issues:
1. Identify naming convention inconsistencies across sources, events, and destinations
2. Flag potential duplicate or redundant tracking (same events from multiple sources)
3. Assess identity resolution configuration for gaps or conflicts
4. Review computed traits for optimization opportunities (can any be simplified?)
5. Identify sources or destinations that appear misconfigured or underutilized
6. Recommend a data governance framework based on current state

Focus on actionable recommendations with specific examples from the data.
```

### Architecture Review
```
Review the Segment architecture in this audit and provide:
1. Source architecture analysis: Are sources properly organized by environment/purpose?
2. Destination strategy: Identify redundant destinations or missing critical destinations
3. Data flow optimization: Suggest consolidation opportunities
4. Personas/Engage architecture: Assess space strategy and shadow source patterns
5. Warehouse setup: Evaluate warehouse connections and sync patterns
6. Scalability assessment: Will this architecture handle 10x growth?

Include a recommended target architecture diagram (in text/ASCII).
```

### Cost Optimization
```
Analyze this workspace for cost optimization opportunities:
1. Calculate MTU usage patterns across sources (identify spikes or waste)
2. Identify low-value destinations that could be retired
3. Find computed traits or audiences that are unused or redundant
4. Assess RETL model efficiency
5. Recommend consolidation opportunities for sources
6. Estimate potential cost savings for each recommendation

Prioritize recommendations by potential savings vs. implementation effort.
```

### Event Strategy Review
```
Review the event tracking strategy in this workspace:
1. Assess event volume distribution - are events well-balanced or dominated by a few sources?
2. Identify event tracking patterns (page vs track vs identify usage)
3. Flag potential over-instrumentation or under-instrumentation
4. Evaluate event naming patterns for consistency
5. Recommend an optimal event taxonomy for this business
6. Identify gaps in tracking critical user journeys

Consider the workspace maturity level in your recommendations.
```

---

## 🚀 Use Case Specific Prompts

### Marketing Activation Analysis
```
I'm a marketing leader reviewing this Segment workspace. Please analyze:
1. Which audience destinations are set up and how effectively are they used?
2. Are there gaps in our marketing tool stack based on the destinations?
3. Review journey/campaign setup - are we maximizing Engage capabilities?
4. Identify opportunities for better personalization using existing data
5. Recommend new destinations or integrations to improve marketing performance
6. Assess if identity resolution is sufficient for cross-channel attribution

Provide recommendations that balance quick wins with strategic improvements.
```

### Product Analytics Setup
```
As a product manager, I want to understand our analytics setup:
1. Which product analytics tools are we sending data to?
2. Are we tracking the right events for product insights (funnels, retention, etc.)?
3. Identify gaps in user behavior tracking
4. Assess if we have proper experiment/feature flag tracking
5. Review if computed traits support product-led growth metrics
6. Recommend improvements to support better product decisions

Focus on actionable changes that improve product team velocity.
```

### Customer Data Platform Strategy
```
Evaluate this workspace as a CDP implementation:
1. How well does the architecture support a unified customer view?
2. Is identity resolution configured optimally for this business?
3. Are we effectively using Personas/Profiles capabilities?
4. Assess real-time vs batch data strategies
5. Evaluate if the warehouse is being used as a strategic data asset
6. Identify gaps between CDP capabilities and actual implementation
7. Recommend a roadmap to maximize CDP value

Consider this workspace's industry and use case in your assessment.
```

### Compliance & Privacy Review
```
Review this workspace for privacy and compliance considerations:
1. Identify sources that may be collecting PII without proper consent management
2. Assess if destinations handling PII have appropriate privacy settings
3. Review if identity resolution configuration creates privacy risks
4. Flag any destinations sending data to regions with data residency concerns
5. Evaluate if data retention policies are properly configured
6. Recommend privacy-by-design improvements
7. Create a compliance checklist for GDPR/CCPA readiness

Highlight high-risk areas that need immediate attention.
```

---

## 🛠️ Technical Implementation Prompts

### Migration Planning
```
We're planning to migrate/consolidate sources in this workspace. Please:
1. Identify sources that are good candidates for consolidation
2. Create a migration risk assessment for each source
3. Recommend a migration sequence (dependencies, lowest risk first)
4. Identify downstream impacts on destinations and computed traits
5. Estimate migration complexity and effort for each source
6. Create a testing checklist for post-migration validation

Provide a step-by-step migration plan with rollback procedures.
```

### Troubleshooting Guide
```
Based on this workspace configuration, create a troubleshooting guide for common issues:
1. If events aren't appearing in destination X, what should I check?
2. If MTUs spike unexpectedly, where should I investigate?
3. If identity resolution isn't working, what are likely culprits?
4. If computed traits aren't computing, what could be wrong?
5. If warehouse syncs are failing, what should I verify?

Include specific commands, API calls, or queries to diagnose issues.
```

### Onboarding New Team Members
```
Create an onboarding guide for new engineers joining this Segment workspace:
1. Explain the overall architecture and data flow
2. List the most important sources and what they track
3. Explain the destination strategy and why each destination exists
4. Describe the Personas/Engage setup and space strategy
5. Provide a glossary of key terms specific to this workspace
6. List common tasks and how to accomplish them
7. Include links to relevant documentation sections

Make this practical and example-driven for quick ramp-up.
```

---

## 📊 Reporting & Documentation Prompts

### Quarterly Business Review
```
Create a QBR presentation outline based on this workspace audit:
1. Workspace growth metrics (sources, destinations, MTUs, events)
2. Key accomplishments this quarter (new integrations, optimizations)
3. Data quality improvements and impact
4. Cost metrics and optimization savings
5. Upcoming initiatives and roadmap
6. Team asks (budget, resources, tools)

Format as slide-by-slide outline with talking points.
```

### Technical Documentation
```
Generate comprehensive technical documentation for this workspace:
1. Architecture overview with data flow diagrams (text-based)
2. Source inventory with purpose, owner, and criticality
3. Destination matrix showing which sources send to which destinations
4. Personas/Engage configuration documentation
5. Naming conventions and standards (inferred from current state)
6. Troubleshooting decision trees
7. Runbook for common operations

Use a format that can be dropped into a wiki or Notion.
```

### Audit Trail for Compliance
```
Create an audit trail document for compliance purposes:
1. Inventory all data collection points (sources) and data types
2. Map data flows from sources through destinations
3. Document PII handling and retention policies
4. List all third-party data processors (destinations)
5. Track consent management implementation
6. Document data deletion/right-to-be-forgotten capabilities
7. Create a data lineage chart

Format for submission to compliance/legal teams.
```

---

## 🎓 Learning & Best Practices

### Segment Maturity Assessment
```
Assess this workspace's maturity across Segment's capabilities:
1. Rate maturity (1-5) for: Sources, Destinations, Identity Resolution, Personas, Protocols, Warehouses
2. For each area, explain the rating with specific evidence
3. Compare against the maturity framework in the audit
4. Create a roadmap to advance one level in each area
5. Identify prerequisites and blockers for advancing
6. Estimate effort/time for each maturity increase

Provide a visual maturity matrix if possible.
```

### Benchmarking Analysis
```
Compare this workspace against Segment best practices and typical implementations:
1. Source-to-destination ratio - are we over/under connected?
2. MTU per source - are any sources anomalous?
3. Computed trait complexity - are we using them effectively?
4. Destination categories - are we missing critical tools?
5. Identity resolution - are we using advanced features?
6. Event volume patterns - how do we compare?

Highlight areas where we're ahead or behind the curve.
```

### Training Recommendations
```
Based on this workspace, recommend team training priorities:
1. What Segment features are we not using that we should be?
2. What areas show signs of misunderstanding (antipatterns)?
3. Which team members need training on what topics?
4. Should we focus on best practices, advanced features, or troubleshooting?
5. Create a learning path with specific topics in priority order

Include links to relevant Segment documentation for each topic.
```

---

## 💡 Innovation & Experimentation

### New Capability Ideas
```
Based on the data in this workspace, suggest innovative use cases:
1. Untapped personalization opportunities with existing data
2. New audience segments we could create for better targeting
3. Predictive models we could build with warehouse data
4. Real-time use cases enabled by event triggers
5. Cross-product/cross-channel experiences we could enable
6. Data products we could build for other teams

Focus on ideas that leverage existing infrastructure with minimal new data collection.
```

### Experimental Hypotheses
```
Generate data-driven hypotheses we could test:
1. Based on event volumes, what user behaviors warrant deeper investigation?
2. What A/B tests would benefit from Segment's experimentation tools?
3. Which computed traits could we test for improving conversion?
4. What audience segments should we test in different destinations?
5. Which data gaps, if filled, would unlock new insights?

Provide a testing plan for the top 3 hypotheses.
```

---

## 🔧 Custom Analysis Prompts

### Compare Before/After
```
[Upload two audit exports from different time periods]

Compare these two Segment workspace audits and identify:
1. What sources/destinations were added or removed?
2. How did event volumes change?
3. Did data quality improve or degrade?
4. Were there architectural improvements?
5. What optimization efforts had measurable impact?
6. What new capabilities were enabled?

Create a change summary with impact assessment.
```

### Multi-Workspace Analysis
```
[Upload multiple workspace audits]

Compare these Segment workspaces:
1. Identify common patterns and antipatterns
2. Which workspace is best-in-class for each capability?
3. What unique approaches should be shared across workspaces?
4. Are there opportunities for consolidation?
5. How can we standardize while preserving flexibility?

Create a cross-workspace best practices guide.
```

---

## 📝 How to Use These Prompts

1. **Export your markdown**: Click "✨ AI Export" in the dashboard
2. **Choose a prompt**: Pick the prompt that matches your goal
3. **Submit to Claude**: Paste the prompt + markdown into Claude.ai or Claude Code
4. **Iterate**: Ask follow-up questions to dive deeper
5. **Act**: Turn insights into tickets, docs, or presentations

## 🎯 Pro Tips

- **Be specific**: Modify prompts to mention your industry, company stage, or specific concerns
- **Combine prompts**: Use multiple prompts in sequence for comprehensive analysis
- **Add context**: Include business goals, team size, or constraints in your prompt
- **Request formats**: Specify if you want output as slides, tickets, code, or documentation
- **Iterate**: Start broad, then ask targeted follow-ups based on initial insights

---

## 🤖 Advanced Prompt Engineering

### Chain-of-Thought Analysis
```
Analyze this Segment workspace using chain-of-thought reasoning:

First, summarize what type of business this appears to be based on source names and event patterns.

Then, evaluate if the Segment implementation matches expected patterns for this business type.

Next, identify the top 3 gaps between best practices and current state.

Finally, create a prioritized action plan with clear reasoning for each priority.

Show your reasoning at each step.
```

### Role-Based Analysis
```
Analyze this workspace from three perspectives:

1. As a data engineer: Focus on data quality, pipeline health, and technical debt
2. As a marketing ops manager: Focus on activation, audiences, and campaign capability
3. As a product manager: Focus on analytics, experimentation, and user insights

For each role, provide top priorities and quick wins.
```

---

*Last updated: 2026-04-14*
*Compatible with Segment Audit Dashboard v1.0*
