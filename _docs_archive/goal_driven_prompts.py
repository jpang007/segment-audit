#!/usr/bin/env python3
"""
Goal-Driven Prompt System - User selects goal, system generates targeted recommendations

Goals:
1. Find Quick Wins - Low-effort, high-impact opportunities
2. Improve Data Strategy - Identity, events, audiences, governance
3. Generate Growth Use Cases - Lifecycle campaigns, behavioral targeting
4. Identify Expansion Opportunities - Unused destinations, upsell, activation gaps

Output Types:
1. Executive Summary - Customer-friendly, concise
2. Action Plan - Internal SA use, detailed steps
"""

import json
from typing import Dict, Any


class GoalDrivenPrompts:
    """
    Generates targeted prompts based on user's selected goal and output type

    Three distinct goals:
    1. Workspace Audit - Technical/strategic workspace analysis
    2. Growth Use Cases - Marketing/lifecycle activation ideas
    3. Activation & Expansion - Underutilization and upsell opportunities
    """

    @staticmethod
    def get_system_instructions() -> str:
        """System instructions for goal-driven analysis"""
        return """You are a Segment Solutions Architect conducting a workspace audit.

Your expertise:
- CDP architecture and data governance
- Audience activation strategies
- Marketing technology optimization
- Data utilization and workspace health

Your communication style:
- Evidence-based (only reference observable data)
- Consultative (diagnostic, not prescriptive)
- Specific (use actual names, numbers from data)
- Actionable (clear, realistic next steps)

Critical rules:
- Use ONLY the data provided
- Reference specific audiences, events, destinations by name
- No fabricated metrics or performance claims
- Clear about assumptions vs. observations"""

    @staticmethod
    def format_output_instructions(output_type: str) -> str:
        """Get format-specific instructions based on output type"""
        if output_type == "workspace_summary":
            return """
### Output Format: Workspace Summary (Narrative)

**CRITICAL**: Generate a readable NARRATIVE document, NOT JSON.

Structure as a clean, readable document with these sections:

---

## Workspace Overview
[2-3 sentences: workspace size, maturity, key characteristics]

## Key Findings
[3-5 bullet points of most important discoveries]

## Risks & Concerns
[List specific risks observed in the data with brief explanations]

## Opportunities
[List actionable opportunities with context]

## Recommended Next Steps
[Prioritized list of 3-5 concrete actions]

## Questions to Validate
[2-3 questions for the customer to confirm or clarify]

---

**Tone**: Consultative, concise, customer-friendly
**Length**: Readable in 2-3 minutes
**Style**: Clear narrative prose, not technical data dump
**Avoid**: Raw JSON, overly technical jargon, data tables

This should feel like a polished workspace health report you'd share with a customer.
"""
        else:  # recommended_actions
            return """
### Output Format: Recommended Actions (Structured JSON)

**CRITICAL**: Return structured JSON for internal SA/CSM use.

This is for execution and traceability - preserve all analysis and evidence.

Include:
- Prioritized action list with evidence
- Risk assessment with severity
- Audience opportunities with reach
- Source issues with impact
- All data that supports recommendations

**Tone**: Detailed, precise, data-backed
**Purpose**: Internal execution and system integration
**Style**: Structured, traceable, comprehensive
"""

    @staticmethod
    def goal_quick_wins(structured_data: Dict[str, Any], business_context: str, user_notes: str = "") -> str:
        """
        GOAL: Find Quick Wins
        Focus: Low-effort, high-impact opportunities based on observable data gaps
        """
        workspace = structured_data.get('workspace_summary', {})
        audiences = structured_data.get('audience_insights', [])
        sources = structured_data.get('source_insights', [])

        # Find obvious quick wins in data
        large_unactivated = [a for a in audiences if a.get('signal') == 'activation_opportunity' and a.get('size', 0) > 10000]

        return f"""## Evidence-Based Quick Wins Analysis

You are a Segment Solutions Architect identifying low-effort, high-value improvements.

{business_context}

{"### Customer Context: " + user_notes if user_notes else ""}

### Workspace Overview
- Total audiences: {workspace.get('total_audiences', 0)}
- Enabled audiences: {workspace.get('enabled_audiences', 0)}
- Audiences with users not activated: {len(large_unactivated)}
- Total addressable users: {workspace.get('total_users_in_audiences', 0):,}

### Critical Instructions

**DATA GROUNDING REQUIREMENTS:**
1. ONLY recommend actions based on observable gaps or unused resources
2. DO NOT claim specific performance improvements (e.g., "15% lift")
3. DO NOT invent thresholds or engagement metrics
4. Base recommendations ONLY on: audience state, destination connections, data collection gaps

**What makes a "Quick Win":**
- Uses resources that already exist (audiences built, destinations connected)
- Requires configuration, not development
- Addresses clear data gap or unused capability
- Implementable in <1 week

### Data Available
```json
{json.dumps(structured_data, indent=2)}
```

### Task: Identify 3-5 Quick Wins

Find opportunities where:
1. An audience exists with users but is not activated
2. A destination is connected but underutilized
3. A source is collecting events but not being used in audiences
4. Configuration issues (disabled audiences with users)

### Output Format

Return JSON with this EXACT structure:
```json
{{
  "quick_wins": [
    {{
      "opportunity": "Descriptive title using actual audience/destination names",
      "evidence": {{
        "data_signal": "What you observed (e.g., 'audience_va_subs has 144K users but 0 destinations')",
        "current_state": "Specific current configuration",
        "resources_available": ["What already exists that makes this quick"]
      }},
      "why_quick": {{
        "reason": "Explain why this is low-effort (be specific about what's already built)",
        "prerequisites_met": ["List what's already in place"],
        "complexity": "low"
      }},
      "impact": {{
        "reach": "Number of users affected (from data)",
        "impact_level": "high | medium | low",
        "reasoning": "Why this matters (based on size or strategic importance)",
        "assumptions": ["What we're assuming that isn't directly observable"]
      }},
      "implementation": {{
        "steps": [
          "Step 1: Specific action",
          "Step 2: Specific action",
          "Step 3: Specific action"
        ],
        "time_to_value": "Realistic estimate (e.g., '1-2 days', '3-5 days')",
        "owner": "Who would need to do this (e.g., 'Marketing Ops', 'Data team')"
      }},
      "confidence": "high | medium | low",
      "data_quality": "How confident are we in the data that supports this?"
    }}
  ],
  "summary": {{
    "total_quick_wins": 3,
    "aggregate_reach": "Total users across all quick wins",
    "highest_confidence": "Name of most data-grounded quick win",
    "implementation_priority": "Which to do first and why"
  }}
}}
```

### Tone Guidelines

Write as a Solutions Architect in a workspace review:
- Diagnostic: "I notice that..."
- Data-specific: Use exact names and numbers
- Actionable: Clear next steps
- Honest: Call out when you're making assumptions

DO NOT:
- Claim performance improvements (no "X% lift")
- Use marketing language ("unlock growth", "maximize ROI")
- Invent engagement metrics
- Speculate about business outcomes

DO:
- Reference specific audiences, destinations, and sources by name
- Use actual user counts from data
- Describe impact qualitatively (high/medium/low)
- Be clear about what's an assumption vs. observation

Generate quick wins now."""

    @staticmethod
    def goal_workspace_audit(structured_data: Dict[str, Any], business_context: str, user_notes: str = "", output_type: str = "recommended_actions") -> str:
        """
        GOAL 1: Workspace Audit
        Technical + strategic analysis of workspace health and architecture
        Focus: sources, events, audiences, destinations, risks, opportunities
        """
        workspace = structured_data.get('workspace_summary', {})
        audiences = structured_data.get('audience_insights', [])
        sources = structured_data.get('source_insights', [])

        return f"""## Workspace Audit - Technical & Strategic Analysis

You are a Segment Solutions Architect conducting a comprehensive workspace audit.

{business_context}

{"### Customer Context: " + user_notes if user_notes else ""}

### Workspace Snapshot
- Sources: {workspace.get('total_sources', 0)}
- Audiences: {workspace.get('total_audiences', 0)} ({workspace.get('enabled_audiences', 0)} enabled)
- Total users: {workspace.get('total_users_in_audiences', 0):,}

### Goal: Workspace Audit

This is a **technical + strategic assessment** covering:
1. **Sources & Events**: Data collection health, volumes, instrumentation quality
2. **Audience Health**: Usage patterns, redundancies, unactivated audiences
3. **Destination Coverage**: Activation strategy and gaps
4. **Key Risks**: Broken sources, stale data, governance issues
5. **Underutilized Data**: High-volume events not used, audiences not activated

### Critical Instructions

**DATA GROUNDING:**
- Analyze only what exists in the workspace data
- Identify patterns, gaps, and risks based on configuration
- Do NOT fabricate metrics or assume business context
- Be specific with names and numbers

**TONE:**
- Technical consultant conducting a workspace review
- Diagnostic and analytical, not prescriptive
- Honest about data limitations

### Data Available
```json
{json.dumps(structured_data, indent=2)}
```

### Output Format

Return JSON with this EXACT structure:
```json
{{
  "workspace_summary": {{
    "overall_health": "good | fair | poor",
    "health_summary": "2-3 sentence diagnostic summary",
    "key_metrics": {{
      "sources": 16,
      "audiences_total": 242,
      "audiences_activated": 120,
      "activation_rate": "50%",
      "total_addressable_users": 62000000
    }}
  }},
  "sources_and_events": {{
    "observations": [
      {{
        "finding": "Specific pattern or issue",
        "evidence": "What data shows this",
        "risk_level": "high | medium | low",
        "recommendation": "Actionable next step"
      }}
    ],
    "high_volume_events_unused": [
      {{
        "event_name": "actual event name",
        "volume": "observed or 'high'",
        "why_matters": "Opportunity this represents",
        "suggested_use": "How it could be activated"
      }}
    ]
  }},
  "audience_health": {{
    "unactivated_audiences": [
      {{
        "name": "audience_name",
        "size": 12345,
        "reason": "why not activated",
        "opportunity": "what could be done"
      }}
    ],
    "potential_redundancies": [
      {{
        "audiences": ["name1", "name2"],
        "similarity": "why they appear similar",
        "recommendation": "consolidate or clarify"
      }}
    ],
    "disabled_with_users": [
      {{
        "name": "audience_name",
        "user_count": 5000,
        "recommendation": "re-enable or archive"
      }}
    ]
  }},
  "destination_coverage": {{
    "connected_categories": ["email", "analytics", "ads"],
    "gaps": [
      {{
        "category": "missing category",
        "rationale": "why this gap matters based on data",
        "recommendation": "suggested destination type"
      }}
    ],
    "activation_coverage_assessment": "Brief summary of how well audiences are activated"
  }},
  "key_risks": [
    {{
      "risk": "Specific risk identified",
      "severity": "high | medium | low",
      "evidence": "What indicates this risk",
      "mitigation": "How to address"
    }}
  ],
  "top_opportunities": [
    {{
      "opportunity": "Specific opportunity",
      "evidence": "Data that supports this",
      "impact": "Why this matters",
      "next_step": "Concrete action"
    }}
  ]
}}
```

**Output Guidelines:**
- Write as if presenting audit findings to the customer
- Be diagnostic and specific
- Use actual resource names and numbers
- Honest about assumptions
- Focus on actionable insights

{GoalDrivenPrompts.format_output_instructions(output_type)}

Generate the workspace audit now."""

    @staticmethod
    def goal_growth_usecases(structured_data: Dict[str, Any], business_context: str, user_notes: str = "", output_type: str = "recommended_actions") -> str:
        """
        GOAL: Generate Growth / Marketing Use Cases
        Focus: Lifecycle campaigns, behavioral targeting, activation ideas
        """
        workspace = structured_data.get('workspace_summary', {})
        audiences = structured_data.get('audience_insights', [])
        destinations = structured_data.get('destination_summary', {})

        return f"""## Evidence-Based Growth Use Case Analysis

You are a Segment Solutions Architect conducting a workspace audit to identify growth opportunities.

{business_context}

{"### Customer Context: " + user_notes if user_notes else ""}

### Workspace Overview
- Total audiences: {workspace.get('total_audiences', 0)}
- Audiences with users: {len([a for a in audiences if a.get('size', 0) > 0])}
- Total addressable users: {workspace.get('total_users_in_audiences', 0):,}
- Connected destinations: {', '.join(destinations.get('all_destinations', [])[:5])}

### Critical Instructions - READ CAREFULLY

**DATA GROUNDING REQUIREMENTS:**
1. ONLY reference audiences, events, and destinations that exist in the data
2. DO NOT invent metrics, thresholds, or performance claims
3. DO NOT assume engagement rates, conversion rates, or ROI
4. Base ALL recommendations on observable data signals

**FORBIDDEN - Do NOT include:**
- Percentage lift estimates (e.g., "15-20% lift")
- ROI projections or revenue impact claims
- Fabricated behavioral triggers (e.g., "3+ opens in 48 hours")
- Engagement thresholds not present in data (e.g., "60% open rate")
- Marketing copy or promotional language

**REQUIRED - Every use case must have:**
- Evidence: What data signal supports this?
- Impact qualifier: high/medium/low (NOT percentages)
- Assumptions: What are you inferring?
- Data gaps: What would strengthen this recommendation?

### Data Available
```json
{json.dumps(structured_data, indent=2)}
```

### Task: Generate 3-5 Evidence-Based Growth Opportunities

Analyze the workspace data and identify opportunities where:
1. An audience exists but is not activated to relevant destinations
2. Event data suggests user behavior that could drive campaigns
3. Audience definitions indicate untapped segments

### Output Format

Return JSON with this EXACT structure:
```json
{{
  "use_cases": [
    {{
      "name": "Descriptive name based on audience/behavior",
      "category": "retention | acquisition | engagement | monetization",
      "evidence": {{
        "audience": "Exact audience name from data",
        "size": 12345,
        "current_state": "not activated | disabled | only sent to X",
        "data_signals": ["List specific signals from the data that support this"]
      }},
      "opportunity": {{
        "description": "What could be done with this audience (consultative tone)",
        "trigger_logic": "Describe based on audience definition or general behavior pattern - NO fabricated thresholds",
        "destination_recommendation": "Specific destination from available list OR category if none connected",
        "implementation_notes": "What needs to be done to activate this"
      }},
      "impact_assessment": {{
        "potential_reach": "Number from audience size",
        "impact_level": "high | medium | low",
        "reasoning": "Why this matters, based on audience size or business context",
        "assumptions": ["What are we inferring that isn't directly in the data?"],
        "confidence": "high | medium | low",
        "data_gaps": ["What additional data would strengthen this recommendation?"]
      }},
      "implementation": {{
        "complexity": "low | medium | high",
        "estimated_time": "Realistic timeframe",
        "prerequisites": ["What needs to exist or be done first"]
      }}
    }}
  ],
  "summary": {{
    "total_opportunities_identified": 3,
    "highest_confidence_use_case": "Name of most data-grounded recommendation",
    "data_quality_notes": "Brief assessment of how complete the data is for recommendations"
  }}
}}
```

### Tone Guidelines

Write as a Solutions Architect would in a customer conversation:
- Consultative and diagnostic (NOT marketing copy)
- Data-driven and analytical (NOT speculative)
- Actionable and realistic (NOT aspirational)
- Honest about assumptions and data gaps

Example phrases to USE:
- "Based on the [audience_name] audience definition..."
- "The data shows [X users] are currently not activated..."
- "This could enable campaigns, though exact engagement metrics would need to be measured..."

Example phrases to AVOID:
- "This will increase conversion by X%..."
- "Expected ROI of $X..."
- "Users who engage 3+ times..."
- "Drive significant revenue growth..."

{GoalDrivenPrompts.format_output_instructions(output_type)}

Generate recommendations now."""

    @staticmethod
    def goal_activation_expansion(structured_data: Dict[str, Any], business_context: str, user_notes: str = "", output_type: str = "recommended_actions") -> str:
        """
        GOAL 3: Activation & Expansion Opportunities
        Identify underutilization and areas where customer is leaving value on the table
        Focus: unused audiences, unused destinations, missing activation flows, Segment product opportunities
        """
        workspace = structured_data.get('workspace_summary', {})
        destinations = structured_data.get('destination_summary', {})
        audiences = structured_data.get('audience_insights', [])

        unactivated_users = sum(a.get('size', 0) for a in audiences if a.get('signal') == 'activation_opportunity')

        return f"""## Activation & Expansion Opportunities

You are a Segment Solutions Architect identifying where the customer is underutilizing Segment capabilities.

{business_context}

{"### Customer Context: " + user_notes if user_notes else ""}

### Workspace Snapshot
- Total audiences: {workspace.get('total_audiences', 0)}
- Audiences with destinations: {len([a for a in audiences if a.get('destination_count', 0) > 0])}
- Unactivated users in built audiences: {unactivated_users:,}
- Current destination categories: {', '.join(destinations.get('by_category', {}).keys()) if destinations.get('by_category') else 'None'}

### Goal: Identify Underutilization & Expansion Areas

Focus on where value is being left on the table:

1. **Unused Audiences** - Built but not activated to any destination
2. **Unused Destinations** - Connected but not receiving audiences
3. **Missing Activation Flows** - Data collected but not activated
4. **Segment Product Opportunities** - Engage, Profiles, rETL, new destinations

### Critical Instructions

**DATA GROUNDING:**
- Only identify gaps visible in the workspace data
- Do NOT fabricate revenue estimates or ROI
- Do NOT assume business priorities
- Be specific about what's unused vs. what's missing

**FORBIDDEN:**
- Revenue projections ("$X opportunity")
- Growth claims ("will increase revenue by X%")
- Assumptions about customer goals
- **DO NOT recommend Journeys/Campaigns if journey_insights.has_journeys=false** (means Engage not enabled)
- **DO NOT recommend Profiles API if profile_insights.has_profile_resolution=false** (feature not available)

### Data Available
```json
{json.dumps(structured_data, indent=2)}
```

### Output Format

Return JSON with this EXACT structure:
```json
{{
  "unused_audiences": [
    {{
      "audience_name": "exact name",
      "user_count": 12345,
      "status": "enabled | disabled",
      "opportunity": "what could be done with this",
      "blocking_factor": "why not activated (if observable)",
      "suggested_action": "specific next step (for disabled: 'Review why disabled. If still valid, consider enabling for...')",
      "estimated_effort": "low | medium | high",
      "owner": "SA | CSM | Customer Marketing | Customer Eng",
      "evidence": {{
        "audience_id": "audience ID from data",
        "space_id": "space ID from data",
        "destination_count": 0,
        "enabled": true
      }},
      "caveats": [
        "Validate audience definition before activation",
        "Confirm consent/compliance if syncing to ad destinations"
      ]
    }}
  ],
  "unused_destinations": [
    {{
      "destination_name": "exact name",
      "category": "email | analytics | ads | other",
      "connected_but_unused": true,
      "opportunity": "how this could be utilized",
      "suggested_audiences": ["audience names that fit"],
      "estimated_effort": "low | medium | high",
      "owner": "SA | CSM | Customer Marketing | Customer Eng",
      "caveats": [
        "Confirm destination is intentionally unused before activating",
        "Validate match rates and consent requirements for ad destinations"
      ]
    }}
  ],
  "missing_activation_flows": [
    {{
      "data_source": "source collecting data",
      "data_type": "events | traits | pages",
      "not_used_in": "audiences | destinations",
      "opportunity": "what could be built",
      "impact_level": "high | medium | low",
      "reasoning": "why this matters based on data",
      "estimated_effort": "low | medium | high",
      "owner": "SA | Customer Eng | Customer Data",
      "evidence": {{
        "source_id": "source ID from data",
        "source_status": "ENABLED | DISABLED | NO_RECENT_DATA",
        "destination_count": 0
      }}
    }}
  ],
  "segment_product_opportunities": [
    {{
      "product": "Engage | Profiles API | Reverse ETL | Connections",
      "evidence": "what in workspace suggests this",
      "use_case": "specific problem it would solve",
      "impact": "qualitative benefit",
      "confidence": "high | medium | low",
      "estimated_effort": "low | medium | high",
      "owner": "SA | CSM | Sales",
      "prerequisite": "Feature must be enabled (check journey_insights.has_journeys or profile_insights.has_profile_resolution)",
      "caveats": [
        "Requires product purchase if not currently enabled",
        "May require implementation/onboarding effort"
      ],
      "CRITICAL": "Check journey_insights.has_journeys before recommending Engage. If false, DO NOT recommend Journeys."
    }}
  ],
  "expansion_summary": {{
    "total_untapped_users": 50000,
    "total_untapped_users_definition": "Sum of enabled audiences with zero connected destinations (excludes disabled audiences)",
    "highest_impact_opportunity": "name of top opportunity",
    "quick_wins": ["list of easy activation opportunities"],
    "strategic_opportunities": ["list of longer-term expansion plays"]
  }}
}}
```

**Output Guidelines:**
- Be consultative, not sales-y
- Specific with names and numbers
- Honest about what would require customer input
- Focus on observable underutilization

**CRITICAL FEATURE AVAILABILITY CHECKS:**
- **Before recommending Engage (Journeys)**: Check if `journey_insights.has_journeys == true`
  - If `false`: Customer does NOT have Engage enabled, DO NOT recommend
  - If `true` but `maturity_level == "none"`: They have it but aren't using it
- **Before recommending Profiles API**: Check if `profile_insights.has_profile_resolution == true`
  - If `false`: Feature not configured, handle as expansion opportunity not activation gap

{GoalDrivenPrompts.format_output_instructions(output_type)}

Generate the analysis now."""

    @staticmethod
    def format_executive_summary(analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format analysis for Executive Summary (customer-facing)
        Concise, high-level, business-focused
        """
        return {
            "format": "executive_summary",
            "sections": {
                "overview": "2-3 sentence summary",
                "key_findings": "Top 3-5 findings only",
                "top_recommendations": "Top 3 actions",
                "expected_impact": "Quantified business value"
            },
            "tone": "customer-friendly, concise, business-focused"
        }

    @staticmethod
    def format_action_plan(analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format analysis for Action Plan (internal SA use)
        Detailed, technical, step-by-step
        """
        return {
            "format": "action_plan",
            "sections": {
                "situation_assessment": "Current state analysis",
                "all_findings": "Complete findings list",
                "action_steps": "Detailed implementation steps",
                "timeline": "Week-by-week plan",
                "success_metrics": "How to measure success",
                "technical_notes": "Implementation details"
            },
            "tone": "internal-facing, technical, comprehensive"
        }


# CLI testing
if __name__ == '__main__':
    print("=== GOAL-DRIVEN PROMPT SYSTEM ===\n")

    prompts = GoalDrivenPrompts()

    sample_data = {
        "workspace_summary": {
            "total_audiences": 239,
            "enabled_audiences": 166,
            "total_users_in_audiences": 62000000
        },
        "audience_insights": [
            {
                "name": "audience_va_subs",
                "size": 144765,
                "signal": "activation_opportunity",
                "destination_count": 0
            }
        ]
    }

    business_context = "Media/Publishing company, Subscription model"

    print("1. QUICK WINS Prompt Length:", len(prompts.goal_quick_wins(sample_data, business_context)))
    print("2. DATA STRATEGY Prompt Length:", len(prompts.goal_data_strategy(sample_data, business_context)))
    print("3. GROWTH USE CASES Prompt Length:", len(prompts.goal_growth_usecases(sample_data, business_context)))
    print("4. EXPANSION Prompt Length:", len(prompts.goal_expansion_opportunities(sample_data, business_context)))
