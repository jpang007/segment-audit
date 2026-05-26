# Technical Health Check PowerPoint Template Reference

This document describes the exact formatting, positioning, and styling for the Technical Health Check PowerPoint template.

---

## Slide Dimensions
- **Width**: 10.00 inches
- **Height**: 5.62 inches (16:9 aspect ratio)

---

## Color Palette

Use these exact RGB values when generating slides:

- **Primary Blue**: RGB(82, 138, 202) / #528ACA
- **Teal/Cyan**: RGB(82, 204, 138) / #52CC8A
- **Orange**: RGB(255, 138, 82) / #FF8A52
- **Purple**: RGB(138, 82, 204) / #8A52CC
- **Yellow**: RGB(255, 204, 82) / #FFCC52
- **Red**: RGB(255, 82, 82) / #FF5252

**Text Colors:**
- **Dark Text**: RGB(33, 33, 33) / #212121
- **Gray Text**: RGB(102, 102, 102) / #666666
- **Light Gray**: RGB(154, 160, 166) / #9AA0A6

---

## Typography

### Font Families
- **Primary**: Proxima Nova
- **Secondary**: Helvetica Neue
- **Accent**: Archivo

**Fallbacks** (if fonts not available):
- Proxima Nova → Helvetica → Arial
- Helvetica Neue → Helvetica → Arial

### Font Sizes
- **Slide Titles**: 28pt (from template), Bold
- **Main Content**: 14pt
- **Big Numbers/KPIs**: 48-72pt, Bold
- **Subtext/Details**: 10-12pt
- **Chart Labels**: 11pt

---

## Slide-by-Slide Reference

### Slide 1: Title Slide
**Purpose**: Title card with customer name

**Layout**:
- **Title Box**:
  - Position: (0.50", 1.94")
  - Size: 9.00" x 1.84"
  - Font: 33pt
  - Text: "{Customer Name}\nHealth Check"
  - Alignment: Left

- **Date/Preparer Box**:
  - Position: (0.34", 4.82")
  - Size: 5.93" x 0.51"
  - Font: Proxima Nova, 10pt
  - Text: "Prepared {DATE} by {YOUR NAME}"

- **Header Label**:
  - Position: (1.81", 0.56")
  - Size: 2.39" x 0.48"
  - Font: Proxima Nova, 11pt, Bold
  - Text: "Professional Services"

- **Logo** (image):
  - Position: (0.11", 0.48")
  - Size: 1.70" x 0.59"

---

### Slide 2: Data - Limits
**Purpose**: MTU usage and quota information

**Template Structure**:
- **Slide Title**: "Data: Limits"
  - Position: (0.44", 0.27")
  - Size: 9.00" x 0.82"
  - Font: 28pt

- **Insight Box**: "Enter your insight here!"
  - Position: (1.23", 0.82")
  - Size: 8.44" x 0.51"
  - Font: ~11pt
  - **Replace with**: Customer-specific insight about MTU usage

- **Main Chart Area** (image placeholder):
  - Position: (1.54", 1.29")
  - Size: 5.59" x 3.99"
  - **Replace with**: 4 small charts
    - % of Limits Consumed (line chart)
    - API Calls (area chart with quota line)
    - MTUs (area chart showing Classic vs Deduped)
    - Throughput (area chart with quota line)

**Code Generation Notes**:
- Show big MTU percentage on left side
- Small charts stacked 2x2 on right side
- Use Teal color for healthy metrics

---

### Slide 3: Data - Events & Props
**Purpose**: Event volume and unique events analysis

**Template Structure**:
- **Slide Title**: "Data: Events & Props"
  - Position: (0.44", 0.27")
  - Font: 28pt

- **Insight Box**:
  - Position: (1.23", 0.82")
  - Size: 8.44" x 0.51"

- **Main Chart Area** (image placeholder):
  - Position: (2.51", 1.17")
  - Size: 3.82" x 4.29"
  - **Replace with**:
    - Horizontal bar chart: Top events by volume
    - Bar chart: Unique events per source
    - Bar chart: Avg properties per event

**Code Generation Notes**:
- Horizontal bars for event volume (easier to read long event names)
- Use Blue for primary charts
- Show top 10-15 events only

---

### Slide 4: Data - Syntax
**Purpose**: Event naming validation and syntax issues

**Template Structure**:
- **Slide Title**: "Data: Syntax"
  - Position: (0.44", 0.27")

- **Insight Box**:
  - Position: (1.23", 0.82")

**Code Generation Notes**:
- Left side: Health score badge (Good/Fair/Poor)
- Right side: List of issues with:
  - Issue type + count
  - Examples (3-4 event names)
  - Recommendation in Blue italic text
- Use color coding:
  - Good: Green
  - Fair: Yellow  
  - Poor: Red

---

### Slide 5: Stack - Source Variety
**Purpose**: Sources broken down by library type

**Template Structure**:
- **Slide Title**: "Stack: Source Variety"
  - Position: (0.44", 0.27")

- **Insight Box**:
  - Position: (1.23", 0.82")

**Code Generation Notes**:
- Column chart: Sources by library (Javascript, iOS, Node.js, etc.)
- Big number (right side): Total active sources
- Show categories count below
- Use multiple colors for different libraries

---

### Slide 6: Stack - Source Volume
**Purpose**: Top sources by event volume

**Template Structure**:
- **Slide Title**: "Stack: Source Volume"
  - Position: (0.44", 0.27")

- **Insight Box**:
  - Position: (1.23", 0.82")

**Code Generation Notes**:
- Horizontal bar chart: Top sources ranked by event count
- Use Teal/Green color
- Show top 8-10 sources

---

### Slide 7: Stack - Destination Variety
**Purpose**: Destinations broken down by category

**Template Structure**:
- **Slide Title**: "Stack: Destination Variety"
  - Position: (0.44", 0.27")

- **Insight Box**:
  - Position: (1.23", 0.82")

**Code Generation Notes**:
- Column chart: Destinations by category
- Big number (right): Total active destinations
- Categories: Warehouse, Analytics, Marketing, Advertising, etc.
- Use multiple colors for categories

---

### Slide 8: Stack - Source↔Destination Connections
**Purpose**: Connection matrix overview

**Template Structure**:
- **Slide Title**: "Stack: Source<>Destination Connections"
  - Position: (0.44", 0.27")

- **Insight Box**:
  - Position: (1.23", 0.82")

**Code Generation Notes**:
- Big number (left): Total connections
- Bar chart (right): Top destinations by source count
- Use Orange color for connections theme

---

### Slide 9: Team - Active Workspace Users
**Purpose**: User activity and workspace events

**Template Structure**:
- **Slide Title**: "Team: Active Workspace Users"
  - Position: (0.44", 0.27")

- **Insight Box**:
  - Position: (1.23", 0.82")

**Code Generation Notes**:
- Big number (left): Active user count (last 30-90 days)
- Right side: Workspace events breakdown
  - Sources added
  - Destinations modified
  - Users invited
  - Violations detected
- Use Purple color for team/people theme

---

### Slide 10: Team - Open Tickets
**Purpose**: Support ticket summary (optional)

**Template Structure**:
- Similar to other slides
- Often skipped if no ticket data

---

### Slide 11: Summary
**Purpose**: Health ratings overview

**Template Structure**:
- **Slide Title**: "Summary for [Customer]"
  - Position: (0.44", 0.27")

**Code Generation Notes**:
- Checklist format with health indicators:
  - ✓ (Green) = Healthy
  - ⚠ (Yellow) = Needs Attention
  - ✗ (Red) = Critical
- Categories:
  - Source Variety
  - Source Volume
  - Destination Variety
  - Data Limits
  - Event Syntax

---

### Slide 12: Conclusions
**Purpose**: Key findings and recommendations

**Template Structure**:
- **Slide Title**: "Conclusions for [Customer]"
  - Position: (0.44", 0.27")

**Code Generation Notes**:
- 3 equal columns:
  1. **Biggest Issues** (left)
  2. **Possible Causes** (middle)
  3. **How to Address** (right)
- Each column: 2-3 bullet points
- Font: 11pt
- Use Blue for column headers

---

### Slide 13: Thank You
**Purpose**: Closing slide

**Template Structure**:
- Centered text: "Thank You!"
- Subtext: "Let's discuss your questions."

**Code Generation Notes**:
- Large centered text (44pt)
- Position: (2", 2.5")
- Dark text color

---

## Chart Styling Guidelines

### Bar Charts (Horizontal)
- Use for: Rankings, top lists
- Color: Single color (Blue or Teal)
- No legend needed
- Show values on bars
- Sort: Descending (highest first)

### Column Charts (Vertical)
- Use for: Comparisons, categories
- Color: Multiple colors for different categories
- No legend if colors are self-explanatory
- Show values on top of bars

### Area Charts
- Use for: Trends over time, quota tracking
- Color: Fill with transparency (Teal or Blue)
- Show quota line in different color (if applicable)
- Grid lines: Light gray, minimal

### Chart Positioning
- Left side charts: (0.5", 1.5") to (6", 5")
- Right side charts: (6", 1.5") to (9.5", 4.5")
- Full-width charts: (1", 1.5") to (9", 5")

---

## Standard Element Positions

### Slide Title
- Position: (0.44", 0.27")
- Size: 9.00" x 0.82"
- Font: 28pt
- Color: Dark Text (#212121)

### Insight Box
- Position: (1.23", 0.82")
- Size: 8.44" x 0.51"
- Font: 10-11pt
- Color: Gray Text (#666666)
- Style: Italic
- Prefix with: "💡 " (optional emoji)

### Slide Number
- Position: (9.50", 5.00")
- Size: 0.50" x 0.62"
- Font: Small (~10pt)
- Format: "‹#›" (auto-number)

### Big Numbers/KPIs
- Font: 48-72pt, Bold
- Color: Varies by metric (Teal for healthy, Yellow for warning, Red for critical)
- Position: Usually left side (1.5", 2") with ~2.5" width

---

## Data Formatting

### Numbers
- Use commas: `2,399,879` (not `2399879`)
- Percentages: One decimal `20.0%` (not `20%` or `20.00%`)
- Large numbers: Use M/K suffixes for readability when appropriate

### Dates
- Format: "May 14, 2026" (not "05/14/2026")
- Relative: "Last 30 days", "Last 90 days"

---

## Color Usage by Metric Type

- **MTU/Usage**: Teal (#52CC8A)
- **Events/Data**: Blue (#528ACA)
- **Connections**: Orange (#FF8A52)
- **Team/Users**: Purple (#8A52CC)
- **Warnings**: Yellow (#FFCC52)
- **Critical Issues**: Red (#FF5252)

---

## Python-PPTX Code Patterns

### Add Slide Title
```python
def add_slide_title(slide, title_text):
    title_box = slide.shapes.add_textbox(Inches(0.44), Inches(0.27), Inches(9), Inches(0.82))
    tf = title_box.text_frame
    tf.text = title_text
    p = tf.paragraphs[0]
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.color.rgb = RGBColor(33, 33, 33)
```

### Add Insight Box
```python
def add_insight_box(slide, insight_text):
    insight = slide.shapes.add_textbox(Inches(1.23), Inches(0.82), Inches(8.44), Inches(0.51))
    tf = insight.text_frame
    tf.text = f"💡 {insight_text}"
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.font.size = Pt(11)
    p.font.italic = True
    p.font.color.rgb = RGBColor(102, 102, 102)
```

### Add Big Number
```python
def add_big_number(slide, value, label, color_rgb, left, top):
    # Number
    num_box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(2.5), Inches(1))
    tf = num_box.text_frame
    tf.text = str(value)
    p = tf.paragraphs[0]
    p.font.size = Pt(64)
    p.font.bold = True
    p.font.color.rgb = RGBColor(*color_rgb)
    p.alignment = PP_ALIGN.CENTER
    
    # Label
    label_box = slide.shapes.add_textbox(Inches(left), Inches(top + 0.9), Inches(2.5), Inches(0.4))
    lf = label_box.text_frame
    lf.text = label
    lf.paragraphs[0].font.size = Pt(14)
    lf.paragraphs[0].alignment = PP_ALIGN.CENTER
```

---

## Notes for Gem Code Generation

When generating Python code:

1. **Use exact positioning** from this reference
2. **Match colors** from the Color Palette section
3. **Include all 13 slides** (can skip Slide 10 if no ticket data)
4. **Embed data** as constants at top of script
5. **Handle missing data** gracefully (don't crash, show "N/A" or skip chart)
6. **Include helper functions** (add_slide_title, add_insight_box, etc.)
7. **Make code runnable** immediately without external files
8. **Use template fonts** with fallbacks
9. **Format numbers** with commas and proper decimals
10. **Add comments** explaining each section

---

## Success Criteria

Generated PowerPoint matches template when:
- [ ] All slides present and in correct order
- [ ] Slide titles match template positioning
- [ ] Charts use correct colors from palette
- [ ] Fonts match (Proxima Nova or fallback)
- [ ] Big numbers properly sized and colored
- [ ] Insights boxes positioned correctly
- [ ] Data formatted with commas/decimals
- [ ] Visual style matches template images
- [ ] Opens without errors in PowerPoint/Keynote

---

**Last Updated**: May 14, 2026  
**Template Version**: Technical Health Check v1.0
