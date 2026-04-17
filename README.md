# Segment Audit Dashboard (Gateway API)

A comprehensive Flask web application for auditing and analyzing Segment workspaces using the Gateway GraphQL API with interactive visual dashboards.

![Dashboard Preview](https://img.shields.io/badge/Flask-3.1.3-blue)
![Python](https://img.shields.io/badge/Python-3.11-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Overview

The Segment Audit Dashboard provides a unified interface to analyze, visualize, and export comprehensive workspace data from Segment. It connects to the **Segment Gateway API (GraphQL)** to collect data across audiences, sources, journeys, and profile insights, presenting everything in an intuitive web interface.

> **Note:** This version uses the Gateway API. A backup of the Public API version is available in the `backup-public-api` branch.

## 🎯 Key Features

### 📊 Dashboard Overview
- **Workspace Summary**: At-a-glance view of sources, audiences, and journeys count
- **Quick Navigation**: Easy access to all audit sections with visual icons
- **Audit Metadata**: Track when audits were run and by which workspace

### 👥 Audiences
- **Complete Catalog**: View all audiences with size, enabled status, and destinations
- **Space Organization**: Filter and group audiences by Segment spaces
- **Definition Viewer**: Click any audience to see SQL definition in modal
- **Destination Tracking**: See which destinations each audience syncs to with counts
- **Advanced Filtering**: Search by name, filter by space, sort by size/status/dates
- **Pagination**: 50 audiences per page for optimal performance
- **CSV Export**: Download filtered audience data with all metadata

### 🔌 Sources
- **Source Inventory**: Complete catalog with source types, categories, and labels
- **Connection Mapping**: View connected destinations and warehouses for each source
- **Event Schema Viewer**: Click any source to see full event collections and properties
- **Status Tracking**: Filter by enabled/disabled status with visual badges
- **Label Analysis**: See all source labels (e.g., environment, team tags)
- **Search & Sort**: Find sources by name, filter by category
- **CSV Export**: Export source data with connection details

### 🚀 Journeys & Campaigns
- **Journey Tracking**: View all Journeys and Campaigns with version history
- **Type Distinction**: Visual differentiation (🚀 for Journeys, 📧 for Campaigns)
- **State Badges**: Published (green), Draft (gray), Live (green) with version numbers
- **Destination Mapping**: See which destinations each journey/campaign sends to
- **Space Organization**: Filter journeys by space, search by name
- **Version Control**: Track current version and max version for each journey
- **Creator Attribution**: See who created and last updated each journey
- **CSV Export**: Download journey configurations with full metadata

### 🔍 Profile Insights
- **Identity Resolution Configuration**:
  - View ID types configured per space (user_id, email, anonymous_id, etc.)
  - See priority order (1, 2, 3) for identity resolution hierarchy
  - Check limits (e.g., "1 ever", "6 monthly") for each identifier type
  - Track which identifiers have been seen in actual data
  - Sorted by space and priority for easy review

- **Workspace Entitlements**:
  - Check if Personas is enabled
  - Verify Profiles feature status
  - See Linked Audiences availability

- **Space Sources Analysis**:
  - **Inbound Sources**: Data sources feeding into each space
  - **Profile Debuggers**: Outbound Personas sources with destination mappings
  - Status tracking (enabled/disabled) for each source
  - Separate tables for clear organization

- **Profile Violations & Errors** (⚠️ Work in Progress):
  - Track identity resolution violations (last 7 days)
  - See dropped identifiers and exceeded limits
  - Filter by space and violation type
  - Limited to 100 most recent violations per space
  
- **CSV Exports**: Separate exports for identity configs, sources, and violations

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Segment workspace with Gateway API access
- Gateway JWT token from Segment app

### Local Installation

1. **Clone the repository**
```bash
git clone https://github.com/jpang007/segment-audit.git
cd segment-audit
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Run the application**
```bash
python app.py
```

4. **Access the dashboard**
Open your browser to `http://localhost:5003`

### Getting Your Gateway Token

1. Log into your Segment workspace at app.segment.com
2. Open browser DevTools (F12)
3. Go to Network tab and filter for "graphql"
4. Look for the `Authorization` header in any request
5. Copy the JWT token (starts with `eyJ...`)

## 📦 Deployment

### Render Deployment

This app is configured for automatic deployment on Render:

1. **Connect Repository**: Link your GitHub repo to Render
2. **Environment**: Render will auto-detect the Flask app
3. **Build Command**: `pip install -r requirements.txt`
4. **Start Command**: `gunicorn app:app`

The app uses environment variable `PORT` which Render provides automatically.

### Configuration Files
- `Procfile`: Gunicorn configuration for production
- `requirements.txt`: Python dependencies
- `render.yaml`: Render service configuration
- `runtime.txt`: Python version specification

## 🛠️ Technology Stack

- **Backend**: Flask 3.1.3
- **API Client**: Requests (GraphQL)
- **Frontend**: Vanilla JavaScript, Chart.js
- **Styling**: Custom CSS
- **Deployment**: Gunicorn, Render

## 📊 Data Collected

The dashboard collects the following data via Gateway GraphQL API:

### Core Workspace Data
- **Sources**: ID, name, slug, status, type, category, labels, connected destinations, connected warehouses, created date
- **Audiences**: ID, name, key, enabled status, size, space, folder, destinations, destination count, definitions (SQL)
- **Spaces**: All Personas spaces in the workspace with metadata

### Engage (Journeys)
- **Journeys**: ID, name, description, state (LIVE/DRAFT), execution status, version info, destinations, action counts (email/SMS/WhatsApp/push), creator, updated dates
- **Campaigns**: Container ID, name, state, version count, destinations, published status, creator, dates

### Profile Insights
- **Identity Resolution Config** (per space):
  - External ID types (user_id, email, anonymous_id, etc.)
  - Priority order for identity resolution
  - Merge limits (e.g., "1 ever", "6 monthly")
  - Seen status (whether identifier has been received)
  
- **Space Sources** (per space):
  - Inbound sources: Name, status, type, category, destinations
  - Profile debuggers (Personas sources): Name, status, destinations

- **Profile Violations** (last 7 days):
  - Violation type, timestamp, source ID, event type
  - External IDs involved, dropped identifiers
  - Limit exceeded events and traits
  - Limited to 100 most recent per space

### Workspace Configuration
- **Entitlements**: Personas enabled, Profiles enabled, Linked Audiences availability
- **Account Type**: Free vs paid tier (if available)
- **Spaces Count**: Total number of Personas spaces

## 🔒 Security Notes

- Gateway tokens expire and must be refreshed periodically
- Tokens are stored in Flask session (not persisted)
- Use the "New Audit" button to enter a fresh token
- Never commit tokens to version control

## 📝 Version History

### Gateway API Version (Current - April 2026)
**Major Features:**
- ✅ Gateway GraphQL API integration
- ✅ JWT token authentication (auto-expires for security)
- ✅ **Journeys & Campaigns** tracking with version control
- ✅ **Profile Insights** with Identity Resolution configuration
- ✅ **Profile Violations** monitoring (last 7 days)
- ✅ **Space Sources** analysis (inbound/outbound)
- ✅ **Workspace Entitlements** visibility
- ✅ Improved audience definitions viewer
- ✅ Event schema exploration
- ✅ Enhanced UI with gradient banners

**What's Different:**
- Uses GraphQL queries instead of REST endpoints
- Session-based token storage (no persistent credentials)
- Real-time identity resolution insights
- Journey/Campaign tracking (Engage features)
- Profile violation monitoring

### Public API Version (Legacy)
**Available in `backup-public-api` branch**

**Features:**
- ⚡ Public REST API integration
- 🔑 API token authentication (persistent)
- 🧮 **Computed Traits** analysis (requires private beta)
- 🔄 **Reverse ETL Models** with SQL queries
- 📈 **Observability** with 14-day event volumes
- 🤖 **AI Export** for LLM analysis
- ⚙️ Connection topology mapping

**When to Use:**
- Need Computed Traits analysis
- Need RETL model SQL queries
- Need historical event volume charts
- Prefer REST API over GraphQL
- Want AI-optimized markdown exports

### Feature Comparison

| Feature | Gateway API ✅ | Public API 💾 |
|---------|---------------|---------------|
| **Core Features** | | |
| Sources & Destinations | ✅ | ✅ |
| Audiences | ✅ | ✅ |
| Audience Definitions | ✅ Enhanced | ✅ Basic |
| **Engage Features** | | |
| Journeys | ✅ | ❌ |
| Campaigns | ✅ | ❌ |
| **Profile/Identity** | | |
| Identity Resolution Config | ✅ | ❌ |
| Profile Violations | ✅ | ❌ |
| Space Sources | ✅ | ❌ |
| **Analytics** | | |
| Computed Traits | ❌ | ✅ |
| RETL Models | ❌ | ✅ |
| Event Volume Charts | ❌ | ✅ |
| **Export** | | |
| CSV Exports | ✅ | ✅ |
| AI Markdown Export | ❌ | ✅ |
| **Authentication** | | |
| JWT Token (Gateway) | ✅ | ❌ |
| API Token (Public) | ❌ | ✅ |

## 🤝 Contributing

This is a personal project for Segment workspace analysis. Feel free to fork and customize for your needs.

## 📄 License

MIT License - Feel free to use and modify as needed.

## 🔗 Links

- [Segment Documentation](https://segment.com/docs/)
- [Gateway API Access](https://app.segment.com/)
- [Render Deployment](https://render.com/)

## ⚠️ Known Limitations

- Profile violations limited to last 7 days
- 100 most recent violations per space
- Some GraphQL fields may require specific workspace entitlements
- Identity resolution priority/limits depend on Profiles/Personas features
