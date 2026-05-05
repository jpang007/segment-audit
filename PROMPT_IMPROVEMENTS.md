# Enhanced SA-Quality Audit Prompts

## Summary of Improvements

Based on feedback from Claude and ChatGPT analysis of the Axios audit output, we've created an enhanced prompt system that generates SA-ready workspace audits.

---

## Key Problems Identified in Original Output

### 1. **Too Assumptive / Alarmist**
- ❌ "Significant operational decay" / "poor health"
- ❌ Treats disabled sources as automatically broken
- ❌ NO_RECENT_DATA assumed to be pipeline failure (could be scheduled)

### 2. **Lacks Confidence Levels**
- No distinction between:
  - **Facts**: "axios_web_PROD is disabled"
  - **Likely implications**: "production collection may have stopped"
  - **Judgments**: "operational decay"

### 3. **Speculative Tool Recommendations**
- Recommends Zendesk, Intercom, Optimizely, Braze without knowing customer needs
- Labels these as "audit findings" when they're actually "expansion ideas"

### 4. **Not SA-Ready**
- No validation questions for customer
- No owner/effort estimates
- No confidence ratings
- Same finding repeated multiple times
- Missing data limitations called out

### 5. **Weak Event Analysis**
- Says "Unknown Event data not provided" but still tries to analyze events
- Should explicitly state: "Event-level audit unavailable - add event data for better analysis"

---

## New Enhanced Prompt Features

### 1. **Confidence Levels (High/Medium/Low)**

Every finding now includes:

```json
{
  "finding_fact": "axios_web_PROD is disabled with 0 destinations",
  "confidence": "High",
  "confidence_reasoning": "High: directly observable in source configuration",
  "interpretation": {
    "likely_implication": "Production web collection may have stopped or moved",
    "alternative_explanations": [
      "Client-side tracking migrated to GTM",
      "Source disabled for testing",
      "Tracking snippet removed"
    ]
  }
}
```

**Definitions:**
- **High**: Directly observable (source disabled, audience has 0 destinations)
- **Medium**: Strong inference with limited context
- **Low**: Requires customer validation

### 2. **Separate Facts from Interpretations**

**Old approach:**
```json
{
  "risk": "Production Blind Spot - Critical",
  "evidence": "axios_web_PROD is DISABLED"
}
```

**New approach:**
```json
{
  "finding_fact": "axios_web_PROD is disabled and has 0 destinations",
  "interpretation": {
    "likely_implication": "Production web collection may have stopped",
    "alternative_explanations": ["Migration to different source", "Intentional for testing"]
  },
  "why_it_matters": {
    "business_impact": "IF unintentional, web analytics may be incomplete",
    "urgency": "High if unexpected; low if planned migration"
  }
}
```

### 3. **Customer Validation Questions Built-In**

Every finding includes questions the SA should ask:

```json
{
  "customer_validation_questions": [
    "Is axios_web_PROD intentionally disabled?",
    "Has web tracking moved to another source?",
    "When was this source last active?"
  ],
  "sa_next_steps": [
    "Ask customer validation questions above",
    "Review source activity history if available",
    "Check if axios_web_DEV is collecting prod traffic"
  ]
}
```

### 4. **Structured SA Action Plan**

Each finding follows this schema:

```json
{
  "priority": "P0 | P1 | P2",
  "category": "Source Health | Destination Coverage | Audience Hygiene | Activation Gap | Data Quality | Governance",
  "finding_fact": "Observable fact",
  "evidence": ["Data point 1", "Data point 2"],
  "confidence": "High | Medium | Low",
  "confidence_reasoning": "Why this confidence",
  "interpretation": {
    "likely_implication": "What this probably means",
    "alternative_explanations": ["Could also mean X", "Or Y"]
  },
  "why_it_matters": {
    "business_impact": "Revenue/user impact",
    "technical_impact": "Downstream effects",
    "urgency": "Why now (or not)"
  },
  "sa_next_steps": ["Step 1", "Step 2"],
  "customer_validation_questions": ["Q1", "Q2"],
  "owner": "SA | CSM | Customer | Engineering",
  "effort": "Low | Medium | High",
  "estimated_time": "e.g., '30 min', '2 hours'"
}
```

### 5. **Explicit Data Limitations**

```json
{
  "audit_metadata": {
    "data_completeness": {
      "sources": "complete",
      "destinations": "complete",
      "audiences": "complete",
      "event_volumes": "missing",
      "delivery_metrics": "missing",
      "tracking_plan": "missing"
    },
    "limitations": [
      "Event-level volumes not provided - cannot assess high-volume events",
      "Destination delivery health not available - cannot confirm destinations are working"
    ]
  }
}
```

### 6. **Separate Audit Findings from Expansion Ideas**

**Audit Findings** (based on workspace state):
- "8 enabled audiences with 417K users have 0 destinations"
- Confidence: High
- Evidence: Observable in audience config

**Expansion Ideas** (strategic possibilities):
- "Consider Customer Success tool integration"
- Clearly labeled as: "expansion_idea_not_audit_finding"
- Confidence: Low
- Validation needed: "Does customer have CS team? Do they use Zendesk?"

### 7. **Priority Definitions**

**P0**: Active data loss, broken production collection, compliance risk
- Example: "Production source disabled and no alternative collecting data"

**P1**: Activation gaps, stale rETL, large disabled audiences
- Example: "8 regional audiences (417K users) not activated anywhere"

**P2**: Governance, naming conventions, test cleanup
- Example: "Multiple test audiences with similar names"

### 8. **Tone Adjustments**

**Old:**
- "Significant operational decay"
- "Poor health"
- "Trapped in disabled audiences"

**New:**
- "Mixed health with activation gaps"
- "Core infrastructure configured but underutilized"
- "1.6M users in disabled audiences - may represent deprecated segments or re-enable opportunities"

---

## Example Comparison

### Original Axios Output (6.5/10):

```json
{
  "key_risks": [{
    "risk": "Production Blind Spot",
    "severity": "high",
    "evidence": "axios_web_PROD is DISABLED",
    "mitigation": "Verify if tracking was removed."
  }],
  "overall_health": "poor",
  "health_summary": "Significant operational decay..."
}
```

**Issues:**
- "Production Blind Spot" is a judgment, not a fact
- "Poor health" without acknowledging alternative explanations
- No validation questions
- No confidence level
- Alarmist tone

### Enhanced Output (9/10):

```json
{
  "findings": [{
    "priority": "P0",
    "category": "Source Health",
    "finding_fact": "axios_web_PROD is disabled and has 0 destinations connected",
    "evidence": [
      "Source status: DISABLED",
      "Destination count: 0",
      "Last modified: unknown"
    ],
    "confidence": "High",
    "confidence_reasoning": "High: directly observable in source configuration",
    "interpretation": {
      "likely_implication": "Production web event collection may have stopped, moved, or been intentionally disabled",
      "alternative_explanations": [
        "Client-side tracking migrated to GTM or different source",
        "Source disabled for migration or testing",
        "Tracking snippet removed from site"
      ]
    },
    "why_it_matters": {
      "business_impact": "IF unintentional, web analytics and user identification may be incomplete",
      "technical_impact": "Audiences depending on web events will have stale data",
      "urgency": "High if unexpected; low if this was planned"
    },
    "sa_next_steps": [
      "Ask customer: 'Is axios_web_PROD intentionally disabled?'",
      "Check if axios_web_DEV or another source is collecting prod traffic",
      "Review recent source activity history"
    ],
    "customer_validation_questions": [
      "Is your production website still sending data to Segment?",
      "Did you recently migrate web tracking to a different source?",
      "When was axios_web_PROD last active?"
    ],
    "owner": "SA",
    "effort": "Low",
    "estimated_time": "30 min conversation to validate"
  }],
  "workspace_health_assessment": {
    "overall_tone": "Mixed",
    "health_reasoning": "Core infrastructure configured but activation gaps exist. Key concern is data freshness on rETL sources.",
    "key_strengths": [
      "247 audiences configured showing mature segmentation strategy",
      "20 destinations connected covering email, ads, analytics, warehouse"
    ],
    "key_concerns": [
      "Primary production web source disabled - requires validation",
      "11 of 16 sources show NO_RECENT_DATA - may indicate stale rETL or scheduled syncs",
      "8 high-value regional audiences not activated to any destination"
    ]
  }
}
```

**Improvements:**
- ✅ Confidence level (High) with reasoning
- ✅ Separates fact from likely implication
- ✅ Lists alternative explanations
- ✅ Includes validation questions
- ✅ Specifies owner and effort
- ✅ Less alarmist tone
- ✅ Acknowledges uncertainties

---

## How to Use

### Option 1: Direct Integration (Recommended)

Update `recommendations_engine.py` to use enhanced prompts:

```python
from enhanced_audit_prompts import get_enhanced_prompt

# Replace existing prompt generation
prompt = get_enhanced_prompt(
    goal='workspace_audit',
    structured_data=structured_data,
    business_context=business_context,
    user_notes=user_notes
)
```

### Option 2: A/B Test

Run both prompt systems and compare outputs:

```python
# Old system
old_prompt = GoalDrivenPrompts.goal_workspace_audit(...)

# New system
new_prompt = get_enhanced_prompt('workspace_audit', ...)

# Send both to Gemini, compare results
```

---

## Expected Outcome

Using the enhanced prompts, the Axios audit would score **9/10** instead of **6.5/10**:

✅ **Added:**
- Confidence levels on all findings
- Customer validation questions
- Separation of facts vs. interpretations
- Data limitation acknowledgments
- Owner/effort estimates
- Less alarmist tone

✅ **Removed:**
- Speculative tool recommendations
- Duplicate findings
- Assumptive language ("operational decay")
- Invented event analysis when no data provided

✅ **Improved:**
- Structure (SA Action Plan + Executive Brief)
- Actionability (clear next steps)
- Credibility (honest about uncertainties)
- Usability (can use as working checklist)

---

## Next Steps

1. **Test with Axios data** - Re-run audit with enhanced prompts
2. **Compare outputs** - Side-by-side old vs. new
3. **Iterate prompt** - Refine based on Gemini responses
4. **Add destination health** - Layer in delivery metrics we can now fetch
5. **Deploy to production** - Replace old prompt system

---

## Additional Enhancements We Could Add

1. **Cost Analysis** - MTU impact of redundant audiences
2. **Tracking Plan Integration** - Schema violations, blocked events
3. **Destination Delivery Health** - Success rates, failures (we can fetch this now!)
4. **Historical Comparison** - "Last month X, this month Y"
5. **Benchmark Comparisons** - "Typical activation rate is 70%, yours is 62%"
