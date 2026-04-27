#!/usr/bin/env python3
"""
Gemini Prompt System - Optimized prompts for consistent, high-quality outputs
Uses prompt engineering best practices for CDP workspace analysis
"""

class GeminiPromptSystem:
    """Manages prompts and system instructions for Gemini API"""

    @staticmethod
    def get_system_instructions() -> str:
        """
        System instructions defining the AI's role and expertise
        This sets the context for all interactions
        """
        return """You are a Senior Customer Data Platform (CDP) Solutions Architect specializing in Segment and audience activation strategies.

Your expertise includes:
- Data governance and quality best practices
- Identity resolution and user stitching
- Audience segmentation and activation
- Marketing technology stack optimization
- ROI analysis for data investments

Your communication style:
- Concise and actionable (no fluff)
- Business-focused (tie technical issues to revenue/efficiency)
- Pragmatic (recommend practical solutions, not ideal-world scenarios)
- Prioritized (most impactful recommendations first)

Your outputs are used by:
- Technical teams (engineers, data analysts)
- Business stakeholders (CMOs, growth teams)
- Customer success managers (for health checks)"""

    @staticmethod
    def get_analysis_prompt(findings_data: dict, customer_context=None) -> str:
        """
        Generate the analysis prompt with structured findings
        Uses chain-of-thought reasoning for better outputs

        Args:
            findings_data: Structured audit findings
            customer_context: Optional CustomerContext object for tailored recommendations
        """
        import json
        findings_json = json.dumps(findings_data, indent=2)

        # Get customer context section
        context_section = ""
        if customer_context:
            try:
                from customer_context import get_contextual_prompt_section
                context_section = get_contextual_prompt_section(customer_context)
            except ImportError:
                context_section = ""

        return f"""## Task: Analyze Segment Workspace Health

You have audited a customer's Segment workspace and identified {findings_data.get('total_findings', 0)} findings.

### Input Data
```json
{findings_json}
```

{context_section}

### Your Analysis Process

**Step 1: Understand the Context**
{'- Use the provided customer context above to tailor recommendations' if context_section else '- No customer context provided - give GENERIC, universally applicable recommendations'}
- Focus on TACTICAL improvements based on the findings (data quality, activation gaps, hygiene)
- Do NOT infer business type or make assumptions beyond what's explicitly stated

**Step 2: Identify Themes**
- Are there patterns across the findings?
- What's the root cause of multiple issues?
- What's the most critical blocker to value?

**Step 3: Prioritize by Impact**
Consider:
- Revenue impact (can this drive more conversions/retention?)
- Time to value (how quickly can they implement?)
- Risk level (what breaks if not addressed?)
- Dependency chains (what unlocks other improvements?)

**Step 4: Generate Recommendations**
For each recommendation:
- What specific action should they take?
- Why does this matter (business impact, not just technical debt)?
- What's the expected outcome?
- How hard is it to implement?

### Output Format

Return a JSON object with this EXACT structure:

```json
{{
  "workspace_context": {{
    "business_type": "inferred type (e.g., media company, SaaS, ecommerce)",
    "maturity_level": "beginner | intermediate | advanced",
    "primary_use_case": "primary use case inferred from patterns"
  }},
  "executive_summary": "2-3 sentences: overall health, biggest opportunity, critical action needed",
  "key_themes": [
    "theme 1: brief description",
    "theme 2: brief description"
  ],
  "top_recommendations": [
    {{
      "priority": 1,
      "severity": "high | medium | low",
      "action": "One-line action (verb + object)",
      "reason": "Why this matters in business terms",
      "estimated_impact": "Specific outcome (e.g., 'unlock 60M user reach', 'reduce manual work by 10hrs/week')",
      "effort": "low | medium | high",
      "time_to_value": "immediate | 1-2 weeks | 1 month+"
    }}
  ],
  "quick_wins": [
    {{
      "action": "Specific task that takes <1 day",
      "impact": "Measurable benefit",
      "how_to": "1-2 sentence implementation guide"
    }}
  ],
  "risks_to_flag": [
    {{
      "risk": "What could go wrong",
      "likelihood": "high | medium | low",
      "consequence": "Business impact if it happens",
      "mitigation": "How to prevent/address"
    }}
  ],
  "next_steps": [
    "Step 1: Most critical action",
    "Step 2: Enables future steps",
    "Step 3: Longer-term optimization"
  ],
  "metrics_to_track": [
    "metric 1: what to measure to validate improvements",
    "metric 2: leading indicator of success"
  ]
}}
```

### Critical Guidelines

1. **Be Specific**: "Connect top 10 audiences to Braze" not "Activate audiences"
2. **Be Quantitative**: "62M users" not "many users"
3. **Be Pragmatic**: Don't recommend building from scratch if 80% works
4. **Be Honest**: If findings are minor, say "workspace is healthy, here are optimizations"
5. **Limit Scope**:
   - Max 5 top recommendations
   - Max 3 quick wins
   - Max 3 risks
   - Max 5 next steps

6. **Business Language**:
   - ✅ "Unlock $X in potential revenue"
   - ❌ "Improve data quality metrics"

7. **No Hallucinations**: Only reference what's in the findings data. Don't invent issues.

### Special Cases

**If findings are minimal** (1-2 low-priority items):
- Acknowledge the workspace is well-maintained
- Suggest optimization opportunities, not "fixes"
- Focus on maximizing existing infrastructure

**If findings are severe** (multiple high-priority items):
- Triage ruthlessly (what must be fixed first?)
- Identify if there's a common root cause
- Suggest a phased rollout plan

Return ONLY the JSON object. No markdown, no explanations outside the JSON structure."""

    @staticmethod
    def get_fallback_enhancement_prompt() -> str:
        """
        Lightweight prompt for when Gemini API is unavailable
        Can be used to enhance rule-based outputs client-side
        """
        return """Given these workspace findings, provide:
1. One-sentence executive summary
2. Top 3 action items (most impactful first)
3. One quick win

Keep it under 100 words total."""

    @staticmethod
    def get_validation_prompt(gemini_output: str) -> str:
        """
        Validate that Gemini's output meets requirements
        This is for quality assurance
        """
        return f"""Review this analysis output for quality:

{gemini_output}

Check:
1. Is the executive summary concise (2-3 sentences)?
2. Are recommendations specific and actionable?
3. Are business impacts quantified where possible?
4. Is the JSON structure valid?
5. Are there any hallucinations (invented details not in source data)?

Return: {{"valid": true/false, "issues": ["list of problems if any"]}}"""


class PromptTemplates:
    """Pre-built prompt templates for common scenarios"""

    @staticmethod
    def get_comparison_prompt(workspace_a: dict, workspace_b: dict) -> str:
        """Compare two workspaces (for benchmarking)"""
        return f"""Compare these two Segment workspaces:

Workspace A: {workspace_a}
Workspace B: {workspace_b}

Identify:
1. Which workspace is healthier overall?
2. What can each learn from the other?
3. Any common anti-patterns?

Return as JSON."""

    @staticmethod
    def get_trend_analysis_prompt(current: dict, previous: dict) -> str:
        """Analyze changes over time"""
        return f"""Analyze workspace health trend:

Current audit: {current}
Previous audit: {previous}

Identify:
1. What improved?
2. What got worse?
3. Are they making progress on recommendations?
4. New issues that emerged?

Return as JSON."""

    @staticmethod
    def get_persona_specific_prompt(findings: dict, persona: str) -> str:
        """Tailor recommendations to specific persona"""
        personas = {
            "engineer": "Focus on technical implementation, APIs, code examples",
            "marketer": "Focus on campaign activation, audience reach, channel strategy",
            "executive": "Focus on ROI, business impact, strategic initiatives",
            "cs_manager": "Focus on customer health, risk factors, success metrics"
        }

        context = personas.get(persona, "general recommendations")

        return f"""Analyze these findings for a {persona}:

{findings}

{context}

Tailor language, priorities, and recommendations accordingly."""


# Example usage and testing
if __name__ == '__main__':
    import json

    # Test the prompt system
    prompt_system = GeminiPromptSystem()

    print("=== SYSTEM INSTRUCTIONS ===")
    print(prompt_system.get_system_instructions())
    print()

    # Sample findings
    sample_findings = {
        "workspace": "test",
        "total_findings": 3,
        "high_priority": 1,
        "findings": [
            {
                "type": "activation_gap",
                "severity": "high",
                "title": "Audiences Not Activated",
                "evidence": "100 audiences with 5M users",
                "impact": "Potential reach not utilized",
                "recommendation": "Connect to destinations"
            }
        ]
    }

    print("=== ANALYSIS PROMPT LENGTH ===")
    prompt = prompt_system.get_analysis_prompt(sample_findings)
    print(f"Characters: {len(prompt)}")
    print(f"Estimated tokens: ~{len(prompt) // 4}")
    print()
    print("=== FIRST 500 CHARS OF PROMPT ===")
    print(prompt[:500] + "...")
