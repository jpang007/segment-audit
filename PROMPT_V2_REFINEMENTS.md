# Enhanced Prompts v2 - ChatGPT Refinements

## Score Progression
- **Original**: 6.5/10
- **v1 (Enhanced)**: 9/10 (Claude) / 8.5/10 (ChatGPT)
- **v2 (Refined)**: Target 9.5/10

---

## Changes from v1 → v2

Based on ChatGPT's feedback on the Axios output, we've made the following refinements:

---

### 1. ✅ Split Steps: Validation vs. Implementation

**Problem:**
v1 mixed validation and action in `sa_next_steps`, making it unclear when to validate vs. implement.

**Old (v1):**
```json
{
  "sa_next_steps": [
    "Ask customer: 'Is axios_web_PROD intentionally disabled?'",
    "Review source activity history",
    "Re-enable source if needed"
  ]
}
```

**New (v2):**
```json
{
  "validation_steps": [
    "Step 1: Ask customer validation questions",
    "Step 2: Review Segment UI for source activity history",
    "Step 3: Check if another source shows production traffic"
  ],
  "implementation_steps": [
    "Only proceed after validation confirms action is needed:",
    "Step 1: Re-enable axios_web_PROD source in Segment UI",
    "Step 2: Verify tracking snippet on live site",
    "Step 3: Reconnect to required destinations"
  ]
}
```

**Why:** Makes it explicit that validation happens FIRST, implementation only if needed.

---

### 2. ✅ Effort Ranges Instead of Precise Time Estimates

**Problem:**
"15 min to validate" sounds too precise and can be wrong if access/permissions are delayed.

**Old (v1):**
```json
{
  "effort": "Low",
  "estimated_time": "15 min to validate"
}
```

**New (v2):**
```json
{
  "effort_estimate": {
    "validation_effort": "Low",
    "validation_time_range": "15-30 min if customer knows their tracking setup",
    "implementation_effort": "Low to Medium",
    "implementation_dependencies": [
      "Quick if source just needs re-enabling in UI",
      "Longer if tracking snippet needs to be added back to site",
      "May require Engineering involvement if GTM changes needed"
    ]
  }
}
```

**Why:** More honest about variability; acknowledges dependencies that could slow things down.

---

### 3. ✅ Split Ownership: SA / Customer / Escalation

**Problem:**
"Owner: SA" doesn't clarify who does what in a customer engagement.

**Old (v1):**
```json
{
  "owner": "SA"
}
```

**New (v2):**
```json
{
  "ownership": {
    "sa_owner": "Review source configuration and guide customer through validation",
    "customer_owner": "Engineering team to confirm current production tracking setup",
    "escalation_path": "Segment Support only if source cannot be re-enabled or event flow issues persist"
  }
}
```

**Why:** Clear delineation of responsibilities and when to escalate.

---

### 4. ✅ Customer-Safe Wording

**Problem:**
SA needs to present findings without sounding accusatory.

**New (v2):**
```json
{
  "customer_safe_wording": "During the audit, we noticed that the axios_web_PROD source is currently disabled and not connected to any destinations. Before assuming this is an issue, we'd like to confirm whether production web tracking has moved to a different source or whether this source should still be active."
}
```

**Why:** Gives SAs ready-to-use language for customer conversations. Non-accusatory, collaborative tone.

---

### 5. ✅ Language Precision Guide

**Problem:**
Terms like "stale pipelines" are interpretations, not observations.

**Added to prompts:**
```
Language Precision Guide:

✅ "Sources reporting NO_RECENT_DATA" (what we observe)
❌ "Stale data pipelines" (interpretation without validation)

✅ "axios_web_PROD is disabled" (fact)
❌ "Production tracking is broken" (assumption)

✅ "8 enabled audiences have 0 destinations connected" (observable)
❌ "Audiences are unused" (could be used via Profile API)
```

**Why:** Ensures Gemini uses precise, defensible language.

---

### 6. ✅ Renamed: executive_brief → account_brief

**Rationale from ChatGPT:**
> "Executive brief" is good, but "Account Brief" may be more natural internally because not every output is truly for an executive. It might be for a CSM, account team, or SA preparing for a customer conversation.

**Change:**
```json
{
  "account_brief": {
    "workspace_health_assessment": {...}
  }
}
```

**Why:** More accurate term for internal SA/CSM use.

---

## Full Schema Changes

### Old (v1):
```json
{
  "sa_next_steps": [...],
  "owner": "SA",
  "effort": "Low",
  "estimated_time": "30 min"
}
```

### New (v2):
```json
{
  "validation_steps": [...],
  "implementation_steps": [...],
  "customer_safe_wording": "...",
  "ownership": {
    "sa_owner": "...",
    "customer_owner": "...",
    "escalation_path": "..."
  },
  "effort_estimate": {
    "validation_effort": "Low",
    "validation_time_range": "15-30 min",
    "implementation_effort": "Medium",
    "implementation_dependencies": [...]
  }
}
```

---

## Impact on SA Workflow

### Before (v1):
- SA sees "Re-enable source" as a next step
- Unclear if validation happens first
- Precise time estimates create false expectations
- Unclear when to escalate to Support

### After (v2):
- SA follows validation steps first
- Implementation only if validation confirms need
- Time ranges with dependencies are realistic
- Clear escalation path defined
- Customer-safe wording ready to copy/paste into email/meeting

---

## Expected Output Quality

### v1 Output (Axios Example):
- ✅ Confidence levels
- ✅ Alternative explanations
- ✅ Validation questions
- ⚠️ Mixed validation and action
- ⚠️ Precise time estimates
- ⚠️ Broad ownership
- ❌ No customer-safe wording

**Score: 8.5/10**

### v2 Output (Expected):
- ✅ Confidence levels
- ✅ Alternative explanations
- ✅ Validation questions
- ✅ Validation steps separate from implementation
- ✅ Time ranges with dependencies
- ✅ Split ownership (SA/Customer/Escalation)
- ✅ Customer-safe wording included
- ✅ More precise observable language

**Expected Score: 9.5/10**

---

## Remaining Opportunities (Path to 10/10)

1. **Cross-references between findings**
   - Link related findings (e.g., "See also Finding #3 about rETL")
   
2. **Risk scoring**
   - Add numeric risk score based on impact + likelihood

3. **Timeline visualization**
   - "This finding suggests issue began ~2 weeks ago based on NO_RECENT_DATA"

4. **Business impact quantification**
   - "417K unactivated users × $2 CPM = ~$834/month missed opportunity" (if data available)

5. **Automated follow-ups**
   - "Revisit this finding in 2 weeks to confirm rETL has been restored"

---

## Product Recommendation: Two-Tab UI

As ChatGPT suggested:

### Default View: SA Action Plan
- Primary working checklist
- Detailed findings with validation/implementation steps
- Owner assignments and effort estimates
- For: SAs, CSMs doing the work

### Secondary View: Account Brief
- Customer-friendly summary
- Workspace health assessment
- Top opportunities and concerns
- Exportable for: Account team alignment, manager updates, customer prep

**Interaction:**
- Toggle button: "SA View" / "Account View"
- Export options: "Copy Account Brief" / "Export SA Checklist"

---

## Files Updated

1. **enhanced_audit_prompts.py** - Core prompt system with v2 refinements
2. **PROMPT_V2_REFINEMENTS.md** - This document

---

## Testing v2

To test the v2 refinements:

1. **Clear cache** (important!)
   ```bash
   rm -rf audit_data/recommendations_cache_*.json
   ```

2. **Run Axios audit again** with same settings

3. **Look for v2 improvements:**
   - [ ] `validation_steps` and `implementation_steps` are separate
   - [ ] `effort_estimate` has time ranges, not precise times
   - [ ] `ownership` is split (sa_owner, customer_owner, escalation_path)
   - [ ] `customer_safe_wording` is present
   - [ ] More precise language ("sources reporting NO_RECENT_DATA" not "stale pipelines")

4. **Compare to v1 Axios output** - should see clear improvements

---

## Summary

**v1 was excellent** (8.5-9/10) but had room for polish around:
- Mixing validation and action
- Overly precise time estimates
- Unclear ownership split
- No customer-facing language

**v2 addresses these** with:
- Explicit validation-first workflow
- Realistic effort ranges with dependencies
- Clear SA/Customer/Escalation roles
- Customer-safe wording for every finding
- More precise observable language

This should push us from **8.5/10 → 9.5/10** in terms of SA-readiness and customer presentation quality.
