# Technical Health Check - Quick Setup Guide

This guide explains how to generate customer-facing Technical Health Check PowerPoint presentations using your audit dashboard + Gemini Gem.

---

## 🎯 Goal

Speed up creation of PowerPoint Health Check presentations by using AI to generate slide-ready content instead of building custom charts in the dashboard.

**Time Savings**: 
- Traditional approach (building dashboard charts): ~2-3 days dev time
- Gem approach: ~30 mins setup + 5-10 mins per health check

---

## 📋 One-Time Setup (30 minutes)

### Step 1: Create the Gemini Gem

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Click **"Create new"** → **"Gem"**
3. Name it: **"Segment Technical Health Check - PowerPoint Generator"**
4. Copy the entire contents of `GEMINI_GEM_HEALTH_CHECK_PPT.md` (from this repo)
5. Paste into the Gem's "Instructions" field
6. Configure settings:
   - **Model**: `gemini-2.0-flash-exp` or `gemini-1.5-pro`
   - **Temperature**: `0.3`
7. Click **"Save"**
8. Note the Gem URL for later

That's it! Gem is ready to use.

---

## 🔄 Generating a Health Check (5-10 minutes)

### Step 1: Export Audit Data from Dashboard

1. Run your workspace audit as normal in the dashboard
2. Click **"Download All Files"** button (in Dashboard or Sources page)
3. This downloads a ZIP file: `segment_audit_[workspace]_[date].zip`

### Step 2: Extract the Health Check File

1. Unzip the downloaded file
2. Navigate to: `for_gem_analysis/`
3. You'll see two files:
   - `technical_health_check_data.json` ⭐ **This is the one for PowerPoint!**
   - `HEALTH_CHECK_README.txt` (instructions)
   - `workspace_audit_data.json` (for SA internal analysis, different Gem)

### Step 3: Generate PowerPoint Content via Gem

1. Open the `technical_health_check_data.json` file in a text editor
2. Copy all contents (Ctrl+A, Ctrl+C)
3. Open your **"Technical Health Check - PowerPoint Generator"** Gem
4. Paste the JSON into the Gem chat
5. Add this prompt:

```
Generate PowerPoint Health Check content for this Segment workspace.

Customer context: [Brief description: industry, use case, e.g., "E-commerce, web + mobile"]

Focus areas: [Optional: "Event quality", "Activation gaps", etc.]
```

6. Hit Enter and wait ~30 seconds

### Step 4: Copy Results into PowerPoint

The Gem will return structured JSON with slide-ready content. Example output:

```json
{
  "slide_2_limits": {
    "title": "Data: Limits",
    "key_metrics": {
      "mtu_usage": {
        "current": 2347594,
        "quota": 12000000,
        "percent_consumed": "19.6%"
      }
    },
    "insight": "MTU usage at 19.6% of quota - healthy margin for growth"
  },
  "slide_3_events": {
    "charts": {
      "top_events_by_volume": [
        {"event_name": "Page Viewed", "volume": 9326897},
        {"event_name": "Order Created", "volume": 7461754}
      ]
    }
  }
  // ... more slides
}
```

### Step 5: Populate PowerPoint Template

1. Open the PowerPoint template: `[T] Health Check for _________.pptx`
2. For each slide, copy the relevant data from Gem output:
   - **Slide 2 (Limits)**: Copy `percent_consumed`, insert into large text box
   - **Slide 3 (Events)**: Use `top_events_by_volume` array to create horizontal bar chart
   - **Slide 4 (Syntax)**: Copy validation issues and examples
   - **Slide 5-9**: Similar pattern for other sections
   - **Slide 11 (Summary)**: Copy health ratings
   - **Slide 12 (Conclusions)**: Copy findings and recommendations

3. Customize customer name, date, and other placeholders
4. Save as: `Health Check - [Customer Name] - [Date].pptx`

Done! ✅

---

## 📊 What Charts Can Be Generated

Based on data your dashboard already collects:

✅ **Slide 2 - Data Limits**: MTU usage percentage, quota comparison  
✅ **Slide 3 - Events & Props**: Top events by volume, unique events per source  
✅ **Slide 4 - Syntax**: Event naming validation with examples  
✅ **Slide 5 - Source Variety**: Sources grouped by library (Javascript, iOS, etc.)  
✅ **Slide 6 - Source Volume**: Event volume rankings  
✅ **Slide 7 - Destination Variety**: Destinations by category  
✅ **Slide 8 - Connections**: Source→Destination connection counts  
✅ **Slide 9 - Team Activity**: Active users and workspace events  
✅ **Slide 11 - Summary**: Health ratings across all dimensions  
✅ **Slide 12 - Conclusions**: Key findings with recommendations  

---

## 💡 Tips for Best Results

1. **Provide Customer Context**: Tell the Gem about the customer's industry and use case
   - Good: "E-commerce company, primarily web and iOS app, using Segment for analytics and warehouse syncing"
   - Bad: "A company using Segment"

2. **Specify Focus Areas**: If you know problem areas, mention them
   - "Focus on event naming consistency"
   - "Highlight activation opportunities"

3. **Iterate if Needed**: If Gem output isn't perfect, ask follow-up questions
   - "Provide more detail on syntax validation issues"
   - "Expand the recommendations section"

4. **Save Gem Outputs**: Store the JSON responses for reference and comparison over time

5. **Customize Before Sending**: The Gem provides data and insights, but you should still:
   - Adjust wording for customer tone
   - Add specific context you know about
   - Remove sensitive information if needed

---

## 🔍 What Data is Analyzed

The Health Check Gem analyzes:

- **Sources**: Names, status, libraries, event schemas, volumes, connections
- **Destinations**: Names, categories, enabled status
- **Events**: Names, types (track/page/screen), volumes, properties
- **Syntax**: Event naming patterns, consistency issues
- **Usage**: MTU consumption, quota limits, plan details
- **Team**: Active users, workspace activity types, recent changes

All data comes from your audit dashboard's Gateway API collection.

---

## 🆚 Comparison: Dashboard Charts vs Gem Approach

### Building Charts in Dashboard
**Time**: 2-3 days of development  
**Pros**: Fully automated, integrated UI  
**Cons**: High dev effort, maintenance overhead  

### Using Gem + PowerPoint
**Time**: 30 mins setup, then 5-10 mins per health check  
**Pros**: Fast setup, flexible, easy to iterate, professional PowerPoint output  
**Cons**: Manual copy/paste step  

**Recommendation**: Use Gem approach unless you need to generate 50+ health checks per month.

---

## 📂 File Reference

In your audit dashboard repo:

- **`GEMINI_GEM_HEALTH_CHECK_PPT.md`** - Gem instructions (paste into Google AI Studio)
- **`HEALTH_CHECK_GEM_WORKFLOW.md`** - Detailed workflow documentation
- **`export_manager.py`** - Updated to export `technical_health_check_data.json`

In the exported ZIP file (`for_gem_analysis/` folder):

- **`technical_health_check_data.json`** - Upload this to your Health Check Gem
- **`HEALTH_CHECK_README.txt`** - Quick reference guide
- **`workspace_audit_data.json`** - For SA internal analysis (different Gem)

---

## ❓ FAQ

**Q: Do I need a Gemini API key?**  
A: No! Gems are free to use in Google AI Studio. No API key or billing required.

**Q: Can the Gem generate the PowerPoint file directly?**  
A: Not yet. Gemini can't create binary files. But we could build a python-pptx script in the future to fully automate this.

**Q: What if my data doesn't have historical trends?**  
A: The Gem works with current snapshots. For quarterly trends, run audits regularly and compare outputs over time.

**Q: Can I use both Gems (Health Check + SA Auditor)?**  
A: Yes! They serve different purposes:
  - **Health Check Gem**: Customer-facing PowerPoint presentations
  - **SA Auditor Gem**: Internal SA action plans and recommendations

**Q: How do I update the Gem instructions?**  
A: Edit `GEMINI_GEM_HEALTH_CHECK_PPT.md` in the repo, then update your Gem in Google AI Studio.

---

## 🚀 Next Steps

1. **Today**: Create your Health Check Gem (30 mins)
2. **This Week**: Run 1-2 test health checks with real data
3. **Next Month**: Decide if you need python-pptx automation (for high volume)

---

## 📞 Questions?

Check the related documentation:
- `HEALTH_CHECK_GEM_WORKFLOW.md` - Detailed workflow
- `GEMINI_GEM_HEALTH_CHECK_PPT.md` - Gem instructions and examples
- `HEALTH_CHECK_README.txt` - In the exported ZIP file

Or contact the dashboard maintainer.
