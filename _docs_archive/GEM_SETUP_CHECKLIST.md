# Gem Setup Checklist - Python Code Generator

Quick reference for setting up your Technical Health Check PowerPoint Generator Gem.

---

## ✅ Files You Need

1. **`GEMINI_GEM_PPT_CODE_GENERATOR.md`** ✅ - Gem instructions (paste into Gem)
2. **`template_reference.md`** ✅ - Template specs (upload to Gem as context)
3. **`[T] Health Check for _________.pptx`** - Your PowerPoint template (optional, for visual reference)

---

## 🚀 Setup Steps (10 minutes)

### Step 1: Create the Gem

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Click **"Create new"** → **"Gem"**
3. Name: **"Segment Health Check - Python Code Generator"**

### Step 2: Add Instructions

1. Open `GEMINI_GEM_PPT_CODE_GENERATOR.md` from your repo
2. Copy entire contents (Cmd+A, Cmd+C)
3. Paste into Gem's "Instructions" field

### Step 3: Upload Template Reference

1. In Gem editor, look for **"Add file"** or **"Upload"** button
2. Upload: `template_reference.md`
3. This gives Gem the exact template specs (colors, positioning, fonts)

### Step 4: Configure Settings

- **Model**: `gemini-2.0-flash-exp` (best for code generation)
- **Temperature**: `0.2` (low = consistent, precise code)
- **Max Output Tokens**: `16000` (to fit full Python script)
- **Top-P**: `0.95` (default)
- **Top-K**: `40` (default)

### Step 5: Save & Test

1. Click **"Save"**
2. Test with sample data (see below)

---

## 🧪 Testing Your Gem

### Get Test Data

```bash
# In your dashboard, download all files
# Extract: for_gem_analysis/technical_health_check_data.json
```

### Test Prompt

Paste this into your new Gem:

```
[Paste contents of technical_health_check_data.json here]

Generate Python code to create a Technical Health Check PowerPoint for this workspace.

Customer: Test Company
Context: E-commerce, web + mobile apps
Focus: Event quality

Match the template reference exactly. Output complete, runnable Python code.
```

### Expected Output

Gem should return:

```
📊 WORKSPACE DATA ANALYSIS
========================
[... data summary ...]

Here's your Python code:

```python
#!/usr/bin/env python3
"""
Technical Health Check PowerPoint Generator
Customer: Test Company
...
"""
[... complete Python code ...]
```

To use:
1. Save as `generate_ppt.py`
2. Run: `python generate_ppt.py`
```

### Run Generated Code

```bash
# Copy code from Gem output
nano generate_ppt.py
# Paste, save (Ctrl+X, Y, Enter)

# Run it
python3 generate_ppt.py

# Should create:
✅ Health_Check_Test_Company_20260514.pptx
```

### Verify Output

Open the PowerPoint and check:
- [ ] All 13 slides present
- [ ] Charts display with data
- [ ] Colors match template (Blue, Teal, Orange)
- [ ] Positioning looks correct
- [ ] Customer name on title slide
- [ ] No errors opening file

---

## 📂 File Locations

```
segment-audit-dashboard/
├── GEMINI_GEM_PPT_CODE_GENERATOR.md    ← Paste into Gem instructions
├── template_reference.md               ← Upload to Gem as context file
├── GEM_WITH_TEMPLATE_SETUP.md          ← Detailed guide (reference)
├── GEM_SETUP_CHECKLIST.md              ← This file (quick reference)
└── generate_health_check_ppt.py        ← Old standalone script (backup)
```

---

## 🎯 Usage Workflow

Once Gem is set up:

1. **Export audit data** from dashboard
   - Click "Download All Files"
   - Extract `technical_health_check_data.json`

2. **Open Gem** in Google AI Studio

3. **Paste data + prompt**:
   ```
   [JSON data]
   
   Generate Python code for Technical Health Check PowerPoint.
   Customer: [Name]
   Context: [Industry, use case]
   ```

4. **Get Python code** from Gem

5. **Run code**:
   ```bash
   python3 generated_code.py
   ```

6. **PowerPoint created!** ✅

**Total time**: ~5 minutes per health check

---

## 🔧 Troubleshooting

### Gem output is truncated
**Fix**: Increase "Max Output Tokens" to 20000

### Code has syntax errors
**Fix**: Lower temperature to 0.1, add to prompt: "Output valid Python code only, no markdown"

### Positioning doesn't match template
**Fix**: Check `template_reference.md` has correct Inches() values, re-upload to Gem

### Colors are wrong
**Fix**: Verify RGB values in `template_reference.md`, update Color Palette section

### Gem not using template reference
**Fix**: Add to prompt: "Reference the uploaded template_reference.md file for exact formatting"

### Charts are empty
**Fix**: Gem might need more context. Add to prompt: "Ensure all charts have data from the workspace JSON"

---

## 💡 Pro Tips

### Tip 1: Save Gem URL
After creating Gem, save the URL for quick access:
```
https://aistudio.google.com/app/gems/[your-gem-id]
```

### Tip 2: Create Multiple Gems
- One for standard template (Segment branding)
- One for co-branded template (Customer + Segment)
- One for different template versions

### Tip 3: Update Template Reference
As template evolves, update `template_reference.md` and re-upload to Gem.

### Tip 4: Add Example Output
Include a screenshot of good PowerPoint output in template reference for Gem to "see" the goal.

### Tip 5: Version Control
Keep Gem instructions in Git so you can track changes and revert if needed.

---

## 📝 Quick Reference Commands

```bash
# Create Gem
# → Go to aistudio.google.com → Create Gem

# Upload files to Gem
# → Click "Add file" → Select template_reference.md

# Test generated code
python3 generated_code.py

# Requirements (if not installed)
pip install python-pptx XlsxWriter

# Open PowerPoint
open "Health_Check_*.pptx"
```

---

## ✅ Success Checklist

You're ready when:

- [x] Gem created with name "Segment Health Check - Python Code Generator"
- [x] Instructions from `GEMINI_GEM_PPT_CODE_GENERATOR.md` pasted
- [x] `template_reference.md` uploaded as context
- [x] Settings configured (model, temperature, max tokens)
- [x] Tested with sample data
- [x] Generated code runs without errors
- [x] PowerPoint matches template visually

---

## 🎉 You're Done!

Your Gem is now ready to generate template-matching Technical Health Check PowerPoints in 5 minutes per customer!

**Next**: Use it for real customer audits and iterate on template specs as needed.
