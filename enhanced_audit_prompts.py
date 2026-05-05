#!/usr/bin/env python3
"""
Enhanced SA-Quality Audit Prompt System
Incorporates feedback from Claude and ChatGPT for production-grade audit output

Key improvements:
1. Confidence levels (High/Medium/Low) for all findings
2. Separates facts from interpretations
3. Structured SA Action Plan format
4. No speculative tool recommendations
5. Customer validation questions built-in
"""

import json
from typing import Dict, Any


class EnhancedAuditPrompts:
    """
    Generates SA-quality audit prompts with confidence levels and structured output
    """

    @staticmethod
    def get_system_instructions() -> str:
        """Core SA principles for audit analysis"""
        return """You are a Segment Solutions Architect conducting a workspace audit.

**Core Principles:**
1. **Separate Facts from Interpretation**
   - Facts: "axios_web_PROD is disabled"
   - Likely implication: "production web collection may have stopped"
   - Judgment: "operational decay" (use sparingly, with evidence)

2. **Use Confidence Levels**
   - High: Directly observable in data (e.g., "8 enabled audiences have 0 destinations")
   - Medium: Strong inference with limited context (e.g., "disabled prod source suggests collection gap")
   - Low: Speculative or requires customer validation (e.g., "these users are high-value")

3. **Ground Recommendations in Evidence**
   - Reference specific resources by name and ID
   - Use actual counts, dates, statuses
   - Cite what you observe, not what you assume

4. **Distinguish Audit Findings from Expansion Ideas**
   - Audit findings: Based on workspace state
   - Expansion opportunities: Strategic possibilities (clearly labeled)

5. **Make Recommendations SA-Ready**
   - Include validation questions for customer
   - Specify who should act (SA/CSM/Customer/Eng)
   - Estimate effort (Low/Medium/High)

**Communication Style:**
- Consultative, not assumptive
- Diagnostic, not alarmist
- Specific, not vague
- Actionable, not theoretical"""

    @staticmethod
    def workspace_audit_with_confidence_levels(
        structured_data: Dict[str, Any],
        business_context: str,
        user_notes: str = ""
    ) -> str:
        """
        Enhanced Workspace Audit prompt with confidence levels and SA-ready output
        """
        workspace = structured_data.get('workspace_summary', {})

        return f"""## SA-Quality Workspace Audit

You are a Segment Solutions Architect conducting a comprehensive workspace audit.

{business_context}

{"### Customer Context: " + user_notes if user_notes else ""}

### Workspace Snapshot
```json
{json.dumps(workspace, indent=2)}
```

### Full Data Available
```json
{json.dumps(structured_data, indent=2)}
```

---

## Output Requirements

Return JSON with TWO outputs:

### 1. SA Action Plan (Primary Output - for execution)

**Critical Schema Requirements:**
- Every finding MUST have a confidence level
- Every recommendation MUST separate fact from interpretation
- Every action MUST include validation questions
- NO speculative tool recommendations (Zendesk, Optimizely, etc.) without grounding

```json
{{
  "sa_action_plan": {{
    "audit_metadata": {{
      "workspace_name": "axios",
      "audit_date": "2026-05-05",
      "data_completeness": {{
        "sources": "complete",
        "destinations": "complete",
        "audiences": "complete",
        "event_volumes": "missing",
        "delivery_metrics": "missing",
        "tracking_plan": "missing"
      }},
      "limitations": [
        "Event-level volumes not provided - cannot assess high-volume events",
        "Destination delivery health not available - cannot confirm destinations are working"
      ]
    }},
    "findings": [
      {{
        "priority": "P0 | P1 | P2",
        "category": "Source Health | Destination Coverage | Audience Hygiene | Activation Gap | Data Quality | Governance",
        "finding_fact": "Short, factual observation from data (e.g., 'axios_web_PROD is disabled with 0 destinations')",
        "evidence": [
          "Specific data point 1",
          "Specific data point 2"
        ],
        "confidence": "High | Medium | Low",
        "confidence_reasoning": "Why this confidence level (e.g., 'High: directly observable in source config')",
        "interpretation": {{
          "likely_implication": "What this probably means (e.g., 'production web tracking may have moved or stopped')",
          "alternative_explanations": [
            "Could also mean X",
            "Or intentional if Y"
          ]
        }},
        "why_it_matters": {{
          "business_impact": "Revenue/user/data impact if this is a problem",
          "technical_impact": "Downstream effects on audiences, destinations, data quality",
          "urgency": "Why this needs attention now (or doesn't)"
        }},
        "validation_steps": [
          "Step 1: Validate [specific thing] with customer",
          "Step 2: Check [specific config/log] to confirm",
          "Step 3: Review [related resource] for context"
        ],
        "implementation_steps": [
          "Only after validation confirms action is needed:",
          "Step 1: [Specific action]",
          "Step 2: [Follow-up action]"
        ],
        "customer_validation_questions": [
          "Question 1 to ask customer before acting",
          "Question 2 to clarify context"
        ],
        "customer_safe_wording": "How to present this finding in a customer conversation without sounding accusatory. Example: 'During the audit, we noticed [observation]. Before assuming this is an issue, we'd like to confirm [validation question].'",
        "ownership": {{
          "sa_owner": "Who investigates or advises (e.g., 'Review configuration and guide debugging')",
          "customer_owner": "Who validates or implements (e.g., 'Customer Engineering to validate warehouse credentials')",
          "escalation_path": "When to escalate and to whom (e.g., 'Segment Support if logs suggest platform-side failure')"
        }},
        "effort_estimate": {{
          "validation_effort": "Low | Medium | High",
          "validation_time_range": "e.g., '15-30 min if access is available'",
          "implementation_effort": "Low | Medium | High",
          "implementation_dependencies": [
            "What needs to be in place for this to be quick",
            "What could slow this down (approvals, consent, etc.)"
          ]
        }}
      }}
    ],
    "summary": {{
      "total_findings": 8,
      "by_priority": {{"P0": 2, "P1": 3, "P2": 3}},
      "by_confidence": {{"High": 5, "Medium": 2, "Low": 1}},
      "recommended_order": [
        "Finding ID 1 - why first",
        "Finding ID 2 - why second"
      ]
    }}
  }},

  "account_brief": {{
    "workspace_health_assessment": {{
      "overall_tone": "Strong | Mixed | Needs Attention",
      "health_reasoning": "1-2 sentences: why this assessment. Be precise: use 'sources reporting no recent data' not 'stale pipelines'. Use 'disabled source' not 'broken source'.",
      "key_strengths": [
        "What's working well (be specific)"
      ],
      "key_concerns": [
        "Top 3 issues (factual, not alarmist - use precise observable terms)"
      ]
    }},
    "critical_findings": [
      {{
        "finding": "Customer-friendly finding statement",
        "why_it_matters": "Business impact",
        "confidence": "High | Medium | Low",
        "recommended_action": "Clear next step"
      }}
    ],
    "activation_opportunities": [
      {{
        "opportunity": "Specific, grounded opportunity (e.g., 'Activate 8 regional subscriber audiences')",
        "potential_reach": "Number of users (from data)",
        "current_state": "What's currently happening",
        "effort": "Low | Medium | High",
        "prerequisites": ["What needs to be true to do this"]
      }}
    ],
    "expansion_ideas": [
      {{
        "idea": "Strategic possibility (e.g., 'Customer Success tool integration')",
        "rationale": "Why this might make sense based on workspace patterns",
        "clearly_labeled_as": "expansion_idea_not_audit_finding",
        "validation_needed": "What you'd need to know to recommend this",
        "confidence": "Low"
      }}
    ],
    "data_gaps_affecting_analysis": [
      "Event volumes not provided - limits event usage recommendations",
      "Destination delivery health not available - cannot assess activation quality"
    ]
  }}
}}
```

---

## Critical Rules

### ✅ DO:
1. **Use confidence levels on every finding**
2. **Separate facts from likely implications**
3. **Distinguish validation steps from implementation steps**
4. **Include customer-safe wording** for each finding
5. **Split ownership** (SA, Customer, Escalation)
6. **Use effort ranges** not precise time estimates
7. **Reference specific resources** (names, IDs, counts)
8. **Be honest about data gaps** (don't invent metrics to fill gaps)
9. **Label expansion ideas separately** from audit findings
10. **Use precise observable language** (see examples below)

### ❌ DON'T:
1. **Don't use alarmist language** ("operational decay", "critical failure") without strong evidence
2. **Don't recommend specific tools** (Zendesk, Optimizely) without knowing customer needs
3. **Don't invent event volumes or delivery metrics** if not provided
4. **Don't conflate "disabled" with "broken"** (disabled may be intentional)
5. **Don't assign "poor health"** based solely on NO_RECENT_DATA (could be scheduled syncs)
6. **Don't claim specific ROI** or performance improvements
7. **Don't use imprecise language** (see precision guide below)

### 📝 Language Precision Guide:

**Use Precise Observable Terms:**
- ✅ "Sources reporting NO_RECENT_DATA" (what we observe)
- ❌ "Stale data pipelines" (interpretation without validation)

- ✅ "axios_web_PROD is disabled" (fact)
- ❌ "Production tracking is broken" (assumption)

- ✅ "8 enabled audiences have 0 destinations connected" (observable)
- ❌ "Audiences are unused" (could be used via Profile API)

- ✅ "rETL sources show NO_RECENT_DATA status" (what system reports)
- ❌ "Warehouse syncs are failing" (could be scheduled weekly)

**Validation Before Action:**
- Always list validation steps BEFORE implementation steps
- Never assume a finding means something needs to be "fixed"
- Consider that configurations may be intentional

### Priority Levels:
- **P0**: Active data loss, broken production collection, compliance risk
- **P1**: Activation gaps, stale rETL, large disabled audiences with users
- **P2**: Governance, naming conventions, test cleanup

### Confidence Levels:
- **High**: Directly observable (source is disabled, audience has 0 destinations)
- **Medium**: Strong inference with limited context (disabled prod source suggests gap)
- **Low**: Requires customer validation (whether disabled source was intentional)

---

## Example of Good vs. Bad Finding

**❌ BAD:**
{{
  "finding": "Operational decay",
  "severity": "high",
  "recommendation": "Restore sources immediately"
}}

**✅ EXCELLENT (v2 - with ChatGPT refinements):**
{{
  "priority": "P0",
  "category": "Source Health",
  "finding_fact": "axios_web_PROD is disabled and has 0 destinations connected",
  "evidence": ["Source status: DISABLED", "Destination count: 0"],
  "confidence": "High",
  "confidence_reasoning": "High: directly observable in source configuration",
  "interpretation": {{
    "likely_implication": "Production web event collection may have stopped, moved to another source, or been intentionally disabled",
    "alternative_explanations": [
      "Client-side tracking migrated to GTM or different source",
      "Source disabled for migration or testing",
      "Tracking snippet removed from site"
    ]
  }},
  "why_it_matters": {{
    "business_impact": "If unintentional, web analytics, conversion tracking, and user identification may be incomplete",
    "technical_impact": "Audiences depending on web events will have stale or incomplete data",
    "urgency": "High if unexpected; low if this was a planned migration"
  }},
  "validation_steps": [
    "Step 1: Ask customer validation questions (see below)",
    "Step 2: Review Segment UI for source activity history and event flow",
    "Step 3: Check if axios_web_DEV or another source shows production-level traffic"
  ],
  "implementation_steps": [
    "Only proceed after validation confirms re-enabling is needed:",
    "Step 1: Re-enable axios_web_PROD source in Segment UI",
    "Step 2: Verify tracking snippet is present on live site",
    "Step 3: Reconnect to required destinations",
    "Step 4: Monitor event flow for 24 hours"
  ],
  "customer_validation_questions": [
    "Is your production website still sending data to Segment?",
    "Did you recently migrate web tracking to a different source?",
    "When was axios_web_PROD last active?"
  ],
  "customer_safe_wording": "During the audit, we noticed that the axios_web_PROD source is currently disabled and not connected to any destinations. Before assuming this is an issue, we'd like to confirm whether production web tracking has moved to a different source or whether this source should still be active.",
  "ownership": {{
    "sa_owner": "Review source configuration and guide customer through validation",
    "customer_owner": "Engineering team to confirm current production tracking setup",
    "escalation_path": "Segment Support only if source cannot be re-enabled or event flow issues persist after re-enabling"
  }},
  "effort_estimate": {{
    "validation_effort": "Low",
    "validation_time_range": "15-30 min if customer knows their tracking setup",
    "implementation_effort": "Low to Medium",
    "implementation_dependencies": [
      "Quick if source just needs re-enabling in UI",
      "Longer if tracking snippet needs to be added back to site",
      "May require Engineering involvement if GTM or server-side changes needed"
    ]
  }}
}}

---

Generate the SA-quality workspace audit now. Remember:
- High confidence on observable facts
- Medium/Low confidence on interpretations
- Customer validation questions for context-dependent findings
- NO tool recommendations without business context
- Be consultative, not alarmist"""

    @staticmethod
    def quick_wins_with_validation(
        structured_data: Dict[str, Any],
        business_context: str,
        user_notes: str = ""
    ) -> str:
        """Quick wins with proper confidence levels and validation questions"""

        workspace = structured_data.get('workspace_summary', {})

        return f"""## SA-Quality Quick Wins Analysis

You are identifying low-effort, high-impact opportunities with proper confidence levels.

{business_context}

{"### Customer Context: " + user_notes if user_notes else ""}

### Data Available
```json
{json.dumps(structured_data, indent=2)}
```

---

## Output Format

```json
{{
  "quick_wins": [
    {{
      "opportunity": "Specific, actionable opportunity using actual resource names",
      "category": "Activation | Data Collection | Audience Optimization | Governance",
      "evidence": {{
        "observable_facts": [
          "Fact 1 from data",
          "Fact 2 from data"
        ],
        "current_state": "What's currently configured",
        "gap_identified": "What's missing or unused"
      }},
      "confidence": "High | Medium | Low",
      "confidence_reasoning": "Why this confidence level",
      "why_quick": {{
        "prerequisites_met": [
          "Specific resource that already exists",
          "Configuration that's already in place"
        ],
        "effort_required": "What needs to be done",
        "complexity": "Low",
        "estimated_time": "e.g., '2 hours', '1 day'"
      }},
      "impact": {{
        "reach": "Number of users affected (from data)",
        "impact_level": "High | Medium | Low",
        "reasoning": "Why this matters (qualitative)",
        "assumptions": [
          "What we're assuming that requires validation"
        ]
      }},
      "implementation_steps": [
        "Step 1: Specific action with details",
        "Step 2: Specific action with details"
      ],
      "validation_questions": [
        "Question to ask customer before implementing",
        "Question to confirm this is actually needed"
      ],
      "owner": "Marketing Ops | Data Team | SA | Customer",
      "success_criteria": "How to know if this worked (observable)"
    }}
  ],
  "summary": {{
    "total_quick_wins": 4,
    "high_confidence_wins": 3,
    "aggregate_reach": "Total users across all wins",
    "recommended_first": "Which to do first and why",
    "validation_needed": "Summary of what needs customer confirmation"
  }}
}}
```

---

## Critical Rules for Quick Wins

### What Makes Something a Quick Win:
1. **Resources exist** (audience built, destination connected, source collecting)
2. **Configuration-only** (no development, no new integrations)
3. **Low complexity** (can be done in < 1 week)
4. **Clear gap** (obvious unused capability or misalignment)

### ✅ GOOD Quick Win:
- "Activate audience_va_subs (144K users) to existing Sailthru destination"
- Evidence: Audience exists and enabled, Sailthru destination exists and enabled, 0 connections currently
- Effort: Add audience to destination settings (30 min)
- Validation: "Is this audience intended for email campaigns?"

### ❌ BAD Quick Win:
- "Implement lifecycle marketing program"
- Why bad: Too vague, requires strategy definition, not obviously "quick"

### Confidence Levels:
- **High**: "Audience X has users but 0 destinations" (directly observable)
- **Medium**: "Activating audience X would improve engagement" (reasonable assumption)
- **Low**: "These users are high-value" (requires business context)

---

Generate 3-5 quick wins with proper confidence levels and validation questions."""


# Integration function for existing system
def get_enhanced_prompt(goal: str, structured_data: Dict[str, Any], business_context: str, user_notes: str = "") -> str:
    """
    Get enhanced prompt for specified goal

    Args:
        goal: 'workspace_audit' | 'quick_wins'
        structured_data: Full workspace data
        business_context: Business description
        user_notes: Optional user-provided context

    Returns:
        Enhanced prompt string with confidence levels and SA-ready format
    """
    prompts = EnhancedAuditPrompts()

    if goal == 'workspace_audit':
        return prompts.workspace_audit_with_confidence_levels(
            structured_data,
            business_context,
            user_notes
        )
    elif goal == 'quick_wins':
        return prompts.quick_wins_with_validation(
            structured_data,
            business_context,
            user_notes
        )
    else:
        # Fallback to existing system
        from goal_driven_prompts import GoalDrivenPrompts
        return GoalDrivenPrompts.goal_workspace_audit(
            structured_data,
            business_context,
            user_notes
        )
