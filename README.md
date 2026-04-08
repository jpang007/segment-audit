# Segment Audit Dashboard

A comprehensive Flask web application for auditing and analyzing Segment workspaces with interactive visual dashboards and AI-powered exports.

![Dashboard Preview](https://img.shields.io/badge/Flask-3.1.3-blue)
![Python](https://img.shields.io/badge/Python-3.11-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Overview

The Segment Audit Dashboard provides a unified interface to analyze, visualize, and export comprehensive workspace data from Segment. It connects to the Segment Public API to collect data across audiences, sources, destinations, computed traits, Reverse ETL models, and observability metrics, presenting everything in an intuitive web interface.

## 🎯 Key Features

### 📊 Audiences Dashboard
- **Visual Analytics**: Interactive charts showing audience distribution, enabled/disabled/empty counts
- **Audience Insights**: View definitions with syntax-highlighted event and trait references
- **Direct Links**: Click audience names to jump directly to Segment workspace
- **Advanced Filtering**: Search, filter by space, sort by size/status/name/created/updated dates
- **Event/Trait Coverage**: Automatically extracts and analyzes all events and traits referenced

### 🔌 Sources & Connections
- **Source Inventory**: Complete catalog with logos, types, categories, and labels
- **Connection Mapping**: View all source → destination connections with visual status indicators
- **Category Analysis**: Filter by JavaScript, Mobile, Server, Cloud sources
- **Status Tracking**: See enabled/disabled distribution with real-time filtering

### 🧮 Computed Traits
- **Type Breakdown**: Automatic classification (Event Count, Sum, Most Frequent, Unique Count, etc.)
- **Definition Viewer**: Syntax-highlighted trait definitions with event highlighting
- **Beta Detection**: Automatic warning for workspaces without private beta access
- **Sort & Filter**: Search by name/type, filter by enabled status, sort by created/updated dates

### 🔄 Reverse ETL Models
- **Model Catalog**: View all warehouse sync models with source mapping
- **SQL Query Viewer**: Click any model to see full SQL query in modal dialog
- **Query Identifiers**: Display primary keys and identifier columns
- **Status Overview**: Track enabled vs disabled syncs

### 📈 Observability
- **Event Volume Tracking**: 14-day event volume history by source
- **Flexible Timeframes**: Toggle between 7-day and 14-day views
- **Visual Charts**: Stacked bar charts showing daily event counts per source
- **Volume Analysis**: Identify high-volume sources and unusual spikes

### ✨ AI Export
- **Comprehensive Markdown**: Single-click export of entire workspace analysis
- **Smart Formatting**: Structured sections for sources, audiences, traits, RETL models, observability
- **Context-Aware**: Automatically excludes private beta features (computed traits) if inaccessible
- **AI-Ready Format**: Optimized for feeding into Claude or other LLMs for analysis

## 💡 Use Cases

### Customer Success & Solutions Architects
- **Workspace Health Checks**: Quickly assess customer implementations during onboarding or QBRs
- **Migration Planning**: Export comprehensive workspace state before/after migrations
- **Best Practice Reviews**: Identify unused sources, empty audiences, or misconfigured connections
- **Documentation**: Generate instant workspace summaries for customer handoffs

### Technical Account Management
- **Troubleshooting**: View complete connection topology when debugging data flow issues
- **Audit Trails**: Track computed traits, RETL models, and audience configurations
- **Capacity Planning**: Analyze event volumes to identify high-traffic sources
- **Optimization**: Find opportunities to consolidate sources or clean up unused resources

### Data Engineering & Analytics
- **Dependency Mapping**: Understand which events/traits are used across audiences and computed traits
- **Schema Analysis**: Review all computed trait definitions and aggregation patterns
- **Query Auditing**: Inspect all RETL SQL queries and identifier mappings
- **Volume Monitoring**: Track event volumes over time to detect anomalies

### Sales Engineering & Pre-Sales
- **Discovery Calls**: Quick workspace analysis to understand prospect's current implementation
- **POC Planning**: Identify integration points and data patterns
- **Competitive Analysis**: Compare configurations across customer segments

## 🚀 Quick Start

### Prerequisites
- Python 3.11 or higher
- Segment API Token (Workspace Owner or Workspace Member with API access)
- Workspace ID and Space IDs

### Installation

```bash
# Clone the repository
git clone https://github.com/jpang007/segment-audit.git
cd segment-audit-dashboard

# Install dependencies
pip install -r requirements.txt

# Run the application
python3 app.py

# Open browser to http://localhost:5001
```

### Configuration

1. **API Token**: Create a token in Segment (Settings → Workspace Settings → Access Management → Tokens)
   - Required permissions: `Workspace Member` (read-only access)
   
2. **Workspace ID**: Found in Segment URL or Settings

3. **Space IDs**: One or more Personas Space IDs (comma-separated for multi-space audits)

4. **SSL Verification**: Disable if behind corporate VPN causing certificate issues

## 📊 Technical Capabilities

### API Integration
- **Comprehensive Coverage**: Integrates with Segment Public API v1 endpoints
- **Pagination Handling**: Automatically fetches ALL resources (not limited to first page)
- **Rate Limiting**: Graceful handling with proper error messages
- **Multi-Space Support**: Aggregates data across multiple Personas spaces

### Data Processing
- **Smart Parsing**: Extracts events and traits from audience SQL definitions using regex
- **Type Inference**: Automatically classifies computed traits based on query patterns
- **Deduplication**: Handles cross-space resources without duplication
- **Error Handling**: Graceful degradation when features are unavailable (e.g., computed traits private beta)

### Frontend
- **Responsive Design**: Works on desktop and mobile devices
- **Real-Time Updates**: Progress tracking during data collection
- **Interactive Charts**: Chart.js visualizations with hover details
- **No Framework Overhead**: Pure vanilla JavaScript for fast load times

### Session Management
- **Persistent Sessions**: Session lasts 7 days (no need to re-enter API token)
- **Background Processing**: Async data collection with real-time progress updates
- **Fresh Data**: Automatic cleanup of previous audit data when running new audits

## 🛠️ Tech Stack

- **Backend**: Flask 3.1.3 (Python web framework)
- **API Client**: Requests 2.32.5 with retry logic
- **Data Processing**: Pandas 3.0.1 for CSV/JSON handling
- **Frontend**: Vanilla JavaScript ES6+
- **Visualization**: Chart.js 4.4.0 with ChartDataLabels plugin
- **Styling**: Custom CSS with purple gradient theme
- **Server**: Gunicorn WSGI (production deployment)

## 📁 Project Structure

```
segment-audit-dashboard/
├── app.py                          # Main Flask application & API client
├── templates/
│   ├── index.html                  # Landing page & configuration
│   ├── dashboard.html              # Audiences dashboard
│   ├── sources.html                # Sources inventory
│   ├── connections.html            # Source → Destination connections
│   ├── computed_traits.html        # Computed traits analysis
│   ├── retl_models.html            # Reverse ETL models
│   └── observability.html          # Event volume metrics
├── static/
│   └── css/
│       └── style.css               # Unified stylesheet
├── audit_data/                     # Runtime data directory
│   ├── audit_summary.json          # Audit metadata & stats
│   ├── segment_audiences_audit.csv # Audience data
│   ├── segment_sources_audit.csv   # Source data
│   ├── segment_computed_traits_audit.csv # Computed trait data
│   ├── segment_retl_models.json    # RETL model data (JSON for SQL queries)
│   └── segment_event_volumes.json  # Observability data
├── requirements.txt                # Python dependencies
├── Procfile                        # Gunicorn configuration
└── runtime.txt                     # Python version
```

## 🔐 Security & Privacy

- **No Persistent Storage**: API tokens stored only in session (7-day expiry)
- **Local Processing**: All data processing happens in-memory or local filesystem
- **Read-Only Access**: Requires only read permissions, never modifies Segment data
- **SSL Options**: Configurable SSL verification for corporate VPN environments
- **CORS Proxy**: Logo images proxied through backend to avoid CORS issues

## 📖 API Reference

The dashboard interacts with these Segment Public API v1 endpoints:

- `GET /spaces` - List all Personas spaces
- `GET /spaces/{id}/computed-traits` - Computed traits (private beta)
- `GET /audiences` - All audiences with definitions
- `GET /sources` - Source catalog
- `GET /destinations` - Destination catalog  
- `GET /sources/{id}/connected-destinations` - Connection mappings
- `GET /reverse-etl-models` - Warehouse sync models
- `GET /usage/mau` - Event volume metrics (with date range and groupBy)

## 🤝 Contributing

Contributions are welcome! Areas for improvement:

- Additional visualizations (trend analysis, anomaly detection)
- Export formats (Excel, PDF reports)
- Scheduling (automated recurring audits)
- Alerting (notify on configuration changes)
- Multi-workspace comparison views

## 📄 License

MIT License - Free to use for personal and commercial Segment auditing

---

**Built for Segment workspace analysis and optimization**
