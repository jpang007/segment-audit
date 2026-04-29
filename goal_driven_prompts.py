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
    This replaces the generic 5-layer analysis with focused, goal-specific analysis
    """

    @staticmethod
    def get_system_instructions() -> str:
        """System instructions for goal-driven analysis"""
        return """You are a Segment Solutions Architect conducting a workspace audit.

Your expertise:
- CDP architecture and data governance
- Audience activation strategies
- Marketing technology optimization
- Growth marketing and lifecycle campaigns
- ROI analysis and business impact

Your communication style:
- Specific (use actual audience names, destinations, numbers)
- Actionable (clear next steps, not theory)
- Business-focused (tie to revenue, efficiency, growth)
- Realistic (implementable recommendations)

Critical rules:
- Use ONLY the data provided
- Reference specific audiences, events, destinations by name
- Avoid generic best practices
- Provide quantified impact estimates where possible"""

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
    def goal_data_strategy(structured_data: Dict[str, Any], business_context: str, user_notes: str = "") -> str:
        """
        GOAL: Improve Data & Audience Strategy
        Focus: Identity, event usage, audience structure, governance
        """
        workspace = structured_data.get('workspace_summary', {})
        audiences = structured_data.get('audience_insights', [])
        sources = structured_data.get('source_insights', [])

        return f"""## Evidence-Based Data Strategy Audit

You are a Segment Solutions Architect conducting a technical workspace audit.

{business_context}

{"### Customer Context: " + user_notes if user_notes else ""}

### Workspace Overview
- Total sources: {workspace.get('total_sources', 0)}
- Total audiences: {workspace.get('total_audiences', 0)}
- Enabled audiences: {workspace.get('enabled_audiences', 0)}
- Total users in audiences: {workspace.get('total_users_in_audiences', 0):,}

### Critical Instructions

**DATA GROUNDING REQUIREMENTS:**
1. Base all observations on workspace configuration data
2. DO NOT assume business processes or team structures
3. DO NOT claim performance benchmarks without data
4. ONLY identify patterns observable in the workspace

**FORBIDDEN:**
- Industry benchmark comparisons without clear basis
- Assumptions about "best practices" not grounded in this workspace
- Claims about what "should" exist without evidence
- Speculation about business impact

### Data Available
```json
{json.dumps(structured_data, indent=2)}
```

### Task: Technical Workspace Assessment

Analyze workspace configuration and identify:
1. **Data Collection Gaps**: Sources, events, or schemas that appear incomplete
2. **Audience Architecture Issues**: Redundancies, naming inconsistencies, unused audiences
3. **Governance Issues**: Disabled resources with users, empty audiences, quota waste
4. **Activation Gaps**: Audiences with users but no destinations

### Output Format

Return JSON with this EXACT structure:
```json
{{
  "data_collection": {{
    "sources_analyzed": 16,
    "observations": [
      {{
        "finding": "Specific observation from data",
        "evidence": "What in the data shows this",
        "impact_level": "high | medium | low",
        "recommendation": "Specific, actionable next step"
      }}
    ],
    "data_quality_assessment": "Brief summary of data completeness"
  }},
  "audience_architecture": {{
    "total_audiences": 242,
    "enabled_audiences": 166,
    "observations": [
      {{
        "pattern": "What pattern you observed (e.g., naming convention inconsistency)",
        "examples": ["aud_name_1", "aud_name_2"],
        "impact": "Why this matters",
        "recommendation": "What to do about it",
        "confidence": "high | medium | low"
      }}
    ],
    "potential_redundancies": [
      {{
        "audience_group": ["list", "of", "similar", "audiences"],
        "similarity_basis": "What makes them appear similar",
        "requires_verification": "What you'd need to confirm this"
      }}
    ]
  }},
  "governance": {{
    "issues_found": [
      {{
        "issue_type": "disabled_with_users | empty_audience | unused_destination",
        "affected_resources": ["specific names"],
        "user_count": 12345,
        "business_impact": "Why this matters (qualitative)",
        "recommended_action": "Specific fix",
        "urgency": "high | medium | low"
      }}
    ]
  }},
  "activation_strategy": {{
    "activation_rate": "X out of Y audiences activated",
    "observations": [
      {{
        "finding": "Specific pattern in destination usage",
        "evidence": "Data that supports this",
        "gap_identified": "What's missing",
        "recommendation": "What to consider"
      }}
    ]
  }},
  "prioritized_actions": [
    {{
      "priority": 1,
      "action": "Specific task with resource names",
      "category": "data_collection | audience_architecture | governance | activation",
      "effort": "low | medium | high",
      "impact": "high | medium | low",
      "evidence": "Why this is prioritized",
      "prerequisites": ["What needs to be true or done first"]
    }}
  ],
  "summary": {{
    "overall_health": "Brief diagnostic summary",
    "highest_priority_area": "Which area needs most attention",
    "data_completeness": "Assessment of how complete the audit data is"
  }}
}}
```

### Tone Guidelines

Write as a technical consultant reviewing workspace configuration:
- Analytical and diagnostic
- Specific with names and numbers
- Clear about what's observable vs. inferred
- Actionable with clear next steps

DO NOT:
- Make claims about "best practices" without evidence
- Compare to industry benchmarks you don't have
- Assume team structures or business processes
- Use vague language ("consider optimizing...")

DO:
- Reference specific resource names
- Use actual counts from data
- Describe patterns you observe
- Be clear when something needs customer confirmation

Generate the assessment now."""

    @staticmethod
    def goal_growth_usecases(structured_data: Dict[str, Any], business_context: str, user_notes: str = "") -> str:
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
- "Based on the {audience_name} audience definition..."
- "The data shows {X users} are currently not activated..."
- "This could enable campaigns, though exact engagement metrics would need to be measured..."

Example phrases to AVOID:
- "This will increase conversion by X%..."
- "Expected ROI of $X..."
- "Users who engage 3+ times..."
- "Drive significant revenue growth..."

Generate recommendations now."""

    @staticmethod
    def goal_expansion_opportunities(structured_data: Dict[str, Any], business_context: str, user_notes: str = "") -> str:
        """
        GOAL: Identify Expansion Opportunities
        Focus: Unused destinations, upsell opportunities, activation gaps
        """
        workspace = structured_data.get('workspace_summary', {})
        destinations = structured_data.get('destination_summary', {})
        audiences = structured_data.get('audience_insights', [])

        unactivated_users = sum(a.get('size', 0) for a in audiences if a.get('signal') == 'activation_opportunity')

        return f"""## Expansion Opportunity Analysis

You are identifying **revenue expansion and upsell opportunities** in this workspace.

{business_context}

{"### Customer Notes: " + user_notes if user_notes else ""}

### Workspace Snapshot
- Total audiences: {workspace.get('total_audiences', 0)}
- Activated audiences: {len([a for a in audiences if a.get('destination_count', 0) > 0])}
- Unactivated users: {unactivated_users:,}
- Current destination categories: {', '.join(destinations.get('by_category', {}).keys())}

### Task: Identify Expansion Opportunities

Focus on:

1. **Activation Gaps** - Built audiences not being used
2. **Missing Destination Categories** - Categories common in this industry but not connected
3. **Underutilized Data** - Collected data not activated
4. **Upsell Opportunities** - Segment products/features that would add value

### Data Available
```json
{json.dumps(structured_data, indent=2)}
```

### Output Format

Return JSON:
```json
{{
  "activation_expansion": {{
    "untapped_reach": "{unactivated_users:,} users in unactivated audiences",
    "revenue_opportunity": "estimated value of activating",
    "top_opportunities": [
      {{
        "audience": "name (size)",
        "current_state": "not connected",
        "expansion_play": "Connect to [destination] for [use case]",
        "estimated_value": "quantified impact"
      }}
    ]
  }},
  "missing_destinations": [
    {{
      "category": "email | analytics | ads | warehouse | cdp",
      "rationale": "why this matters for their business",
      "recommended_tools": ["tool 1", "tool 2"],
      "use_cases": ["use case 1", "use case 2"],
      "expected_impact": "business value"
    }}
  ],
  "segment_product_opportunities": [
    {{
      "product": "Personas | Protocols | Engage | Connections",
      "use_case": "specific problem it solves",
      "evidence": "what in their workspace indicates this need",
      "expected_value": "business outcome"
    }}
  ],
  "prioritized_expansion_plan": [
    {{
      "priority": 1,
      "opportunity": "specific expansion",
      "rationale": "why this first",
      "estimated_impact": "revenue/efficiency gain",
      "effort": "low | medium | high"
    }}
  ]
}}
```

Think like a CSM/Sales - what would drive more value and deeper product adoption?"""

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
