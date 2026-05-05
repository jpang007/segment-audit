# Segment Audit Dashboard - Flask Web App

**A complete web application with form input and visual dashboard**

---

## 🎯 What This Is

A single Flask app where you:
1. **Enter** your Segment credentials in a web form
2. **Click** "Run Audit" button
3. **Watch** real-time progress
4. **View** beautiful dashboard with charts

**No command line needed!** Everything happens in the browser.

---

## 🚀 Quick Start (3 Steps)

### Step 1: Install Dependencies

```bash
pip3 install flask flask-cors requests pandas
```

### Step 2: Start the App

```bash
python3 app.py
```

### Step 3: Open Browser

```bash
open http://localhost:5000
```

**That's it!** You'll see a configuration form.

---

## 📋 How to Use

### 1. Configuration Page

When you open http://localhost:5000, you'll see a form:

**Required fields:**
- **Customer/Company Name** - Will appear in dashboard title
- **Segment API Token** - Your Segment API token (spa_...)
- **Personas Space ID(s)** - One or more space IDs

**Optional field:**
- **Workspace ID** - Only needed if you want source data

**Example:**
```
Customer Name: Acme Corp
API Token: spa_abc123xyz789...
Workspace ID: spa_workspace_abc (optional)
Space IDs: spa_liv_space123
           spa_onnit_space456
```

### 2. Progress Page

After clicking "Run Audit":
- See real-time progress bar
- Watch status messages update
- Automatically redirects when complete

### 3. Dashboard Page

Beautiful visual dashboard with:
- ✨ Stats cards (audiences, sources, events, traits)
- 📊 Pie charts (audience distribution, source status)
- 📈 Bar charts (top events, top traits)
- 📋 Table of recent audiences

---

## 📁 File Structure

```
/Users/jpang/
├── app.py                          # Main Flask application
├── templates/
│   ├── index.html                  # Configuration form
│   ├── progress.html               # Progress/loading page
│   └── dashboard.html              # Visual dashboard
├── static/
│   └── css/
│       └── style.css               # All styling
└── audit_data/                     # Generated data (created automatically)
    ├── audit_summary.json
    ├── segment_audiences_audit.csv
    ├── event_coverage.csv
    └── trait_coverage.csv
```

---

## 🎨 Features

### Configuration Form
- Clean, professional design
- Helpful tooltips and examples
- Real-time validation
- Password field for API token
- Multi-line space ID input

### Progress Tracking
- Real-time progress bar (0-100%)
- Status messages ("Collecting sources...", etc.)
- Automatic redirect when complete
- Error handling with retry option

### Visual Dashboard
- Purple gradient design
- Interactive Chart.js graphs
- Hover for exact numbers
- Responsive layout (mobile friendly)
- "New Audit" button to start over

---

## 🔧 Configuration Options

### Multiple Spaces

Enter multiple space IDs separated by:
- **Commas:** `spa_space1, spa_space2, spa_space3`
- **Newlines:** One per line
- **Mixed:** Any combination

The app will collect data from all spaces and combine results.

### With/Without Sources

- **With workspace ID:** Collects source data (shows source status chart)
- **Without workspace ID:** Only collects audience data (source chart will show zeros)

---

## 📊 What Gets Collected

### From Segment APIs:
- Audience inventory (name, size, enabled status, owner, dates)
- Event references (which events are used in audiences)
- Trait references (which traits are used in audiences)
- Source list (if workspace ID provided)

### Generated Files:
- `audit_summary.json` - High-level statistics
- `segment_audiences_audit.csv` - Full audience list
- `event_coverage.csv` - Events with usage count
- `trait_coverage.csv` - Traits with usage count
- `segment_sources_audit.csv` - Source list (if workspace provided)

---

## 🎯 Use Cases

### Internal Team Review
1. Product manager opens app
2. Enters credentials
3. Reviews dashboard in team meeting
4. Identifies cleanup opportunities

### Customer Presentation
1. Run audit beforehand
2. Screen share the dashboard
3. Walk through stats and charts
4. Answer questions in real-time

### Regular Health Checks
1. Set reminder to run monthly
2. Enter same credentials each time
3. Compare dashboards month-over-month
4. Track workspace health trends

---

## 🔐 Security Notes

### API Token
- Entered in password field (hidden)
- Not stored anywhere
- Only used during audit run
- Cleared after completion

### Data Storage
- All data stored locally in `audit_data/`
- Never sent to external servers
- Can be deleted anytime
- No database needed

### Network
- Only connects to Segment APIs
- No third-party services
- All charts render client-side
- No analytics or tracking

---

## 🛠️ Customization

### Change Colors

Edit `static/css/style.css`:

```css
/* Find gradient definitions */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

/* Change to your brand colors */
background: linear-gradient(135deg, #YOUR_COLOR 0%, #YOUR_COLOR 100%);
```

### Add Logo

Edit `templates/index.html` or `templates/dashboard.html`:

```html
<div class="header">
    <img src="/static/logo.png" style="height: 60px;">
    <h1>Your Dashboard</h1>
</div>
```

### Modify Form Fields

Edit `templates/index.html` to add/remove fields:

```html
<div class="form-group">
    <label for="new_field">New Field</label>
    <input type="text" id="new_field" name="new_field">
</div>
```

Then update `app.py` to handle the new field:

```python
new_field = request.form.get('new_field')
```

---

## 🐛 Troubleshooting

### "Address already in use"
```bash
# Port 5000 is taken, change it in app.py:
app.run(host='0.0.0.0', port=5001)  # Changed from 5000
```

### "Module not found"
```bash
pip3 install flask flask-cors requests pandas
```

### Dashboard shows no data
- Check `audit_data/` directory exists
- Verify CSV/JSON files were created
- Look at browser console (F12) for errors

### Progress stuck at 0%
- Check terminal for error messages
- Verify API token is valid
- Ensure space IDs are correct

### Charts not rendering
- Clear browser cache (Ctrl+Shift+R)
- Check browser console (F12)
- Verify Chart.js is loading (check network tab)

---

## 🌐 Deployment Options

### Local (Development)
```bash
python3 app.py
# Access at http://localhost:5000
```

### Production Server
```bash
# Install gunicorn
pip3 install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Docker (Advanced)
```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "app.py"]
```

---

## 📈 Workflow Example

### Typical Session:

**9:00 AM - Open app**
```
http://localhost:5000
```

**9:01 AM - Enter credentials**
```
Customer: Acme Corp
Token: spa_abc123...
Space IDs: spa_space123, spa_space456
```

**9:02 AM - Click "Run Audit"**
```
→ Progress: "Collecting sources..." (20%)
→ Progress: "Collecting audiences..." (50%)
→ Progress: "Saving data..." (80%)
→ Complete! Redirecting...
```

**9:04 AM - Review dashboard**
```
Stats: 256 audiences, 12 sources
Charts: Distribution, top events, top traits
Table: Recent audiences with owners
```

**9:05 AM - Present to team**
```
Screen share → Walk through dashboard → Discuss findings
```

**Total time:** 5 minutes from start to presentation!

---

## 💡 Pro Tips

### Before Running
- ✅ Have API token ready (copy to clipboard)
- ✅ Know your workspace/space IDs
- ✅ Close other apps using port 5000

### During Audit
- ⏳ Don't refresh progress page (will restart)
- 📊 Progress takes 30s - 2 mins depending on data size
- 🔄 If it errors, click "Try Again"

### After Completion
- 💾 Take screenshots for records
- 📧 Share dashboard URL with team (if on shared server)
- 🔄 Click "New Audit" to run another

### For Presentations
- 🖼️ Full-screen the browser (F11)
- 🎨 Hide browser toolbars
- 💬 Prepare talking points for each chart
- 📱 Have backup screenshots

---

## 🎬 Demo Script

**Opening:**
> "I've set up a dashboard to show our Segment workspace health. Let me pull up the latest data."

**Configuration:**
> "I'll enter our workspace credentials..." [Fill form] "...and click Run Audit."

**Progress:**
> "This will take about a minute to collect data from Segment's API." [Wait for progress bar]

**Dashboard:**
> "Here's our dashboard. At the top, we have 256 total audiences..."

**Charts:**
> "This pie chart shows the breakdown. The purple doughnut is our sources..."

**Table:**
> "And here's a list of our most recent audiences with their owners and sizes."

**Wrap:**
> "I can run this anytime we want to check workspace health. Any questions?"

---

## 🆚 Compared to Command Line Tools

| Feature | Flask App | Command Line |
|---------|-----------|--------------|
| **Ease of Use** | Form-based, no commands | Requires typing commands |
| **Progress Tracking** | Real-time progress bar | Terminal output only |
| **Dashboard** | Opens automatically | Manual navigation |
| **Sharing** | Send URL | Send files |
| **Learning Curve** | None (just fill form) | Need to learn commands |
| **Automation** | Can add cron/scheduler | Already easy to automate |

**Best for:** Non-technical users, presentations, demos
**Command line best for:** Automation, scheduled jobs, scripts

---

## ✅ Next Steps

1. **Start the app:** `python3 app.py`
2. **Open browser:** http://localhost:5000
3. **Enter your credentials**
4. **Run first audit**
5. **Review dashboard**

---

## 📚 Related Files

- `DASHBOARD_README.md` - Original dashboard guide
- `COMPLETE_WORKFLOW.md` - Command line workflow
- `SEGMENT_AUDIT_QUICKSTART.md` - Data collection guide
- `START_HERE.md` - Master navigation

---

**The Flask app makes auditing accessible to everyone on your team!** 🎉

No technical knowledge required - just open browser, fill form, click button.
