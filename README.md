# Segment Audit Dashboard

A Flask web application for auditing Segment workspaces with beautiful visual dashboards.

![Dashboard Preview](https://img.shields.io/badge/Flask-3.1.3-blue)
![Python](https://img.shields.io/badge/Python-3.11-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 🎯 Features

### Audience Audit
- 📊 Visual dashboard with stats cards and charts
- 🔍 Real-time search (case-insensitive)
- 📋 Sort by status, size, or name
- 🏷️ Filter by space ID
- 📥 Export to CSV
- 📄 Pagination (20 per page)

### Source Audit
- 🔌 Complete source inventory
- 🏷️ Filter by category, status, and labels
- 🔍 Search sources instantly
- 📊 Source status distribution chart
- 📥 Export filtered results

### Data Collection
- ⚡ Real-time progress tracking
- 🔄 Background data collection
- 🌐 Pagination support (fetches ALL data)
- 🔒 SSL bypass option for VPN users
- 🎯 Extracts events/traits from audience definitions

## 🚀 Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py

# Open browser
open http://localhost:5001
```

### Configuration
1. Enter your Segment API token (starts with `spg_`)
2. Add Workspace ID (optional - for sources)
3. Add one or more Personas Space IDs
4. Check SSL bypass if behind VPN
5. Click "Run Audit"

## 📦 Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions to:
- **Render** (recommended) - Free tier with persistent storage
- **Railway** - $5/month free credit
- **PythonAnywhere** - Simple Python hosting

### Quick Deploy to Render

1. Push this repo to GitHub
2. Go to [render.com](https://render.com)
3. Create new Web Service
4. Connect your GitHub repo
5. Use these settings:
   - **Build:** `pip install -r requirements.txt`
   - **Start:** `gunicorn app:app`
   - **Instance:** Free

Your app will be live in 2-3 minutes! 🎉

## 📁 Project Structure

```
segment-audit-dashboard/
├── app.py                   # Main Flask application
├── templates/
│   ├── index.html          # Configuration form
│   ├── progress.html       # Real-time progress tracker
│   ├── dashboard.html      # Audience audit dashboard
│   └── sources.html        # Source audit page
├── static/
│   └── css/
│       └── style.css       # Purple gradient design
├── requirements.txt        # Python dependencies
├── Procfile               # Deployment configuration
├── runtime.txt            # Python version
└── README.md              # This file
```

## 🛠️ Tech Stack

- **Backend:** Flask 3.1.3
- **Frontend:** Vanilla JS, Chart.js 4.4.0
- **Styling:** Custom CSS (purple gradient theme)
- **Data:** Pandas, CSV/JSON storage
- **Deployment:** Gunicorn WSGI server

## 🔧 Requirements

- Python 3.11+
- Flask 3.1.3
- Requests 2.32.5
- Pandas 3.0.1
- Chart.js 4.4.0 (CDN)

## 📖 Documentation

- **[FLASK_APP_README.md](FLASK_APP_README.md)** - Detailed app usage guide
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Complete deployment instructions

## 🎨 Features in Detail

### Smart Data Collection
- Fetches ALL audiences (not just first 100)
- Parses audience definitions for events/traits
- Handles regex extraction from query strings
- Filters out Segment-generated Personas sources

### CSV Parsing
- Proper handling of quoted fields with commas
- Respects nested quote escaping
- Maintains data integrity

### Search & Filter
- Case-insensitive search
- Real-time filtering
- Multiple filter combinations
- Export respects all filters

## 🔒 Security

- SSL verification can be bypassed for VPN users
- API tokens never stored permanently
- All data stays local
- HTTPS provided by hosting platforms

## 📄 License

MIT License - Feel free to use this for your Segment auditing needs!

## 🤝 Contributing

Contributions welcome! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests

## 📞 Support

For issues or questions, please open a GitHub issue.

---

**Built with ❤️ for Segment workspace auditing**
