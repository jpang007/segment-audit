# Technical Health Check Gem Workflow

This guide explains how to use the **Segment Technical Health Check PowerPoint Generator Gem** to speed up creation of customer-facing health check presentations.

---

## Why Use a Gem for This?

**Problem**: Building all the chart visualizations in the dashboard takes significant dev time.

**Solution**: Use a Gemini Gem to generate PowerPoint-ready structured data that you can:
1. Manually insert into the PowerPoint template (fast)
2. Use to auto-generate slides with python-pptx (future enhancement)
3. Export as a formatted report

**Benefits**:
- ✅ Much faster than building custom chart pages in Flask
- ✅ Leverage Gemini's data analysis without API costs
- ✅ Get customer-facing insights automatically
- ✅ Easy to iterate on the prompt/instructions
- ✅ Can generate multiple formats (JSON, Markdown, PowerPoint outline)

---

## Step 1: Create the Gem

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Click **"Create new"** → **"Gem"**
3. Name it: **"Segment Health Check - PowerPoint Generator"**
4. Copy the entire contents of `GEMINI_GEM_HEALTH_CHECK_PPT.md` into the "Instructions" field
5. Set parameters:
   - Model: `gemini-2.0-flash-exp` or `gemini-1.5-pro`
   - Temperature: `0.3` (consistent, factual output)
6. Click **"Save"**

---

## Step 2: Add Export Feature to Dashboard

Add a button to export audit data in a format optimized for the Gem:

```python
@app.route('/api/export-health-check-data')
def export_health_check_data():
    """Export audit data formatted for Health Check Gem"""
    try:
        # Load audit data files
        sources = json.load(open(DATA_DIR / 'gateway_sources.json'))
        destinations = json.load(open(DATA_DIR / 'gateway_destinations.json'))
        usage = json.load(open(DATA_DIR / 'gateway_usage_data.json'))
        audit_trail = json.load(open(DATA_DIR / 'gateway_audit_trail.json'))
        
        # Create Gem-optimized structure
        health_check_data = {
            "workspace_info": {
                "name": session.get('customer_name', 'Unknown Customer'),
                "slug": session.get('workspace_slug', ''),
                "plan": usage.get('billing', {}).get('planName', 'Unknown')
            },
            "sources": [
                {
                    "name": s['name'],
                    "slug": s['slug'],
                    "status": s['status'],
                    "metadata": s['metadata'],
                    "schema": s.get('schema', {}),
                    "integrations": s.get('integrations', [])
                }
                for s in sources
            ],
            "destinations": [
                {
                    "name": d['name'],
                    "metadata": d['metadata'],
                    "status": d.get('enabled', True)
                }
                for d in destinations
            ],
            "usage": {
                "billing": usage.get('billing', {}),
                "mtus": usage.get('billing', {}).get('usage', {}).get('mtus', {}),
            },
            "audit_trail": audit_trail[:100]  # Last 100 events
        }
        
        return jsonify(health_check_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

Add button to `gateway_dashboard.html`:

```html
<button onclick="exportHealthCheck()" class="btn btn-success">
    📊 Generate Health Check Report
</button>

<script>
async function exportHealthCheck() {
    try {
        const response = await fetch('/api/export-health-check-data');
        const data = await response.json();
        
        // Download as JSON
        const blob = new Blob([JSON.stringify(data, null, 2)], {type: 'application/json'});
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `health-check-${data.workspace_info.name}-${new Date().toISOString().split('T')[0]}.json`;
        a.click();
        
        // Open Gem in new tab
        alert('Data exported! Opening Health Check Gem...\n\nPaste the downloaded JSON and ask:\n"Generate PowerPoint Health Check content for this workspace"');
        
        // Replace with your actual Gem URL
        window.open('YOUR_HEALTH_CHECK_GEM_URL', '_blank');
        
    } catch (error) {
        console.error('Error:', error);
        alert('Error exporting data');
    }
}
</script>
```

---

## Step 3: Run the Health Check

### Workflow:

1. **In Dashboard**: Click "Generate Health Check Report"
   - Downloads JSON file (e.g., `health-check-Mission-Lane-2026-05-14.json`)
   - Opens Gem in new browser tab

2. **In Gemini Gem**: 
   - Paste the JSON content
   - Add prompt: 
     ```
     Generate PowerPoint Health Check content for this Segment workspace.
     
     Customer context: E-commerce company focused on web and mobile
     Focus areas: Event data quality, destination activation gaps
     ```

3. **Gem Returns**: Structured JSON with all slide content:
   ```json
   {
     "slide_2_limits": { ... },
     "slide_3_events": { ... },
     "slide_4_syntax": { ... },
     ...
   }
   ```

4. **Copy Results**: Copy the JSON output from Gem

5. **Populate PowerPoint**:
   - **Option A (Manual)**: Open the PowerPoint template, manually insert charts/text from JSON
   - **Option B (Semi-Auto)**: Use a simple script to parse JSON and generate charts
   - **Option C (Future)**: Build python-pptx automation to fully generate slides

---

## Step 4: Insert into PowerPoint (Manual Method)

For each slide in the template:

### Slide 2: Data Limits
From `slide_2_limits.key_metrics`:
- Large text: **19.6%** (mtu_usage.percent_consumed)
- Small text: **2,347,594 / 12,000,000 MTUs**
- Insight text box: Copy `slide_2_limits.insight`

### Slide 3: Events & Props
From `slide_3_events.charts`:
- Create horizontal bar chart using `top_events_by_volume` array
- Create bar chart using `unique_events_by_source` array
- Insight: Copy `slide_3_events.insight`

### Slide 4: Syntax
From `slide_4_syntax.validation_results`:
- List issues with counts
- Add examples
- Health score badge
- Insight: Copy `slide_4_syntax.insight`

### Slide 5: Source Variety
From `slide_5_source_variety.charts`:
- Create bar chart from `sources_by_library`
- Big number: `total_active_sources`
- Categories count: `total_categories`

### Slide 6: Source Volume
From `slide_6_source_volume.charts`:
- Horizontal bar: `top_sources_by_events`

### Slides 7-9: Similar pattern...

---

## Step 5: (Optional) Semi-Automated Chart Generation

You can create a simple Python script to generate charts from the JSON:

```python
import json
import matplotlib.pyplot as plt
from io import BytesIO

def generate_bar_chart(data, title, filename):
    """Generate a horizontal bar chart from Gem JSON output"""
    labels = [item['label'] for item in data]
    values = [item['value'] for item in data]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(labels, values)
    ax.set_title(title)
    ax.set_xlabel('Count')
    
    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()

# Load Gem output
with open('gem_output.json') as f:
    gem_data = json.load(f)

# Generate charts
generate_bar_chart(
    gem_data['slide_5_source_variety']['charts']['sources_by_library'],
    'Active Sources by Library',
    'chart_source_variety.png'
)

# Repeat for other slides...
```

Then just drag/drop the generated PNG files into PowerPoint.

---

## Step 6: (Future) Full Automation with python-pptx

If this becomes a frequent workflow, build a script to auto-populate the template:

```python
from pptx import Presentation
from pptx.util import Inches, Pt
import json

def populate_health_check_ppt(gem_json_path, template_path, output_path):
    """
    Automatically populate PowerPoint template with Gem-generated data
    """
    # Load Gem output
    with open(gem_json_path) as f:
        data = json.load(f)
    
    # Load PowerPoint template
    prs = Presentation(template_path)
    
    # Slide 2: Data Limits
    slide = prs.slides[1]  # 0-indexed
    # Find text boxes and populate...
    for shape in slide.shapes:
        if shape.has_text_frame:
            if 'REPLACE' in shape.text:
                shape.text = data['slide_2_limits']['insight']
    
    # Slide 3: Events (add chart)
    slide = prs.slides[2]
    # Use python-pptx chart creation...
    
    # Save modified presentation
    prs.save(output_path)

# Usage
populate_health_check_ppt(
    'gem_output.json',
    'Health Check Template.pptx',
    'Health Check - Mission Lane - 2026-05-14.pptx'
)
```

---

## Comparison: Dashboard vs Gem Approach

### Building Charts in Dashboard
**Pros:**
- Fully automated
- Integrated experience
- Can add interactivity

**Cons:**
- **High dev effort**: Need to build each chart type
- Need Chart.js configurations
- HTML/CSS layout work
- Data formatting logic

**Time estimate**: 2-3 days of development

### Using Gem + Manual PowerPoint
**Pros:**
- **Fast**: ~30 minutes to set up Gem
- No chart rendering code needed
- Flexible output formats
- Easy to iterate on insights
- Customer gets professional PowerPoint

**Cons:**
- Manual step (copy/paste)
- Two tools (dashboard + Gem)

**Time estimate**: 30 mins setup, 10 mins per health check

---

## ROI Analysis

### Scenario: 10 Health Checks per Month

**Option A: Build full dashboard charts**
- Dev time: 16 hours ($2,400 at $150/hr)
- Per health check: 5 mins (automated)
- Total time/month: 16 hrs + 0.8 hrs = 16.8 hrs

**Option B: Use Gem + Manual**
- Setup time: 1 hour ($150)
- Per health check: 15 mins (export + Gem + manual entry)
- Total time/month: 1 hr + 2.5 hrs = 3.5 hrs

**Savings**: 13.3 hours/month = $1,995/month

**Break-even**: Immediately (unless you need >40 health checks/month)

---

## Recommended Next Steps

1. ✅ **Today**: Create the Health Check Gem
2. ✅ **Today**: Add export button to dashboard
3. ✅ **This week**: Run 1-2 test health checks manually
4. ⏳ **Next sprint** (if needed): Build python-pptx automation
5. ⏳ **Future** (if volume increases): Consider building dashboard charts

---

## Tips for Best Results

### When Using the Gem:

1. **Provide context**: Tell the Gem about the customer's industry/use case
2. **Request specific focus**: "Focus on event quality" or "Emphasize activation gaps"
3. **Iterate**: If output isn't perfect, refine with follow-up prompts
4. **Save outputs**: Store Gem JSON results in `audit_data/` folder for reference

### Improving the Gem Instructions:

As you use the Gem, update `GEMINI_GEM_HEALTH_CHECK_PPT.md` with:
- Better examples of good insights
- Common edge cases to handle
- Refined output formatting
- Additional chart types

The Gem instructions are version-controlled, so you can iterate quickly!

---

## Example End-to-End (5 minutes)

1. Open dashboard → "Generate Health Check Report" → JSON downloads, Gem opens
2. Paste JSON into Gem → Add: "Customer: Mission Lane (fintech), Focus: data quality"
3. Gem returns structured JSON in 30 seconds
4. Copy JSON → Open PowerPoint template
5. Insert key metrics, charts, and insights from JSON (3-4 minutes)
6. Save as "Health Check - Mission Lane - 2026-05-14.pptx"
7. Done! ✅

**Total time**: 5 minutes  
**vs building dashboard charts**: 16+ hours

---

## Questions?

**Q: Can the Gem generate the PowerPoint directly?**  
A: Not yet. Gemini can't create binary files. But it can generate python-pptx code that you run locally.

**Q: What if data is missing (e.g., no historical trends)?**  
A: The Gem will note "Data not available" and work with current snapshots.

**Q: Can I customize the output format?**  
A: Yes! Edit `GEMINI_GEM_HEALTH_CHECK_PPT.md` and update your Gem instructions anytime.

**Q: Is this better than the existing audit Gem?**  
A: Different purpose. The audit Gem is for SA action plans. This Gem is for customer-facing PowerPoint presentations.

**Q: Can I use both Gems together?**  
A: Absolutely! Export data → Run through both Gems → Get SA action plan + customer presentation.
