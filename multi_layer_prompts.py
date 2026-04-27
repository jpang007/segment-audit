#!/usr/bin/env python3
"""
Multi-Layer Prompt System - Implements 4-layer prompting for high-quality outputs
Based on best practices: Summarization → Diagnosis → Opportunities → Execution
"""

import json
from typing import Dict, Any


class MultiLayerPrompts:
    """
    Implements 4-layer prompt strategy:
    1. Summarization - What's happening?
    2. Diagnosis - What's wrong/missing?
    3. Opportunities - What could they do?
    4. Execution - What should they do next?
    """

    @staticmethod
    def get_system_instructions() -> str:
        """Define AI role and expertise"""
        return """You are a Solutions Architect specializing in Segment and customer data platforms.

Your expertise:
- Data activation and audience strategy
- Marketing technology stack optimization
- Growth and retention campaigns
- CDP best practices and governance

Your communication style:
- Specific (use actual names, numbers, destinations)
- Actionable (clear next steps, not theory)
- Business-focused (tie to revenue, efficiency, growth)
- Realistic (implementable recommendations, not ideal-world scenarios)

Critical constraints:
- Use ONLY the data provided - do NOT invent data
- Reference specific audiences, events, and destinations by name
- Avoid generic best practices - be specific to THIS workspace
- Prioritize realistic, implementable actions
- Tie technical issues to business impact"""

    @staticmethod
    def layer1_summarization(structured_data: Dict[str, Any], business_context: str = "") -> str:
        """
        Layer 1: What's happening?
        Executive summary of workspace state
        """
        return f"""## Layer 1: Workspace Summarization

Analyze this Segment workspace and provide a high-level summary.

{business_context}

### Workspace Data
```json
{json.dumps(structured_data, indent=2)}
```

### Task
Provide a 3-4 sentence executive summary covering:
1. Overall workspace health (beginner, intermediate, advanced setup)
2. Primary strength (what's working well)
3. Biggest gap (what's missing or underutilized)

Focus on:
- Data collection maturity
- Audience activation readiness
- Destination connectivity

Be concise and specific. Reference actual numbers.

Return JSON:
```json
{{
  "executive_summary": "3-4 sentences",
  "maturity_level": "beginner | intermediate | advanced",
  "key_strength": "what's working well",
  "biggest_gap": "most critical missing piece"
}}
```"""

    @staticmethod
    def layer2_diagnosis(structured_data: Dict[str, Any], business_context: str = "") -> str:
        """
        Layer 2: What's wrong/missing?
        Data utilization diagnosis
        """
        return f"""## Layer 2: Data Utilization Diagnosis

Analyze how data is being used (or not used) in this workspace.

{business_context}

### Workspace Data
```json
{json.dumps(structured_data, indent=2)}
```

### Task
Identify specific utilization issues:

1. **Audience Analysis**
   - Large audiences NOT connected to destinations
   - Empty enabled audiences (wasted computation)
   - Disabled audiences that could be valuable

2. **Source Analysis**
   - Enabled sources not sending to any destination
   - Sources that could benefit from more connections

3. **Destination Analysis**
   - Available destinations that aren't being used
   - Missing destination categories (email, analytics, ads, warehouse)

For EACH issue identified:
- Explain WHY it matters (business impact, not just technical debt)
- Provide a SPECIFIC recommendation (use actual names)
- Estimate potential impact

CRITICAL: Do NOT give generic advice. Tie each recommendation to the actual data.

Example of GOOD output:
"audience_va_subs (144K users) is not connected to any destination. This represents untapped reach for Virginia-specific campaigns. Recommendation: Connect to Braze for geo-targeted newsletter personalization. Expected impact: Enable 144K localized sends."

Example of BAD output:
"Some audiences aren't activated. You should connect them to destinations."

Return JSON:
```json
{{
  "issues": [
    {{
      "category": "audience | source | destination",
      "specific_item": "exact name from data",
      "problem": "what's wrong",
      "why_it_matters": "business impact",
      "recommendation": "specific action with names",
      "estimated_impact": "quantified outcome"
    }}
  ]
}}
```"""

    @staticmethod
    def layer3_opportunities(structured_data: Dict[str, Any], customer_context=None, business_context: str = "") -> str:
        """
        Layer 3: What could they do?
        Marketing and growth use cases
        """
        # Extract key info for context
        workspace = structured_data.get('workspace_summary', {})
        audiences = structured_data.get('audience_insights', [])
        destinations = structured_data.get('destination_summary', {})

        # Build destination context
        dest_list = destinations.get('all_destinations', [])
        dest_context = f"Available destinations: {', '.join(dest_list)}" if dest_list else "Destinations not yet configured"

        # Detect business type from audience categories
        categories = Counter([a.get('category') for a in audiences if a.get('category')])
        likely_business = "general"
        if categories.get('subscription', 0) > 10:
            likely_business = "media/newsletter company"
        elif categories.get('acquisition', 0) > 5 and categories.get('monetization', 0) > 5:
            likely_business = "SaaS company"

        return f"""## Layer 3: Marketing & Growth Opportunities

Generate high-quality, realistic marketing use cases for this workspace.

{business_context}

### Workspace Context
- Business type (inferred): {likely_business}
- {dest_context}
- Audiences analyzed: {len(audiences)}
- Total addressable users: {workspace.get('total_users_in_audiences', 0):,}

### Workspace Data
```json
{json.dumps(structured_data, indent=2)}
```

### Task
Generate 5 HIGH-QUALITY marketing use cases that are:
- Implementable with current data and destinations
- Tied to specific audiences and business outcomes
- Realistic (not aspirational)

Each use case MUST include:
1. **Use Case Name** - Clear, benefit-oriented title
2. **Target Audience** - Use ACTUAL audience names from the data
3. **Trigger/Condition** - Behavioral signal or attribute (be specific)
4. **Activation Channel** - Must match AVAILABLE destinations
5. **Campaign Description** - What messages/content to send
6. **Expected Business Impact** - Quantified outcome (conversion, retention, revenue)
7. **Implementation Complexity** - low/medium/high

CRITICAL CONSTRAINTS:
- Do NOT give generic ideas like "send emails" or "improve targeting"
- Use the ACTUAL audience names provided in the data
- Only suggest destinations that are ALREADY CONNECTED
- Focus on realistic, implementable campaigns
- Provide specific trigger conditions

Example of GOOD use case:
{{
  "name": "Virginia Subscriber Geo-Targeting Campaign",
  "target_audience": "audience_va_subs (144,765 users)",
  "trigger": "User is active subscriber AND located in Virginia",
  "channel": "Braze (already connected)",
  "campaign": "Send VA-specific news digest highlighting Richmond/NoVA stories with 'Your Local News' subject line personalization",
  "expected_impact": "15-20% lift in open rates vs generic sends, reduce churn by surfacing relevant local content",
  "complexity": "low"
}}

Example of BAD use case:
{{
  "name": "Improve engagement",
  "target_audience": "engaged users",
  "trigger": "when engaged",
  "channel": "email",
  "campaign": "send personalized content",
  "expected_impact": "better engagement",
  "complexity": "medium"
}}

Return JSON:
```json
{{
  "use_cases": [
    {{
      "name": "...",
      "target_audience": "...",
      "trigger": "...",
      "channel": "...",
      "campaign": "...",
      "expected_impact": "...",
      "complexity": "low | medium | high"
    }}
  ]
}}
```"""

    @staticmethod
    def layer4_execution(structured_data: Dict[str, Any], layer2_issues: Dict, layer3_opportunities: Dict, business_context: str = "") -> str:
        """
        Layer 4: What should they do next?
        Prioritized execution plan
        """
        return f"""## Layer 4: Execution Plan

Based on the diagnosis and opportunities identified, create a prioritized action plan.

{business_context}

### Context
**Issues Identified:**
```json
{json.dumps(layer2_issues, indent=2)}
```

**Opportunities Identified:**
```json
{json.dumps(layer3_opportunities, indent=2)}
```

**Current State:**
```json
{json.dumps(structured_data['workspace_summary'], indent=2)}
```

### Task
If this were YOUR customer, what would you do in the next 30 days?

Provide:
1. **Top 5 Prioritized Actions** - Ordered by impact (biggest wins first)
2. **Quick Wins** - Actions that take <1 day but deliver value
3. **Biggest Missed Opportunity** - The one thing they're leaving on the table
4. **Hidden Revenue Opportunities** - Ways to drive growth/retention
5. **Next 30 Days Plan** - Weekly breakdown

For each action include:
- What to do (specific, with names)
- Why it matters (business impact)
- Expected outcome (quantified)
- Effort level (low/medium/high)
- Time to value (immediate/1-2 weeks/1 month+)

Prioritization criteria:
1. Revenue impact - Can this drive conversions/retention/expansion?
2. Time to value - How quickly can they see results?
3. Risk level - What breaks if not addressed?
4. Dependency chains - What unlocks other improvements?

Return JSON:
```json
{{
  "top_5_actions": [
    {{
      "priority": 1,
      "action": "specific task with names",
      "why": "business impact",
      "outcome": "quantified result",
      "effort": "low | medium | high",
      "time_to_value": "immediate | 1-2 weeks | 1 month+"
    }}
  ],
  "quick_wins": [
    {{
      "action": "takes <1 day",
      "impact": "measurable benefit",
      "how_to": "implementation guide"
    }}
  ],
  "biggest_missed_opportunity": {{
    "opportunity": "what they're leaving on table",
    "why_critical": "business case",
    "how_to_capture": "execution steps"
  }},
  "hidden_revenue_opportunities": [
    {{
      "opportunity": "growth/retention driver",
      "revenue_potential": "estimated impact",
      "implementation": "how to activate"
    }}
  ],
  "next_30_days": {{
    "week_1": ["action 1", "action 2"],
    "week_2": ["action 3", "action 4"],
    "week_3": ["action 5"],
    "week_4": ["action 6"]
  }}
}}
```"""

    @staticmethod
    def audience_optimization_prompt(structured_data: Dict[str, Any]) -> str:
        """
        Bonus Layer: Audience Optimization
        Identify redundancy, gaps, and new audience opportunities
        """
        audiences = structured_data.get('audience_insights', [])

        return f"""## Audience Optimization Analysis

Analyze the current audience strategy and suggest improvements.

### Current Audiences
```json
{json.dumps(audiences, indent=2)}
```

### Task
Identify:
1. **Redundant Audiences** - Overlapping or duplicate audiences that could be consolidated
2. **Audiences with Unclear Purpose** - Poorly named or ambiguous audiences
3. **Missing High-Value Audiences** - Audiences that SHOULD exist based on patterns

Then:
- Suggest 3 NEW audiences that should be built
- Base them on behavioral signals (not just traits)
- Explain the business use case for each

Be specific and actionable.

Return JSON:
```json
{{
  "redundant_audiences": [
    {{
      "audiences": ["name1", "name2"],
      "issue": "why redundant",
      "recommendation": "how to consolidate"
    }}
  ],
  "unclear_purpose": [
    {{
      "audience": "name",
      "issue": "why unclear",
      "suggested_rename": "better name"
    }}
  ],
  "missing_audiences": [
    {{
      "suggested_name": "descriptive name",
      "definition": "behavioral logic",
      "use_case": "business application",
      "priority": "high | medium | low"
    }}
  ]
}}
```"""


# CLI testing
if __name__ == '__main__':
    print("=== MULTI-LAYER PROMPT SYSTEM ===\n")
    print("System Instructions:")
    print(MultiLayerPrompts.get_system_instructions())
    print("\n" + "="*70 + "\n")

    # Test with sample data
    sample_data = {
        "workspace_summary": {
            "workspace_slug": "test",
            "total_audiences": 100,
            "enabled_audiences": 80
        },
        "audience_insights": [
            {
                "name": "test_audience",
                "size": 10000,
                "enabled": True,
                "destination_count": 0,
                "signal": "activation_opportunity"
            }
        ]
    }

    print("Layer 1 Prompt Length:", len(MultiLayerPrompts.layer1_summarization(sample_data)))
    print("Layer 2 Prompt Length:", len(MultiLayerPrompts.layer2_diagnosis(sample_data)))
    print("Layer 3 Prompt Length:", len(MultiLayerPrompts.layer3_opportunities(sample_data)))
