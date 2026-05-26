# Segment Workspace Audit Dashboard

A Flask web application for auditing Segment workspaces using the Gateway API. Generates comprehensive reports on sources, destinations, audiences, MTU usage, and more.

## Features

- 🔍 **Complete Workspace Audit** - Sources, destinations, audiences, MTU data, audit trail
- 📊 **One-Click PowerPoint Generation** - Generate Technical Health Check presentations instantly
- 📦 **Export All Data** - Download complete audit as ZIP with CSV, JSON, and analysis-ready files
- 🎯 **Gateway API Only** - Uses official Segment Gateway GraphQL API
- 🚀 **Easy Deployment** - Runs locally or deploys to Render

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run Locally

```bash
python app.py
```

Open http://localhost:5001

### 3. Run an Audit

1. Enter workspace slug (e.g., `my-company`)
2. Enter Gateway API token ([How to get token](https://segment.com/docs/api/))
3. Click "Start Audit"
4. Wait for completion (1-2 minutes)

### 4. Generate PowerPoint

Click the green **"📊 Generate Health Check PPT"** button to instantly download a Technical Health Check PowerPoint presentation.

## What You Get

### Dashboard Pages

- **Overview** - High-level summary with key metrics
- **Sources** - All sources with status, libraries, connections
- **Audiences** - Engage audiences with sizes and destinations
- **Destinations** - Connected destinations by category
- **Observability** - Event volumes and stacked charts
- **Audit Trail** - Recent workspace activity
- **Usage** - MTU data and quota tracking

### Exports

#### PowerPoint Generation (NEW!)
- **One-Click**: Generate Technical Health Check presentation
- **6 Slides**: Title, Limits, Events, Source Variety, Summary, Thank You
- **Template Colors**: Blue, Teal, Orange matching Segment style
- **Charts**: Bar charts, column charts, big numbers, insights

#### Download All Files (ZIP)
- `processed/` - Analysis-ready CSVs
  - sources_with_destinations.csv
  - audiences_with_destinations.csv
  - top_events.csv
- `raw_data/` - Complete JSON exports
  - gateway_sources.json (with event schemas)
  - gateway_destinations.json
  - gateway_audiences.csv
  - gateway_mtu.json
  - gateway_usage_data.json
  - gateway_audit_trail.json
- `for_gem_analysis/` - Formatted for Gemini Gem analysis
  - workspace_audit_data.json (SA recommendations)
  - technical_health_check_data.json (PowerPoint data)

## PowerPoint Generation

### Usage

1. Run audit
2. Click "📊 Generate Health Check PPT"
3. PowerPoint downloads automatically (10 seconds)

### What's Generated:

- **Slide 1**: Title with customer name
- **Slide 2**: MTU usage (big percentage + quota)
- **Slide 3**: Top events chart (horizontal bars)
- **Slide 4**: Source variety (column chart by library)
- **Slide 5**: Summary with health indicators
- **Slide 6**: Thank you slide

See [DASHBOARD_PPT_BUTTON.md](DASHBOARD_PPT_BUTTON.md) for details.

## Architecture

### Core Files

- **app.py** (140KB) - Main Flask application with all routes
- **export_manager.py** (35KB) - Handles all data exports and ZIP generation
- **ppt_generator_api.py** (12KB) - PowerPoint generation from audit data
- **gemini_client.py** (12KB) - Gemini API integration (optional)

### Data Flow

```
Gateway API → app.py → audit_data/*.json → 
  ├─→ Dashboard pages (HTML/JS)
  ├─→ PowerPoint generation (ppt_generator_api.py)
  └─→ ZIP export (export_manager.py)
```

## Configuration

### Environment Variables

Create a `.env` file (or set in Render):

```bash
# Optional: Enable experimental features
ENABLE_EXPERIMENTAL_FEATURES=false

# Optional: Gemini API for recommendations
ENABLE_GEMINI_API=false
GEMINI_API_KEY=your_key_here
```

### Session Storage

- Workspace data stored in `audit_data/` folder
- Session persists for 7 days
- Click "New Audit" to reset

## Deployment

### Deploy to Render

1. Connect GitHub repo to Render
2. Set environment: Python 3
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app`
5. Auto-deploys on push to main

See [DEPLOYMENT.md](DEPLOYMENT.md) for details.

## Development

### Project Structure

```
segment-audit-dashboard/
├── app.py                    # Main application
├── export_manager.py         # Export logic
├── ppt_generator_api.py      # PowerPoint generation
├── gemini_client.py          # Gemini integration (optional)
├── requirements.txt          # Python dependencies
├── templates/                # HTML templates
├── static/                   # CSS, JS assets
├── audit_data/              # Workspace data (gitignored)
└── _docs_archive/           # Development documentation
```

### Adding Features

**New Dashboard Page:**
1. Add route in `app.py`
2. Create template in `templates/`
3. Add navigation link

**New Export Format:**
1. Add method to `ExportManager` in `export_manager.py`
2. Call from route in `app.py`

**Customize PowerPoint:**
1. Edit `ppt_generator_api.py`
2. Modify `generate_ppt_from_data()` function
3. Add slides, change colors, adjust layouts

## Troubleshooting

### PowerPoint Generation Fails
- Check: `audit_data/` folder has JSON files
- Fix: Run audit first to collect data

### "No module named 'pptx'"
- Fix: `pip install python-pptx XlsxWriter`

### Charts are empty
- Check: Sources have event schema data
- Fix: Ensure Gateway API token has correct permissions

### Session expired
- Fix: Click "New Audit" and re-authenticate

## Requirements

- Python 3.8+
- Flask 3.x
- python-pptx (for PowerPoint generation)
- XlsxWriter (for charts in PowerPoint)
- openpyxl (for Excel exports)
- requests (for Gateway API)

See `requirements.txt` for complete list.

## Gemini Gem Integration (Optional)

For enhanced analysis, you can use Gemini Gems:

1. Export: `for_gem_analysis/workspace_audit_data.json`
2. Upload to your "Segment SA Auditor" Gem
3. Get detailed recommendations and action plans

Gem instructions available in `_docs_archive/GEMINI_GEM_INSTRUCTIONS_V2.md`.

## Documentation

- **DASHBOARD_PPT_BUTTON.md** - PowerPoint generation guide
- **DEPLOYMENT.md** - Deployment instructions
- **_docs_archive/** - Development notes and Gem instructions

## Support

For issues or questions, check the documentation files or contact maintainer.

---

**Last Updated:** May 2026  
**Version:** 2.0 (PowerPoint generation integrated)
