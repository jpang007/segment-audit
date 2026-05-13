# Segment Audit Dashboard - Gemini Gems Approach

## Overview

This dashboard no longer includes built-in AI recommendations. Instead, we use **Google Gemini Gems** - custom AI assistants that provide more flexible, powerful, and cost-effective analysis.

## Why Gems Instead of Built-in Recommendations?

### Benefits:
- **Zero API costs**: Gems run on Google's infrastructure at no additional cost
- **Better context retention**: Gems maintain longer conversation memory
- **More flexible**: Easy to iterate on prompts and instructions without redeploying
- **Reusable**: Same Gem can be used across multiple workspaces
- **Collaborative**: Share Gems with your team
- **Always improving**: Update Gem instructions without touching code

### Previous Approach (Removed):
- ❌ In-app recommendations page
- ❌ Costly Gemini API calls ($$$)
- ❌ Rate limiting issues
- ❌ Complex caching logic
- ❌ Harder to iterate on prompts

## Available Gems

### 1. Segment SA Auditor Gem
**Purpose:** Workspace health checks and technical recommendations

**File:** `GEMINI_GEM_INSTRUCTIONS.md`

**What it does:**
- Identifies data quality issues
- Finds activation gaps
- Detects workspace hygiene problems
- Recommends technical fixes
- Provides confidence-rated findings

**Best for:**
- Initial workspace audits
- QBRs and health checks
- Technical recommendations
- Compliance and governance reviews

---

### 2. Segment Use Case Builder Gem
**Purpose:** Strategic use case development and growth opportunities

**File:** `GEMINI_GEM_USE_CASE_BUILDER.md`

**What it does:**
- Analyzes business model and maturity
- Develops complete use cases with implementation roadmaps
- Prioritizes opportunities (P0 quick wins → P2 future)
- Provides industry-specific recommendations
- Creates activation maturity roadmaps

**Best for:**
- Customer workshops
- Use case discovery
- Strategic planning
- Business reviews
- Growth initiatives

---

## How to Use

### Step 1: Run the Audit
1. Go to the dashboard home page
2. Enter your Gateway token and workspace slug
3. Run the audit to collect workspace data
4. Click "📦 Download All Files" button

### Step 2: Extract the Gem Data File
1. Open the downloaded ZIP file
2. Navigate to `/for_gem_analysis/`
3. Find `workspace_audit_data.json`
4. Open it in a text editor

### Step 3: Add Business Context (Optional)
Edit the `business_context` field at the bottom of the JSON:

```json
{
  ...
  "business_context": "Axios is a digital media company focused on politics and business news. They have a subscription model with both free and Pro tiers. Key business goals: grow Pro subscriptions, increase newsletter engagement, improve content personalization."
}
```

### Step 4: Create Your Gem

**For Workspace Auditor:**
1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Create a new Gem
3. Copy the contents of `GEMINI_GEM_INSTRUCTIONS.md`
4. Paste into the Gem's system instructions
5. Name it "Segment SA Auditor"

**For Use Case Builder:**
1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Create a new Gem
3. Copy the contents of `GEMINI_GEM_USE_CASE_BUILDER.md`
4. Paste into the Gem's system instructions
5. Name it "Segment Use Case Builder"

### Step 5: Upload and Analyze
1. Open your Gem
2. Upload the `workspace_audit_data.json` file
3. Ask: "Analyze this workspace and provide recommendations"
4. Review the detailed findings

### Step 6: Iterate
Continue the conversation with your Gem:
- "Focus on the top 3 quick wins"
- "Give me more details on the cart abandonment use case"
- "How would this work for a B2B company?"
- "Create an implementation plan for the next 30 days"

## Tips for Best Results

### For the Auditor Gem:
- Provide accurate business context
- Ask for confidence levels on findings
- Request specific output formats (e.g., "as a table", "executive summary")
- Follow up on high-confidence findings first

### For the Use Case Builder Gem:
- Be specific about business goals
- Mention current pain points or initiatives
- Ask for phased implementation plans
- Request specific success metrics

## Example Prompts

### Initial Analysis:
```
"Analyze this workspace and provide your top recommendations with confidence levels"
```

### Focused Requests:
```
"What are the top 3 quick wins I can implement this week?"

"Develop a complete use case for improving trial conversion"

"Create a 90-day activation maturity roadmap"

"Show me what audience definitions I should build for an eCommerce company"
```

### Refinement:
```
"Make that recommendation more specific with actual event names from this workspace"

"What tools do I need to implement use case #2?"

"Translate this into a customer-facing proposal"
```

## Files in This Repo

| File | Purpose |
|------|---------|
| `GEMINI_GEM_INSTRUCTIONS.md` | Workspace Auditor Gem instructions |
| `GEMINI_GEM_USE_CASE_BUILDER.md` | Use Case Builder Gem instructions |
| `GEMINI_GEM_SETUP_GUIDE.md` | Step-by-step Gem setup |
| `GEM_QUICK_REFERENCE.md` | Quick reference card |
| `GEMINI_GEMS_README.md` | This file |

## Cost Comparison

### Old Approach (Built-in Recommendations):
- Gemini API: ~$0.02-0.05 per workspace analysis
- Rate limits: 60 requests/minute
- Monthly costs: ~$50-100 for heavy usage

### New Approach (Gems):
- Cost: **$0** (included with Google account)
- Rate limits: Generous (part of Gemini Pro quota)
- Monthly costs: **$0**

## Migration Notes

**What was removed:**
- `/recommendations` page
- `/api/generate-recommendations` endpoint
- `recommendations_engine.py`
- `recommendations_cache.py`
- `business_context_analyzer.py`
- All in-app AI recommendation logic

**What stayed:**
- All audit data collection
- Export functionality (including Gem-ready JSON)
- Dashboard visualizations
- CSV exports

**What improved:**
- Better recommendations (more context, better prompts)
- Zero API costs
- Faster iteration on prompts
- Team collaboration on Gems
- Conversation memory across sessions

## Support

For questions or improvements to the Gem instructions:
1. Test changes with your Gem first
2. Update the instruction files in this repo
3. Share successful prompt patterns with the team

---

**Ready to get started?** See `GEMINI_GEM_SETUP_GUIDE.md` for detailed setup instructions.
