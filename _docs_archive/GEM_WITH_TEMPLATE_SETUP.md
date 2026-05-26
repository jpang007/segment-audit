# Setting Up Gem with PowerPoint Template Context

This guide explains how to create a Gemini Gem that generates Python code referencing your actual PowerPoint template for exact formatting.

---

## 🎯 Goal

Create a Gem that:
1. Analyzes workspace audit data
2. References your PowerPoint template for styling/positioning
3. Generates **executable Python code** that creates the PowerPoint
4. Produces consistent, template-matching output every time

---

## 📋 What You'll Need

1. **PowerPoint Template**: `[T] Health Check for _________ [MAKE A COPY IN CUSTOMER FOLDER].pptx`
2. **Gem Instructions**: `GEMINI_GEM_PPT_CODE_GENERATOR.md` (from repo)
3. **Google AI Studio Account**: [aistudio.google.com](https://aistudio.google.com/)

---

## 🚀 Step-by-Step Setup

### Step 1: Prepare Template for Upload

Gemini Gems can accept uploaded files as context! Here's how:

1. **Convert PowerPoint to PDF** (for better compatibility):
   ```bash
   # Option A: Use PowerPoint
   # Open template → File → Export → PDF → Save as "health_check_template.pdf"
   
   # Option B: Use preview (Mac)
   open "[T] Health Check for _________.pptx"
   # File → Export as PDF
   ```

2. **Extract template as images** (alternative - better for Gem to "see" layout):
   ```bash
   # Open PowerPoint
   # File → Export → JPEG (or PNG)
   # Save all slides as: slide_01.jpg, slide_02.jpg, etc.
   ```

3. **Create template reference document** (recommended):
   - Create a markdown file describing the template
   - Include screenshots of each slide
   - Specify exact colors, fonts, positioning

### Step 2: Create the Gem

1. Go to [Google AI Studio](https://aistudio.google.com/)

2. Click **"Create new"** → **"Gem"**

3. Name it: **"Segment Health Check - Python Code Generator"**

4. Paste the contents of `GEMINI_GEM_PPT_CODE_GENERATOR.md` into the "Instructions" field

5. **Upload Template Context**:
   - Click **"Add file"** or **"Upload"** in the Gem editor
   - Upload either:
     - `health_check_template.pdf` (converted template)
     - OR a ZIP with all slide images: `template_slides.zip`
     - OR a markdown doc with template specs

6. **Add this to the instructions** (at the top):
   ```
   You have access to the PowerPoint template file. Reference it for:
   - Exact slide layouts and positioning
   - Font choices and sizes
   - Color schemes (hex/RGB values)
   - Chart styles and formatting
   - Text alignment and spacing
   
   Match the template exactly in generated Python code.
   ```

7. Configure settings:
   - **Model**: `gemini-2.0-flash-exp` (best for code generation)
   - **Temperature**: `0.2` (low for consistent, precise code)
   - **Max Output Tokens**: `8000` (to fit complete Python code)

8. Click **"Save"**

### Step 3: Create Template Reference Document (Recommended)

Since Gems work best with text context, create a detailed template spec:

**`template_reference.md`:**

```markdown
# Technical Health Check PowerPoint Template Reference

## Slide Dimensions
- Width: 10 inches
- Height: 5.625 inches (16:9 aspect ratio)

## Color Palette
- **Primary Blue**: #528ACA (RGB: 82, 138, 202)
- **Teal**: #52CC8A (RGB: 82, 204, 138)
- **Orange**: #FF8A52 (RGB: 255, 138, 82)
- **Dark Text**: #212121 (RGB: 33, 33, 33)
- **Gray Text**: #666666 (RGB: 102, 102, 102)
- **Light Gray**: #9AA0A6 (RGB: 154, 160, 166)

## Typography
- **Primary Font**: Proxima Nova
- **Secondary Font**: Helvetica Neue
- **Accent Font**: Archivo

### Font Sizes:
- Slide Titles: 32pt, Bold
- Main Content: 14pt
- Chart Labels: 11pt
- Big Numbers: 72pt, Bold
- Subtext: 12pt

## Slide Layouts

### Slide 1: Title
- Title: Centered, 44pt Bold, 2" from top
- Date: Centered, 18pt, 3.5" from top

### Slide 2: Data Limits
- Title: "Data: Limits" (32pt, top left)
- Big Percentage: 72pt Bold, Teal color, left side (1.5", 2")
- Details below: 14pt, centered under percentage
- 4 small charts on right side (API Calls, MTUs, Throughput, Limits)

### Slide 3: Events & Props
- Title: "Data: Events & Props"
- Horizontal bar chart (left): Top events by volume
  - Position: 0.5" left, 1.5" top
  - Size: 5.5" wide, 3.5" tall
  - Color: Blue bars
- Column chart (right): Unique events by source
  - Position: 6" left, 1.5" top
  - Size: 3.5" wide, 2.5" tall
  - Color: Teal bars

### Slide 4: Syntax Validation
- Title: "Data: Syntax"
- Health badge (left): Big circle with score
- Issues list (right): 3 columns
  - Issue type + count
  - Examples (italics)
  - Recommendation (blue text)

### Slide 5: Source Variety
- Title: "Stack: Source Variety"
- Stacked bar chart (left): Sources by library over time
  - Multiple colored bars (Javascript, iOS, Node.js, etc.)
- Big number (right): Total active sources
- Categories count below

### Slide 6: Source Volume
- Title: "Stack: Source Volume"
- Horizontal bar chart: Top sources by event count
  - Position: 1" left, 1.5" top
  - Size: 7" wide, 3.5" tall
  - Color: Green bars

### Slide 7: Destination Variety
- Title: "Stack: Destination Variety"
- Stacked bar chart: Destinations by category
  - Multiple categories (Warehouse, Analytics, Marketing)
- Big number (right): Total active destinations

### Slide 8: Connections
- Title: "Stack: Source<>Destination Connections"
- Big number (left): Total connections
  - 48pt Bold, Orange
- Bar chart (right): Top destinations by source count

### Slide 9: Team Activity
- Title: "Team: Active Workspace Users"
- Combo chart: Bars + line overlay
  - Active users (bars)
  - Actions per user (line)
- Workspace events list below

### Slide 11: Summary
- Title: "Summary"
- Health checklist:
  - ✓ Source Variety: Healthy
  - ✓ Source Volume: Healthy
  - ⚠ Event Syntax: Needs Attention
  - (Green for ✓, Yellow for ⚠, Red for ✗)

### Slide 12: Conclusions
- Title: "Conclusions"
- 3 columns (equal width):
  1. Biggest Issues (bullet list)
  2. Possible Causes (bullet list)
  3. How to Address (bullet list)

### Slide 13: Thank You
- Centered text: "Thank You!"
- Subtext: "Let's discuss your questions."

## Chart Styling
- No legends (show in title or labels)
- Grid lines: Light gray, minimal
- Bar spacing: Medium
- Font: 11pt for labels
- Colors: Rotate through Blue, Teal, Orange, Purple
```

Upload this to your Gem as a file.

---

## 🎨 Alternative: Extract Template Specs Programmatically

You can also analyze your template with python-pptx:

```python
from pptx import Presentation

prs = Presentation('[T] Health Check for _________.pptx')

print("📐 Template Analysis")
print("=" * 50)
print(f"Slides: {len(prs.slides)}")
print(f"Dimensions: {prs.slide_width / 914400}\" x {prs.slide_height / 914400}\"")

for idx, slide in enumerate(prs.slides):
    print(f"\n--- Slide {idx + 1} ---")
    for shape in slide.shapes:
        if hasattr(shape, "text"):
            print(f"  Text: {shape.text[:50]}...")
            print(f"  Position: ({shape.left / 914400:.2f}\", {shape.top / 914400:.2f}\")")
            print(f"  Size: {shape.width / 914400:.2f}\" x {shape.height / 914400:.2f}\"")
        elif shape.has_chart:
            print(f"  Chart: {shape.chart.chart_type}")
```

Save output to `template_analysis.txt` and upload to Gem.

---

## 🔄 Usage Workflow

### Step 1: Export Audit Data
```bash
# In dashboard: Download All Files
# Extract: for_gem_analysis/technical_health_check_data.json
```

### Step 2: Upload to Gem
1. Open your "Python Code Generator" Gem
2. Paste the contents of `technical_health_check_data.json`
3. Add prompt:

```
Generate Python code to create a Technical Health Check PowerPoint for this workspace.

Customer: Edible Arrangements
Context: E-commerce, web + mobile apps
Focus: Event quality, activation gaps

Match the template file exactly (colors, fonts, positioning).
Output: Complete Python script that runs immediately.
```

### Step 3: Get Python Code
Gem will output:

```
📊 WORKSPACE DATA ANALYSIS
[... data summary ...]

========================

Here's your Python code:

```python
#!/usr/bin/env python3
[... complete executable code ...]
```

**To use:**
1. Save as `generate_ppt.py`
2. Run: `python generate_ppt.py`
```

### Step 4: Run Generated Code
```bash
# Copy code from Gem
nano generate_ppt.py
# Paste code, save (Ctrl+X, Y, Enter)

# Run it
python3 generate_ppt.py

# Opens PowerPoint
✅ Health_Check_Edible_Arrangements_20260514.pptx
```

---

## 💡 Pro Tips

### 1. Version Your Template Reference
As template changes, update the reference doc and re-upload to Gem.

### 2. Create Template Snippets
Include common code patterns in Gem instructions:

```python
# Example: Add slide title (matches template)
def add_slide_title(slide, title_text):
    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(9), Inches(0.6))
    tf = title_box.text_frame
    tf.text = title_text
    tf.paragraphs[0].font.name = "Proxima Nova"
    tf.paragraphs[0].font.size = Pt(32)
    tf.paragraphs[0].font.bold = True
    tf.paragraphs[0].font.color.rgb = RGBColor(33, 33, 33)
```

### 3. Include Example Output
Upload a sample generated PowerPoint to Gem so it knows what "good" looks like.

### 4. Test with Sample Data
Before using with real customers, test with sample workspace data.

---

## 🎯 Comparison: JSON vs Python Code Output

### Original Gem (JSON Output):
**User workflow:**
1. Upload data to Gem
2. Get JSON with slide content
3. Manually run `generate_health_check_ppt.py gem_output.json`
4. Get PowerPoint

**Pros:** Separates data from code  
**Cons:** Extra manual step, JSON parsing needed

### New Gem (Python Code Output):
**User workflow:**
1. Upload data to Gem
2. Get complete Python script
3. Run: `python generated_script.py`
4. Get PowerPoint

**Pros:** One-step execution, all data embedded, no JSON parsing  
**Cons:** Larger Gem output (full Python code)

**Recommendation**: Use Python Code output for simplicity!

---

## 🔧 Customization

### Add Custom Branding
Update Gem instructions with your logo:

```
In the generated code, include this in the title slide:

# Add logo
logo_path = "company_logo.png"
if os.path.exists(logo_path):
    slide.shapes.add_picture(logo_path, Inches(8.5), Inches(0.2), width=Inches(1))
```

### Different Color Schemes
Create multiple Gems for different brands:
- "Health Check - Segment Branding"
- "Health Check - Customer Co-Branding"
- "Health Check - Enterprise Theme"

### Export to Different Formats
Update instructions to generate Google Slides format or PDF export code.

---

## 📂 Files to Upload to Gem

Upload these files as context:

1. **`template_reference.md`** (required) - Detailed template specs
2. **`template_slides.pdf`** (recommended) - Visual reference
3. **`code_snippets.py`** (optional) - Reusable python-pptx patterns
4. **`sample_output.pptx`** (optional) - Example of good output

---

## ✅ Success Criteria

Gem is working correctly when:
1. Generated code runs without errors
2. PowerPoint matches template visually
3. Colors/fonts/positioning accurate
4. All 12 slides present
5. Charts formatted correctly
6. Customer-specific data embedded
7. No manual editing needed

---

## 🐛 Troubleshooting

### Issue: Generated code has syntax errors
**Solution:** Lower Gem temperature to 0.1, specify "output valid Python code only"

### Issue: Positioning doesn't match template
**Solution:** Update template_reference.md with exact Inches() values

### Issue: Fonts not available
**Solution:** Use fallback fonts:
```python
try:
    p.font.name = "Proxima Nova"
except:
    p.font.name = "Helvetica"  # Fallback
```

### Issue: Gem output is truncated
**Solution:** Increase "Max Output Tokens" to 10000-16000

### Issue: Template reference not being used
**Solution:** Add to prompt: "Reference the uploaded template file for exact formatting"

---

## 📝 Example Gem Prompt

```
Generate Python code to create a Technical Health Check PowerPoint for this workspace.

Customer: Edible Arrangements
Date: May 14, 2026
Context: E-commerce company with web and mobile apps, using Segment for analytics and activation

Focus areas:
- Event naming quality
- Activation opportunities
- Warehouse syncing health

Requirements:
- Match the uploaded template exactly (colors, fonts, chart styles)
- Embed all data as constants in the code
- Make code immediately runnable (no external files needed)
- Include all 12 slides
- Output clean, well-commented Python code

[Paste technical_health_check_data.json here]
```

---

## 🚀 Next Steps

1. ✅ Create Gem with `GEMINI_GEM_PPT_CODE_GENERATOR.md` instructions
2. ✅ Upload `template_reference.md` to Gem
3. ✅ Test with sample audit data
4. ✅ Refine template specs based on output
5. ✅ Use for real customer health checks!

---

**You're all set! Your Gem will now generate production-ready Python code that creates template-matching PowerPoints! 🎉**
