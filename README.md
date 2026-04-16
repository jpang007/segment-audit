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
- **Sources Summary**: Track all data sources with connection details
- **Audiences Overview**: View audience distribution and status across spaces
- **Quick Navigation**: Easy access to all audit sections

### 👥 Audiences
- **Audience Catalog**: Complete list with size, status, destinations
- **Space Organization**: Filter and group by Segment spaces
- **Definition Viewer**: Click to see audience logic and SQL
- **Advanced Filtering**: Search, filter by space, sort by various criteria
- **CSV Export**: Download filtered audience data

### 🔌 Sources
- **Source Inventory**: Complete catalog with types, categories, and labels
- **Connection Mapping**: View connected destinations and warehouses
- **Event Schema**: Click sources to see event collections and properties
- **Status Tracking**: Filter by enabled/disabled status
- **CSV Export**: Export source data with connections

### 🚀 Journeys & Campaigns
- **Journey Tracking**: View all Journeys with state and version info
- **Destination Mapping**: See which destinations each journey sends to
- **Status Overview**: Track published vs draft journeys
- **Search & Filter**: Find journeys by name or space
- **CSV Export**: Download journey configurations

### 🔍 Profile Insights
- **Identity Resolution Config**: View ID types, priority, and limits per space
- **Workspace Entitlements**: Check Personas, Profiles, and Linked Audiences features
- **Space Sources**: Inbound data sources feeding into each space
- **Profile Debuggers**: Outbound Personas sources sending to destinations
- **Profile Violations**: Track identity resolution violations and errors
- **CSV Export**: Export identity configs and violations

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

The dashboard collects the following data via Gateway API:

- **Sources**: ID, name, status, connections, labels
- **Audiences**: ID, name, size, status, destinations, definitions
- **Journeys**: Name, state, version, destinations
- **Campaigns**: Name, state, destinations
- **Identity Resolution**: ID types, priority, limits, violations
- **Space Sources**: Inbound sources and outbound debuggers
- **Workspace Entitlements**: Personas, Profiles features

## 🔒 Security Notes

- Gateway tokens expire and must be refreshed periodically
- Tokens are stored in Flask session (not persisted)
- Use the "New Audit" button to enter a fresh token
- Never commit tokens to version control

## 📝 Version History

### Gateway API Version (Current)
- Uses Segment Gateway GraphQL API
- Requires JWT token authentication
- Supports Profile Insights and Violations
- Includes Journeys and Campaigns

### Public API Version (Legacy)
- Available in `backup-public-api` branch
- Uses Segment Public REST API
- Requires API token authentication
- Includes Computed Traits and RETL models

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
