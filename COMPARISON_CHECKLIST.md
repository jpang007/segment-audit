# Enhanced Prompts - Axios Comparison Checklist

## Setup Complete ✓

The enhanced prompt system is now integrated into the app:
- **File**: `enhanced_audit_prompts.py` added
- **Integration**: `app.py` updated to use enhanced prompts for workspace_audit goal
- **Active**: When you run "Workspace Audit" it will use the NEW enhanced prompt system

---

## How to Compare Results

### Step 1: Clear Cache (Important!)
The app caches recommendations, so you need to force a refresh:

**Option A - Clear cache via UI:**
- Look for "Force Refresh" checkbox when generating recommendations
- OR delete the cache files manually

**Option B - Clear cache manually:**
```bash
cd /Users/jpang/segment-audit-dashboard
rm -rf audit_data/recommendations_cache_*.json
```

### Step 2: Run Axios Audit Again

**Settings to use (same as before):**
- Goal: `Workspace Audit`
- Output Type: `Recommended Actions`
- Industry: (leave as detected or specify)
- Business Model: (leave as detected or specify)
- User Notes: (leave blank or add same notes as before)
- **DO NOT** fill in audience definitions (same as before)

### Step 3: Compare Outputs

Look for these improvements in the NEW output:

---

## Comparison Checklist

### ✅ Structure Improvements

**Old Output Had:**
```json
{
  "workspace_summary": {...},
  "sources_and_events": {...},
  "audience_health": {...},
  "key_risks": [...]
}
```

**New Output Should Have:**
```json
{
  "sa_action_plan": {
    "audit_metadata": {...},
    "findings": [...],
    "summary": {...}
  },
  "executive_brief": {
    "workspace_health_assessment": {...},
    "critical_findings": [...],
    "activation_opportunities": [...],
    "expansion_ideas": [...],
    "data_gaps_affecting_analysis": [...]
  }
}
```

---

### ✅ Each Finding Should Now Have:

**Required Fields:**
- [ ] `priority`: P0/P1/P2 (not just "high/medium/low")
- [ ] `category`: Specific category (Source Health, Destination Coverage, etc.)
- [ ] `finding_fact`: Observable fact (not interpretation)
- [ ] `evidence`: Array of specific data points
- [ ] `confidence`: High/Medium/Low
- [ ] `confidence_reasoning`: Why this confidence level
- [ ] `interpretation.likely_implication`: What it probably means
- [ ] `interpretation.alternative_explanations`: Other possibilities
- [ ] `why_it_matters.business_impact`: Business consequences
- [ ] `why_it_matters.technical_impact`: Technical consequences
- [ ] `sa_next_steps`: Array of specific actions
- [ ] `customer_validation_questions`: Questions to ask customer
- [ ] `owner`: SA/CSM/Customer/Engineering
- [ ] `effort`: Low/Medium/High
- [ ] `estimated_time`: Time estimate

**Example:**
Instead of:
```json
{
  "risk": "Production Blind Spot",
  "severity": "high",
  "evidence": "axios_web_PROD is DISABLED"
}
```

Should see:
```json
{
  "priority": "P0",
  "category": "Source Health",
  "finding_fact": "axios_web_PROD is disabled with 0 destinations",
  "confidence": "High",
  "interpretation": {
    "likely_implication": "Production collection may have stopped or moved",
    "alternative_explanations": ["Migrated to GTM", "Intentional"]
  },
  "customer_validation_questions": [
    "Is axios_web_PROD intentionally disabled?",
    "Has web tracking moved to another source?"
  ]
}
```

---

### ✅ Tone & Language Improvements

**Old (Alarmist):**
- [ ] ~~"Significant operational decay"~~
- [ ] ~~"Poor health"~~
- [ ] ~~"Trapped in disabled audiences"~~
- [ ] ~~"Critical failure"~~

**New (Consultative):**
- [ ] "Mixed health with activation gaps"
- [ ] "Core infrastructure configured but underutilized"
- [ ] "1.6M users in disabled audiences - potential re-enable opportunity"
- [ ] "Requires validation"

---

### ✅ Confidence Levels Throughout

**Check that:**
- [ ] Every finding has `confidence: "High|Medium|Low"`
- [ ] High confidence = directly observable (source disabled, audience count)
- [ ] Medium confidence = reasonable inference (disabled source suggests gap)
- [ ] Low confidence = requires customer validation (whether intentional)
- [ ] Each confidence level has reasoning

---

### ✅ Customer Validation Questions

**Check that:**
- [ ] Every finding includes 2-3 validation questions
- [ ] Questions are specific (not generic)
- [ ] Questions help clarify context before taking action
- [ ] Questions check for alternative explanations

**Example good questions:**
- "Is axios_web_PROD intentionally disabled?"
- "Has web tracking moved to another source?"
- "When was this source last active?"

---

### ✅ Data Limitations Acknowledged

**Check for:**
- [ ] `audit_metadata.data_completeness` section
- [ ] Explicit listing of what data is missing
- [ ] `limitations` array explaining impact of missing data
- [ ] No invented metrics for missing data

**Example:**
```json
{
  "data_completeness": {
    "event_volumes": "missing",
    "delivery_metrics": "missing"
  },
  "limitations": [
    "Event-level volumes not provided - cannot assess high-volume events",
    "Destination delivery health not available"
  ]
}
```

---

### ✅ Expansion Ideas Separated

**Check that:**
- [ ] Tool recommendations (Zendesk, Optimizely) are in `expansion_ideas` section
- [ ] Each expansion idea is labeled: `clearly_labeled_as: "expansion_idea_not_audit_finding"`
- [ ] Each has `confidence: "Low"`
- [ ] Each includes `validation_needed` field
- [ ] NOT mixed with audit findings

---

### ✅ No Duplicate Findings

**Old had:**
- axios_web_PROD mentioned in key_risks, observations, and sources section

**New should:**
- [ ] Each finding appears only once
- [ ] Related findings reference each other if needed
- [ ] No redundant information

---

### ✅ SA-Ready Format

**Each finding should include:**
- [ ] `owner`: Who should act
- [ ] `effort`: Low/Medium/High
- [ ] `estimated_time`: "30 min", "2 hours", etc.
- [ ] `sa_next_steps`: Concrete actions in order
- [ ] Can be used as a working checklist

---

### ✅ Prioritization

**Check summary includes:**
- [ ] `by_priority`: Count of P0/P1/P2 findings
- [ ] `by_confidence`: Count of High/Medium/Low findings
- [ ] `recommended_order`: Which to do first and why

---

## Score Comparison

### Old Output (Original Prompts): 6.5/10
**Issues:**
- ❌ No confidence levels
- ❌ Alarmist tone
- ❌ Speculative tool recommendations
- ❌ Duplicate findings
- ❌ No validation questions
- ❌ Not SA-ready

### New Output (Enhanced Prompts): Target 9/10
**Expected:**
- ✅ Confidence levels on every finding
- ✅ Consultative tone
- ✅ Expansion ideas clearly separated
- ✅ No duplicate findings
- ✅ Validation questions included
- ✅ SA-ready with owner/effort/time

---

## Key Improvements to Look For

### 1. **Confidence > Certainty**
Old says: "This is broken"
New says: "This appears broken (High confidence), but could be intentional - validate with customer"

### 2. **Facts > Judgments**
Old says: "Operational decay"
New says: "11 of 16 sources show NO_RECENT_DATA (fact), which may indicate stale pipelines (likely) or scheduled syncs (alternative)"

### 3. **Validation > Assumption**
Old says: "Restore sources immediately"
New says: "Ask customer: 'Are these sources expected to be active?' Then determine action"

### 4. **Expansion Ideas Separate**
Old mixes: "Connect Zendesk" (as audit finding)
New separates: "Customer Success tool integration" (in expansion_ideas, clearly labeled, low confidence)

### 5. **Data Limitations Explicit**
Old invents: "High-volume events unused"
New states: "Event volumes not provided - cannot assess event usage"

---

## After Comparison

Document your findings:
1. **What improved?** (structure, tone, actionability)
2. **What's still missing?** (anything you expected but didn't see)
3. **Quality score:** Rate the new output /10
4. **Would you trust this in front of a customer?** (Yes/No and why)

---

## Next Steps After Comparison

Based on results:
- ✅ If 8-9/10: Deploy to production, iterate on edge cases
- 🔄 If 6-7/10: Adjust prompts based on what's still off
- ❌ If <6/10: Review what Gemini is/isn't following from prompt

The enhanced prompts are very explicit, so if Gemini isn't following them, we may need to:
1. Simplify the schema
2. Add more examples
3. Test different models (gemini-3-flash vs gemini-2-pro)
