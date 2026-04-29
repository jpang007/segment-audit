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
        Focus: Low-effort, high-impact opportunities that can be implemented quickly
        """
        workspace = structured_data.get('workspace_summary', {})
        audiences = structured_data.get('audience_insights', [])
        sources = structured_data.get('source_insights', [])

        # Find obvious quick wins in data
        large_unactivated = [a for a in audiences if a.get('signal') == 'activation_opportunity' and a.get('size', 0) > 10000]

        return f"""## Quick Wins Analysis

You are conducting a workspace audit focused on identifying **immediate, low-effort opportunities**.

{business_context}

{"### Customer Notes: " + user_notes if user_notes else ""}

### Workspace Overview
- Total audiences: {workspace.get('total_audiences', 0)}
- Enabled audiences: {workspace.get('enabled_audiences', 0)}
- Total users: {workspace.get('total_users_in_audiences', 0):,}
- Large unactivated audiences: {len(large_unactivated)}

### Task: Identify Top 5 Quick Wins

A "Quick Win" is:
- Implementable in <1 week
- Low technical complexity
- High business impact
- Requires minimal resources

For each quick win, provide:

1. **Opportunity** - What specific action (use actual audience/source names)
2. **Why It's Quick** - What makes this low-effort (e.g., "audience already built", "destination already connected")
3. **Impact** - Quantified expected outcome
4. **Implementation** - 2-3 bullet steps to execute
5. **Time to Value** - Days/weeks to see results

### Data Available
```json
{json.dumps(structured_data, indent=2)}
```

### Output Format

Return JSON:
```json
{{
  "quick_wins": [
    {{
      "opportunity": "Connect audience_va_subs (144K users) to Braze",
      "why_quick": "Audience already built, Braze already connected to workspace, just needs destination mapping",
      "impact": "Enable 144K geo-targeted sends, expected 15-20% engagement lift",
      "implementation": [
        "Navigate to audience settings",
        "Add Braze destination",
        "Map to existing connection"
      ],
      "time_to_value": "1-2 days"
    }}
  ],
  "summary": "One-sentence summary of quick win potential"
}}
```

CRITICAL:
- Use actual names from the data
- Be specific about implementation
- Provide realistic time estimates
- Focus on opportunities that exist NOW (don't suggest building new things)"""

    @staticmethod
    def goal_data_strategy(structured_data: Dict[str, Any], business_context: str, user_notes: str = "") -> str:
        """
        GOAL: Improve Data & Audience Strategy
        Focus: Identity, event usage, audience structure, governance
        """
        workspace = structured_data.get('workspace_summary', {})
        audiences = structured_data.get('audience_insights', [])
        sources = structured_data.get('source_insights', [])

        return f"""## Data & Audience Strategy Analysis

You are conducting a technical audit focused on **data quality, governance, and audience architecture**.

{business_context}

{"### Customer Notes: " + user_notes if user_notes else ""}

### Workspace Overview
```json
{json.dumps(workspace, indent=2)}
```

### Task: Comprehensive Data Strategy Assessment

Analyze these areas:

1. **Data Collection**
   - Source health and coverage
   - Event instrumentation quality
   - Missing data signals

2. **Audience Architecture**
   - Audience organization and naming
   - Redundant or overlapping audiences
   - Missing high-value audiences
   - Audience-to-destination strategy

3. **Governance & Hygiene**
   - Stale or empty audiences
   - Disabled resources consuming quota
   - Workspace organization

4. **Activation Strategy**
   - Destination coverage by category
   - Audience activation rate
   - Gaps in activation strategy

### Data Available
```json
{json.dumps(structured_data, indent=2)}
```

### Output Format

Return JSON:
```json
{{
  "data_collection_assessment": {{
    "overall_health": "good | fair | poor",
    "strengths": ["strength 1", "strength 2"],
    "gaps": ["gap 1", "gap 2"],
    "recommendations": ["rec 1", "rec 2"]
  }},
  "audience_architecture": {{
    "organization_score": "1-10",
    "redundancies": [
      {{"audiences": ["aud1", "aud2"], "issue": "description", "recommendation": "action"}}
    ],
    "missing_audiences": [
      {{"suggested_name": "name", "definition": "logic", "use_case": "business value"}}
    ],
    "naming_improvements": ["suggestion 1", "suggestion 2"]
  }},
  "governance_issues": [
    {{"category": "hygiene | performance | cost", "issue": "description", "impact": "business impact", "fix": "action"}}
  ],
  "activation_strategy": {{
    "current_rate": "percentage",
    "industry_benchmark": "percentage",
    "gaps": ["gap 1", "gap 2"],
    "recommendations": ["rec 1", "rec 2"]
  }},
  "prioritized_actions": [
    {{"priority": 1, "action": "specific task", "category": "data | audiences | governance | activation", "effort": "low | medium | high"}}
  ]
}}
```

Be thorough and technical - this is for internal SA/data team use."""

    @staticmethod
    def goal_growth_usecases(structured_data: Dict[str, Any], business_context: str, user_notes: str = "") -> str:
        """
        GOAL: Generate Growth / Marketing Use Cases
        Focus: Lifecycle campaigns, behavioral targeting, activation ideas
        """
        workspace = structured_data.get('workspace_summary', {})
        audiences = structured_data.get('audience_insights', [])
        destinations = structured_data.get('destination_summary', {})

        return f"""## Growth & Marketing Use Case Generation

You are a growth strategist generating **implementable marketing use cases**.

{business_context}

{"### Customer Notes: " + user_notes if user_notes else ""}

### Workspace Context
- Total addressable users: {workspace.get('total_users_in_audiences', 0):,}
- Available destinations: {', '.join(destinations.get('all_destinations', [])[:5])}
- Destination categories: {', '.join(destinations.get('by_category', {}).keys())}

### Task: Generate 5-7 Implementable Marketing Use Cases

Each use case MUST:
- Be tied to actual audiences in the workspace
- Use available destinations only
- Include specific trigger conditions
- Provide campaign messaging guidance
- Estimate business impact

### Data Available
```json
{json.dumps(structured_data, indent=2)}
```

### Output Format

Return JSON:
```json
{{
  "use_cases": [
    {{
      "name": "Virginia Subscriber Local News Campaign",
      "category": "retention | acquisition | monetization | engagement",
      "target_audience": "audience_va_subs (144,765 users)",
      "trigger": "Daily at 6am ET OR user opens previous newsletter",
      "channel": "Braze (needs connection)",
      "campaign_description": "Send VA-specific news digest highlighting Richmond/NoVA stories with 'Your Local Headlines' subject line",
      "messaging_guidance": [
        "Lead with most-clicked local story from previous day",
        "Include 3 regional headlines",
        "Personalize send time by user's typical open time"
      ],
      "expected_impact": "15-20% lift in open rates vs generic sends, 10-15% churn reduction",
      "implementation_complexity": "low | medium | high",
      "estimated_setup_time": "1-2 weeks"
    }}
  ],
  "campaign_priorities": [
    {{"use_case": "name", "rationale": "why prioritize this", "expected_roi": "quantified"}}
  ]
}}
```

CRITICAL:
- Use actual audience names from data
- Only suggest destinations that are available or commonly used in this industry
- Provide specific campaign messaging (not "personalized content")
- Estimate realistic impact based on industry benchmarks"""

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
