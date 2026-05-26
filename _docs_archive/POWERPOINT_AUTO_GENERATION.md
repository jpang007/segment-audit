# PowerPoint Auto-Generation - Complete Workflow

This document explains the **complete end-to-end workflow** for automatically generating Technical Health Check PowerPoint presentations from your audit data.

---

## 🎯 Overview

**Flow:**
1. Run audit in dashboard → Export data
2. Upload JSON to Gemini Gem → Get structured content
3. Run Python script → **PowerPoint generated automatically with charts!**

**Time:** ~5 minutes total (down from 2-3 days building dashboard charts!)

---

## 🚀 Quick Start (3 steps)

### Step 1: Export & Get Gem Analysis

```bash
# 1. In dashboard: Click "Download All Files"
# 2. Extract: for_gem_analysis/technical_health_check_data.json
# 3. Upload to Health Check Gem in Google AI Studio
# 4. Copy Gem's JSON output to a file (e.g., gem_output.json)
```

### Step 2: Generate PowerPoint

```bash
python3 generate_health_check_ppt.py gem_output.json "Customer Name"
```

### Step 3: Open & Present!

```bash
# PowerPoint file created: Health_Check_Customer_Name_YYYYMMDD.pptx
open "Health_Check_Customer_Name_20260514.pptx"
```

Done! ✅

---

## 📋 Prerequisites

### One-Time Setup (5 minutes)

1. **Install dependencies**:
```bash
pip install python-pptx XlsxWriter
```

2. **Create the Gemini Gem**:
   - Go to [Google AI Studio](https://aistudio.google.com/)
   - Create new Gem: "Segment Technical Health Check - PowerPoint Generator"
   - Paste instructions from `GEMINI_GEM_HEALTH_CHECK_PPT.md`
   - Set temperature to 0.3
   - Save

---

## 📊 What Gets Generated

The script creates a complete PowerPoint with **12 slides**:

1. **Title Slide** - Customer name, date
2. **Data: Limits** - MTU usage percentage (big number + details)
3. **Data: Events & Props** - Horizontal bar chart (top events) + Column chart (unique events)
4. **Data: Syntax** - Validation issues with examples and recommendations
5. **Stack: Source Variety** - Column chart (sources by library) + stats
6. **Stack: Source Volume** - Horizontal bar chart (top sources)
7. **Stack: Destination Variety** - Column chart (destinations by category)
8. **Stack: Connections** - Connection count + bar chart (top destinations)
9. **Team Activity** - Active users count + workspace events list
10. (Skip slide 10)
11. **Summary** - Health ratings with color coding (✓/⚠/✗)
12. **Conclusions** - 3 columns: Issues / Causes / Solutions
13. **Thank You** - Closing slide

### Chart Types:
- ✅ Horizontal bar charts (for rankings)
- ✅ Column charts (for comparisons)
- ✅ Big numbers with labels (KPIs)
- ✅ Color-coded health indicators
- ✅ Insight boxes on every slide
- ✅ Segment brand colors

---

## 💡 Usage Examples

### Basic Usage:
```bash
python3 generate_health_check_ppt.py gem_output.json "Mission Lane"
# Creates: Health_Check_Mission_Lane_20260514.pptx
```

### With Full Path:
```bash
python3 generate_health_check_ppt.py ~/Downloads/gem_output.json "Edible Arrangements"
```

### From Export Folder:
```bash
# After extracting audit export ZIP
cd ~/Downloads/segment_audit_edible_20260514/for_gem_analysis
# (Upload technical_health_check_data.json to Gem, save output)
python3 ../../segment-audit-dashboard/generate_health_check_ppt.py gem_output.json "Edible"
```

---

## 🔧 Customization

### Changing Colors

Edit `generate_health_check_ppt.py` and modify the color constants:

```python
# Segment brand colors
SEGMENT_GREEN = RGBColor(82, 204, 138)
SEGMENT_BLUE = RGBColor(82, 138, 204)
SEGMENT_ORANGE = RGBColor(255, 138, 82)
# ... etc
```

### Adding Your Logo

```python
# In _add_title_slide method, add:
slide.shapes.add_picture('logo.png', Inches(8.5), Inches(0.2), width=Inches(1))
```

### Adjusting Chart Sizes

Each chart has position and size defined as:
```python
x, y, cx, cy = Inches(1), Inches(1.5), Inches(5), Inches(3)
#              ^left    ^top         ^width      ^height
```

---

## 📁 File Structure

```
segment-audit-dashboard/
├── generate_health_check_ppt.py      ← PowerPoint generator script
├── GEMINI_GEM_HEALTH_CHECK_PPT.md    ← Gem instructions
├── HEALTH_CHECK_GEM_WORKFLOW.md      ← Workflow documentation
├── TECHNICAL_HEALTH_CHECK_SETUP.md   ← Setup guide
├── POWERPOINT_AUTO_GENERATION.md     ← This file
├── export_manager.py                 ← Exports technical_health_check_data.json
└── requirements.txt                  ← Updated with python-pptx, XlsxWriter
```

---

## 🎨 Gem Output Format

The Gem should return JSON in this structure:

```json
{
  "slide_2_limits": {
    "title": "Data: Limits",
    "key_metrics": { "mtu_usage": { ... } },
    "insight": "..."
  },
  "slide_3_events": {
    "title": "Data: Events & Props",
    "charts": {
      "top_events_by_volume": [ { "event_name": "...", "volume": 123 } ],
      "unique_events_by_source": [ { "source": "...", "event_count": 10 } ]
    },
    "insight": "..."
  },
  // ... more slides
}
```

If Gem output doesn't match this format, update `GEMINI_GEM_HEALTH_CHECK_PPT.md` and recreate the Gem.

---

## 🔄 Complete End-to-End Workflow

### Detailed Step-by-Step:

1. **Run Audit in Dashboard**
   ```
   - Login to dashboard
   - Enter workspace slug and Gateway token
   - Click "Start Audit"
   - Wait for completion
   ```

2. **Export Data**
   ```
   - Click "Download All Files" button
   - Save ZIP file (e.g., segment_audit_edible_20260514.zip)
   - Extract ZIP
   ```

3. **Prepare for Gem**
   ```
   - Navigate to: for_gem_analysis/
   - Open: technical_health_check_data.json
   - Copy entire contents (Cmd+A, Cmd+C)
   ```

4. **Generate Content via Gem**
   ```
   - Open Google AI Studio
   - Open your "Technical Health Check - PowerPoint Generator" Gem
   - Paste JSON data
   - Add prompt: "Generate PowerPoint Health Check content for this Segment workspace.
     Customer context: [industry, use case]"
   - Wait ~30 seconds
   - Copy Gem's JSON output
   ```

5. **Save Gem Output**
   ```bash
   # Create a file with Gem output
   nano gem_output.json
   # Paste JSON, save (Ctrl+X, Y, Enter)
   ```

6. **Generate PowerPoint**
   ```bash
   python3 generate_health_check_ppt.py gem_output.json "Customer Name"
   ```

7. **Review & Customize**
   ```
   - Open generated PowerPoint
   - Review charts and content
   - Adjust any customer-specific wording
   - Add company logo if needed
   - Save final version
   ```

8. **Present!**
   ```
   - PowerPoint is ready for customer presentation
   - All charts are properly formatted
   - Segment brand colors applied
   - Professional and consistent
   ```

---

## ⏱️ Time Comparison

| Approach | Setup Time | Per Health Check | Total (10 checks) |
|----------|-----------|------------------|-------------------|
| **Build Dashboard Charts** | 2-3 days | 5 mins | 16-24 hours |
| **Manual PowerPoint** | 0 | 2-3 hours | 20-30 hours |
| **Gem + Auto-Gen** | 30 mins | 5 mins | 1.3 hours |

**Savings**: ~18-28 hours for 10 health checks!

---

## 🎯 Quality Checklist

Before sending to customer, verify:

- [ ] Customer name is correct on title slide
- [ ] Date is current
- [ ] All charts have data (not empty)
- [ ] Insights are customer-specific (not generic)
- [ ] Numbers match audit data
- [ ] No placeholder text remains
- [ ] Color scheme is professional
- [ ] Slides are in correct order
- [ ] Thank you slide is personalized

---

## 🐛 Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'pptx'"
**Solution:**
```bash
pip install python-pptx XlsxWriter
```

### Issue: "FileNotFoundError: gem_output.json"
**Solution:** Ensure you saved the Gem output to a file in the correct location.

### Issue: Charts are empty
**Solution:** Check that Gem output has data in the `charts` objects. The Gem might need more context.

### Issue: "KeyError: 'slide_X_...'"
**Solution:** Gem output might be missing a slide. Re-run Gem with prompt: "Include all slides from 2-12"

### Issue: Colors don't match template
**Solution:** Edit RGB values in `generate_health_check_ppt.py` to match your brand.

---

## 🚀 Future Enhancements

Potential improvements (not yet implemented):

1. **Direct Integration**: Add button in dashboard to generate PPT without manual steps
2. **Template Support**: Use existing PowerPoint template instead of creating from scratch
3. **Custom Themes**: Support for multiple color schemes
4. **Logo Upload**: UI to upload company logo
5. **Batch Generation**: Generate multiple customer PPTs at once
6. **Export Options**: PDF, Google Slides format
7. **Historical Comparison**: Side-by-side with previous health check

---

## 📝 Example Output

After running the script, you'll see:

```bash
$ python3 generate_health_check_ppt.py gem_output.json "Edible Arrangements"

🎨 Generating Health Check PowerPoint for Edible Arrangements...
✅ PowerPoint saved: Health_Check_Edible_Arrangements_20260514.pptx

✅ Success! Open: Health_Check_Edible_Arrangements_20260514.pptx
```

The generated PowerPoint will be ~75-100KB with all charts and formatting.

---

## 📞 Questions?

**For technical issues:**
- Check the script: `generate_health_check_ppt.py`
- Review Gem instructions: `GEMINI_GEM_HEALTH_CHECK_PPT.md`

**For workflow questions:**
- See: `HEALTH_CHECK_GEM_WORKFLOW.md`
- See: `TECHNICAL_HEALTH_CHECK_SETUP.md`

**For customization:**
- Edit the generator script directly
- Modify Gem instructions and recreate Gem
- Update brand colors in RGB values

---

## ✅ Success Criteria

You'll know it's working when:
1. Script runs without errors
2. PowerPoint file is created (75-100KB)
3. All 12 slides are present
4. Charts display correctly with data
5. Colors match Segment brand (blue, green, orange)
6. Customer name appears on title slide
7. Insights are specific and relevant
8. Opens in PowerPoint/Keynote without issues

---

## 🎉 Benefits

**vs Building Dashboard Charts:**
- ✅ 95% faster to implement
- ✅ No frontend JavaScript/Chart.js code
- ✅ No chart rendering debugging
- ✅ Easy to customize per customer
- ✅ Professional PowerPoint output
- ✅ Can be edited after generation

**vs Manual PowerPoint Creation:**
- ✅ 30x faster per health check
- ✅ Consistent formatting
- ✅ No copy/paste errors
- ✅ Charts auto-sized and styled
- ✅ Reproducible results
- ✅ Easy to regenerate if data changes

**vs PowerPoint Template Only:**
- ✅ No manual chart creation
- ✅ No data entry errors
- ✅ Automatic insights generation
- ✅ AI-powered recommendations
- ✅ Scales to any data size

---

## 📦 Dependencies

Required Python packages (in `requirements.txt`):

```txt
python-pptx>=1.0.0    # PowerPoint generation
XlsxWriter>=3.0.0     # Required for charts in python-pptx
```

Optional (if you want to enhance):
```txt
Pillow>=10.0.0        # For image manipulation (logos, screenshots)
pandas>=2.0.0         # For data manipulation (already in requirements)
```

---

**That's it! You're now ready to auto-generate beautiful Technical Health Check PowerPoints in 5 minutes! 🎉**
