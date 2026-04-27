# Gateway API Audit Dashboard

**Testing Gateway API as a replacement for Public API**

This is a test environment to validate that the Gateway API can provide all necessary audit data without requiring a Public API token.

## Key Differences from Production Dashboard

| Feature | Production (port 5001) | Gateway Test (port 5003) |
|---------|------------------------|--------------------------|
| **Authentication** | Public API token required | Gateway JWT only |
| **Sources** | Public API | Gateway API `AllSources` |
| **Audiences** | Public API + Gateway API | Gateway API `AudiencesAndFolders` |
| **Connections** | Public API | Gateway API `getWorkspaceConnections` |
| **Folder Support** | ❌ | ✅ |
| **Event Volumes** | ✅ Public API | ❌ Not implemented yet |
| **Tracking Plans** | ✅ Public API | ❌ Not implemented yet |

## What Works

✅ **Sources** - Complete list with destinations and warehouses  
✅ **Audiences** - With destinations and folder organization  
✅ **Source-Destination Connections** - Full graph of connections  
✅ **Metadata** - Logos, categories, labels  
✅ **Recommendations** - AI-powered workspace analysis (NEW!)

## New Feature: Workspace Recommendations 💡

Automatically analyzes your workspace and provides actionable insights:
- **Activation Gaps**: Audiences not connected to destinations
- **Underutilized Sources**: Data collected but not used
- **Delivery Issues**: High failure rates
- **Quick Wins**: Low-effort, high-impact improvements

**Two modes:**
1. **Rule-Based Analysis** (free, instant)
2. **AI Summary** (optional, requires Gemini API key)

See [RECOMMENDATIONS_FEATURE.md](RECOMMENDATIONS_FEATURE.md) for full details.

## What's Missing (for now)

❌ Event volume metrics (still needs Public API)  
❌ Tracking plan/schema data (need to implement)  
❌ Computed traits  
❌ Journeys/campaigns  
❌ Delivery metrics  

## How to Run

1. Start the server:
```bash
cd /Users/jpang/gateway-audit-dashboard
python3 gateway_app.py
```

2. Open browser: http://localhost:5003

3. Get your Gateway JWT token:
   - Open Segment UI in browser
   - Open DevTools (F12)
   - Go to Application → Cookies → https://app.segment.com
   - Copy the value of `auth_key` cookie

4. Enter:
   - Workspace slug (e.g., "axios")
   - Gateway JWT token
   - Click "Start Gateway Audit"

## Gateway API Queries Used

### Sources
- `AllSources` - Lists all sources with metadata and connections
- `getWorkspaceConnections` - Complete source-destination graph

### Audiences  
- `AudiencesAndFolders` - Audiences with folder support and destinations
- Folder recursion - Queries each folder to get all audiences

### Spaces
- `GetSpaces` - Lists all Engage spaces

## Benefits of Gateway API

1. **No API Token Setup** - Users don't need to create/find API tokens
2. **Richer Metadata** - Logos, categories, detailed type information
3. **Folder Support** - Audiences can be organized in folders
4. **Real-time** - Direct access to live data
5. **Future Features** - Access to Journeys, Campaigns, and other Engage features

## Next Steps

To make this production-ready:
1. Add event schema queries (`getSourceSchemaEvents`)
2. Add delivery metrics (`getDeliveryMetricsBySource`)
3. Add computed traits support
4. Add Journeys/Campaigns (already working in prod)
5. Handle pagination for large workspaces
6. Add error handling and retry logic

## Architecture

```
gateway_app.py
├── GatewayAPIClient
│   ├── get_workspace_connections()
│   ├── get_all_sources()
│   ├── get_audiences_with_folders()
│   └── get_spaces()
├── Routes
│   ├── / (index)
│   ├── /start-audit
│   ├── /progress
│   ├── /sources
│   └── /audiences
└── Templates
    ├── gateway_index.html
    ├── gateway_progress.html
    ├── gateway_sources.html
    └── gateway_audiences.html
```

## Port Usage

- **5001** - Production audit dashboard (Public API + Gateway API)
- **5002** - GraphQL testing framework (not in use)
- **5003** - Gateway-only audit dashboard (this app)
